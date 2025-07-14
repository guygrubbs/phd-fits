#!/usr/bin/env python3

import sys
sys.path.append('src')
from filename_parser import parse_filename

# Test with actual files from data directory
test_files = [
    'ACI ESA 1000eV240922-190315.fits',
    'ACI ESA 912V 5KEV BEAM240921-215501.fits',
    'ACI_ESA-Inner-62-Hor79_Beam-1000eV_Focus-X-pt4-Y-2_Offset-X--pt1_Y-1_Wave-Triangle_ESA--181_MCP-2200-100240922-213604.fits',
    'ACI ESA Dark 240922.fits240922-183755.fits',
    'ACI ESA RAMP UP3240920-222421.fits'
]

for filename in test_files:
    print(f"Testing: {filename}")
    params = parse_filename(filename)
    print(f"  Type: {params.test_type}")
    print(f"  Beam Energy: {params.beam_energy_value} {params.beam_energy_unit}")
    print(f"  ESA Voltage: {params.esa_voltage_value}")
    print(f"  Inner Angle: {params.inner_angle_value}")
    print(f"  Horizontal: {params.horizontal_value_num}")
    print(f"  Timestamp: {params.datetime_obj}")
    print()
