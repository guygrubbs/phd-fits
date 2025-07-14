"""
Data Model and File Management Module

This module provides classes and functions for managing experimental data files
in the XDL Processing project, including file discovery, parameter extraction,
and data organization.

Author: XDL Processing Project
"""

import os
import glob
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np

from filename_parser import ExperimentalParameters, FilenameParser
from fits_handler import FitsHandler, FitsData


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DataFile:
    """Represents a single experimental data file with metadata."""
    
    filepath: str
    parameters: ExperimentalParameters
    file_type: str  # 'fits', 'map', 'phd'
    file_size: Optional[int] = None
    
    # Data content (loaded on demand)
    fits_data: Optional[FitsData] = None
    phd_data: Optional[Dict[str, np.ndarray]] = None
    
    # Processing flags
    is_loaded: bool = False
    has_errors: bool = False
    error_messages: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize file size and validate file existence."""
        if os.path.exists(self.filepath):
            self.file_size = os.path.getsize(self.filepath)
        else:
            self.has_errors = True
            self.error_messages.append(f"File not found: {self.filepath}")
    
    @property
    def filename(self) -> str:
        """Get the filename without path."""
        return os.path.basename(self.filepath)
    
    @property
    def is_fits_or_map(self) -> bool:
        """Check if file is FITS or MAP format."""
        return self.file_type in ['fits', 'map']
    
    @property
    def is_phd(self) -> bool:
        """Check if file is PHD format."""
        return self.file_type == 'phd'


@dataclass
class ExperimentGroup:
    """Represents a group of related experimental files."""
    
    name: str
    description: str
    files: List[DataFile] = field(default_factory=list)
    
    # Grouping criteria
    common_parameters: Dict[str, Any] = field(default_factory=dict)
    varying_parameters: List[str] = field(default_factory=list)
    
    def add_file(self, data_file: DataFile):
        """Add a file to this group."""
        self.files.append(data_file)
    
    def get_files_by_parameter(self, parameter: str, value: Any) -> List[DataFile]:
        """Get files that match a specific parameter value."""
        matching_files = []
        for file in self.files:
            param_value = getattr(file.parameters, parameter, None)
            if param_value == value:
                matching_files.append(file)
        return matching_files
    
    def get_parameter_values(self, parameter: str) -> List[Any]:
        """Get all unique values for a parameter in this group."""
        values = set()
        for file in self.files:
            param_value = getattr(file.parameters, parameter, None)
            if param_value is not None:
                values.add(param_value)
        return sorted(list(values))


class DataManager:
    """Manages experimental data files and provides organization capabilities."""
    
    def __init__(self, data_directory: str = "data"):
        """
        Initialize the data manager.
        
        Args:
            data_directory: Path to the directory containing data files
        """
        self.data_directory = Path(data_directory)
        self.filename_parser = FilenameParser()
        self.fits_handler = FitsHandler()
        
        # Storage for discovered files and groups
        self.files: List[DataFile] = []
        self.groups: List[ExperimentGroup] = []
        
        # File type patterns
        self.file_patterns = {
            'fits': '*.fits',
            'map': '*.map',
            'phd': '*.phd'
        }
    
    def discover_files(self) -> List[DataFile]:
        """
        Discover all data files in the data directory.
        
        Returns:
            List of DataFile objects
        """
        self.files = []
        
        if not self.data_directory.exists():
            logger.error(f"Data directory not found: {self.data_directory}")
            return self.files
        
        # Find files of each type
        for file_type, pattern in self.file_patterns.items():
            file_paths = glob.glob(str(self.data_directory / pattern))
            
            for filepath in file_paths:
                try:
                    # Parse filename to extract parameters
                    parameters = self.filename_parser.parse_filename(filepath)
                    
                    # Create DataFile object
                    data_file = DataFile(
                        filepath=filepath,
                        parameters=parameters,
                        file_type=file_type
                    )
                    
                    self.files.append(data_file)
                    
                except Exception as e:
                    logger.error(f"Error processing file {filepath}: {str(e)}")
        
        logger.info(f"Discovered {len(self.files)} data files")
        return self.files
    
    def load_file_data(self, data_file: DataFile) -> bool:
        """
        Load data content for a specific file.
        
        Args:
            data_file: DataFile object to load
            
        Returns:
            True if loading was successful, False otherwise
        """
        if data_file.is_loaded or data_file.has_errors:
            return not data_file.has_errors
        
        try:
            if data_file.is_fits_or_map:
                # Load FITS or MAP file
                if data_file.file_type == 'fits':
                    data_file.fits_data = self.fits_handler.read_fits_file(data_file.filepath)
                else:  # map file
                    # Try to read as legacy map file first
                    image_data = self.fits_handler.read_legacy_map_file(data_file.filepath)
                    if image_data is not None:
                        # Create a FitsData object for consistency
                        data_file.fits_data = FitsData(
                            filename=data_file.filename,
                            data=image_data,
                            shape=image_data.shape,
                            dtype=str(image_data.dtype)
                        )
                    else:
                        # Try reading as regular FITS file
                        data_file.fits_data = self.fits_handler.read_fits_file(data_file.filepath)
                
                if data_file.fits_data and data_file.fits_data.has_errors:
                    data_file.has_errors = True
                    data_file.error_messages.extend(data_file.fits_data.error_messages)
                    
            elif data_file.is_phd:
                # Load PHD file
                data_file.phd_data = self._load_phd_file(data_file.filepath)
                
            data_file.is_loaded = True
            return not data_file.has_errors
            
        except Exception as e:
            error_msg = f"Error loading data from {data_file.filepath}: {str(e)}"
            data_file.error_messages.append(error_msg)
            data_file.has_errors = True
            logger.error(error_msg)
            return False
    
    def _load_phd_file(self, filepath: str) -> Dict[str, np.ndarray]:
        """
        Load PHD (Pulse Height Distribution) file.
        
        Args:
            filepath: Path to the PHD file
            
        Returns:
            Dictionary with 'adc_bins' and 'counts' arrays
        """
        try:
            # Read tab-separated data
            data = np.loadtxt(filepath, delimiter='\t')
            
            if data.shape[1] >= 2:
                return {
                    'adc_bins': data[:, 0],
                    'counts': data[:, 1]
                }
            else:
                raise ValueError("PHD file must have at least 2 columns (ADC bins and counts)")
                
        except Exception as e:
            logger.error(f"Error loading PHD file {filepath}: {str(e)}")
            raise
    
    def group_files_by_parameter(self, parameter: str, 
                                min_group_size: int = 2) -> List[ExperimentGroup]:
        """
        Group files by a specific parameter value.
        
        Args:
            parameter: Parameter name to group by (e.g., 'beam_energy_value')
            min_group_size: Minimum number of files required for a group
            
        Returns:
            List of ExperimentGroup objects
        """
        groups = {}
        
        for file in self.files:
            param_value = getattr(file.parameters, parameter, None)
            if param_value is not None:
                key = str(param_value)
                if key not in groups:
                    groups[key] = ExperimentGroup(
                        name=f"{parameter}_{key}",
                        description=f"Files with {parameter} = {param_value}",
                        common_parameters={parameter: param_value}
                    )
                groups[key].add_file(file)
        
        # Filter groups by minimum size
        valid_groups = [group for group in groups.values() 
                       if len(group.files) >= min_group_size]
        
        return valid_groups
    
    def group_files_by_multiple_parameters(self, parameters: List[str],
                                         min_group_size: int = 2) -> List[ExperimentGroup]:
        """
        Group files by multiple parameter values.
        
        Args:
            parameters: List of parameter names to group by
            min_group_size: Minimum number of files required for a group
            
        Returns:
            List of ExperimentGroup objects
        """
        groups = {}
        
        for file in self.files:
            # Create a key from all parameter values
            key_parts = []
            param_dict = {}
            
            for param in parameters:
                param_value = getattr(file.parameters, param, None)
                if param_value is not None:
                    key_parts.append(f"{param}_{param_value}")
                    param_dict[param] = param_value
                else:
                    key_parts.append(f"{param}_None")
                    param_dict[param] = None
            
            if key_parts:  # Only group if we have at least some parameters
                key = "_".join(key_parts)
                if key not in groups:
                    groups[key] = ExperimentGroup(
                        name=key,
                        description=f"Files with {', '.join([f'{p}={v}' for p, v in param_dict.items()])}",
                        common_parameters=param_dict
                    )
                groups[key].add_file(file)
        
        # Filter groups by minimum size
        valid_groups = [group for group in groups.values() 
                       if len(group.files) >= min_group_size]
        
        return valid_groups
    
    def find_comparison_sets(self, fixed_parameters: List[str], 
                           varying_parameter: str) -> List[ExperimentGroup]:
        """
        Find sets of files suitable for comparison where some parameters are fixed
        and one parameter varies.
        
        Args:
            fixed_parameters: Parameters that should be constant within each set
            varying_parameter: Parameter that should vary within each set
            
        Returns:
            List of ExperimentGroup objects suitable for comparison
        """
        # First group by fixed parameters
        comparison_groups = self.group_files_by_multiple_parameters(fixed_parameters, min_group_size=2)
        
        # Filter groups that have variation in the varying parameter
        valid_comparison_groups = []
        
        for group in comparison_groups:
            varying_values = group.get_parameter_values(varying_parameter)
            if len(varying_values) > 1:  # Must have at least 2 different values
                group.varying_parameters = [varying_parameter]
                group.description += f", varying {varying_parameter}"
                valid_comparison_groups.append(group)
        
        return valid_comparison_groups
    
    def get_files_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all discovered files.
        
        Returns:
            Dictionary with file statistics and information
        """
        summary = {
            'total_files': len(self.files),
            'by_type': {},
            'by_test_type': {},
            'beam_energies': set(),
            'esa_voltages': set(),
            'timestamps': [],
            'file_sizes': []
        }
        
        for file in self.files:
            # Count by file type
            file_type = file.file_type
            summary['by_type'][file_type] = summary['by_type'].get(file_type, 0) + 1
            
            # Count by test type
            test_type = file.parameters.test_type
            summary['by_test_type'][test_type] = summary['by_test_type'].get(test_type, 0) + 1
            
            # Collect parameter values
            if file.parameters.beam_energy_value:
                summary['beam_energies'].add(file.parameters.beam_energy_value)
            if file.parameters.esa_voltage_value:
                summary['esa_voltages'].add(file.parameters.esa_voltage_value)
            if file.parameters.datetime_obj:
                summary['timestamps'].append(file.parameters.datetime_obj)
            if file.file_size:
                summary['file_sizes'].append(file.file_size)
        
        # Convert sets to sorted lists
        summary['beam_energies'] = sorted(list(summary['beam_energies']))
        summary['esa_voltages'] = sorted(list(summary['esa_voltages']))
        summary['timestamps'] = sorted(summary['timestamps'])
        
        return summary


if __name__ == "__main__":
    # Test the data manager
    manager = DataManager()
    
    # Discover files
    files = manager.discover_files()
    print(f"Discovered {len(files)} files")
    
    # Get summary
    summary = manager.get_files_summary()
    print(f"\nFile Summary:")
    print(f"  Total files: {summary['total_files']}")
    print(f"  By type: {summary['by_type']}")
    print(f"  By test type: {summary['by_test_type']}")
    print(f"  Beam energies: {summary['beam_energies']}")
    print(f"  ESA voltages: {summary['esa_voltages']}")
    
    # Test grouping
    energy_groups = manager.group_files_by_parameter('beam_energy_value')
    print(f"\nEnergy groups: {len(energy_groups)}")
    for group in energy_groups:
        print(f"  {group.name}: {len(group.files)} files")
    
    # Test comparison sets
    comparison_sets = manager.find_comparison_sets(['beam_energy_value'], 'esa_voltage_value')
    print(f"\nComparison sets: {len(comparison_sets)}")
    for group in comparison_sets:
        print(f"  {group.name}: {len(group.files)} files")
