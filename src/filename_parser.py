"""
Filename Parameter Extraction Module

This module provides functionality to parse experimental parameters from 
structured filenames in the XDL Processing project.

Author: XDL Processing Project
"""

import re
import os
from datetime import datetime
from typing import Dict, Optional, List, Union, Tuple
from dataclasses import dataclass


@dataclass
class ExperimentalParameters:
    """Data class to hold experimental parameters extracted from filenames."""
    
    # Basic file info
    filename: str
    file_type: str  # 'fits', 'map', 'phd'
    base_name: str
    
    # Experimental parameters
    beam_energy: Optional[str] = None
    beam_energy_value: Optional[float] = None
    beam_energy_unit: Optional[str] = None
    
    esa_voltage: Optional[str] = None
    esa_voltage_value: Optional[float] = None
    
    mcp_voltage: Optional[str] = None
    mcp_voltage_value: Optional[float] = None
    
    inner_angle: Optional[str] = None
    inner_angle_value: Optional[float] = None
    inner_angle_range: Optional[Tuple[float, float]] = None  # For angle ranges like "84to-118"
    is_angle_range: bool = False
    
    horizontal_value: Optional[str] = None
    horizontal_value_num: Optional[float] = None
    
    focus_x: Optional[str] = None
    focus_y: Optional[str] = None
    offset_x: Optional[str] = None
    offset_y: Optional[str] = None
    
    wave_type: Optional[str] = None
    
    # Timestamp info
    timestamp: Optional[str] = None
    datetime_obj: Optional[datetime] = None
    
    # Special flags
    is_dark: bool = False
    is_ramp: bool = False
    is_rotating: bool = False
    
    # Additional metadata
    test_type: Optional[str] = None
    sequence_info: Optional[str] = None


class FilenameParser:
    """Parser for extracting experimental parameters from structured filenames."""
    
    def __init__(self):
        """Initialize the filename parser with regex patterns."""
        
        # Compile regex patterns for different filename formats
        self.patterns = {
            # Pattern for detailed parameter files
            'detailed': re.compile(
                r'ACI_ESA-Inner-(?P<inner_angle>-?\d+(?:to-?\d+)?)-Hor(?P<hor_value>\d+)_'
                r'Beam-(?P<beam_energy>\d+(?:\.\d+)?(?:k)?eV)_'
                r'Focus-X-(?P<focus_x>[\w\-\.]+)-Y-(?P<focus_y>[\w\-\.]+)_'
                r'Offset-X-(?P<offset_x>[\w\-\.]+)_Y-(?P<offset_y>[\w\-\.]+)_'
                r'Wave-(?P<wave_type>\w+)_'
                r'ESA-(?P<esa_voltage>-?\d+(?:\.\d+)?)_'
                r'MCP-(?P<mcp_voltage>\d+(?:\.\d+)?)-(?P<mcp_extra>\d+)'
                r'(?P<timestamp>\d{6}-\d{6})?'
            ),
            
            # Pattern for simple energy files
            'simple_energy': re.compile(
                r'ACI\s+ESA\s+(?P<beam_energy>\d+(?:\.\d+)?(?:k)?eV)'
                r'(?P<timestamp>\d{6}-\d{6})?'
            ),
            
            # Pattern for voltage and energy files
            'voltage_energy': re.compile(
                r'ACI\s+ESA\s+(?P<esa_voltage>\d+)V\s+(?P<beam_energy>\d+(?:\.\d+)?[kK]?[eE]V)\s+BEAM'
                r'(?P<timestamp>\d{6}-\d{6})?'
            ),

            # Pattern for beam prep files
            'beam_prep': re.compile(
                r'ACI\s+ESA\s+(?P<beam_energy>\d+(?:\.\d+)?[kK]?[eE]V)\s+BEAM\s+PREP'
                r'(?P<timestamp>\d{6}-\d{6})?'
            ),
            
            # Pattern for ramp up files
            'ramp_up': re.compile(
                r'ACI\s+(?:ESA\s+)?RAMP\s+UP(?:\s+(?P<sequence>\w+\d*))?'
                r'(?:\s+(?P<date>\d{8}))?'
                r'(?:\s+ESA\s+(?P<esa_voltage>\d+)V)?'
                r'(?P<timestamp>\d{6}-\d{6})?'
            ),
            
            # Pattern for dark files
            'dark': re.compile(
                r'ACI\s+ESA\s+Dark\s+(?P<date>\d{6})(?:\.fits)?'
                r'(?P<timestamp>\d{6}-\d{6})?'
            ),
            
            # Pattern for rotating files
            'rotating': re.compile(
                r'ACI_ESA_Rotating(?P<sequence>\d+)?_'
                r'Beam-(?P<beam_energy>\d+(?:\.\d+)?(?:k)?eV)_'
                r'Focus-X-(?P<focus_x>[\w\-\.]+)-Y-(?P<focus_y>[\w\-\.]+)_'
                r'Offset-X-(?P<offset_x>[\w\-\.]+)_Y-(?P<offset_y>[\w\-\.]+)_'
                r'Wave-(?P<wave_type>\w+)_'
                r'ESA-(?P<esa_voltage>-?\d+(?:\.\d+)?)_'
                r'MCP-(?P<mcp_voltage>\d+(?:\.\d+)?)-(?P<mcp_extra>\d+)'
                r'(?P<timestamp>\d{6}-\d{6})?'
            )
        }
    
    def parse_filename(self, filename: str) -> ExperimentalParameters:
        """
        Parse a filename and extract experimental parameters.
        
        Args:
            filename: The filename to parse
            
        Returns:
            ExperimentalParameters object with extracted parameters
        """
        # Get base filename without path
        base_name = os.path.basename(filename)
        
        # Determine file type
        file_type = self._get_file_type(base_name)
        
        # Remove file extension for parsing
        name_for_parsing = self._clean_filename_for_parsing(base_name)
        
        # Initialize parameters object
        params = ExperimentalParameters(
            filename=filename,
            file_type=file_type,
            base_name=base_name
        )
        
        # Try each pattern to find a match
        for pattern_name, pattern in self.patterns.items():
            match = pattern.search(name_for_parsing)
            if match:
                self._extract_parameters_from_match(params, match, pattern_name)
                break
        
        # Post-process extracted parameters
        self._post_process_parameters(params)
        
        return params
    
    def _get_file_type(self, filename: str) -> str:
        """Determine the file type from the filename."""
        if filename.endswith('.fits'):
            return 'fits'
        elif filename.endswith('.map'):
            return 'map'
        elif filename.endswith('.phd'):
            return 'phd'
        else:
            return 'unknown'
    
    def _clean_filename_for_parsing(self, filename: str) -> str:
        """Clean filename for parsing by removing extensions."""
        # Remove .fits.map, .fits.phd, .fits, .map, .phd extensions
        name = filename
        if name.endswith('.fits.map'):
            name = name[:-9]
        elif name.endswith('.fits.phd'):
            name = name[:-9]
        elif name.endswith('.fits'):
            name = name[:-5]
        elif name.endswith('.map'):
            name = name[:-4]
        elif name.endswith('.phd'):
            name = name[:-4]
        
        return name
    
    def _extract_parameters_from_match(self, params: ExperimentalParameters, 
                                     match: re.Match, pattern_name: str) -> None:
        """Extract parameters from a regex match."""
        groups = match.groupdict()
        
        # Extract beam energy
        if 'beam_energy' in groups and groups['beam_energy']:
            params.beam_energy = groups['beam_energy']
            params.beam_energy_value, params.beam_energy_unit = self._parse_energy(groups['beam_energy'])
        
        # Extract ESA voltage
        if 'esa_voltage' in groups and groups['esa_voltage']:
            params.esa_voltage = groups['esa_voltage']
            params.esa_voltage_value = float(groups['esa_voltage'])
        
        # Extract MCP voltage
        if 'mcp_voltage' in groups and groups['mcp_voltage']:
            params.mcp_voltage = groups['mcp_voltage']
            params.mcp_voltage_value = float(groups['mcp_voltage'])
        
        # Extract inner angle
        if 'inner_angle' in groups and groups['inner_angle']:
            params.inner_angle = groups['inner_angle']
            angle_result = self._parse_angle(groups['inner_angle'])
            if isinstance(angle_result, tuple):
                params.inner_angle_range = angle_result
                params.inner_angle_value = (angle_result[0] + angle_result[1]) / 2  # Use midpoint
                params.is_angle_range = True
            else:
                params.inner_angle_value = angle_result
                params.is_angle_range = False
        
        # Extract horizontal value
        if 'hor_value' in groups and groups['hor_value']:
            params.horizontal_value = groups['hor_value']
            params.horizontal_value_num = float(groups['hor_value'])
        
        # Extract focus and offset values
        for param in ['focus_x', 'focus_y', 'offset_x', 'offset_y']:
            if param in groups and groups[param]:
                setattr(params, param, groups[param])
        
        # Extract wave type
        if 'wave_type' in groups and groups['wave_type']:
            params.wave_type = groups['wave_type']
        
        # Extract timestamp
        if 'timestamp' in groups and groups['timestamp']:
            params.timestamp = groups['timestamp']
            params.datetime_obj = self._parse_timestamp(groups['timestamp'])
        
        # Extract sequence info
        if 'sequence' in groups and groups['sequence']:
            params.sequence_info = groups['sequence']
        
        # Set special flags based on pattern
        if pattern_name == 'dark':
            params.is_dark = True
        elif pattern_name == 'ramp_up':
            params.is_ramp = True
        elif pattern_name == 'rotating':
            params.is_rotating = True
    
    def _parse_energy(self, energy_str: str) -> tuple[float, str]:
        """Parse energy string and return value and unit."""
        if (energy_str.endswith('keV') or energy_str.endswith('kEV') or
            energy_str.endswith('KEV') or energy_str.endswith('KeV')):
            value = float(energy_str[:-3])
            return value * 1000, 'eV'  # Convert to eV
        elif energy_str.endswith('eV') or energy_str.endswith('EV'):
            value = float(energy_str[:-2])
            return value, 'eV'
        else:
            # Assume eV if no unit
            return float(energy_str), 'eV'
    
    def _parse_angle(self, angle_str: str) -> Union[float, Tuple[float, float]]:
        """Parse angle string and return numeric value or range."""
        # Handle range angles like "84to-118"
        if 'to' in angle_str:
            parts = angle_str.split('to')
            if len(parts) == 2:
                try:
                    angle1 = float(parts[0])
                    angle2 = float(parts[1])
                    return (min(angle1, angle2), max(angle1, angle2))  # Return as (min, max) tuple
                except ValueError:
                    logger.warning(f"Could not parse angle range: {angle_str}")
                    return float(parts[0])  # Fallback to first angle
            else:
                return float(parts[0])
        else:
            return float(angle_str)
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string and return datetime object."""
        try:
            # Format: YYMMDD-HHMMSS
            return datetime.strptime(timestamp_str, '%y%m%d-%H%M%S')
        except ValueError:
            return None
    
    def _post_process_parameters(self, params: ExperimentalParameters) -> None:
        """Post-process extracted parameters for consistency."""
        # Set test type based on extracted parameters
        if params.is_dark:
            params.test_type = 'dark'
        elif params.is_ramp:
            params.test_type = 'ramp_up'
        elif params.is_rotating:
            params.test_type = 'rotating'
        elif params.beam_energy and params.esa_voltage:
            params.test_type = 'voltage_sweep'
        elif params.beam_energy:
            params.test_type = 'energy_test'
        else:
            params.test_type = 'unknown'


def parse_filename(filename: str) -> ExperimentalParameters:
    """
    Convenience function to parse a single filename.
    
    Args:
        filename: The filename to parse
        
    Returns:
        ExperimentalParameters object with extracted parameters
    """
    parser = FilenameParser()
    return parser.parse_filename(filename)


def parse_filenames(filenames: List[str]) -> List[ExperimentalParameters]:
    """
    Parse multiple filenames and return a list of parameter objects.
    
    Args:
        filenames: List of filenames to parse
        
    Returns:
        List of ExperimentalParameters objects
    """
    parser = FilenameParser()
    return [parser.parse_filename(filename) for filename in filenames]


if __name__ == "__main__":
    # Test the parser with sample filenames
    test_files = [
        "ACI ESA 1000eV240922-190315.fits",
        "ACI ESA 912V 5KEV BEAM240921-215501.fits",
        "ACI_ESA-Inner-62-Hor79_Beam-1000eV_Focus-X-pt4-Y-2_Offset-X--pt1_Y-1_Wave-Triangle_ESA--181_MCP-2200-100240922-213604.fits",
        "ACI ESA Dark 240922.fits240922-183755.fits",
        "ACI ESA RAMP UP3240920-222421.fits"
    ]
    
    for filename in test_files:
        params = parse_filename(filename)
        print(f"\nFile: {filename}")
        print(f"  Type: {params.test_type}")
        print(f"  Beam Energy: {params.beam_energy_value} {params.beam_energy_unit}")
        print(f"  ESA Voltage: {params.esa_voltage_value}")
        print(f"  Timestamp: {params.datetime_obj}")
