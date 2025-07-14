"""
Angular Resolution Analysis Module

This module provides tools for creating elevation/azimuth resolution plots
when beam energy and one rotation angle are held constant while ESA voltage
and another rotation angle are varied.

Author: XDL Processing Project
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import logging
from pathlib import Path

from data_model import DataManager, DataFile, ExperimentGroup
from esa_analysis import ESAAnalyzer, ImpactRegion

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AngularResolutionData:
    """Data structure for angular resolution analysis."""
    
    # Fixed parameters
    fixed_beam_energy: float
    fixed_angle_parameter: str  # 'inner_angle' or other angle parameter
    fixed_angle_value: float
    
    # Varying parameters
    varying_esa_voltages: List[float]
    varying_angles: List[float]
    varying_angle_parameter: str
    
    # Impact region data organized by (esa_voltage, angle)
    impact_regions: Dict[Tuple[float, float], ImpactRegion]
    
    # Resolution metrics
    angular_resolution_map: Optional[np.ndarray] = None
    spatial_resolution_map: Optional[np.ndarray] = None


class AngularResolutionAnalyzer:
    """Analyzer for creating elevation/azimuth resolution plots."""
    
    def __init__(self, data_directory: str = "data"):
        """Initialize the angular resolution analyzer."""
        self.data_manager = DataManager(data_directory)
        self.esa_analyzer = ESAAnalyzer(data_directory)
        
    def find_resolution_datasets(self, min_voltage_points: int = 3,
                                min_angle_points: int = 3) -> List[AngularResolutionData]:
        """
        Find datasets suitable for angular resolution analysis.

        Args:
            min_voltage_points: Minimum number of different ESA voltages required
            min_angle_points: Minimum number of different angles required

        Returns:
            List of AngularResolutionData objects
        """
        # Discover all files with complete parameters
        all_files = self.data_manager.discover_files()
        valid_files = []

        for f in all_files:
            if (f.is_fits_or_map and
                f.parameters.beam_energy_value and
                f.parameters.esa_voltage_value is not None):
                # Include files even if angle is not specified (assumed constant)
                valid_files.append(f)

        logger.info(f"Found {len(valid_files)} files with beam energy and ESA voltage")
        
        # Group by beam energy first
        energy_groups = {}
        for f in valid_files:
            energy = f.parameters.beam_energy_value
            if energy not in energy_groups:
                energy_groups[energy] = []
            energy_groups[energy].append(f)
        
        resolution_datasets = []
        
        for beam_energy, files in energy_groups.items():
            # For each beam energy, look for cases where one angle is fixed
            # and ESA voltage + another angle vary

            # Group by inner angle (treat None as a constant value)
            angle_groups = {}
            for f in files:
                angle = f.parameters.inner_angle_value
                # If angle is None, treat as "constant" (not specified in filename)
                angle_key = angle if angle is not None else "constant"
                if angle_key not in angle_groups:
                    angle_groups[angle_key] = []
                angle_groups[angle_key].append(f)
            
            # Look for groups with sufficient voltage and angle variation
            for fixed_angle_key, angle_files in angle_groups.items():
                if len(angle_files) >= min_voltage_points:

                    # Check if we have sufficient ESA voltage variation
                    voltages = set(f.parameters.esa_voltage_value for f in angle_files)

                    if len(voltages) >= min_voltage_points:

                        # Determine the actual angle value
                        if fixed_angle_key == "constant":
                            # Angle not specified in filename - assumed constant
                            fixed_angle_value = 0.0  # Default constant value
                            angle_param_name = 'inner_angle_constant'
                        else:
                            fixed_angle_value = fixed_angle_key
                            angle_param_name = 'inner_angle'

                        # Create resolution dataset
                        dataset = AngularResolutionData(
                            fixed_beam_energy=beam_energy,
                            fixed_angle_parameter=angle_param_name,
                            fixed_angle_value=fixed_angle_value,
                            varying_esa_voltages=sorted(list(voltages)),
                            varying_angles=[fixed_angle_value],  # For now, single angle
                            varying_angle_parameter='esa_voltage',  # Primary varying parameter
                            impact_regions={}
                        )
                        
                        # If we have multiple files with same voltage but different conditions,
                        # this could represent angle variation
                        voltage_groups = {}
                        for f in angle_files:
                            v = f.parameters.esa_voltage_value
                            if v not in voltage_groups:
                                voltage_groups[v] = []
                            voltage_groups[v].append(f)
                        
                        # Check for angle variation within voltage groups
                        has_angle_variation = False
                        all_varying_angles = set()
                        
                        for v, v_files in voltage_groups.items():
                            angles_in_group = set()
                            for f in v_files:
                                # Check if this represents a different angle condition
                                # Could be different horizontal values, focus positions, etc.
                                if hasattr(f.parameters, 'horizontal_value_num') and f.parameters.horizontal_value_num:
                                    angles_in_group.add(f.parameters.horizontal_value_num)
                                else:
                                    angles_in_group.add(f.parameters.inner_angle_value)
                            
                            if len(angles_in_group) > 1:
                                has_angle_variation = True
                                all_varying_angles.update(angles_in_group)
                        
                        if has_angle_variation and len(all_varying_angles) >= min_angle_points:
                            dataset.varying_angles = sorted(list(all_varying_angles))
                            dataset.varying_angle_parameter = 'horizontal_value_num'
                            resolution_datasets.append(dataset)
                        elif len(voltages) >= min_voltage_points:
                            # Even without angle variation, voltage variation is useful
                            resolution_datasets.append(dataset)
        
        logger.info(f"Found {len(resolution_datasets)} potential resolution datasets")
        return resolution_datasets
    
    def analyze_angular_resolution(self, dataset: AngularResolutionData) -> AngularResolutionData:
        """
        Analyze angular resolution for a specific dataset.
        
        Args:
            dataset: AngularResolutionData object to analyze
            
        Returns:
            Updated dataset with impact regions and resolution maps
        """
        # Find files matching the dataset criteria
        all_files = self.data_manager.discover_files()
        matching_files = []
        
        for f in all_files:
            if (f.is_fits_or_map and
                f.parameters.beam_energy_value == dataset.fixed_beam_energy and
                f.parameters.esa_voltage_value in dataset.varying_esa_voltages):

                # Check angle criteria
                if dataset.fixed_angle_parameter == 'inner_angle':
                    if (f.parameters.inner_angle_value is not None and
                        abs(f.parameters.inner_angle_value - dataset.fixed_angle_value) < 1.0):
                        matching_files.append(f)
                elif dataset.fixed_angle_parameter == 'inner_angle_constant':
                    # Angle assumed constant (not specified in filename)
                    if f.parameters.inner_angle_value is None:
                        matching_files.append(f)
        
        logger.info(f"Found {len(matching_files)} files matching resolution criteria")
        
        # Analyze impact regions for matching files
        regions = self.esa_analyzer.analyze_impact_regions(matching_files)
        
        # Organize regions by (voltage, angle) pairs
        for region in regions:
            voltage = region.esa_voltage

            # Determine the varying parameter value
            if dataset.varying_angle_parameter == 'esa_voltage':
                # ESA voltage is the primary varying parameter
                # Use the fixed angle value for all measurements
                angle = dataset.fixed_angle_value
            elif dataset.varying_angle_parameter == 'horizontal_value_num':
                # Use horizontal value as varying angle
                angle = getattr(region, 'horizontal_value', None)
                if angle is None:
                    # Try to get from parameters
                    matching_file = next((f for f in matching_files if f.filename == region.filename), None)
                    if matching_file and hasattr(matching_file.parameters, 'horizontal_value_num'):
                        angle = matching_file.parameters.horizontal_value_num
                    else:
                        angle = region.rotation_angle or dataset.fixed_angle_value
            else:
                # Use rotation angle or fixed value
                angle = region.rotation_angle if region.rotation_angle is not None else dataset.fixed_angle_value

            # Always create a key, using voltage as primary identifier
            key = (voltage, angle)
            dataset.impact_regions[key] = region
        
        # Create resolution maps
        dataset = self._create_resolution_maps(dataset)
        
        return dataset
    
    def _create_resolution_maps(self, dataset: AngularResolutionData) -> AngularResolutionData:
        """Create angular and spatial resolution maps."""
        
        if not dataset.impact_regions:
            logger.warning("No impact regions found for resolution mapping")
            return dataset
        
        # Get unique voltages and angles from actual data
        voltages = sorted(set(key[0] for key in dataset.impact_regions.keys()))
        angles = sorted(set(key[1] for key in dataset.impact_regions.keys()))
        
        # Create meshgrid for resolution maps
        V, A = np.meshgrid(voltages, angles, indexing='ij')
        
        # Initialize resolution maps
        angular_resolution = np.full(V.shape, np.nan)
        spatial_resolution = np.full(V.shape, np.nan)
        
        # Calculate resolution metrics
        for i, voltage in enumerate(voltages):
            for j, angle in enumerate(angles):
                key = (voltage, angle)
                if key in dataset.impact_regions:
                    region = dataset.impact_regions[key]
                    
                    # Angular resolution: based on region size relative to detector
                    detector_size = 1024  # pixels
                    region_size = np.sqrt(region.region_area)
                    angular_resolution[i, j] = region_size / detector_size * 100  # percentage
                    
                    # Spatial resolution: based on signal-to-noise ratio
                    spatial_resolution[i, j] = region.signal_to_noise
        
        dataset.angular_resolution_map = angular_resolution
        dataset.spatial_resolution_map = spatial_resolution
        
        return dataset
    
    def plot_elevation_azimuth_resolution(self, dataset: AngularResolutionData,
                                        save_path: Optional[str] = None) -> None:
        """
        Create elevation/azimuth resolution plots.
        
        Args:
            dataset: AngularResolutionData with analyzed data
            save_path: Optional path to save the plot
        """
        if dataset.angular_resolution_map is None:
            logger.error("No resolution data available for plotting")
            return
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Get voltage and angle arrays
        voltages = dataset.varying_esa_voltages
        angles = dataset.varying_angles
        
        # If we only have one angle, create a simple voltage plot
        if len(angles) == 1:
            self._plot_voltage_sweep(dataset, axes, voltages)
        else:
            self._plot_2d_resolution_maps(dataset, axes, voltages, angles)
        
        # Overall title
        fig.suptitle(f'ESA Angular Resolution Analysis\n'
                    f'Beam Energy: {dataset.fixed_beam_energy:.0f} eV, '
                    f'Fixed {dataset.fixed_angle_parameter}: {dataset.fixed_angle_value:.1f}°',
                    fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Resolution plot saved to {save_path}")
        
        plt.show()
    
    def _plot_voltage_sweep(self, dataset: AngularResolutionData, axes, voltages):
        """Plot resolution vs voltage for single angle case."""
        
        # Extract data for plotting
        voltage_data = []
        angular_res_data = []
        spatial_res_data = []
        centroid_x_data = []
        centroid_y_data = []
        
        for voltage in voltages:
            for key, region in dataset.impact_regions.items():
                if abs(key[0] - voltage) < 0.1:  # Match voltage
                    voltage_data.append(voltage)
                    
                    # Calculate angular resolution
                    region_size = np.sqrt(region.region_area)
                    angular_res = region_size / 1024 * 100
                    angular_res_data.append(angular_res)
                    
                    spatial_res_data.append(region.signal_to_noise)
                    centroid_x_data.append(region.centroid_x)
                    centroid_y_data.append(region.centroid_y)
        
        # Plot 1: Angular resolution vs voltage
        axes[0, 0].scatter(voltage_data, angular_res_data, alpha=0.7, s=50)
        axes[0, 0].set_xlabel('ESA Voltage (V)')
        axes[0, 0].set_ylabel('Angular Resolution (%)')
        axes[0, 0].set_title('Angular Resolution vs ESA Voltage')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Plot 2: Spatial resolution vs voltage
        axes[0, 1].scatter(voltage_data, spatial_res_data, alpha=0.7, s=50, color='orange')
        axes[0, 1].set_xlabel('ESA Voltage (V)')
        axes[0, 1].set_ylabel('Signal-to-Noise Ratio')
        axes[0, 1].set_title('Signal Quality vs ESA Voltage')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Plot 3: Centroid position vs voltage
        axes[1, 0].scatter(voltage_data, centroid_x_data, alpha=0.7, s=50, color='green')
        axes[1, 0].set_xlabel('ESA Voltage (V)')
        axes[1, 0].set_ylabel('Centroid X Position (pixels)')
        axes[1, 0].set_title('Beam Position vs ESA Voltage')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Plot 4: K-factor consistency
        k_factors = [dataset.fixed_beam_energy / abs(v) for v in voltage_data]
        axes[1, 1].scatter(voltage_data, k_factors, alpha=0.7, s=50, color='red')
        axes[1, 1].set_xlabel('ESA Voltage (V)')
        axes[1, 1].set_ylabel('K-Factor (eV/V)')
        axes[1, 1].set_title('K-Factor vs ESA Voltage')
        axes[1, 1].grid(True, alpha=0.3)
    
    def _plot_2d_resolution_maps(self, dataset: AngularResolutionData, axes, voltages, angles):
        """Plot 2D resolution maps for elevation/azimuth analysis."""
        
        # Create meshgrid
        V, A = np.meshgrid(voltages, angles, indexing='ij')
        
        # Plot 1: Angular resolution map
        im1 = axes[0, 0].contourf(A, V, dataset.angular_resolution_map, levels=20, cmap='viridis')
        axes[0, 0].set_xlabel(f'{dataset.varying_angle_parameter} (°)')
        axes[0, 0].set_ylabel('ESA Voltage (V)')
        axes[0, 0].set_title('Angular Resolution Map (%)')
        plt.colorbar(im1, ax=axes[0, 0])
        
        # Plot 2: Spatial resolution map
        im2 = axes[0, 1].contourf(A, V, dataset.spatial_resolution_map, levels=20, cmap='plasma')
        axes[0, 1].set_xlabel(f'{dataset.varying_angle_parameter} (°)')
        axes[0, 1].set_ylabel('ESA Voltage (V)')
        axes[0, 1].set_title('Signal-to-Noise Map')
        plt.colorbar(im2, ax=axes[0, 1])
        
        # Plot 3: Impact region positions
        for key, region in dataset.impact_regions.items():
            voltage, angle = key
            axes[1, 0].scatter(region.centroid_x, region.centroid_y, 
                             c=voltage, s=50, alpha=0.7, cmap='coolwarm')
        axes[1, 0].set_xlabel('X Position (pixels)')
        axes[1, 0].set_ylabel('Y Position (pixels)')
        axes[1, 0].set_title('Impact Region Positions')
        
        # Plot 4: K-factor map
        k_factor_map = np.full(V.shape, np.nan)
        for i, voltage in enumerate(voltages):
            for j, angle in enumerate(angles):
                if (voltage, angle) in dataset.impact_regions:
                    k_factor_map[i, j] = dataset.fixed_beam_energy / abs(voltage)
        
        im4 = axes[1, 1].contourf(A, V, k_factor_map, levels=20, cmap='RdYlBu')
        axes[1, 1].set_xlabel(f'{dataset.varying_angle_parameter} (°)')
        axes[1, 1].set_ylabel('ESA Voltage (V)')
        axes[1, 1].set_title('K-Factor Map (eV/V)')
        plt.colorbar(im4, ax=axes[1, 1])


def main():
    """Main function for angular resolution analysis."""
    analyzer = AngularResolutionAnalyzer()
    
    # Find potential resolution datasets
    datasets = analyzer.find_resolution_datasets(min_voltage_points=2, min_angle_points=1)
    
    if not datasets:
        print("No suitable datasets found for angular resolution analysis")
        return
    
    print(f"Found {len(datasets)} potential resolution datasets:")
    
    for i, dataset in enumerate(datasets):
        print(f"\nDataset {i+1}:")
        print(f"  Beam Energy: {dataset.fixed_beam_energy} eV")
        print(f"  Fixed {dataset.fixed_angle_parameter}: {dataset.fixed_angle_value}°")
        print(f"  ESA Voltages: {dataset.varying_esa_voltages}")
        print(f"  Varying angles: {dataset.varying_angles}")
        
        # Analyze the first dataset
        if i == 0:
            print(f"\nAnalyzing dataset {i+1}...")
            analyzed_dataset = analyzer.analyze_angular_resolution(dataset)
            
            if analyzed_dataset.impact_regions:
                print(f"Found {len(analyzed_dataset.impact_regions)} impact regions")
                
                # Create resolution plot
                save_path = f"results/angular_resolution_analysis_{i+1}.png"
                analyzer.plot_elevation_azimuth_resolution(analyzed_dataset, save_path)
            else:
                print("No impact regions found for this dataset")


if __name__ == "__main__":
    main()
