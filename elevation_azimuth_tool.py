#!/usr/bin/env python3
"""
Elevation vs Azimuth Analysis Tool

This tool creates elevation vs azimuth plots showing count rates at different
angular positions, with proper normalization for varying data collection rates.

Usage:
    python elevation_azimuth_tool.py [options]

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
from elevation_azimuth_analysis import ElevationAzimuthAnalyzer
from data_model import DataManager


def analyze_elevation_azimuth(data_dir: str = "data", output_dir: str = "results",
                            beam_energy: float = None, plot_type: str = 'count_rate'):
    """
    Perform elevation vs azimuth analysis with rate normalization.
    
    Args:
        data_dir: Directory containing experimental data
        output_dir: Directory for output files
        beam_energy: Specific beam energy to analyze (optional)
        plot_type: Type of plot ('count_rate', 'normalized_intensity', 'total_counts')
    """
    print("🌐 Elevation vs Azimuth Analysis with Rate Normalization")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = ElevationAzimuthAnalyzer(data_dir)
    
    # Find angular datasets
    print(f"🔍 Searching for angular datasets...")
    energy_groups = analyzer.find_angular_datasets(beam_energy)
    
    if not energy_groups:
        print("❌ No suitable datasets found for elevation vs azimuth analysis")
        print("\nRequirements:")
        print("  - Files with beam energy and ESA voltage")
        print("  - Angular information (inner angle or horizontal values)")
        print("  - Multiple measurements for comparison")
        return
    
    print(f"✅ Found angular datasets for beam energies: {list(energy_groups.keys())} eV")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Analyze each beam energy
    for energy, files in energy_groups.items():
        print(f"\n📊 Analyzing Beam Energy: {energy:.0f} eV")
        print(f"   Files: {len(files)}")
        
        # Show file details
        print(f"   📋 File breakdown:")
        angle_info = {}
        for f in files:
            params = f.parameters
            elev = params.inner_angle_value
            azim = params.horizontal_value_num
            voltage = params.esa_voltage_value
            
            key = f"E{elev:.0f}°" if elev is not None else "E?"
            if azim is not None:
                key += f"_A{azim:.0f}°"
            key += f"_V{voltage:.0f}V"
            
            if key not in angle_info:
                angle_info[key] = 0
            angle_info[key] += 1
        
        for key, count in sorted(angle_info.items()):
            print(f"      {key}: {count} file(s)")
        
        # Analyze measurements with rate normalization
        print(f"   🔬 Analyzing angular measurements...")
        measurements = analyzer.analyze_angular_measurements(files)
        
        if not measurements:
            print("   ❌ No valid angular measurements found")
            continue
        
        print(f"   ✅ Found {len(measurements)} valid measurements")
        
        # Show rate normalization summary
        collection_times = [m.collection_time for m in measurements if m.collection_time]
        count_rates = [m.count_rate for m in measurements if m.count_rate]
        
        if collection_times:
            print(f"   ⏱️  Collection times: {min(collection_times):.1f} - {max(collection_times):.1f} s")
        
        if count_rates:
            print(f"   📈 Count rates: {min(count_rates):.1f} - {max(count_rates):.1f} counts/s")
        
        # Show angular coverage
        elevations = [m.elevation_angle for m in measurements if m.elevation_angle is not None]
        azimuths = [m.azimuth_angle for m in measurements if m.azimuth_angle is not None]
        
        if elevations:
            print(f"   📐 Elevation range: {min(elevations):.1f}° - {max(elevations):.1f}°")
        if azimuths:
            print(f"   🧭 Azimuth range: {min(azimuths):.1f}° - {max(azimuths):.1f}°")
        
        # Create elevation vs azimuth plot
        plot_filename = f"elevation_azimuth_E{energy:.0f}eV_{plot_type}.png"
        save_path = os.path.join(output_dir, plot_filename)
        
        try:
            analyzer.plot_elevation_azimuth_map(measurements, energy, 
                                              plot_type=plot_type, save_path=save_path)
            print(f"   📈 Plot saved: {plot_filename}")
        except Exception as e:
            print(f"   ❌ Error creating plot: {e}")
            continue
        
        # Generate detailed report
        report_filename = f"elevation_azimuth_E{energy:.0f}eV.md"
        report_path = os.path.join(output_dir, report_filename)
        
        try:
            analyzer.generate_angular_report(measurements, energy, report_path)
            print(f"   📄 Report saved: {report_filename}")
        except Exception as e:
            print(f"   ❌ Error creating report: {e}")
        
        # Print measurement summary
        print_measurement_summary(measurements)


def print_measurement_summary(measurements):
    """Print a summary of the measurements."""
    
    print("   📋 Measurement Summary:")
    
    # Rate statistics
    count_rates = [m.count_rate for m in measurements if m.count_rate is not None]
    if count_rates:
        print(f"      Mean count rate: {np.mean(count_rates):.1f} ± {np.std(count_rates):.1f} counts/s")
        print(f"      Rate range: {min(count_rates):.1f} - {max(count_rates):.1f} counts/s")
    
    # Spatial distribution
    x_positions = [m.centroid_x for m in measurements]
    y_positions = [m.centroid_y for m in measurements]
    
    if x_positions and y_positions:
        print(f"      Spatial coverage: X({min(x_positions):.0f}-{max(x_positions):.0f}), "
              f"Y({min(y_positions):.0f}-{max(y_positions):.0f}) pixels")
    
    # Signal quality
    snr_values = [m.signal_to_noise for m in measurements]
    if snr_values:
        print(f"      Signal quality: SNR {np.mean(snr_values):.1f} ± {np.std(snr_values):.1f}")


def list_available_datasets(data_dir: str = "data"):
    """List available datasets for elevation vs azimuth analysis."""
    
    print("🔍 Available Datasets for Elevation vs Azimuth Analysis")
    print("=" * 60)
    
    analyzer = ElevationAzimuthAnalyzer(data_dir)
    energy_groups = analyzer.find_angular_datasets()
    
    if not energy_groups:
        print("❌ No suitable datasets found")
        return
    
    for energy, files in energy_groups.items():
        print(f"\n📊 Beam Energy: {energy:.0f} eV ({len(files)} files)")
        
        # Analyze angular parameters
        elevations = set()
        azimuths = set()
        voltages = set()
        
        for f in files:
            params = f.parameters
            if params.inner_angle_value is not None:
                elevations.add(params.inner_angle_value)
            if params.horizontal_value_num is not None:
                azimuths.add(params.horizontal_value_num)
            if params.esa_voltage_value is not None:
                voltages.add(params.esa_voltage_value)
        
        print(f"   Elevation angles: {sorted(elevations)}°")
        print(f"   Azimuth angles: {sorted(azimuths)}")
        print(f"   ESA voltages: {sorted(voltages)} V")
        
        # Estimate potential for 2D plotting
        if len(elevations) > 1 and len(azimuths) > 1:
            print(f"   ✅ Excellent for 2D elevation/azimuth plot ({len(elevations)}×{len(azimuths)} grid)")
        elif len(elevations) > 1:
            print(f"   ✅ Good for elevation sweep plot ({len(elevations)} points)")
        elif len(azimuths) > 1:
            print(f"   ✅ Good for azimuth sweep plot ({len(azimuths)} points)")
        else:
            print(f"   ⚠️  Limited angular variation")


def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(description="Elevation vs Azimuth Analysis Tool")
    parser.add_argument("--data-dir", default="data", help="Data directory path")
    parser.add_argument("--output-dir", default="results", help="Output directory path")
    parser.add_argument("--beam-energy", type=float, help="Specific beam energy to analyze (eV)")
    parser.add_argument("--plot-type", choices=['count_rate', 'normalized_intensity', 'total_counts'],
                       default='count_rate', help="Type of intensity plot")
    parser.add_argument("--list-only", action='store_true',
                       help="Only list available datasets without analysis")
    
    args = parser.parse_args()
    
    if args.list_only:
        list_available_datasets(args.data_dir)
    else:
        try:
            analyze_elevation_azimuth(
                args.data_dir,
                args.output_dir,
                args.beam_energy,
                args.plot_type
            )
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
