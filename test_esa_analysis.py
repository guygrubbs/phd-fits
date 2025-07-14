#!/usr/bin/env python3
"""
Test script for ESA analysis functionality focusing on angle ranges.
"""

import sys
import os
sys.path.append('src')
from esa_analysis import ESAAnalyzer
from data_model import DataManager

def test_esa_analysis():
    """Test ESA analysis with focus on angle range handling."""
    
    print("🔬 Testing ESA Analysis with Angle Range Support")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = ESAAnalyzer("data")
    
    # Discover files
    all_files = analyzer.data_manager.discover_files()
    fits_files = [f for f in all_files if f.is_fits_or_map]
    
    print(f"📁 Found {len(fits_files)} FITS/MAP files")
    
    # Filter files with experimental parameters
    valid_files = []
    angle_range_files = []
    single_angle_files = []
    
    for f in fits_files:
        params = f.parameters
        if (params.beam_energy_value and 
            params.esa_voltage_value is not None and 
            params.inner_angle_value is not None):
            valid_files.append(f)
            
            # Check for angle ranges
            if hasattr(params, 'is_angle_range') and params.is_angle_range:
                angle_range_files.append(f)
            else:
                single_angle_files.append(f)
    
    print(f"✅ {len(valid_files)} files have complete experimental parameters")
    print(f"📐 {len(angle_range_files)} files have angle ranges")
    print(f"📍 {len(single_angle_files)} files have single angles")
    
    # Show angle range details
    if angle_range_files:
        print("\n🔄 Files with angle ranges:")
        for f in angle_range_files:
            params = f.parameters
            if hasattr(params, 'inner_angle_range') and params.inner_angle_range:
                print(f"  - {f.filename}")
                print(f"    Range: {params.inner_angle_range[0]:.1f}° to {params.inner_angle_range[1]:.1f}°")
                print(f"    Midpoint: {params.inner_angle_value:.1f}°")
                print(f"    Beam energy: {params.beam_energy_value} eV")
                print(f"    ESA voltage: {params.esa_voltage_value} V")
    
    # Analyze impact regions (without plotting)
    print(f"\n🎯 Analyzing spatial impact regions...")
    regions = analyzer.analyze_impact_regions(valid_files[:5])  # Test with first 5 files
    
    print(f"✅ Found {len(regions)} valid impact regions")
    
    if regions:
        print("\n📊 Region Analysis Summary:")
        for region in regions:
            angle_info = ""
            if region.is_angle_range and region.rotation_angle_range:
                angle_info = f" (range: {region.rotation_angle_range[0]:.1f}° to {region.rotation_angle_range[1]:.1f}°)"
            
            print(f"  - {region.filename}")
            print(f"    Position: ({region.centroid_x:.1f}, {region.centroid_y:.1f})")
            print(f"    Angle: {region.rotation_angle:.1f}°{angle_info}")
            print(f"    Energy: {region.beam_energy} eV, Voltage: {region.esa_voltage} V")
            print(f"    Peak intensity: {region.peak_intensity:.3f}")
            print(f"    SNR: {region.signal_to_noise:.2f}")
        
        # Test k-factor estimation
        print(f"\n⚡ Testing K-factor estimation...")
        k_factor_results = analyzer.estimate_k_factor(regions)
        
        if "error" in k_factor_results:
            print(f"❌ K-factor estimation: {k_factor_results['error']}")
        else:
            print("✅ K-factor estimation successful!")
            print(f"   K-factor = Beam Energy (eV) / |ESA Voltage (V)|")
            print(f"   Mean k-factor: {k_factor_results['k_factor_mean']:.2f} eV/V")
            print(f"   Standard deviation: {k_factor_results['k_factor_std']:.2f} eV/V")
            print(f"   Range: {k_factor_results['k_factor_range'][0]:.2f} - {k_factor_results['k_factor_range'][1]:.2f} eV/V")
            print(f"   Based on {k_factor_results['num_measurements']} measurements")
            
            # Show individual measurements
            if k_factor_results.get('measurements'):
                print(f"\n📋 Individual k-factor calculations:")
                for i, measurement in enumerate(k_factor_results['measurements']):
                    region = measurement.impact_region
                    print(f"  {i+1}. {region.filename}")
                    print(f"     Beam Energy: {region.beam_energy:.0f} eV")
                    print(f"     ESA Voltage: {region.esa_voltage:.0f} V")
                    if measurement.k_factor_estimate:
                        print(f"     K-factor: {region.beam_energy:.0f} / {abs(region.esa_voltage):.0f} = {measurement.k_factor_estimate:.2f} eV/V")
    
    print(f"\n✅ ESA analysis test completed successfully!")

if __name__ == "__main__":
    test_esa_analysis()
