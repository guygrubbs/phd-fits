#!/usr/bin/env python3
"""
Test 5keV file parsing directly to understand why they're not detected.
"""

import sys
sys.path.append('src')
from filename_parser import parse_filename

def test_5kev_parsing():
    """Test parsing of 5keV files directly."""
    
    print("🔍 Testing 5keV File Parsing")
    print("=" * 40)
    
    # Test files that should contain 5keV
    test_files = [
        'ACI ESA 5kEV BEAM PREP240921-214517.fits',
        'ACI ESA 912V 5KEV BEAM240921-215501.fits',
        'ACI ESA 912V 5KEV BEAM240921-215835.fits',
        'ACI ESA 912V 5KEV BEAM240921-220049.fits',
        'ACI ESA 912V 5KEV BEAM240921-221056.fits',
        'ACI ESA 912V 5KEV BEAM240921-221147.fits',
        'ACI ESA 912V 5KEV BEAM240921-222735.fits',
        'ACI ESA 912V 5KEV BEAM240921-223815.fits'
    ]
    
    print(f"Testing {len(test_files)} 5keV files:")
    
    successful_parses = 0
    failed_parses = 0
    
    for filename in test_files:
        print(f"\n📁 Testing: {filename}")
        
        try:
            params = parse_filename(filename)
            
            print(f"   ✅ Parsing successful!")
            print(f"   Beam Energy: {params.beam_energy} -> {params.beam_energy_value} {params.beam_energy_unit}")
            print(f"   ESA Voltage: {params.esa_voltage} -> {params.esa_voltage_value}")
            print(f"   Test Type: {params.test_type}")
            print(f"   File Type: {params.file_type}")
            
            if params.beam_energy_value:
                print(f"   🎯 Energy detected: {params.beam_energy_value} eV")
                successful_parses += 1
            else:
                print(f"   ❌ Energy NOT detected")
                failed_parses += 1
                
        except Exception as e:
            print(f"   ❌ Parsing failed: {e}")
            failed_parses += 1
    
    print(f"\n📊 Parsing Results:")
    print(f"   Successful: {successful_parses}")
    print(f"   Failed: {failed_parses}")
    
    if successful_parses > 0:
        print(f"\n✅ 5keV files CAN be parsed!")
        print(f"   The issue may be in the data manager or file discovery")
    else:
        print(f"\n❌ 5keV files CANNOT be parsed")
        print(f"   The parameter parser needs to be updated")
    
    # Test the data manager directly
    print(f"\n🔧 Testing Data Manager:")
    
    try:
        from data_model import DataManager
        manager = DataManager("data")
        all_files = manager.discover_files()
        
        print(f"   Total files discovered: {len(all_files)}")
        
        # Look for 5keV files
        five_kev_files = []
        for f in all_files:
            if f.parameters.beam_energy_value and abs(f.parameters.beam_energy_value - 5000) < 100:
                five_kev_files.append(f)
        
        print(f"   5keV files found by data manager: {len(five_kev_files)}")
        
        if five_kev_files:
            print(f"   ✅ Data manager DOES find 5keV files!")
            for f in five_kev_files:
                print(f"      - {f.filename}: {f.parameters.beam_energy_value} eV")
        else:
            print(f"   ❌ Data manager does NOT find 5keV files")
            
            # Check what energies are found
            energies = set()
            for f in all_files:
                if f.parameters.beam_energy_value:
                    energies.add(f.parameters.beam_energy_value)
            
            print(f"   Energies found: {sorted(energies)}")
    
    except Exception as e:
        print(f"   ❌ Error testing data manager: {e}")
    
    # Test integrated map analyzer directly
    print(f"\n🗺️  Testing Integrated Map Analyzer:")
    
    try:
        from integrated_map_analysis import IntegratedMapAnalyzer
        analyzer = IntegratedMapAnalyzer("data")
        
        # Try to find 5keV map files
        map_files_5kev = analyzer.find_map_files(beam_energy=5000.0)
        print(f"   5keV map files found: {len(map_files_5kev)}")
        
        if map_files_5kev:
            print(f"   ✅ Integrated analyzer DOES find 5keV files!")
            for f in map_files_5kev:
                print(f"      - {f.filename}: {f.parameters.beam_energy_value} eV")
        else:
            print(f"   ❌ Integrated analyzer does NOT find 5keV files")
            
            # Try without energy filter
            all_map_files = analyzer.find_map_files()
            print(f"   Total map files found: {len(all_map_files)}")
            
            # Check energies in map files
            map_energies = set()
            for f in all_map_files:
                if f.parameters.beam_energy_value:
                    map_energies.add(f.parameters.beam_energy_value)
            
            print(f"   Map file energies: {sorted(map_energies)}")
    
    except Exception as e:
        print(f"   ❌ Error testing integrated analyzer: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n✅ 5keV parsing test complete!")

if __name__ == "__main__":
    test_5kev_parsing()
