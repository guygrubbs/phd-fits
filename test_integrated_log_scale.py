#!/usr/bin/env python3
"""
Test script for integrated map analysis with enhanced log scale visualization.
"""

import sys
import os
sys.path.append('src')
from integrated_map_analysis import IntegratedMapAnalyzer
import numpy as np

def test_integrated_log_scale():
    """Test the integrated map analysis with log scale improvements."""
    
    print("🗺️  Testing Integrated Map Analysis with Enhanced Log Scale")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = IntegratedMapAnalyzer("data")
    
    # Find map files for 1000 eV
    print("🔍 Finding map files...")
    map_files = analyzer.find_map_files(beam_energy=1000.0)
    
    if not map_files:
        print("❌ No map files found")
        return
    
    print(f"✅ Found {len(map_files)} map files")
    
    # Analyze contributions
    print("🔬 Analyzing map contributions...")
    contributions = analyzer.analyze_map_contributions(map_files)
    
    if not contributions:
        print("❌ No valid contributions found")
        return
    
    print(f"✅ Found {len(contributions)} valid contributions")
    
    # Show rate statistics
    count_rates = [c.count_rate for c in contributions]
    print(f"📊 Count rate statistics:")
    print(f"   Range: {min(count_rates):.1f} - {max(count_rates):.1f} counts/s")
    print(f"   Mean: {np.mean(count_rates):.1f} ± {np.std(count_rates):.1f} counts/s")
    print(f"   Dynamic range: {max(count_rates)/min(count_rates):.1f}× variation")
    
    # Create integrated map
    print("🗺️  Creating integrated map...")
    integrated_map, metadata = analyzer.create_integrated_map(contributions)
    
    print(f"✅ Integration complete!")
    print(f"   Peak integrated rate: {metadata['peak_integrated_rate']:.1f} counts/s")
    print(f"   Active pixels: {metadata['active_pixels']:,}")
    print(f"   Total integrated counts: {metadata['total_integrated_counts']:,.0f}")
    
    # Analyze log scale characteristics
    nonzero_data = integrated_map[integrated_map > 0]
    if len(nonzero_data) > 0:
        print(f"\n📈 Log scale analysis:")
        print(f"   Non-zero pixels: {len(nonzero_data):,} ({len(nonzero_data)/integrated_map.size:.1%})")
        print(f"   Min non-zero value: {np.min(nonzero_data):.3f} counts/s")
        print(f"   Max value: {np.max(nonzero_data):.1f} counts/s")
        print(f"   Log dynamic range: {np.log10(np.max(nonzero_data)/np.min(nonzero_data)):.1f} decades")
        
        # Show percentile levels for contours
        percentiles = [50, 75, 90, 95, 99]
        print(f"   Contour levels (percentiles):")
        for p in percentiles:
            value = np.percentile(nonzero_data, p)
            print(f"     {p}th percentile: {value:.3f} counts/s")
    
    # Create enhanced log scale plot
    print("📊 Creating enhanced log scale visualization...")
    save_path = "results/integrated_map_log_scale_test.png"
    
    # Ensure results directory exists
    os.makedirs("results", exist_ok=True)
    
    try:
        analyzer.plot_integrated_map(integrated_map, metadata, contributions, save_path)
        print(f"✅ Enhanced log scale plot saved: {save_path}")
        
        # Show what makes the log scale better
        print(f"\n🎯 Log scale advantages:")
        print(f"   - Reveals low-intensity impact regions")
        print(f"   - Compresses {max(count_rates)/min(count_rates):.0f}× dynamic range")
        print(f"   - Contour lines highlight impact boundaries")
        print(f"   - 'Hot' colormap enhances visibility")
        print(f"   - Shows {len(nonzero_data):,} active pixels clearly")
        
    except Exception as e:
        print(f"❌ Error creating plot: {e}")
        return
    
    print(f"\n✅ Log scale integrated map test completed successfully!")

if __name__ == "__main__":
    test_integrated_log_scale()
