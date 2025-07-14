#!/usr/bin/env python3
"""
Check 5keV filenames and parameter parsing to understand why they're not detected.
"""

import sys
import os
sys.path.append('src')
from data_model import DataManager
from parameter_parser import ParameterParser

def check_5kev_filenames():
    """Check 5keV filenames and parameter parsing."""
    
    print("🔍 Checking 5keV Filename Detection")
    print("=" * 40)
    
    # Get all files in data directory
    data_dir = "data"
    if not os.path.exists(data_dir):
        print(f"❌ Data directory '{data_dir}' not found")
        return
    
    all_files = []
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.lower().endswith(('.fits', '.map', '.phd')):
                all_files.append(os.path.join(root, file))
    
    print(f"📁 Found {len(all_files)} data files total")
    
    # Look for files that might contain 5keV
    potential_5kev_files = []
    for filepath in all_files:
        filename = os.path.basename(filepath)
        if any(term in filename.upper() for term in ['5KEV', '5000EV', '5K', '5000']):
            potential_5kev_files.append(filepath)
    
    print(f"\n🔍 Files potentially containing 5keV:")
    if potential_5kev_files:
        for filepath in potential_5kev_files:
            filename = os.path.basename(filepath)
            print(f"   - {filename}")
    else:
        print(f"   ❌ No files found with 5keV, 5000eV, 5K, or 5000 in filename")
    
    # Check all filenames for energy patterns
    print(f"\n📊 All filenames with energy patterns:")
    parser = ParameterParser()
    
    energy_patterns = {}
    files_by_pattern = {}
    
    for filepath in all_files:
        filename = os.path.basename(filepath)
        
        # Try to parse parameters
        try:
            params = parser.parse_filename(filename)
            
            if params.beam_energy_value:
                energy = params.beam_energy_value
                if energy not in energy_patterns:
                    energy_patterns[energy] = 0
                    files_by_pattern[energy] = []
                energy_patterns[energy] += 1
                files_by_pattern[energy].append(filename)
            else:
                # Check for energy patterns manually
                filename_upper = filename.upper()
                if any(term in filename_upper for term in ['5KEV', '5000EV', 'KEV', 'EV']):
                    if 'UNKNOWN' not in energy_patterns:
                        energy_patterns['UNKNOWN'] = 0
                        files_by_pattern['UNKNOWN'] = []
                    energy_patterns['UNKNOWN'] += 1
                    files_by_pattern['UNKNOWN'].append(filename)
        
        except Exception as e:
            print(f"   ❌ Error parsing {filename}: {e}")
    
    print(f"\n📊 Energy detection results:")
    for energy, count in sorted(energy_patterns.items(), key=lambda x: str(x[0])):
        print(f"   {energy}: {count} files")
        
        # Show first few examples
        examples = files_by_pattern[energy][:3]
        for example in examples:
            print(f"      - {example}")
        if len(files_by_pattern[energy]) > 3:
            print(f"      ... and {len(files_by_pattern[energy]) - 3} more")
    
    # Specifically check files that might be 5keV but not detected
    print(f"\n🔍 Manual check for 5keV patterns:")
    
    possible_5kev_patterns = [
        '5KEV', '5000EV', '5K', '5000', 
        '5 KEV', '5.0KEV', '5000 EV'
    ]
    
    for filepath in all_files:
        filename = os.path.basename(filepath)
        filename_upper = filename.upper()
        
        for pattern in possible_5kev_patterns:
            if pattern in filename_upper:
                print(f"   Found '{pattern}' in: {filename}")
                
                # Try to parse this specific file
                try:
                    params = parser.parse_filename(filename)
                    print(f"      Parsed beam energy: {params.beam_energy_value}")
                    print(f"      Parsed ESA voltage: {params.esa_voltage_value}")
                    print(f"      Parsed inner angle: {params.inner_angle_value}")
                    
                    if not params.beam_energy_value:
                        print(f"      ❌ Beam energy not detected by parser")
                        
                        # Try to extract manually
                        import re
                        energy_match = re.search(r'(\d+)\s*KEV', filename_upper)
                        if energy_match:
                            manual_energy = int(energy_match.group(1)) * 1000
                            print(f"      Manual extraction: {manual_energy} eV")
                        
                        energy_match = re.search(r'(\d+)\s*EV', filename_upper)
                        if energy_match:
                            manual_energy = int(energy_match.group(1))
                            print(f"      Manual extraction: {manual_energy} eV")
                
                except Exception as e:
                    print(f"      ❌ Error parsing: {e}")
                
                break
    
    # Test integrated map tool directly for 5keV
    print(f"\n🗺️  Testing integrated map tool for 5keV:")
    
    try:
        from integrated_map_analysis import IntegratedMapAnalyzer
        analyzer = IntegratedMapAnalyzer("data")
        
        # Try different energy values
        test_energies = [5000, 5000.0, 5]
        
        for test_energy in test_energies:
            map_files = analyzer.find_map_files(beam_energy=test_energy)
            print(f"   Testing {test_energy}: Found {len(map_files)} files")
            
            if map_files:
                print(f"      ✅ Found files for energy {test_energy}")
                for f in map_files[:3]:
                    print(f"         - {f.filename}")
                break
        else:
            print(f"   ❌ No files found for any 5keV energy variant")
    
    except Exception as e:
        print(f"   ❌ Error testing integrated map tool: {e}")
    
    # Check if we can run integrated analysis without energy filter
    print(f"\n🔧 Testing integrated analysis without energy filter:")
    
    try:
        from integrated_map_analysis import IntegratedMapAnalyzer
        analyzer = IntegratedMapAnalyzer("data")
        
        # Get all map files
        all_map_files = analyzer.find_map_files()
        print(f"   Found {len(all_map_files)} total map files")
        
        # Group by detected energy
        energy_groups = {}
        for f in all_map_files:
            energy = f.parameters.beam_energy_value
            if energy not in energy_groups:
                energy_groups[energy] = []
            energy_groups[energy].append(f)
        
        print(f"   Energy groups:")
        for energy, files in energy_groups.items():
            print(f"      {energy} eV: {len(files)} files")
    
    except Exception as e:
        print(f"   ❌ Error in general integrated analysis: {e}")
    
    print(f"\n✅ 5keV filename check complete!")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if not potential_5kev_files:
        print(f"   1. No 5keV files detected in filenames")
        print(f"   2. All detected files are 1000 eV")
        print(f"   3. Check if 5keV data exists in a different directory")
        print(f"   4. Verify filename conventions for 5keV files")
    else:
        print(f"   1. 5keV files exist but parameter parsing may need improvement")
        print(f"   2. Consider updating parameter parser for 5keV patterns")
        print(f"   3. Manual energy extraction may be needed")

if __name__ == "__main__":
    check_5kev_filenames()
