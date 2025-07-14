#!/usr/bin/env python3
"""
Test script for angle range parsing functionality.
"""

import sys
sys.path.append('src')
from filename_parser import parse_filename

# Test files with angle ranges
test_files = [
    "ACI_ESA-Inner-84to-118-Hor79_Beam-1000eV_Focus-X-pt4-Y-2_Offset-X--pt1_Y-1_Wave-Triangle_ESA--181_MCP-2200-100240922-213604.fits",
    "ACI_ESA-Inner-62-Hor79_Beam-1000eV_Focus-X-pt4-Y-2_Offset-X--pt1_Y-1_Wave-Triangle_ESA--181_MCP-2200-100240922-213604.fits",
    "ACI_ESA-Inner--30to45-Hor50_Beam-5000eV_Focus-X-1-Y-1_Offset-X-0_Y-0_Wave-Square_ESA--200_MCP-2000-50240923-120000.fits"
]

print("Testing angle range parsing:")
print("=" * 60)

for filename in test_files:
    print(f"\nFile: {filename}")
    params = parse_filename(filename)
    
    print(f"  Inner angle string: {params.inner_angle}")
    print(f"  Inner angle value: {params.inner_angle_value}")
    print(f"  Is angle range: {params.is_angle_range}")
    if hasattr(params, 'inner_angle_range') and params.inner_angle_range:
        print(f"  Angle range: {params.inner_angle_range[0]:.1f}° to {params.inner_angle_range[1]:.1f}°")
    print(f"  Beam energy: {params.beam_energy_value} eV")
    print(f"  ESA voltage: {params.esa_voltage_value} V")
