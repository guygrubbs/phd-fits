#!/usr/bin/env python3
"""
Integrated Map Analysis Tool

This tool creates an integrated count rate map by normalizing each map file to a 
common count rate and summing all data collection periods together to show 
count rate per area over the entire test collection.

Usage:
    python integrated_map_tool.py [options]

Author: XDL Processing Project
"""

import sys
import os
import argparse
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Add src directory to path
sys.path.append('src')
from integrated_map_analysis import IntegratedMapAnalyzer
from data_model import DataManager


def analyze_integrated_maps(data_dir: str = "data", output_dir: str = "results",
                          beam_energy: float = None, target_rate: float = 100.0):
    """
    Perform integrated map analysis with rate normalization.
    
    Args:
        data_dir: Directory containing experimental data
        output_dir: Directory for output files
        beam_energy: Specific beam energy to analyze (optional)
        target_rate: Target count rate for normalization (counts/s)
    """
    print("🗺️  Integrated Count Rate Map Analysis")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = IntegratedMapAnalyzer(data_dir)
    analyzer.target_count_rate = target_rate
    
    # Find map files
    print(f"🔍 Searching for map files...")
    map_files = analyzer.find_map_files(beam_energy)
    
    if not map_files:
        print("❌ No map files found for integration")
        print("\nRequirements:")
        print("  - FITS or MAP files with image data")
        print("  - Files with beam energy information")
        if beam_energy:
            print(f"  - Beam energy ≈ {beam_energy} eV")
        return
    
    print(f"✅ Found {len(map_files)} map files for integration")
    
    # Show file breakdown
    print(f"\n📋 File breakdown:")
    beam_energies = {}
    esa_voltages = {}
    angles = {}
    
    for f in map_files:
        params = f.parameters
        
        # Count beam energies
        energy = params.beam_energy_value
        if energy not in beam_energies:
            beam_energies[energy] = 0
        beam_energies[energy] += 1
        
        # Count ESA voltages
        voltage = params.esa_voltage_value
        if voltage is not None:
            if voltage not in esa_voltages:
                esa_voltages[voltage] = 0
            esa_voltages[voltage] += 1
        
        # Count angles
        angle = params.inner_angle_value
        if angle is not None:
            if angle not in angles:
                angles[angle] = 0
            angles[angle] += 1
    
    print(f"   Beam energies: {dict(sorted(beam_energies.items()))}")
    print(f"   ESA voltages: {dict(sorted(esa_voltages.items()))}")
    print(f"   Inner angles: {dict(sorted(angles.items()))}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Analyze contributions
    print(f"\n🔬 Analyzing individual map contributions...")
    contributions = analyzer.analyze_map_contributions(map_files)
    
    if not contributions:
        print("❌ No valid contributions found")
        print("   Check that map files contain valid image data")
        return
    
    print(f"✅ Successfully analyzed {len(contributions)} contributions")
    
    # Show rate normalization summary
    count_rates = [c.count_rate for c in contributions]
    collection_times = [c.estimated_collection_time for c in contributions]
    
    print(f"\n📊 Rate normalization summary:")
    print(f"   Target rate: {target_rate:.0f} counts/s")
    print(f"   Original rates: {min(count_rates):.1f} - {max(count_rates):.1f} counts/s")
    print(f"   Mean rate: {np.mean(count_rates):.1f} ± {np.std(count_rates):.1f} counts/s")
    print(f"   Collection times: {min(collection_times):.1f} - {max(collection_times):.1f} s")
    print(f"   Total collection time: {sum(collection_times):.1f} s")
    
    # Create integrated map
    print(f"\n🗺️  Creating integrated count rate map...")
    integrated_map, metadata = analyzer.create_integrated_map(contributions)
    
    print(f"✅ Integration complete!")
    print(f"   Peak integrated rate: {metadata['peak_integrated_rate']:.1f} counts/s")
    print(f"   Total integrated counts: {metadata['total_integrated_counts']:,.0f}")
    print(f"   Active pixels: {metadata['active_pixels']:,} / {np.prod(integrated_map.shape):,} "
          f"({metadata['active_pixels']/np.prod(integrated_map.shape)*100:.1f}%)")
    
    # Create visualization
    plot_filename = f"integrated_count_rate_map"
    if beam_energy:
        plot_filename += f"_E{beam_energy:.0f}eV"
    plot_filename += f"_rate{target_rate:.0f}.png"
    save_path = os.path.join(output_dir, plot_filename)
    
    try:
        analyzer.plot_integrated_map(integrated_map, metadata, contributions, save_path)
        print(f"📈 Plot saved: {plot_filename}")
    except Exception as e:
        print(f"❌ Error creating plot: {e}")
        return
    
    # Generate detailed report
    report_filename = f"integrated_map_analysis"
    if beam_energy:
        report_filename += f"_E{beam_energy:.0f}eV"
    report_filename += f"_rate{target_rate:.0f}.md"
    report_path = os.path.join(output_dir, report_filename)
    
    try:
        analyzer.generate_integration_report(integrated_map, metadata, contributions, report_path)
        print(f"📄 Report saved: {report_filename}")
    except Exception as e:
        print(f"❌ Error creating report: {e}")
    
    # Print final summary
    print_integration_summary(metadata, contributions)


def print_integration_summary(metadata, contributions):
    """Print a summary of the integration results."""
    
    print(f"\n📋 Integration Summary:")
    print(f"   Files integrated: {metadata['total_files']}")
    print(f"   Total collection time: {metadata['total_collection_time']:.1f} seconds")
    print(f"   Beam energies: {', '.join(f'{e:.0f} eV' for e in metadata['beam_energies'])}")
    print(f"   ESA voltages: {', '.join(f'{v:.0f} V' for v in metadata['esa_voltages'])}")
    
    if metadata['elevation_range']:
        elev_range = metadata['elevation_range']
        print(f"   Elevation coverage: {elev_range[0]:.1f}° to {elev_range[1]:.1f}° "
              f"({elev_range[1] - elev_range[0]:.1f}° range)")
    
    if metadata['azimuth_range']:
        azim_range = metadata['azimuth_range']
        print(f"   Azimuth coverage: {azim_range[0]:.1f}° to {azim_range[1]:.1f}° "
              f"({azim_range[1] - azim_range[0]:.1f}° range)")
    
    # Data quality metrics
    total_raw_counts = sum(c.total_counts for c in contributions)
    mean_snr = np.mean([c.signal_to_noise for c in contributions])
    mean_density = np.mean([c.data_density for c in contributions])
    
    print(f"   Total raw counts: {total_raw_counts:,.0f}")
    print(f"   Mean SNR: {mean_snr:.1f}")
    print(f"   Mean data density: {mean_density:.1%}")


def list_available_maps(data_dir: str = "data"):
    """List available map files for integration."""
    
    print("🔍 Available Map Files for Integration")
    print("=" * 40)
    
    analyzer = IntegratedMapAnalyzer(data_dir)
    map_files = analyzer.find_map_files()
    
    if not map_files:
        print("❌ No map files found")
        return
    
    print(f"Found {len(map_files)} map files:")
    
    # Group by beam energy
    energy_groups = {}
    for f in map_files:
        energy = f.parameters.beam_energy_value
        if energy not in energy_groups:
            energy_groups[energy] = []
        energy_groups[energy].append(f)
    
    for energy, files in sorted(energy_groups.items()):
        print(f"\n📊 Beam Energy: {energy:.0f} eV ({len(files)} files)")
        
        # Show parameter distribution
        voltages = set()
        angles = set()
        
        for f in files:
            params = f.parameters
            if params.esa_voltage_value is not None:
                voltages.add(params.esa_voltage_value)
            if params.inner_angle_value is not None:
                angles.add(params.inner_angle_value)
        
        print(f"   ESA voltages: {sorted(voltages)} V")
        print(f"   Inner angles: {sorted(angles)}°")
        
        # Show first few files as examples
        print(f"   Example files:")
        for f in files[:3]:
            params = f.parameters
            angle_str = f"{params.inner_angle_value:.0f}°" if params.inner_angle_value else "N/A"
            voltage_str = f"{params.esa_voltage_value:.0f}V" if params.esa_voltage_value else "N/A"
            print(f"     - {f.filename} (Angle: {angle_str}, ESA: {voltage_str})")
        
        if len(files) > 3:
            print(f"     ... and {len(files) - 3} more files")


def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(description="Integrated Count Rate Map Analysis Tool")
    parser.add_argument("--data-dir", default="data", help="Data directory path")
    parser.add_argument("--output-dir", default="results", help="Output directory path")
    parser.add_argument("--beam-energy", type=float, help="Specific beam energy to analyze (eV)")
    parser.add_argument("--target-rate", type=float, default=100.0,
                       help="Target count rate for normalization (counts/s)")
    parser.add_argument("--list-only", action='store_true',
                       help="Only list available map files without analysis")
    
    args = parser.parse_args()
    
    if args.list_only:
        list_available_maps(args.data_dir)
    else:
        try:
            analyze_integrated_maps(
                args.data_dir,
                args.output_dir,
                args.beam_energy,
                args.target_rate
            )
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
