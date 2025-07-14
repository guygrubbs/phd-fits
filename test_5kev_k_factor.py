#!/usr/bin/env python3
"""
Test k-factor analysis for 5keV files.
"""

import sys
sys.path.append('src')
from esa_analysis import ESAAnalyzer

def test_5kev_k_factor():
    """Test k-factor analysis for 5keV files."""
    
    print("🔬 Testing 5keV K-Factor Analysis")
    print("=" * 40)
    
    # Initialize ESA analyzer
    analyzer = ESAAnalyzer("data")
    
    # Find 5keV files with ESA parameters
    from data_model import DataManager
    data_manager = DataManager("data")
    all_files = data_manager.discover_files()
    
    five_kev_files = []
    for f in all_files:
        if (f.is_fits_or_map and 
            f.parameters.beam_energy_value and 
            abs(f.parameters.beam_energy_value - 5000) < 100 and
            f.parameters.esa_voltage_value is not None):
            five_kev_files.append(f)
    
    print(f"📁 Found {len(five_kev_files)} 5keV files with ESA parameters")
    
    if not five_kev_files:
        print("❌ No 5keV files with ESA parameters found")
        return
    
    # Show file details
    print(f"\n📋 5keV files for k-factor analysis:")
    for f in five_kev_files:
        params = f.parameters
        print(f"   - {f.filename}")
        print(f"     Energy: {params.beam_energy_value} eV")
        print(f"     ESA Voltage: {params.esa_voltage_value} V")
        print(f"     Inner Angle: {params.inner_angle_value}")
    
    # Analyze impact regions
    print(f"\n🔬 Analyzing 5keV impact regions...")
    try:
        regions = analyzer.analyze_impact_regions(five_kev_files)
        print(f"✅ Found {len(regions)} impact regions")
        
        if not regions:
            print("❌ No impact regions found")
            return
        
        # Show region details
        for i, region in enumerate(regions):
            print(f"   {i+1}. {region.filename}")
            print(f"      Position: ({region.centroid_x:.1f}, {region.centroid_y:.1f})")
            print(f"      Total intensity: {region.total_intensity:,.0f}")
            print(f"      SNR: {region.signal_to_noise:.1f}")
        
        # Calculate k-factors
        print(f"\n📊 Calculating 5keV k-factors...")
        k_factor_results = analyzer.estimate_k_factor(regions)
        
        if k_factor_results and k_factor_results.get('mean_k_factor'):
            print(f"✅ K-factor estimation successful!")
            print(f"   K-factor = Beam Energy (eV) / |ESA Voltage (V)|")
            print(f"   Mean k-factor: {k_factor_results['mean_k_factor']:.2f} eV/V")
            print(f"   Standard deviation: {k_factor_results['std_k_factor']:.3f} eV/V")
            print(f"   Range: {k_factor_results['min_k_factor']:.2f} - {k_factor_results['max_k_factor']:.2f} eV/V")
            print(f"   Based on {len(k_factor_results['measurements'])} measurements")
            
            # Show individual calculations
            if k_factor_results.get('measurements'):
                print(f"\n📋 Individual k-factor calculations:")
                for i, measurement in enumerate(k_factor_results['measurements']):
                    region = measurement.impact_region
                    print(f"  {i+1}. {region.filename}")
                    print(f"     Beam Energy: {region.beam_energy:.0f} eV")
                    print(f"     ESA Voltage: {region.esa_voltage:.0f} V")
                    if measurement.k_factor_estimate:
                        print(f"     K-factor: {region.beam_energy:.0f} / {abs(region.esa_voltage):.0f} = {measurement.k_factor_estimate:.2f} eV/V")
            
            # Compare with 1keV results
            print(f"\n🔍 Comparison with 1keV results:")
            print(f"   5keV k-factor: {k_factor_results['mean_k_factor']:.2f} ± {k_factor_results['std_k_factor']:.3f} eV/V")
            print(f"   1keV k-factor: 5.45 ± 0.06 eV/V (from previous analysis)")
            
            # Expected k-factor for 5keV at 912V
            expected_k_factor = 5000 / 912
            print(f"   Expected 5keV k-factor: {expected_k_factor:.2f} eV/V (5000 eV / 912 V)")
            
            if abs(k_factor_results['mean_k_factor'] - expected_k_factor) < 0.1:
                print(f"   ✅ Measured k-factor matches expected value!")
            else:
                print(f"   ⚠️  Measured k-factor differs from expected value")
        
        else:
            print(f"❌ K-factor estimation failed")
            print(f"   This could indicate:")
            print(f"     - Insufficient signal in impact regions")
            print(f"     - Data quality issues")
            print(f"     - Missing ESA voltage information")
    
    except Exception as e:
        print(f"❌ Error in 5keV k-factor analysis: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n✅ 5keV k-factor analysis complete!")

if __name__ == "__main__":
    test_5kev_k_factor()
