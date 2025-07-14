"""
Integrated Map Analysis Module

This module creates integrated count rate maps by normalizing each map file to a 
common count rate and summing all data collection periods together to show 
count rate per area over the entire test collection.

Author: XDL Processing Project
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, Normalize
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import logging
from pathlib import Path
import os

from data_model import DataManager, DataFile
from fits_handler import FitsHandler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MapContribution:
    """Data structure for a single map's contribution to the integrated analysis."""
    
    filename: str
    beam_energy: float
    esa_voltage: float
    elevation_angle: Optional[float]
    azimuth_angle: Optional[float]
    
    # Original data
    raw_data: np.ndarray
    total_counts: float
    peak_counts: float
    non_zero_pixels: int
    
    # Rate normalization
    estimated_collection_time: float
    count_rate: float
    normalized_data: np.ndarray  # Normalized to common rate
    
    # Quality metrics
    signal_to_noise: float
    data_density: float


class IntegratedMapAnalyzer:
    """Analyzer for creating integrated count rate maps from all map files."""
    
    def __init__(self, data_directory: str = "data"):
        """Initialize the integrated map analyzer."""
        self.data_manager = DataManager(data_directory)
        self.fits_handler = FitsHandler()
        
        # Standard detector size (adjust if needed)
        self.detector_size = (1024, 1024)
        
        # Common count rate for normalization (counts/second)
        self.target_count_rate = 100.0  # Can be adjusted
        
    def find_map_files(self, beam_energy: float = None) -> List[DataFile]:
        """
        Find all map files suitable for integration.
        
        Args:
            beam_energy: Optional beam energy filter
            
        Returns:
            List of map files
        """
        all_files = self.data_manager.discover_files()
        map_files = []
        
        for f in all_files:
            if f.is_fits_or_map and f.parameters.beam_energy_value:
                if beam_energy is None or abs(f.parameters.beam_energy_value - beam_energy) < 1.0:
                    map_files.append(f)
        
        logger.info(f"Found {len(map_files)} map files for integration")
        return map_files
    
    def analyze_map_contributions(self, files: List[DataFile]) -> List[MapContribution]:
        """
        Analyze each map file to determine its contribution to the integrated map.
        
        Args:
            files: List of map files to analyze
            
        Returns:
            List of MapContribution objects
        """
        contributions = []
        
        for data_file in files:
            contribution = self._analyze_single_map(data_file)
            if contribution:
                contributions.append(contribution)
        
        logger.info(f"Successfully analyzed {len(contributions)} map contributions")
        return contributions
    
    def _analyze_single_map(self, data_file: DataFile) -> Optional[MapContribution]:
        """Analyze a single map file for integration."""
        
        # Load the data
        if not self.data_manager.load_file_data(data_file):
            logger.warning(f"Failed to load data from {data_file.filename}")
            return None
        
        if not data_file.fits_data or data_file.fits_data.data is None:
            logger.warning(f"No image data in {data_file.filename}")
            return None
        
        # Get raw data
        raw_data = data_file.fits_data.data.copy()
        
        # Handle different data shapes
        if len(raw_data.shape) == 3:
            raw_data = raw_data[0]  # Take first slice if 3D
        
        # Ensure correct size
        if raw_data.shape != self.detector_size:
            logger.warning(f"Unexpected data shape {raw_data.shape} in {data_file.filename}")
            # Resize or pad if needed
            if raw_data.shape[0] <= self.detector_size[0] and raw_data.shape[1] <= self.detector_size[1]:
                # Pad to standard size
                padded_data = np.zeros(self.detector_size)
                padded_data[:raw_data.shape[0], :raw_data.shape[1]] = raw_data
                raw_data = padded_data
            else:
                # Crop to standard size
                raw_data = raw_data[:self.detector_size[0], :self.detector_size[1]]
        
        # Calculate statistics
        total_counts = np.sum(raw_data)
        peak_counts = np.max(raw_data)
        non_zero_pixels = np.count_nonzero(raw_data)
        
        if total_counts == 0:
            logger.warning(f"Empty map file: {data_file.filename}")
            return None
        
        # Estimate collection time based on signal characteristics
        collection_time = self._estimate_collection_time(raw_data, data_file)
        
        # Calculate count rate
        count_rate = total_counts / collection_time if collection_time > 0 else total_counts
        
        # Normalize data to target count rate
        normalization_factor = self.target_count_rate / count_rate if count_rate > 0 else 1.0
        normalized_data = raw_data * normalization_factor
        
        # Calculate signal-to-noise ratio
        signal_region = raw_data[raw_data > 0]
        noise_region = raw_data[raw_data == 0]
        
        if len(signal_region) > 0 and len(noise_region) > 0:
            snr = np.mean(signal_region) / (np.std(noise_region) + 1e-10)
        else:
            snr = np.max(raw_data) / (np.std(raw_data) + 1e-10)
        
        # Extract experimental parameters
        params = data_file.parameters
        elevation_angle = params.inner_angle_value
        azimuth_angle = params.horizontal_value_num
        
        return MapContribution(
            filename=data_file.filename,
            beam_energy=params.beam_energy_value,
            esa_voltage=params.esa_voltage_value or 0.0,
            elevation_angle=elevation_angle,
            azimuth_angle=azimuth_angle,
            raw_data=raw_data,
            total_counts=total_counts,
            peak_counts=peak_counts,
            non_zero_pixels=non_zero_pixels,
            estimated_collection_time=collection_time,
            count_rate=count_rate,
            normalized_data=normalized_data,
            signal_to_noise=snr,
            data_density=non_zero_pixels / raw_data.size
        )
    
    def _estimate_collection_time(self, data: np.ndarray, data_file: DataFile) -> float:
        """
        Estimate collection time for a map file.
        
        Args:
            data: Image data array
            data_file: DataFile object
            
        Returns:
            Estimated collection time in seconds
        """
        # Try to get from FITS header first
        if data_file.fits_data and data_file.fits_data.header:
            time_keywords = ['EXPTIME', 'EXPOSURE', 'OBSTIME', 'TELAPSE', 'LIVETIME']
            for keyword in time_keywords:
                if keyword in data_file.fits_data.header:
                    try:
                        return float(data_file.fits_data.header[keyword])
                    except (ValueError, TypeError):
                        continue
        
        # Estimate based on data characteristics
        total_counts = np.sum(data)
        peak_counts = np.max(data)
        non_zero_pixels = np.count_nonzero(data)
        
        # Heuristic based on signal strength and coverage
        if peak_counts > 1000 and non_zero_pixels > 1000:
            return 10.0  # High signal, long collection
        elif peak_counts > 100 and non_zero_pixels > 100:
            return 5.0   # Medium signal
        elif total_counts > 10:
            return 1.0   # Low signal, short collection
        else:
            return 0.1   # Very low signal
    
    def create_integrated_map(self, contributions: List[MapContribution]) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Create integrated count rate map by summing all normalized contributions.
        
        Args:
            contributions: List of map contributions
            
        Returns:
            Tuple of (integrated_map, metadata)
        """
        if not contributions:
            logger.error("No contributions available for integration")
            return np.zeros(self.detector_size), {}
        
        # Initialize integrated map
        integrated_map = np.zeros(self.detector_size)
        
        # Sum all normalized contributions
        for contribution in contributions:
            integrated_map += contribution.normalized_data
        
        # Calculate metadata
        total_files = len(contributions)
        total_collection_time = sum(c.estimated_collection_time for c in contributions)
        total_raw_counts = sum(c.total_counts for c in contributions)
        
        # Beam energies and voltages
        beam_energies = set(c.beam_energy for c in contributions)
        esa_voltages = set(c.esa_voltage for c in contributions)
        
        # Angular coverage
        elevations = [c.elevation_angle for c in contributions if c.elevation_angle is not None]
        azimuths = [c.azimuth_angle for c in contributions if c.azimuth_angle is not None]
        
        metadata = {
            'total_files': total_files,
            'total_collection_time': total_collection_time,
            'total_raw_counts': total_raw_counts,
            'beam_energies': sorted(list(beam_energies)),
            'esa_voltages': sorted(list(esa_voltages)),
            'elevation_range': (min(elevations), max(elevations)) if elevations else None,
            'azimuth_range': (min(azimuths), max(azimuths)) if azimuths else None,
            'target_count_rate': self.target_count_rate,
            'peak_integrated_rate': np.max(integrated_map),
            'total_integrated_counts': np.sum(integrated_map),
            'active_pixels': np.count_nonzero(integrated_map)
        }
        
        logger.info(f"Created integrated map from {total_files} files")
        logger.info(f"Total collection time: {total_collection_time:.1f} seconds")
        logger.info(f"Peak integrated rate: {metadata['peak_integrated_rate']:.1f} counts/s")
        
        return integrated_map, metadata
    
    def plot_integrated_map(self, integrated_map: np.ndarray, metadata: Dict[str, Any],
                          contributions: List[MapContribution],
                          save_path: Optional[str] = None) -> None:
        """
        Create comprehensive plot of the integrated count rate map.
        
        Args:
            integrated_map: Integrated count rate map
            metadata: Analysis metadata
            contributions: List of individual contributions
            save_path: Optional path to save the plot
        """
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # Plot 1: Main integrated count rate map with log scale for better impact visibility
        # Calculate appropriate log scale limits
        nonzero_data = integrated_map[integrated_map > 0]
        if len(nonzero_data) > 0:
            vmin_log = max(0.01, np.min(nonzero_data))
            vmax_log = np.max(nonzero_data)
        else:
            vmin_log, vmax_log = 0.01, 1.0

        im1 = axes[0, 0].imshow(integrated_map, cmap='viridis', aspect='auto',
                               origin='lower', norm=LogNorm(vmin=vmin_log, vmax=vmax_log))
        axes[0, 0].set_title(f'Integrated Count Rate Map (Log Scale)\n'
                           f'{metadata["total_files"]} files, {metadata["total_collection_time"]:.1f}s total',
                           fontsize=12, fontweight='bold')
        axes[0, 0].set_xlabel('X Position (pixels)')
        axes[0, 0].set_ylabel('Y Position (pixels)')
        cbar1 = plt.colorbar(im1, ax=axes[0, 0])
        cbar1.set_label('Count Rate (counts/s, log scale)', fontsize=10)

        # Plot 2: Enhanced log scale with contours for impact location visibility
        im2 = axes[0, 1].imshow(integrated_map, cmap='hot', aspect='auto', origin='lower',
                               norm=LogNorm(vmin=vmin_log, vmax=vmax_log))

        # Add contour lines to highlight impact regions
        if len(nonzero_data) > 0:
            # Create contour levels at different percentiles of the data
            percentiles = [50, 75, 90, 95, 99]
            contour_levels = [np.percentile(nonzero_data, p) for p in percentiles]

            # Create coordinate arrays for contour
            y_coords, x_coords = np.mgrid[0:integrated_map.shape[0], 0:integrated_map.shape[1]]

            # Add contour lines
            contours = axes[0, 1].contour(x_coords, y_coords, integrated_map,
                                        levels=contour_levels, colors='white',
                                        linewidths=0.8, alpha=0.7)
            axes[0, 1].clabel(contours, inline=True, fontsize=8, fmt='%.1f')

        axes[0, 1].set_title('Impact Locations with Contours (Log Scale)', fontsize=12, fontweight='bold')
        axes[0, 1].set_xlabel('X Position (pixels)')
        axes[0, 1].set_ylabel('Y Position (pixels)')
        cbar2 = plt.colorbar(im2, ax=axes[0, 1])
        cbar2.set_label('Count Rate (counts/s, log scale)', fontsize=10)
        
        # Plot 3: Individual contribution positions
        if contributions:
            # Show where each measurement contributed
            for i, contrib in enumerate(contributions):
                # Find centroid of each contribution
                if np.sum(contrib.normalized_data) > 0:
                    y_coords, x_coords = np.where(contrib.normalized_data > 0)
                    if len(x_coords) > 0:
                        weights = contrib.normalized_data[contrib.normalized_data > 0]
                        centroid_x = np.average(x_coords, weights=weights)
                        centroid_y = np.average(y_coords, weights=weights)
                        
                        # Color by elevation angle if available
                        color = contrib.elevation_angle if contrib.elevation_angle is not None else i
                        axes[1, 0].scatter(centroid_x, centroid_y, c=color, s=50, alpha=0.7, 
                                         cmap='coolwarm', vmin=-180, vmax=180)
            
            axes[1, 0].set_title('Individual Measurement Positions', fontsize=12, fontweight='bold')
            axes[1, 0].set_xlabel('X Position (pixels)')
            axes[1, 0].set_ylabel('Y Position (pixels)')
            axes[1, 0].set_xlim(0, self.detector_size[1])
            axes[1, 0].set_ylim(0, self.detector_size[0])
        
        # Plot 4: Count rate statistics
        if contributions:
            count_rates = [c.count_rate for c in contributions]
            collection_times = [c.estimated_collection_time for c in contributions]
            
            # Histogram of count rates
            axes[1, 1].hist(count_rates, bins=min(20, len(count_rates)), alpha=0.7, color='skyblue')
            axes[1, 1].set_xlabel('Original Count Rate (counts/s)')
            axes[1, 1].set_ylabel('Number of Files')
            axes[1, 1].set_title('Distribution of Count Rates', fontsize=12, fontweight='bold')
            axes[1, 1].grid(True, alpha=0.3)
            
            # Add statistics text
            stats_text = f"Files: {len(contributions)}\n"
            stats_text += f"Rate range: {min(count_rates):.1f} - {max(count_rates):.1f}\n"
            stats_text += f"Mean rate: {np.mean(count_rates):.1f} ± {np.std(count_rates):.1f}\n"
            stats_text += f"Time range: {min(collection_times):.1f} - {max(collection_times):.1f}s"
            
            axes[1, 1].text(0.02, 0.98, stats_text, transform=axes[1, 1].transAxes,
                           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                           fontsize=9)
        
        # Overall title
        beam_energies_str = ', '.join(f"{e:.0f}" for e in metadata['beam_energies'])
        fig.suptitle(f'Integrated Count Rate Analysis (Log Scale for Impact Visibility)\n'
                    f'Beam Energies: {beam_energies_str} eV, '
                    f'Target Rate: {metadata["target_count_rate"]:.0f} counts/s, '
                    f'Peak Rate: {metadata["peak_integrated_rate"]:.1f} counts/s',
                    fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Integrated map plot saved to {save_path}")
        
        plt.show()
    
    def generate_integration_report(self, integrated_map: np.ndarray, metadata: Dict[str, Any],
                                  contributions: List[MapContribution],
                                  output_path: str) -> None:
        """Generate detailed report of the integration analysis."""
        
        with open(output_path, 'w') as f:
            f.write("# Integrated Count Rate Map Analysis Report\n\n")
            
            # Summary
            f.write("## Integration Summary\n\n")
            f.write(f"**Total Files Integrated:** {metadata['total_files']}\n")
            f.write(f"**Total Collection Time:** {metadata['total_collection_time']:.1f} seconds\n")
            f.write(f"**Total Raw Counts:** {metadata['total_raw_counts']:,.0f}\n")
            f.write(f"**Target Count Rate:** {metadata['target_count_rate']:.0f} counts/s\n")
            f.write(f"**Peak Integrated Rate:** {metadata['peak_integrated_rate']:.1f} counts/s\n")
            f.write(f"**Total Integrated Counts:** {metadata['total_integrated_counts']:,.0f}\n")
            f.write(f"**Active Pixels:** {metadata['active_pixels']:,} / {np.prod(integrated_map.shape):,} "
                   f"({metadata['active_pixels']/np.prod(integrated_map.shape)*100:.1f}%)\n\n")
            
            # Experimental conditions
            f.write("## Experimental Conditions\n\n")
            f.write(f"**Beam Energies:** {', '.join(f'{e:.0f} eV' for e in metadata['beam_energies'])}\n")
            f.write(f"**ESA Voltages:** {', '.join(f'{v:.0f} V' for v in metadata['esa_voltages'])}\n")
            
            if metadata['elevation_range']:
                f.write(f"**Elevation Range:** {metadata['elevation_range'][0]:.1f}° to {metadata['elevation_range'][1]:.1f}°\n")
            
            if metadata['azimuth_range']:
                f.write(f"**Azimuth Range:** {metadata['azimuth_range'][0]:.1f}° to {metadata['azimuth_range'][1]:.1f}°\n")
            
            f.write("\n")
            
            # Rate normalization details
            f.write("## Rate Normalization Details\n\n")
            count_rates = [c.count_rate for c in contributions]
            collection_times = [c.estimated_collection_time for c in contributions]
            
            f.write(f"**Original Count Rate Range:** {min(count_rates):.1f} - {max(count_rates):.1f} counts/s\n")
            f.write(f"**Mean Original Rate:** {np.mean(count_rates):.1f} ± {np.std(count_rates):.1f} counts/s\n")
            f.write(f"**Collection Time Range:** {min(collection_times):.1f} - {max(collection_times):.1f} seconds\n")
            f.write(f"**Mean Collection Time:** {np.mean(collection_times):.1f} ± {np.std(collection_times):.1f} seconds\n\n")
            
            # Individual file contributions
            f.write("## Individual File Contributions\n\n")
            f.write("| File | Beam Energy | ESA Voltage | Elevation | Azimuth | Original Rate | Collection Time | Normalization Factor |\n")
            f.write("|------|-------------|-------------|-----------|---------|---------------|-----------------|----------------------|\n")
            
            for contrib in sorted(contributions, key=lambda x: x.count_rate, reverse=True):
                elev_str = f"{contrib.elevation_angle:.1f}°" if contrib.elevation_angle is not None else "N/A"
                azim_str = f"{contrib.azimuth_angle:.1f}°" if contrib.azimuth_angle is not None else "N/A"
                norm_factor = metadata['target_count_rate'] / contrib.count_rate if contrib.count_rate > 0 else 1.0
                
                f.write(f"| {contrib.filename} | {contrib.beam_energy:.0f} eV | {contrib.esa_voltage:.0f} V | "
                       f"{elev_str} | {azim_str} | {contrib.count_rate:.1f} | {contrib.estimated_collection_time:.1f}s | "
                       f"{norm_factor:.3f} |\n")


def main():
    """Main function for integrated map analysis."""
    analyzer = IntegratedMapAnalyzer()
    
    # Find map files
    map_files = analyzer.find_map_files()
    
    if not map_files:
        print("No map files found for integration")
        return
    
    print(f"Found {len(map_files)} map files for integration")
    
    # Analyze contributions
    contributions = analyzer.analyze_map_contributions(map_files)
    
    if not contributions:
        print("No valid contributions found")
        return
    
    print(f"Successfully analyzed {len(contributions)} contributions")
    
    # Create integrated map
    integrated_map, metadata = analyzer.create_integrated_map(contributions)
    
    # Create plots
    save_path = "results/integrated_count_rate_map.png"
    analyzer.plot_integrated_map(integrated_map, metadata, contributions, save_path)
    
    # Generate report
    report_path = "results/integrated_map_analysis.md"
    analyzer.generate_integration_report(integrated_map, metadata, contributions, report_path)
    
    print(f"Integration analysis complete!")
    print(f"Plot saved: {save_path}")
    print(f"Report saved: {report_path}")


if __name__ == "__main__":
    main()
