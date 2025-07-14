#!/usr/bin/env python3
"""
ESA Mapping and K-Factor Analysis Tool

This script provides specialized analysis for ESA (Electrostatic Analyzer) data:
- Qualitative mapping of spatial impact regions
- Local normalization for temporal visibility
- K-factor estimation from rotation angles and voltage settings
- Comparative analysis across experimental conditions

Usage:
    python esa_mapping_analysis.py [options]

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
from esa_analysis import ESAAnalyzer, ImpactRegion
from data_model import DataManager


def analyze_esa_performance(data_dir: str = "data", output_dir: str = "results"):
    """
    Comprehensive ESA performance analysis.
    
    Args:
        data_dir: Directory containing experimental data
        output_dir: Directory for output files and plots
    """
    print("🔬 ESA Mapping and K-Factor Analysis")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = ESAAnalyzer(data_dir)
    
    # Discover and filter files
    all_files = analyzer.data_manager.discover_files()
    fits_files = [f for f in all_files if f.is_fits_or_map]
    
    print(f"📁 Found {len(fits_files)} FITS/MAP files")
    
    # Filter files with meaningful experimental parameters
    valid_files = []
    for f in fits_files:
        params = f.parameters
        if (params.beam_energy_value and 
            params.esa_voltage_value is not None and 
            params.inner_angle_value is not None):
            valid_files.append(f)
    
    print(f"✅ {len(valid_files)} files have complete experimental parameters")
    
    if not valid_files:
        print("❌ No files with complete parameters found. Cannot perform ESA analysis.")
        return
    
    # Analyze impact regions with local normalization
    print("\n🎯 Analyzing spatial impact regions...")
    regions = analyzer.analyze_impact_regions(valid_files)
    
    if not regions:
        print("❌ No valid impact regions found")
        return
    
    print(f"✅ Found {len(regions)} valid impact regions")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate spatial mapping plots
    print("\n🗺️  Generating spatial mapping visualizations...")
    
    # Plot by beam energy
    analyzer.plot_spatial_mapping(
        regions, 
        group_by='beam_energy',
        save_path=os.path.join(output_dir, 'spatial_mapping_by_energy.png')
    )
    
    # Plot by ESA voltage
    analyzer.plot_spatial_mapping(
        regions, 
        group_by='esa_voltage',
        save_path=os.path.join(output_dir, 'spatial_mapping_by_voltage.png')
    )
    
    # Plot by rotation angle
    analyzer.plot_spatial_mapping(
        regions, 
        group_by='rotation_angle',
        save_path=os.path.join(output_dir, 'spatial_mapping_by_angle.png')
    )
    
    # Estimate k-factor
    print("\n⚡ Estimating ESA k-factor...")
    k_factor_results = analyzer.estimate_k_factor(regions)
    
    if "error" in k_factor_results:
        print(f"❌ K-factor estimation failed: {k_factor_results['error']}")
    else:
        print("✅ K-factor estimation successful!")
        print(f"   Mean k-factor: {k_factor_results['k_factor_mean']:.4f}")
        print(f"   Standard deviation: {k_factor_results['k_factor_std']:.4f}")
        print(f"   Range: {k_factor_results['k_factor_range'][0]:.4f} - {k_factor_results['k_factor_range'][1]:.4f}")
        print(f"   Based on {k_factor_results['num_measurements']} measurements")
    
    # Generate detailed analysis plots
    print("\n📊 Creating detailed analysis plots...")
    create_detailed_analysis_plots(regions, k_factor_results, output_dir)
    
    # Generate comprehensive report
    print("\n📝 Generating analysis report...")
    report_path = analyzer.generate_esa_report(k_factor_results, regions, 
                                             os.path.join(output_dir, 'esa_analysis_report.md'))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📋 ANALYSIS SUMMARY")
    print("=" * 50)
    
    # Experimental conditions summary
    beam_energies = sorted(set(r.beam_energy for r in regions))
    esa_voltages = sorted(set(r.esa_voltage for r in regions))
    rotation_angles = sorted(set(r.rotation_angle for r in regions if r.rotation_angle is not None))

    # Count angle ranges
    angle_ranges = [r for r in regions if r.is_angle_range]
    single_angles = [r for r in regions if not r.is_angle_range and r.rotation_angle is not None]

    print(f"🔋 Beam energies tested: {beam_energies} eV")
    print(f"⚡ ESA voltages tested: {esa_voltages} V")
    print(f"🔄 Rotation angles tested: {rotation_angles}°")
    print(f"📐 Files with angle ranges: {len(angle_ranges)}")
    print(f"📍 Files with single angles: {len(single_angles)}")

    if angle_ranges:
        print("   Angle ranges found:")
        for region in angle_ranges:
            if region.rotation_angle_range:
                print(f"     - {region.filename}: {region.rotation_angle_range[0]:.1f}° to {region.rotation_angle_range[1]:.1f}°")
    
    # Spatial distribution summary
    x_positions = [r.centroid_x for r in regions]
    y_positions = [r.centroid_y for r in regions]
    
    print(f"\n🎯 Spatial impact distribution:")
    print(f"   X-range: {min(x_positions):.1f} - {max(x_positions):.1f} pixels")
    print(f"   Y-range: {min(y_positions):.1f} - {max(y_positions):.1f} pixels")
    print(f"   Mean position: ({np.mean(x_positions):.1f}, {np.mean(y_positions):.1f})")
    
    # Data quality summary
    snr_values = [r.signal_to_noise for r in regions]
    intensities = [r.peak_intensity for r in regions]
    
    print(f"\n📈 Data quality metrics:")
    print(f"   Signal-to-noise ratio: {np.mean(snr_values):.2f} ± {np.std(snr_values):.2f}")
    print(f"   Peak intensity range: {min(intensities):.3f} - {max(intensities):.3f}")
    
    print(f"\n📁 Results saved to: {output_dir}")
    print(f"📄 Detailed report: {report_path}")


def create_detailed_analysis_plots(regions: list, k_factor_results: dict, output_dir: str):
    """Create detailed analysis plots for ESA characterization."""
    
    # K-factor vs experimental parameters
    if "error" not in k_factor_results and k_factor_results.get('measurements'):
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        measurements = k_factor_results['measurements']
        
        # K-factor vs beam energy
        beam_energies = [m.impact_region.beam_energy for m in measurements if m.k_factor_estimate]
        k_factors = [m.k_factor_estimate for m in measurements if m.k_factor_estimate]
        
        if beam_energies and k_factors:
            axes[0, 0].scatter(beam_energies, k_factors, alpha=0.7)
            axes[0, 0].set_xlabel('Beam Energy (eV)')
            axes[0, 0].set_ylabel('K-Factor')
            axes[0, 0].set_title('K-Factor vs Beam Energy')
            axes[0, 0].grid(True, alpha=0.3)
        
        # K-factor vs ESA voltage
        esa_voltages = [abs(m.impact_region.esa_voltage) for m in measurements if m.k_factor_estimate]
        
        if esa_voltages and k_factors:
            axes[0, 1].scatter(esa_voltages, k_factors, alpha=0.7, color='orange')
            axes[0, 1].set_xlabel('|ESA Voltage| (V)')
            axes[0, 1].set_ylabel('K-Factor')
            axes[0, 1].set_title('K-Factor vs ESA Voltage')
            axes[0, 1].grid(True, alpha=0.3)
        
        # Deflection correlation
        theoretical = [m.theoretical_deflection for m in measurements]
        measured = [m.measured_deflection for m in measurements]
        
        if theoretical and measured:
            axes[1, 0].scatter(theoretical, measured, alpha=0.7, color='green')
            axes[1, 0].plot([min(theoretical), max(theoretical)], 
                           [min(theoretical), max(theoretical)], 'r--', alpha=0.5)
            axes[1, 0].set_xlabel('Theoretical Deflection')
            axes[1, 0].set_ylabel('Measured Deflection')
            axes[1, 0].set_title('Deflection Correlation')
            axes[1, 0].grid(True, alpha=0.3)
        
        # K-factor distribution
        if k_factors:
            axes[1, 1].hist(k_factors, bins=min(10, len(k_factors)), alpha=0.7, color='purple')
            axes[1, 1].axvline(np.mean(k_factors), color='red', linestyle='--', 
                              label=f'Mean: {np.mean(k_factors):.4f}')
            axes[1, 1].set_xlabel('K-Factor')
            axes[1, 1].set_ylabel('Frequency')
            axes[1, 1].set_title('K-Factor Distribution')
            axes[1, 1].legend()
            axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'k_factor_analysis.png'), dpi=300, bbox_inches='tight')
        plt.show()
    
    # Intensity vs position correlation
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Peak intensity vs X position
    x_positions = [r.centroid_x for r in regions]
    intensities = [r.peak_intensity for r in regions]
    beam_energies = [r.beam_energy for r in regions]
    
    scatter = axes[0].scatter(x_positions, intensities, c=beam_energies, 
                             cmap='viridis', alpha=0.7)
    axes[0].set_xlabel('X Position (pixels)')
    axes[0].set_ylabel('Peak Intensity')
    axes[0].set_title('Intensity vs X Position')
    axes[0].grid(True, alpha=0.3)
    plt.colorbar(scatter, ax=axes[0], label='Beam Energy (eV)')
    
    # Signal-to-noise vs region area
    snr_values = [r.signal_to_noise for r in regions]
    areas = [r.region_area for r in regions]
    
    axes[1].scatter(areas, snr_values, alpha=0.7, color='orange')
    axes[1].set_xlabel('Region Area (pixels)')
    axes[1].set_ylabel('Signal-to-Noise Ratio')
    axes[1].set_title('Data Quality vs Region Size')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'quality_analysis.png'), dpi=300, bbox_inches='tight')
    plt.show()


def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(description="ESA Mapping and K-Factor Analysis Tool")
    parser.add_argument("--data-dir", default="data", help="Data directory path")
    parser.add_argument("--output-dir", default="results", help="Output directory path")
    parser.add_argument("--min-snr", type=float, default=2.0, 
                       help="Minimum signal-to-noise ratio for valid regions")
    
    args = parser.parse_args()
    
    try:
        analyze_esa_performance(args.data_dir, args.output_dir)
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
