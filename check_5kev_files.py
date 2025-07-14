#!/usr/bin/env python3
"""
Check if 5keV beam files are being analyzed and test integrated plot generation.
"""

import sys
sys.path.append('src')
from data_model import DataManager
from integrated_map_analysis import IntegratedMapAnalyzer
import numpy as np

def check_5kev_analysis():
    """Check 5keV file analysis and create integrated plot if possible."""
    
    print("🔍 Checking 5keV Beam File Analysis")
    print("=" * 40)
    
    # Initialize data manager
    data_manager = DataManager("data")
    all_files = data_manager.discover_files()
    fits_files = [f for f in all_files if f.is_fits_or_map]
    
    print(f"📁 Found {len(fits_files)} FITS/MAP files total")
    
    # Find all beam energies
    beam_energies = {}
    files_by_energy = {}
    
    for f in fits_files:
        params = f.parameters
        if params.beam_energy_value:
            energy = params.beam_energy_value
            if energy not in beam_energies:
                beam_energies[energy] = 0
                files_by_energy[energy] = []
            beam_energies[energy] += 1
            files_by_energy[energy].append(f)
    
    print(f"\n📊 Beam energies found:")
    for energy, count in sorted(beam_energies.items()):
        print(f"   {energy:.0f} eV: {count} files")
    
    # Check specifically for 5keV files
    five_kev_files = []
    for energy, files in files_by_energy.items():
        if abs(energy - 5000) < 100:  # Allow some tolerance
            five_kev_files.extend(files)
            print(f"\n✅ Found 5keV files: {energy:.0f} eV ({len(files)} files)")
    
    if not five_kev_files:
        print(f"\n❌ No 5keV beam files found")
        print(f"   Available energies: {sorted(beam_energies.keys())}")
        return
    
    print(f"\n🔍 Analyzing 5keV files:")
    for f in five_kev_files:
        params = f.parameters
        print(f"   - {f.filename}")
        print(f"     Energy: {params.beam_energy_value} eV")
        print(f"     ESA Voltage: {params.esa_voltage_value}")
        print(f"     Inner Angle: {params.inner_angle_value}")
        print(f"     Horizontal: {params.horizontal_value_num}")
    
    # Test integrated map analysis for 5keV
    print(f"\n🗺️  Testing integrated map analysis for 5keV...")
    
    try:
        analyzer = IntegratedMapAnalyzer("data")
        
        # Find map files for 5keV
        map_files_5kev = analyzer.find_map_files(beam_energy=5000.0)
        print(f"   Found {len(map_files_5kev)} map files for 5keV analysis")
        
        if not map_files_5kev:
            print(f"   ❌ No 5keV map files found for integration")
            return
        
        # Analyze contributions
        print(f"   🔬 Analyzing 5keV map contributions...")
        contributions = analyzer.analyze_map_contributions(map_files_5kev)
        
        if not contributions:
            print(f"   ❌ No valid 5keV contributions found")
            print(f"   This could mean:")
            print(f"     - Files are empty or corrupted")
            print(f"     - Files don't contain valid image data")
            print(f"     - Files have incompatible format")
            return
        
        print(f"   ✅ Found {len(contributions)} valid 5keV contributions")
        
        # Show contribution details
        for i, contrib in enumerate(contributions):
            print(f"     {i+1}. {contrib.filename}")
            print(f"        Total counts: {contrib.total_counts:,.0f}")
            print(f"        Count rate: {contrib.count_rate:.1f} counts/s")
            print(f"        Collection time: {contrib.estimated_collection_time:.1f}s")
            print(f"        SNR: {contrib.signal_to_noise:.1f}")
        
        # Create integrated map
        print(f"   🗺️  Creating integrated 5keV map...")
        integrated_map, metadata = analyzer.create_integrated_map(contributions)
        
        print(f"   ✅ 5keV integration complete!")
        print(f"      Peak integrated rate: {metadata['peak_integrated_rate']:.1f} counts/s")
        print(f"      Total integrated counts: {metadata['total_integrated_counts']:,.0f}")
        print(f"      Active pixels: {metadata['active_pixels']:,}")
        
        # Create plot
        save_path = "results/integrated_count_rate_map_E5000eV_rate100.png"
        print(f"   📊 Creating 5keV integrated plot...")
        
        try:
            analyzer.plot_integrated_map(integrated_map, metadata, contributions, save_path)
            print(f"   ✅ 5keV integrated plot saved: {save_path}")
        except Exception as e:
            print(f"   ❌ Error creating 5keV plot: {e}")
        
        # Generate report
        report_path = "results/integrated_map_analysis_E5000eV_rate100.md"
        try:
            analyzer.generate_integration_report(integrated_map, metadata, contributions, report_path)
            print(f"   📄 5keV report saved: {report_path}")
        except Exception as e:
            print(f"   ❌ Error creating 5keV report: {e}")
        
    except Exception as e:
        print(f"   ❌ Error in 5keV integrated analysis: {e}")
        import traceback
        traceback.print_exc()
    
    # Test other analysis tools for 5keV
    print(f"\n🔧 Testing other analysis tools for 5keV:")
    
    # Test elevation/azimuth analysis
    try:
        from elevation_azimuth_analysis import ElevationAzimuthAnalyzer
        elev_analyzer = ElevationAzimuthAnalyzer("data")
        energy_groups = elev_analyzer.find_angular_datasets(beam_energy=5000.0)
        
        if energy_groups:
            print(f"   ✅ Elevation/azimuth analysis: Found datasets for 5keV")
            for energy, files in energy_groups.items():
                print(f"      {energy:.0f} eV: {len(files)} files")
        else:
            print(f"   ❌ Elevation/azimuth analysis: No 5keV datasets found")
    
    except Exception as e:
        print(f"   ❌ Error testing elevation/azimuth for 5keV: {e}")
    
    # Test angular resolution analysis
    try:
        from angular_resolution_analysis import AngularResolutionAnalyzer
        res_analyzer = AngularResolutionAnalyzer("data")
        datasets = res_analyzer.find_resolution_datasets()
        
        five_kev_datasets = [d for d in datasets if abs(d.fixed_beam_energy - 5000) < 100]
        
        if five_kev_datasets:
            print(f"   ✅ Angular resolution analysis: Found {len(five_kev_datasets)} 5keV datasets")
        else:
            print(f"   ❌ Angular resolution analysis: No 5keV datasets found")
    
    except Exception as e:
        print(f"   ❌ Error testing angular resolution for 5keV: {e}")
    
    # Test ESA analysis
    try:
        from esa_analysis import ESAAnalyzer
        esa_analyzer = ESAAnalyzer("data")
        
        # Find 5keV files with ESA parameters
        five_kev_esa_files = []
        for f in five_kev_files:
            if (f.parameters.beam_energy_value and 
                f.parameters.esa_voltage_value is not None):
                five_kev_esa_files.append(f)
        
        if five_kev_esa_files:
            print(f"   ✅ ESA analysis: Found {len(five_kev_esa_files)} 5keV files with ESA parameters")
            
            # Try to analyze impact regions
            regions = esa_analyzer.analyze_impact_regions(five_kev_esa_files)
            print(f"      Impact regions found: {len(regions)}")
            
            if regions:
                # Try k-factor estimation
                k_factor_results = esa_analyzer.estimate_k_factor(regions)
                if k_factor_results and k_factor_results.get('mean_k_factor'):
                    print(f"      K-factor: {k_factor_results['mean_k_factor']:.2f} ± {k_factor_results['std_k_factor']:.3f} eV/V")
                else:
                    print(f"      K-factor estimation failed")
        else:
            print(f"   ❌ ESA analysis: No 5keV files with ESA parameters")
    
    except Exception as e:
        print(f"   ❌ Error testing ESA analysis for 5keV: {e}")
    
    print(f"\n✅ 5keV analysis check complete!")

if __name__ == "__main__":
    check_5kev_analysis()
