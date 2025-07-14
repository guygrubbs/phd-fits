"""
Elevation vs Azimuth Analysis Module

This module creates elevation vs azimuth plots showing count rates at different
angular positions, with proper normalization for varying data collection rates.

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
import os

from data_model import DataManager, DataFile
from esa_analysis import ESAAnalyzer, ImpactRegion
from fits_handler import FitsHandler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AngularMeasurement:
    """Data structure for a single angular measurement with rate normalization."""
    
    filename: str
    beam_energy: float
    esa_voltage: float
    
    # Angular coordinates (elevation/azimuth interpretation)
    elevation_angle: Optional[float] = None  # Inner angle or primary rotation
    azimuth_angle: Optional[float] = None    # Horizontal angle or secondary rotation
    
    # Spatial impact data
    centroid_x: float = 0.0
    centroid_y: float = 0.0
    total_counts: float = 0.0
    peak_counts: float = 0.0
    region_area: int = 0
    
    # Rate normalization
    collection_time: Optional[float] = None  # If available from metadata
    count_rate: Optional[float] = None       # Counts per unit time
    normalized_intensity: float = 0.0        # Normalized for comparison
    
    # Data quality
    signal_to_noise: float = 0.0
    data_density: float = 0.0


class ElevationAzimuthAnalyzer:
    """Analyzer for creating elevation vs azimuth count rate plots."""
    
    def __init__(self, data_directory: str = "data"):
        """Initialize the elevation/azimuth analyzer."""
        self.data_manager = DataManager(data_directory)
        self.esa_analyzer = ESAAnalyzer(data_directory)
        self.fits_handler = FitsHandler()
        
    def find_angular_datasets(self, beam_energy: float = None) -> Dict[float, List[DataFile]]:
        """
        Find datasets suitable for elevation vs azimuth analysis.
        
        Args:
            beam_energy: Specific beam energy to analyze (optional)
            
        Returns:
            Dictionary mapping beam energies to lists of files
        """
        all_files = self.data_manager.discover_files()
        angular_files = []
        
        # Filter files with angular information
        for f in all_files:
            if (f.is_fits_or_map and 
                f.parameters.beam_energy_value and 
                f.parameters.esa_voltage_value is not None):
                
                # Check if we have angular information
                has_angles = (f.parameters.inner_angle_value is not None or 
                            f.parameters.horizontal_value_num is not None)
                
                if has_angles:
                    angular_files.append(f)
        
        logger.info(f"Found {len(angular_files)} files with angular information")
        
        # Group by beam energy
        energy_groups = {}
        for f in angular_files:
            energy = f.parameters.beam_energy_value
            if beam_energy is None or abs(energy - beam_energy) < 1.0:
                if energy not in energy_groups:
                    energy_groups[energy] = []
                energy_groups[energy].append(f)
        
        return energy_groups
    
    def analyze_angular_measurements(self, files: List[DataFile]) -> List[AngularMeasurement]:
        """
        Analyze files to extract angular measurements with rate normalization.
        
        Args:
            files: List of files to analyze
            
        Returns:
            List of AngularMeasurement objects
        """
        measurements = []
        
        # First pass: analyze impact regions
        regions = self.esa_analyzer.analyze_impact_regions(files)
        
        # Create measurement objects with rate normalization
        for region in regions:
            # Find corresponding file
            matching_file = next((f for f in files if f.filename == region.filename), None)
            if not matching_file:
                continue
            
            params = matching_file.parameters
            
            # Determine elevation and azimuth angles
            elevation_angle = self._extract_elevation_angle(params)
            azimuth_angle = self._extract_azimuth_angle(params)
            
            # Calculate count rate and normalization
            measurement = AngularMeasurement(
                filename=region.filename,
                beam_energy=region.beam_energy,
                esa_voltage=region.esa_voltage,
                elevation_angle=elevation_angle,
                azimuth_angle=azimuth_angle,
                centroid_x=region.centroid_x,
                centroid_y=region.centroid_y,
                total_counts=region.total_intensity,
                peak_counts=region.peak_intensity,
                region_area=region.region_area,
                signal_to_noise=region.signal_to_noise,
                data_density=region.data_density
            )
            
            # Estimate collection time and calculate rate
            measurement = self._estimate_collection_rate(measurement, matching_file)
            
            measurements.append(measurement)
        
        # Normalize intensities across all measurements
        measurements = self._normalize_measurements(measurements)
        
        return measurements
    
    def _extract_elevation_angle(self, params) -> Optional[float]:
        """Extract elevation angle from parameters."""
        # Primary rotation angle (inner angle) as elevation
        if params.inner_angle_value is not None:
            return params.inner_angle_value
        
        # If no inner angle, check for other angle parameters
        if hasattr(params, 'rotation_angle') and params.rotation_angle is not None:
            return params.rotation_angle
        
        return None
    
    def _extract_azimuth_angle(self, params) -> Optional[float]:
        """Extract azimuth angle from parameters."""
        # Horizontal value as azimuth
        if params.horizontal_value_num is not None:
            return params.horizontal_value_num
        
        # Could extend to use other parameters like focus positions
        # as azimuth indicators if needed
        
        return None
    
    def _estimate_collection_rate(self, measurement: AngularMeasurement, 
                                data_file: DataFile) -> AngularMeasurement:
        """
        Estimate collection time and calculate count rate.
        
        Args:
            measurement: AngularMeasurement to update
            data_file: Original data file for metadata
            
        Returns:
            Updated measurement with rate information
        """
        # Try to extract collection time from FITS header if available
        collection_time = None
        
        if data_file.fits_data and data_file.fits_data.header:
            # Look for common exposure time keywords
            time_keywords = ['EXPTIME', 'EXPOSURE', 'OBSTIME', 'TELAPSE', 'LIVETIME']
            for keyword in time_keywords:
                if keyword in data_file.fits_data.header:
                    try:
                        collection_time = float(data_file.fits_data.header[keyword])
                        break
                    except (ValueError, TypeError):
                        continue
        
        # If no time found in header, estimate from file characteristics
        if collection_time is None:
            # Estimate based on signal strength and typical collection rates
            # Higher SNR might indicate longer collection times
            if measurement.signal_to_noise > 1000:
                collection_time = 10.0  # seconds (high SNR = longer collection)
            elif measurement.signal_to_noise > 100:
                collection_time = 5.0   # seconds (medium SNR)
            else:
                collection_time = 1.0   # seconds (low SNR = shorter collection)
            
            logger.info(f"Estimated collection time for {measurement.filename}: {collection_time}s "
                       f"(based on SNR: {measurement.signal_to_noise:.1f})")
        else:
            logger.info(f"Found collection time in header for {measurement.filename}: {collection_time}s")
        
        measurement.collection_time = collection_time
        
        # Calculate count rate
        if collection_time > 0:
            measurement.count_rate = measurement.total_counts / collection_time
        else:
            measurement.count_rate = measurement.total_counts
        
        return measurement
    
    def _normalize_measurements(self, measurements: List[AngularMeasurement]) -> List[AngularMeasurement]:
        """
        Normalize measurements for comparison across different collection conditions.
        
        Args:
            measurements: List of measurements to normalize
            
        Returns:
            List of measurements with normalized intensities
        """
        if not measurements:
            return measurements
        
        # Get count rates for normalization
        count_rates = [m.count_rate for m in measurements if m.count_rate is not None]
        
        if not count_rates:
            # Fallback to total counts if no rates available
            count_rates = [m.total_counts for m in measurements]
        
        if count_rates:
            max_rate = max(count_rates)
            
            for measurement in measurements:
                rate = measurement.count_rate if measurement.count_rate is not None else measurement.total_counts
                measurement.normalized_intensity = rate / max_rate if max_rate > 0 else 0.0
        
        return measurements
    
    def plot_elevation_azimuth_map(self, measurements: List[AngularMeasurement],
                                 beam_energy: float,
                                 plot_type: str = 'count_rate',
                                 save_path: Optional[str] = None) -> None:
        """
        Create elevation vs azimuth plot showing count rates.
        
        Args:
            measurements: List of angular measurements
            beam_energy: Beam energy for the dataset
            plot_type: 'count_rate', 'normalized_intensity', or 'total_counts'
            save_path: Optional path to save the plot
        """
        if not measurements:
            logger.error("No measurements available for plotting")
            return
        
        # Extract data for plotting
        elevations = []
        azimuths = []
        intensities = []
        positions_x = []
        positions_y = []
        
        for m in measurements:
            if m.elevation_angle is not None:
                elevations.append(m.elevation_angle)
                azimuths.append(m.azimuth_angle if m.azimuth_angle is not None else 0.0)
                
                if plot_type == 'count_rate':
                    intensities.append(m.count_rate if m.count_rate is not None else m.total_counts)
                elif plot_type == 'normalized_intensity':
                    intensities.append(m.normalized_intensity)
                else:  # total_counts
                    intensities.append(m.total_counts)
                
                positions_x.append(m.centroid_x)
                positions_y.append(m.centroid_y)
        
        if not elevations:
            logger.error("No elevation angles found for plotting")
            return
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Plot 1: Elevation vs Azimuth with count rate
        if len(set(azimuths)) > 1:  # Multiple azimuth values
            scatter1 = axes[0, 0].scatter(azimuths, elevations, c=intensities, 
                                        s=100, alpha=0.8, cmap='viridis')
            axes[0, 0].set_xlabel('Azimuth Angle (Horizontal)')
            axes[0, 0].set_ylabel('Elevation Angle (Inner Rotation)')
            axes[0, 0].set_title(f'Elevation vs Azimuth - {plot_type.replace("_", " ").title()}')
            plt.colorbar(scatter1, ax=axes[0, 0], label=self._get_intensity_label(plot_type))
        else:
            # Single azimuth - plot elevation vs intensity
            axes[0, 0].plot(elevations, intensities, 'o-', markersize=8, linewidth=2)
            axes[0, 0].set_xlabel('Elevation Angle (degrees)')
            axes[0, 0].set_ylabel(self._get_intensity_label(plot_type))
            axes[0, 0].set_title(f'Elevation Sweep - {plot_type.replace("_", " ").title()}')
            axes[0, 0].grid(True, alpha=0.3)
        
        # Plot 2: Spatial positions with elevation color coding
        scatter2 = axes[0, 1].scatter(positions_x, positions_y, c=elevations, 
                                    s=100, alpha=0.8, cmap='plasma')
        axes[0, 1].set_xlabel('X Position (pixels)')
        axes[0, 1].set_ylabel('Y Position (pixels)')
        axes[0, 1].set_title('Detector Impact Positions')
        plt.colorbar(scatter2, ax=axes[0, 1], label='Elevation Angle (°)')
        
        # Plot 3: Count rate vs elevation
        axes[1, 0].scatter(elevations, intensities, alpha=0.7, s=80)
        axes[1, 0].set_xlabel('Elevation Angle (degrees)')
        axes[1, 0].set_ylabel(self._get_intensity_label(plot_type))
        axes[1, 0].set_title(f'{plot_type.replace("_", " ").title()} vs Elevation')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Plot 4: ESA voltage vs elevation (if voltage varies)
        esa_voltages = [m.esa_voltage for m in measurements]
        if len(set(esa_voltages)) > 1:
            scatter4 = axes[1, 1].scatter(elevations, esa_voltages, c=intensities,
                                        s=80, alpha=0.7, cmap='coolwarm')
            axes[1, 1].set_xlabel('Elevation Angle (degrees)')
            axes[1, 1].set_ylabel('ESA Voltage (V)')
            axes[1, 1].set_title('ESA Voltage vs Elevation')
            plt.colorbar(scatter4, ax=axes[1, 1], label=self._get_intensity_label(plot_type))
        else:
            # Single voltage - show collection time estimates
            times = [m.collection_time for m in measurements if m.collection_time]
            if times:
                axes[1, 1].scatter(elevations, times, alpha=0.7, s=80, color='green')
                axes[1, 1].set_xlabel('Elevation Angle (degrees)')
                axes[1, 1].set_ylabel('Collection Time (s)')
                axes[1, 1].set_title('Collection Time vs Elevation')
                axes[1, 1].grid(True, alpha=0.3)
        
        # Overall title
        fig.suptitle(f'Elevation vs Azimuth Analysis - Beam Energy: {beam_energy:.0f} eV\n'
                    f'Rate-Normalized Data ({len(measurements)} measurements)',
                    fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Elevation/azimuth plot saved to {save_path}")
        
        plt.show()
    
    def _get_intensity_label(self, plot_type: str) -> str:
        """Get appropriate label for intensity axis."""
        if plot_type == 'count_rate':
            return 'Count Rate (counts/s)'
        elif plot_type == 'normalized_intensity':
            return 'Normalized Intensity'
        else:
            return 'Total Counts'
    
    def generate_angular_report(self, measurements: List[AngularMeasurement],
                              beam_energy: float,
                              output_path: str) -> None:
        """Generate detailed report of angular analysis."""
        
        with open(output_path, 'w') as f:
            f.write("# Elevation vs Azimuth Analysis Report\n\n")
            f.write(f"**Beam Energy:** {beam_energy:.0f} eV (held constant)\n")
            f.write(f"**Number of Measurements:** {len(measurements)}\n\n")
            
            # Rate normalization summary
            f.write("## Rate Normalization Summary\n\n")
            collection_times = [m.collection_time for m in measurements if m.collection_time]
            count_rates = [m.count_rate for m in measurements if m.count_rate]
            
            if collection_times:
                f.write(f"**Collection Time Range:** {min(collection_times):.1f} - {max(collection_times):.1f} seconds\n")
                f.write(f"**Mean Collection Time:** {np.mean(collection_times):.1f} seconds\n")
            
            if count_rates:
                f.write(f"**Count Rate Range:** {min(count_rates):.1f} - {max(count_rates):.1f} counts/s\n")
                f.write(f"**Mean Count Rate:** {np.mean(count_rates):.1f} counts/s\n")
            
            f.write("\n")
            
            # Angular coverage
            elevations = [m.elevation_angle for m in measurements if m.elevation_angle is not None]
            azimuths = [m.azimuth_angle for m in measurements if m.azimuth_angle is not None]
            
            f.write("## Angular Coverage\n\n")
            if elevations:
                f.write(f"**Elevation Range:** {min(elevations):.1f}° - {max(elevations):.1f}°\n")
                f.write(f"**Number of Elevation Points:** {len(set(elevations))}\n")
            
            if azimuths:
                f.write(f"**Azimuth Range:** {min(azimuths):.1f}° - {max(azimuths):.1f}°\n")
                f.write(f"**Number of Azimuth Points:** {len(set(azimuths))}\n")
            
            f.write("\n")
            
            # Detailed measurements table
            f.write("## Detailed Measurements\n\n")
            f.write("| File | Elevation | Azimuth | ESA Voltage | Count Rate | Collection Time | Position (X,Y) |\n")
            f.write("|------|-----------|---------|-------------|------------|-----------------|----------------|\n")
            
            for m in sorted(measurements, key=lambda x: (x.elevation_angle or 0, x.azimuth_angle or 0)):
                elev_str = f"{m.elevation_angle:.1f}°" if m.elevation_angle is not None else "N/A"
                azim_str = f"{m.azimuth_angle:.1f}°" if m.azimuth_angle is not None else "N/A"
                rate_str = f"{m.count_rate:.1f}" if m.count_rate is not None else "N/A"
                time_str = f"{m.collection_time:.1f}s" if m.collection_time is not None else "Est."
                
                f.write(f"| {m.filename} | {elev_str} | {azim_str} | {m.esa_voltage:.0f}V | "
                       f"{rate_str} | {time_str} | ({m.centroid_x:.1f}, {m.centroid_y:.1f}) |\n")


def main():
    """Main function for elevation vs azimuth analysis."""
    analyzer = ElevationAzimuthAnalyzer()
    
    # Find angular datasets
    energy_groups = analyzer.find_angular_datasets()
    
    if not energy_groups:
        print("No suitable datasets found for elevation vs azimuth analysis")
        return
    
    print(f"Found angular datasets for beam energies: {list(energy_groups.keys())} eV")
    
    # Analyze each beam energy
    for beam_energy, files in energy_groups.items():
        print(f"\nAnalyzing beam energy: {beam_energy:.0f} eV ({len(files)} files)")
        
        # Analyze measurements
        measurements = analyzer.analyze_angular_measurements(files)
        
        if measurements:
            print(f"Found {len(measurements)} valid angular measurements")
            
            # Create elevation vs azimuth plot
            save_path = f"results/elevation_azimuth_E{beam_energy:.0f}eV.png"
            analyzer.plot_elevation_azimuth_map(measurements, beam_energy, 
                                              plot_type='count_rate', save_path=save_path)
            
            # Generate report
            report_path = f"results/elevation_azimuth_E{beam_energy:.0f}eV.md"
            analyzer.generate_angular_report(measurements, beam_energy, report_path)
            
            print(f"Results saved: {save_path}, {report_path}")
        else:
            print("No valid measurements found")


if __name__ == "__main__":
    main()
