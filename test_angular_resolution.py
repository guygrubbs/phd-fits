#!/usr/bin/env python3
"""
Test script for angular resolution analysis with constant angle handling.
"""

import sys
sys.path.append('src')
from angular_resolution_analysis import AngularResolutionAnalyzer
from data_model import DataManager

def test_angular_resolution():
    """Test angular resolution analysis with improved constant angle handling."""
    
    print("🔬 Testing Angular Resolution Analysis")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = AngularResolutionAnalyzer("data")
    
    # Discover all files first
    all_files = analyzer.data_manager.discover_files()
    fits_files = [f for f in all_files if f.is_fits_or_map]
    
    print(f"📁 Found {len(fits_files)} FITS/MAP files total")
    
    # Analyze file parameters
    files_with_energy_voltage = []
    files_with_angles = []
    files_without_angles = []
    
    for f in fits_files:
        params = f.parameters
        if params.beam_energy_value and params.esa_voltage_value is not None:
            files_with_energy_voltage.append(f)
            
            if params.inner_angle_value is not None:
                files_with_angles.append(f)
            else:
                files_without_angles.append(f)
    
    print(f"✅ {len(files_with_energy_voltage)} files have beam energy and ESA voltage")
    print(f"📐 {len(files_with_angles)} files have explicit angle parameters")
    print(f"📍 {len(files_without_angles)} files have NO angle (assumed constant)")
    
    # Show examples of files without angles
    if files_without_angles:
        print(f"\n🔍 Files with assumed constant angles:")
        for f in files_without_angles[:5]:  # Show first 5
            params = f.parameters
            print(f"  - {f.filename}")
            print(f"    Energy: {params.beam_energy_value} eV")
            print(f"    ESA Voltage: {params.esa_voltage_value} V")
            print(f"    Inner angle: {params.inner_angle_value} (None = constant)")
    
    # Group by beam energy and ESA voltage combinations
    print(f"\n📊 Grouping by experimental conditions...")
    
    energy_voltage_groups = {}
    for f in files_with_energy_voltage:
        energy = f.parameters.beam_energy_value
        voltage = f.parameters.esa_voltage_value
        key = (energy, voltage)
        
        if key not in energy_voltage_groups:
            energy_voltage_groups[key] = {'with_angles': [], 'without_angles': []}
        
        if f.parameters.inner_angle_value is not None:
            energy_voltage_groups[key]['with_angles'].append(f)
        else:
            energy_voltage_groups[key]['without_angles'].append(f)
    
    print(f"Found {len(energy_voltage_groups)} unique (energy, voltage) combinations:")
    
    for (energy, voltage), group in energy_voltage_groups.items():
        with_angles = len(group['with_angles'])
        without_angles = len(group['without_angles'])
        total = with_angles + without_angles
        
        print(f"  - {energy:.0f} eV, {voltage:.0f} V: {total} files "
              f"({with_angles} with angles, {without_angles} constant angles)")
    
    # Find potential resolution datasets
    print(f"\n🎯 Searching for angular resolution datasets...")
    datasets = analyzer.find_resolution_datasets(min_voltage_points=2, min_angle_points=1)
    
    print(f"✅ Found {len(datasets)} potential resolution datasets:")
    
    for i, dataset in enumerate(datasets):
        print(f"\n{i+1}. Dataset:")
        print(f"   Beam Energy: {dataset.fixed_beam_energy:.0f} eV")
        print(f"   Fixed {dataset.fixed_angle_parameter}: {dataset.fixed_angle_value:.1f}°")
        print(f"   ESA Voltages: {dataset.varying_esa_voltages}")
        print(f"   Varying parameter: {dataset.varying_angle_parameter}")
        
        # Test analysis for first dataset
        if i == 0:
            print(f"\n🔬 Testing analysis for dataset {i+1}...")
            try:
                analyzed_dataset = analyzer.analyze_angular_resolution(dataset)
                print(f"   ✅ Found {len(analyzed_dataset.impact_regions)} impact regions")
                
                # Show some details
                for (voltage, angle), region in list(analyzed_dataset.impact_regions.items())[:3]:
                    print(f"     - Voltage {voltage:.0f}V, Angle {angle:.1f}°: "
                          f"Position ({region.centroid_x:.1f}, {region.centroid_y:.1f}), "
                          f"SNR {region.signal_to_noise:.1f}")
                
            except Exception as e:
                print(f"   ❌ Analysis failed: {e}")
    
    print(f"\n✅ Angular resolution test completed!")

if __name__ == "__main__":
    test_angular_resolution()
