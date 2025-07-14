#!/usr/bin/env python3
"""
Angular Resolution Analysis Tool

This tool creates elevation/azimuth resolution plots when beam energy and one 
rotation angle are held constant while ESA voltage and another rotation angle 
are varied.

Usage:
    python angular_resolution_tool.py [options]

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
from angular_resolution_analysis import AngularResolutionAnalyzer, AngularResolutionData
from data_model import DataManager


def analyze_angular_resolution(data_dir: str = "data", output_dir: str = "results",
                             beam_energy: float = None, fixed_angle: float = None,
                             min_voltage_points: int = 2, min_angle_points: int = 1):
    """
    Perform angular resolution analysis.
    
    Args:
        data_dir: Directory containing experimental data
        output_dir: Directory for output files
        beam_energy: Specific beam energy to analyze (optional)
        fixed_angle: Specific angle to hold constant (optional)
        min_voltage_points: Minimum ESA voltage variations required
        min_angle_points: Minimum angle variations required
    """
    print("🔬 ESA Angular Resolution Analysis")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = AngularResolutionAnalyzer(data_dir)
    
    # Find potential datasets
    print(f"🔍 Searching for resolution datasets...")
    datasets = analyzer.find_resolution_datasets(
        min_voltage_points=min_voltage_points,
        min_angle_points=min_angle_points
    )
    
    if not datasets:
        print("❌ No suitable datasets found for angular resolution analysis")
        print("\nRequirements:")
        print(f"  - At least {min_voltage_points} different ESA voltages")
        print(f"  - At least {min_angle_points} different angle conditions")
        print("  - Beam energy and one angle parameter held constant")
        return
    
    print(f"✅ Found {len(datasets)} potential resolution datasets")
    
    # Filter by user criteria if specified
    if beam_energy is not None:
        datasets = [d for d in datasets if abs(d.fixed_beam_energy - beam_energy) < 1.0]
        print(f"🎯 Filtered to {len(datasets)} datasets with beam energy ≈ {beam_energy} eV")
    
    if fixed_angle is not None:
        datasets = [d for d in datasets if abs(d.fixed_angle_value - fixed_angle) < 1.0]
        print(f"🎯 Filtered to {len(datasets)} datasets with fixed angle ≈ {fixed_angle}°")
    
    if not datasets:
        print("❌ No datasets match the specified criteria")
        return
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Analyze each dataset
    for i, dataset in enumerate(datasets):
        print(f"\n📊 Analyzing Dataset {i+1}/{len(datasets)}")
        print(f"   Beam Energy: {dataset.fixed_beam_energy:.0f} eV")
        print(f"   Fixed {dataset.fixed_angle_parameter}: {dataset.fixed_angle_value:.1f}°")
        print(f"   ESA Voltages: {dataset.varying_esa_voltages}")
        print(f"   Varying parameter: {dataset.varying_angle_parameter}")
        
        # Analyze the dataset
        analyzed_dataset = analyzer.analyze_angular_resolution(dataset)
        
        if not analyzed_dataset.impact_regions:
            print("   ❌ No impact regions found for this dataset")
            continue
        
        print(f"   ✅ Found {len(analyzed_dataset.impact_regions)} impact regions")
        
        # Create resolution plot
        plot_filename = f"angular_resolution_E{dataset.fixed_beam_energy:.0f}eV_A{dataset.fixed_angle_value:.0f}deg.png"
        save_path = os.path.join(output_dir, plot_filename)
        
        try:
            analyzer.plot_elevation_azimuth_resolution(analyzed_dataset, save_path)
            print(f"   📈 Resolution plot saved: {plot_filename}")
        except Exception as e:
            print(f"   ❌ Error creating plot: {e}")
            continue
        
        # Generate summary report
        report_filename = f"angular_resolution_E{dataset.fixed_beam_energy:.0f}eV_A{dataset.fixed_angle_value:.0f}deg.md"
        report_path = os.path.join(output_dir, report_filename)
        
        generate_resolution_report(analyzed_dataset, report_path)
        print(f"   📄 Report saved: {report_filename}")
        
        # Print summary statistics
        print_dataset_summary(analyzed_dataset)


def generate_resolution_report(dataset: AngularResolutionData, output_path: str):
    """Generate a detailed resolution analysis report."""
    
    with open(output_path, 'w') as f:
        f.write("# Angular Resolution Analysis Report\n\n")
        
        # Dataset parameters
        f.write("## Dataset Parameters\n\n")
        f.write(f"**Fixed Beam Energy:** {dataset.fixed_beam_energy:.0f} eV\n")
        f.write(f"**Fixed {dataset.fixed_angle_parameter}:** {dataset.fixed_angle_value:.1f}°\n")
        f.write(f"**Varying ESA Voltages:** {', '.join(f'{v:.0f}V' for v in dataset.varying_esa_voltages)}\n")
        f.write(f"**Varying {dataset.varying_angle_parameter}:** {', '.join(f'{a:.1f}°' for a in dataset.varying_angles)}\n")
        f.write(f"**Number of Impact Regions:** {len(dataset.impact_regions)}\n\n")
        
        # K-factor analysis
        f.write("## K-Factor Analysis\n\n")
        k_factors = []
        for (voltage, angle), region in dataset.impact_regions.items():
            k_factor = dataset.fixed_beam_energy / abs(voltage)
            k_factors.append(k_factor)
        
        if k_factors:
            f.write(f"**Mean K-Factor:** {np.mean(k_factors):.2f} eV/V\n")
            f.write(f"**K-Factor Range:** {np.min(k_factors):.2f} - {np.max(k_factors):.2f} eV/V\n")
            f.write(f"**K-Factor Std Dev:** {np.std(k_factors):.3f} eV/V\n\n")
        
        # Resolution analysis
        if dataset.angular_resolution_map is not None:
            f.write("## Angular Resolution Analysis\n\n")
            valid_res = dataset.angular_resolution_map[~np.isnan(dataset.angular_resolution_map)]
            if len(valid_res) > 0:
                f.write(f"**Mean Angular Resolution:** {np.mean(valid_res):.2f}%\n")
                f.write(f"**Resolution Range:** {np.min(valid_res):.2f}% - {np.max(valid_res):.2f}%\n")
                f.write(f"**Resolution Std Dev:** {np.std(valid_res):.3f}%\n\n")
        
        # Signal quality analysis
        if dataset.spatial_resolution_map is not None:
            f.write("## Signal Quality Analysis\n\n")
            valid_snr = dataset.spatial_resolution_map[~np.isnan(dataset.spatial_resolution_map)]
            if len(valid_snr) > 0:
                f.write(f"**Mean Signal-to-Noise Ratio:** {np.mean(valid_snr):.1f}\n")
                f.write(f"**SNR Range:** {np.min(valid_snr):.1f} - {np.max(valid_snr):.1f}\n")
                f.write(f"**SNR Std Dev:** {np.std(valid_snr):.2f}\n\n")
        
        # Detailed measurements
        f.write("## Detailed Measurements\n\n")
        f.write("| ESA Voltage | Angle | Centroid (X,Y) | Angular Res (%) | SNR | K-Factor |\n")
        f.write("|-------------|-------|----------------|-----------------|-----|----------|\n")
        
        for (voltage, angle), region in sorted(dataset.impact_regions.items()):
            angular_res = np.sqrt(region.region_area) / 1024 * 100
            k_factor = dataset.fixed_beam_energy / abs(voltage)
            
            f.write(f"| {voltage:.0f}V | {angle:.1f}° | "
                   f"({region.centroid_x:.1f}, {region.centroid_y:.1f}) | "
                   f"{angular_res:.2f}% | {region.signal_to_noise:.1f} | {k_factor:.2f} |\n")


def print_dataset_summary(dataset: AngularResolutionData):
    """Print a summary of the dataset analysis."""
    
    print("   📋 Analysis Summary:")
    
    # K-factor statistics
    k_factors = []
    angular_resolutions = []
    snr_values = []
    
    for (voltage, angle), region in dataset.impact_regions.items():
        k_factor = dataset.fixed_beam_energy / abs(voltage)
        k_factors.append(k_factor)
        
        angular_res = np.sqrt(region.region_area) / 1024 * 100
        angular_resolutions.append(angular_res)
        
        snr_values.append(region.signal_to_noise)
    
    if k_factors:
        print(f"      K-Factor: {np.mean(k_factors):.2f} ± {np.std(k_factors):.3f} eV/V")
    
    if angular_resolutions:
        print(f"      Angular Resolution: {np.mean(angular_resolutions):.2f} ± {np.std(angular_resolutions):.2f}%")
    
    if snr_values:
        print(f"      Signal-to-Noise: {np.mean(snr_values):.1f} ± {np.std(snr_values):.1f}")


def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(description="ESA Angular Resolution Analysis Tool")
    parser.add_argument("--data-dir", default="data", help="Data directory path")
    parser.add_argument("--output-dir", default="results", help="Output directory path")
    parser.add_argument("--beam-energy", type=float, help="Specific beam energy to analyze (eV)")
    parser.add_argument("--fixed-angle", type=float, help="Specific angle to hold constant (degrees)")
    parser.add_argument("--min-voltages", type=int, default=2, 
                       help="Minimum number of ESA voltage points required")
    parser.add_argument("--min-angles", type=int, default=1,
                       help="Minimum number of angle variations required")
    parser.add_argument("--list-only", action='store_true',
                       help="Only list available datasets without analysis")
    
    args = parser.parse_args()
    
    if args.list_only:
        # Just list available datasets
        analyzer = AngularResolutionAnalyzer(args.data_dir)
        datasets = analyzer.find_resolution_datasets(args.min_voltages, args.min_angles)
        
        print(f"Found {len(datasets)} potential angular resolution datasets:")
        for i, dataset in enumerate(datasets):
            print(f"\n{i+1}. Beam Energy: {dataset.fixed_beam_energy:.0f} eV")
            print(f"   Fixed {dataset.fixed_angle_parameter}: {dataset.fixed_angle_value:.1f}°")
            print(f"   ESA Voltages: {dataset.varying_esa_voltages}")
            print(f"   Varying parameter: {dataset.varying_angle_parameter}")
    else:
        # Perform full analysis
        try:
            analyze_angular_resolution(
                args.data_dir, 
                args.output_dir,
                args.beam_energy,
                args.fixed_angle,
                args.min_voltages,
                args.min_angles
            )
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
