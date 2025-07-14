#!/usr/bin/env python3
"""
Analyze which parameters actually varied in the experimental data to verify
if tools correctly recognize the primary variation pattern.
"""

import sys
sys.path.append('src')
from data_model import DataManager
import numpy as np
from collections import defaultdict

def analyze_parameter_variation():
    """Analyze which parameters actually varied in the experimental data."""
    
    print("🔍 Analyzing Parameter Variation Patterns")
    print("=" * 50)
    
    # Initialize data manager
    data_manager = DataManager("data")
    all_files = data_manager.discover_files()
    fits_files = [f for f in all_files if f.is_fits_or_map]
    
    print(f"📁 Found {len(fits_files)} FITS/MAP files total")
    
    # Collect all parameter values
    beam_energies = set()
    esa_voltages = set()
    inner_angles = set()
    horizontal_values = set()
    focus_x_values = set()
    focus_y_values = set()
    mcp_voltages = set()
    
    # Track files with complete parameters
    complete_files = []
    
    for f in fits_files:
        params = f.parameters
        
        # Only analyze files with beam energy (primary filter)
        if params.beam_energy_value:
            complete_files.append(f)
            
            beam_energies.add(params.beam_energy_value)
            
            if params.esa_voltage_value is not None:
                esa_voltages.add(params.esa_voltage_value)
            
            if params.inner_angle_value is not None:
                inner_angles.add(params.inner_angle_value)
            
            if params.horizontal_value_num is not None:
                horizontal_values.add(params.horizontal_value_num)
            
            if params.focus_x is not None:
                focus_x_values.add(params.focus_x)
            
            if params.focus_y is not None:
                focus_y_values.add(params.focus_y)
            
            if hasattr(params, 'mcp_voltage') and params.mcp_voltage is not None:
                mcp_voltages.add(params.mcp_voltage)
    
    print(f"✅ {len(complete_files)} files have beam energy information")
    
    # Analyze parameter variation
    print(f"\n📊 Parameter Variation Analysis:")
    
    def analyze_parameter(name, values, files_with_param):
        if len(values) == 0:
            print(f"   {name}: No values found")
            return 0
        elif len(values) == 1:
            print(f"   {name}: CONSTANT - {list(values)[0]} ({files_with_param} files)")
            return 0
        else:
            sorted_values = sorted(list(values))
            print(f"   {name}: VARIES - {len(values)} unique values")
            print(f"      Range: {sorted_values}")
            print(f"      Files with this parameter: {files_with_param}")
            return len(values)
    
    # Count files with each parameter
    files_with_esa = len([f for f in complete_files if f.parameters.esa_voltage_value is not None])
    files_with_inner = len([f for f in complete_files if f.parameters.inner_angle_value is not None])
    files_with_horizontal = len([f for f in complete_files if f.parameters.horizontal_value_num is not None])
    files_with_focus_x = len([f for f in complete_files if f.parameters.focus_x is not None])
    files_with_focus_y = len([f for f in complete_files if f.parameters.focus_y is not None])
    
    # Analyze each parameter
    beam_variation = analyze_parameter("Beam Energy", beam_energies, len(complete_files))
    esa_variation = analyze_parameter("ESA Voltage", esa_voltages, files_with_esa)
    inner_variation = analyze_parameter("Inner Angle", inner_angles, files_with_inner)
    horizontal_variation = analyze_parameter("Horizontal Value", horizontal_values, files_with_horizontal)
    focus_x_variation = analyze_parameter("Focus X", focus_x_values, files_with_focus_x)
    focus_y_variation = analyze_parameter("Focus Y", focus_y_values, files_with_focus_y)
    
    # Determine primary varying parameter
    print(f"\n🎯 Primary Variation Analysis:")
    
    variations = {
        "Inner Angle": (inner_variation, files_with_inner),
        "ESA Voltage": (esa_variation, files_with_esa),
        "Horizontal Value": (horizontal_variation, files_with_horizontal),
        "Beam Energy": (beam_variation, len(complete_files)),
        "Focus X": (focus_x_variation, files_with_focus_x),
        "Focus Y": (focus_y_variation, files_with_focus_y)
    }
    
    # Sort by number of unique values and file coverage
    sorted_variations = sorted(variations.items(), 
                              key=lambda x: (x[1][0], x[1][1]), reverse=True)
    
    print(f"   Parameter variation ranking (by unique values and file coverage):")
    for i, (param_name, (unique_count, file_count)) in enumerate(sorted_variations):
        if unique_count > 0:
            coverage = file_count / len(complete_files) * 100
            print(f"   {i+1}. {param_name}: {unique_count} values across {file_count} files ({coverage:.1f}% coverage)")
    
    # Identify the primary experimental design
    primary_param = sorted_variations[0][0] if sorted_variations[0][1][0] > 1 else None
    
    if primary_param:
        print(f"\n✅ PRIMARY VARYING PARAMETER: {primary_param}")
        print(f"   This appears to be the main experimental variable")
    else:
        print(f"\n⚠️  No clear primary varying parameter identified")
    
    # Analyze specific combinations for elevation/azimuth potential
    print(f"\n🧭 Elevation/Azimuth Analysis Potential:")
    
    # Group files by beam energy
    energy_groups = defaultdict(list)
    for f in complete_files:
        energy_groups[f.parameters.beam_energy_value].append(f)
    
    for energy, files in energy_groups.items():
        print(f"\n   Beam Energy: {energy:.0f} eV ({len(files)} files)")
        
        # Analyze parameter combinations within this energy
        inner_angles_in_group = set()
        horizontal_values_in_group = set()
        esa_voltages_in_group = set()
        
        for f in files:
            if f.parameters.inner_angle_value is not None:
                inner_angles_in_group.add(f.parameters.inner_angle_value)
            if f.parameters.horizontal_value_num is not None:
                horizontal_values_in_group.add(f.parameters.horizontal_value_num)
            if f.parameters.esa_voltage_value is not None:
                esa_voltages_in_group.add(f.parameters.esa_voltage_value)
        
        print(f"      Inner angles: {len(inner_angles_in_group)} unique ({sorted(inner_angles_in_group)})")
        print(f"      Horizontal values: {len(horizontal_values_in_group)} unique ({sorted(horizontal_values_in_group)})")
        print(f"      ESA voltages: {len(esa_voltages_in_group)} unique ({sorted(esa_voltages_in_group)})")
        
        # Determine best analysis approach
        if len(inner_angles_in_group) > 1 and len(horizontal_values_in_group) > 1:
            print(f"      ✅ EXCELLENT for 2D elevation/azimuth analysis")
        elif len(inner_angles_in_group) > 1 and len(esa_voltages_in_group) > 1:
            print(f"      ✅ GOOD for inner angle vs ESA voltage analysis")
        elif len(inner_angles_in_group) > 1:
            print(f"      ✅ GOOD for inner angle sweep analysis (primary variation)")
        elif len(esa_voltages_in_group) > 1:
            print(f"      ⚠️  Limited to ESA voltage variation only")
        else:
            print(f"      ❌ Limited variation for meaningful analysis")
    
    # Check if analysis tools recognize this pattern
    print(f"\n🔧 Analysis Tool Recognition:")
    
    # Test what each tool would find
    try:
        from elevation_azimuth_analysis import ElevationAzimuthAnalyzer
        analyzer = ElevationAzimuthAnalyzer("data")
        energy_groups = analyzer.find_angular_datasets()
        
        print(f"   Elevation/Azimuth Tool:")
        for energy, files in energy_groups.items():
            print(f"      Found {len(files)} files for {energy:.0f} eV")
            
            # Check what angles it detects
            elevations = set()
            azimuths = set()
            for f in files:
                if f.parameters.inner_angle_value is not None:
                    elevations.add(f.parameters.inner_angle_value)
                if f.parameters.horizontal_value_num is not None:
                    azimuths.add(f.parameters.horizontal_value_num)
            
            print(f"         Elevation angles (inner): {len(elevations)} unique")
            print(f"         Azimuth angles (horizontal): {len(azimuths)} unique")
            
            if len(elevations) > 1 and len(azimuths) <= 3:
                print(f"         ✅ Correctly identifies inner angle as primary variation")
            elif len(elevations) > 1:
                print(f"         ✅ Recognizes inner angle variation")
            else:
                print(f"         ⚠️  May not detect sufficient variation")
    
    except Exception as e:
        print(f"   ❌ Error testing elevation/azimuth tool: {e}")
    
    try:
        from angular_resolution_analysis import AngularResolutionAnalyzer
        analyzer = AngularResolutionAnalyzer("data")
        datasets = analyzer.find_resolution_datasets(min_voltage_points=2, min_angle_points=1)
        
        print(f"   Angular Resolution Tool:")
        print(f"      Found {len(datasets)} potential resolution datasets")
        
        for i, dataset in enumerate(datasets):
            print(f"         Dataset {i+1}: Fixed {dataset.fixed_angle_parameter} = {dataset.fixed_angle_value}")
            print(f"         Varying: {dataset.varying_angle_parameter}")
            print(f"         ESA voltages: {len(dataset.varying_esa_voltages)} unique")
            
            if dataset.varying_angle_parameter == 'esa_voltage':
                print(f"         ✅ Correctly identifies ESA voltage as varying parameter")
            else:
                print(f"         ⚠️  May not correctly identify primary variation")
    
    except Exception as e:
        print(f"   ❌ Error testing angular resolution tool: {e}")
    
    # Summary and recommendations
    print(f"\n📋 Summary and Recommendations:")
    
    if primary_param == "Inner Angle":
        print(f"   ✅ CONFIRMED: Inner rotation angle is the primary varying parameter")
        print(f"   📊 Recommended analysis:")
        print(f"      1. Inner angle sweep analysis (elevation analysis)")
        print(f"      2. Integrated mapping to show all impact locations")
        print(f"      3. K-factor analysis across angle range")
        
        if len(esa_voltages) > 1:
            print(f"      4. Secondary analysis: ESA voltage effects")
        
        if len(horizontal_values) > 1:
            print(f"      5. Secondary analysis: Horizontal positioning effects")
    
    else:
        print(f"   ⚠️  Primary varying parameter: {primary_param}")
        print(f"   📊 Analysis tools may need adjustment for this parameter pattern")
    
    print(f"\n✅ Parameter variation analysis complete!")

if __name__ == "__main__":
    analyze_parameter_variation()
