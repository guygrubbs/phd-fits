#!/usr/bin/env python3
"""
Analyze available angle parameters for elevation vs azimuth plotting.
"""

import sys
sys.path.append('src')
from data_model import DataManager
import numpy as np

def analyze_angle_parameters():
    """Analyze what angle parameters are available in the data files."""
    
    print("🔍 Analyzing Angle Parameters for Elevation vs Azimuth Plotting")
    print("=" * 70)
    
    # Initialize data manager
    data_manager = DataManager("data")
    all_files = data_manager.discover_files()
    fits_files = [f for f in all_files if f.is_fits_or_map]
    
    print(f"📁 Found {len(fits_files)} FITS/MAP files")
    
    # Analyze available parameters
    beam_energies = set()
    esa_voltages = set()
    inner_angles = set()
    horizontal_values = set()
    focus_x_values = set()
    focus_y_values = set()
    offset_x_values = set()
    offset_y_values = set()
    
    files_with_angles = []
    files_by_energy = {}
    
    for f in fits_files:
        params = f.parameters
        
        # Collect all parameter values
        if params.beam_energy_value:
            beam_energies.add(params.beam_energy_value)
            
            if params.beam_energy_value not in files_by_energy:
                files_by_energy[params.beam_energy_value] = []
            files_by_energy[params.beam_energy_value].append(f)
        
        if params.esa_voltage_value is not None:
            esa_voltages.add(params.esa_voltage_value)
        
        if params.inner_angle_value is not None:
            inner_angles.add(params.inner_angle_value)
            files_with_angles.append(f)
        
        if params.horizontal_value_num is not None:
            horizontal_values.add(params.horizontal_value_num)
        
        if params.focus_x:
            focus_x_values.add(params.focus_x)
        
        if params.focus_y:
            focus_y_values.add(params.focus_y)
        
        if params.offset_x:
            offset_x_values.add(params.offset_x)
        
        if params.offset_y:
            offset_y_values.add(params.offset_y)
    
    # Print summary
    print(f"\n📊 Parameter Summary:")
    print(f"  Beam Energies: {sorted(beam_energies)} eV")
    print(f"  ESA Voltages: {sorted(esa_voltages)} V")
    print(f"  Inner Angles: {sorted(inner_angles)}°")
    print(f"  Horizontal Values: {sorted(horizontal_values)}")
    print(f"  Focus X Values: {sorted(focus_x_values)}")
    print(f"  Focus Y Values: {sorted(focus_y_values)}")
    print(f"  Offset X Values: {sorted(offset_x_values)}")
    print(f"  Offset Y Values: {sorted(offset_y_values)}")
    
    # Analyze by beam energy
    print(f"\n🎯 Analysis by Beam Energy:")
    for energy, files in sorted(files_by_energy.items()):
        print(f"\n  Beam Energy: {energy:.0f} eV ({len(files)} files)")
        
        # Collect angle parameters for this energy
        energy_inner_angles = set()
        energy_horizontal = set()
        energy_esa_voltages = set()
        energy_focus_positions = set()
        
        for f in files:
            params = f.parameters
            if params.inner_angle_value is not None:
                energy_inner_angles.add(params.inner_angle_value)
            if params.horizontal_value_num is not None:
                energy_horizontal.add(params.horizontal_value_num)
            if params.esa_voltage_value is not None:
                energy_esa_voltages.add(params.esa_voltage_value)
            if params.focus_x and params.focus_y:
                energy_focus_positions.add((params.focus_x, params.focus_y))
        
        print(f"    Inner Angles: {sorted(energy_inner_angles)}°")
        print(f"    Horizontal Values: {sorted(energy_horizontal)}")
        print(f"    ESA Voltages: {sorted(energy_esa_voltages)} V")
        print(f"    Focus Positions: {sorted(energy_focus_positions)}")
        
        # Check for potential elevation/azimuth combinations
        if len(energy_inner_angles) > 1 and len(energy_horizontal) > 1:
            print(f"    ✅ Potential for elevation/azimuth plot: {len(energy_inner_angles)} inner angles × {len(energy_horizontal)} horizontal values")
        elif len(energy_inner_angles) > 1 and len(energy_esa_voltages) > 1:
            print(f"    ✅ Potential for angle/voltage plot: {len(energy_inner_angles)} inner angles × {len(energy_esa_voltages)} voltages")
        elif len(energy_horizontal) > 1 and len(energy_esa_voltages) > 1:
            print(f"    ✅ Potential for horizontal/voltage plot: {len(energy_horizontal)} horizontal × {len(energy_esa_voltages)} voltages")
        else:
            print(f"    ⚠️  Limited variation for 2D plotting")
    
    # Show detailed file analysis for main beam energy
    main_energy = max(beam_energies) if beam_energies else None
    if main_energy:
        print(f"\n📋 Detailed Analysis for {main_energy:.0f} eV:")
        main_files = files_by_energy[main_energy]
        
        print(f"  Files with angle parameters:")
        for f in main_files:
            params = f.parameters
            if params.inner_angle_value is not None or params.horizontal_value_num is not None:
                angle_info = []
                if params.inner_angle_value is not None:
                    if hasattr(params, 'is_angle_range') and params.is_angle_range:
                        range_info = f"{params.inner_angle_range[0]:.0f}° to {params.inner_angle_range[1]:.0f}°" if hasattr(params, 'inner_angle_range') and params.inner_angle_range else "range"
                        angle_info.append(f"Inner: {range_info}")
                    else:
                        angle_info.append(f"Inner: {params.inner_angle_value:.0f}°")
                
                if params.horizontal_value_num is not None:
                    angle_info.append(f"Hor: {params.horizontal_value_num:.0f}")
                
                if params.esa_voltage_value is not None:
                    angle_info.append(f"ESA: {params.esa_voltage_value:.0f}V")
                
                print(f"    - {f.filename}")
                print(f"      {', '.join(angle_info)}")
    
    return files_by_energy, beam_energies

if __name__ == "__main__":
    analyze_angle_parameters()
