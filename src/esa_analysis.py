"""
ESA K-Factor Analysis Module

This module provides specialized analysis tools for estimating the k-factor of the 
Electrostatic Analyzer (ESA) and qualitatively describing spatial impact regions
based on beam energies, ESA voltages, and rotation angles.

Author: XDL Processing Project
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import logging
from pathlib import Path
from scipy import ndimage
from scipy.optimize import curve_fit

from data_model import DataManager, DataFile, ExperimentGroup
from fits_handler import FitsHandler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ImpactRegion:
    """Describes a spatial impact region on the detector."""

    filename: str
    beam_energy: float
    esa_voltage: float
    rotation_angle: Optional[float]

    # Spatial characteristics
    centroid_x: float
    centroid_y: float
    peak_intensity: float
    total_intensity: float
    region_area: int  # Number of non-zero pixels

    # Region bounds
    min_x: int
    max_x: int
    min_y: int
    max_y: int

    # Quality metrics
    signal_to_noise: float
    data_density: float

    # Optional fields with defaults
    rotation_angle_range: Optional[Tuple[float, float]] = None
    is_angle_range: bool = False


@dataclass
class ESAMeasurement:
    """Represents a complete ESA measurement with calculated parameters."""
    
    impact_region: ImpactRegion
    theoretical_deflection: float
    measured_deflection: float
    k_factor_estimate: Optional[float] = None
    
    def calculate_k_factor(self) -> float:
        """Calculate k-factor as beam energy (eV) divided by ESA voltage (V)."""
        if self.impact_region.esa_voltage != 0 and self.impact_region.beam_energy != 0:
            # K-factor = E_beam (eV) / V_esa (V)
            self.k_factor_estimate = self.impact_region.beam_energy / abs(self.impact_region.esa_voltage)
        return self.k_factor_estimate


class ESAAnalyzer:
    """Specialized analyzer for ESA k-factor estimation and spatial mapping."""
    
    def __init__(self, data_directory: str = "data"):
        """Initialize the ESA analyzer."""
        self.data_manager = DataManager(data_directory)
        self.fits_handler = FitsHandler()
        
        # Analysis parameters
        self.noise_threshold = 0.05  # Fraction of peak for noise estimation
        self.min_region_size = 10    # Minimum pixels for valid region
        
    def analyze_impact_regions(self, files: List[DataFile]) -> List[ImpactRegion]:
        """
        Analyze spatial impact regions for a set of files.
        
        Args:
            files: List of FITS/MAP files to analyze
            
        Returns:
            List of ImpactRegion objects
        """
        regions = []
        
        for data_file in files:
            region = self._analyze_single_impact_region(data_file)
            if region:
                regions.append(region)
        
        return regions
    
    def _analyze_single_impact_region(self, data_file: DataFile) -> Optional[ImpactRegion]:
        """Analyze impact region for a single file."""
        # Load data with local normalization
        if not self.data_manager.load_file_data(data_file):
            return None
        
        if not data_file.fits_data or data_file.fits_data.data is None:
            return None
        
        # Get raw data (no global normalization)
        raw_data = data_file.fits_data.data.copy()
        
        # Apply local normalization for visibility
        if np.max(raw_data) > 0:
            normalized_data = raw_data / np.max(raw_data)
        else:
            logger.warning(f"Empty data in {data_file.filename}")
            return None
        
        # Find significant regions (above noise threshold)
        peak_value = np.max(normalized_data)
        threshold = peak_value * self.noise_threshold
        significant_mask = normalized_data > threshold
        
        if np.sum(significant_mask) < self.min_region_size:
            logger.warning(f"Insufficient signal in {data_file.filename}")
            return None
        
        # Calculate spatial characteristics
        y_coords, x_coords = np.where(significant_mask)
        
        if len(x_coords) == 0:
            return None
        
        # Calculate weighted centroid
        weights = normalized_data[significant_mask]
        centroid_x = np.average(x_coords, weights=weights)
        centroid_y = np.average(y_coords, weights=weights)
        
        # Calculate region bounds
        min_x, max_x = np.min(x_coords), np.max(x_coords)
        min_y, max_y = np.min(y_coords), np.max(y_coords)
        
        # Calculate signal-to-noise ratio
        signal_region = normalized_data[significant_mask]
        noise_region = normalized_data[~significant_mask]
        snr = np.mean(signal_region) / (np.std(noise_region) + 1e-10)
        
        # Extract experimental parameters
        params = data_file.parameters
        beam_energy = params.beam_energy_value or 0.0
        esa_voltage = params.esa_voltage_value or 0.0
        rotation_angle = params.inner_angle_value
        rotation_angle_range = getattr(params, 'inner_angle_range', None)
        is_angle_range = getattr(params, 'is_angle_range', False)
        
        return ImpactRegion(
            filename=data_file.filename,
            beam_energy=beam_energy,
            esa_voltage=esa_voltage,
            rotation_angle=rotation_angle,
            rotation_angle_range=rotation_angle_range,
            is_angle_range=is_angle_range,
            centroid_x=centroid_x,
            centroid_y=centroid_y,
            peak_intensity=peak_value,
            total_intensity=np.sum(weights),
            region_area=len(x_coords),
            min_x=min_x,
            max_x=max_x,
            min_y=min_y,
            max_y=max_y,
            signal_to_noise=snr,
            data_density=len(x_coords) / raw_data.size
        )
    
    def estimate_k_factor(self, regions: List[ImpactRegion]) -> Dict[str, Any]:
        """
        Estimate ESA k-factor from impact region analysis.
        
        Args:
            regions: List of analyzed impact regions
            
        Returns:
            Dictionary with k-factor analysis results
        """
        measurements = []
        
        # Convert regions to measurements and calculate k-factors
        for region in regions:
            if region.esa_voltage != 0 and region.beam_energy != 0:
                # Calculate theoretical deflection for reference (optional)
                theoretical_deflection = self._calculate_theoretical_deflection(
                    region.beam_energy, region.esa_voltage
                )

                # Measured deflection is the centroid position relative to detector center
                detector_center_x = 512  # Assuming 1024x1024 detector
                measured_deflection = (region.centroid_x - detector_center_x) / detector_center_x

                measurement = ESAMeasurement(
                    impact_region=region,
                    theoretical_deflection=theoretical_deflection,
                    measured_deflection=measured_deflection
                )

                measurements.append(measurement)

                # For angle ranges, log additional information
                if region.is_angle_range and region.rotation_angle_range:
                    logger.info(f"File {region.filename} collected over angle range: "
                              f"{region.rotation_angle_range[0]:.1f}° to {region.rotation_angle_range[1]:.1f}° "
                              f"(using midpoint {region.rotation_angle:.1f}° for analysis)")
        
        if not measurements:
            return {"error": "No valid measurements for k-factor estimation"}
        
        # Calculate k-factors for each measurement
        k_factors = []
        for measurement in measurements:
            k_factor = measurement.calculate_k_factor()
            if k_factor is not None:
                k_factors.append(k_factor)
        
        if not k_factors:
            return {"error": "Could not calculate any k-factors"}
        
        # Statistical analysis of k-factors
        k_factors = np.array(k_factors)
        
        results = {
            "k_factor_mean": np.mean(k_factors),
            "k_factor_std": np.std(k_factors),
            "k_factor_median": np.median(k_factors),
            "k_factor_range": (np.min(k_factors), np.max(k_factors)),
            "num_measurements": len(k_factors),
            "measurements": measurements,
            "k_factors": k_factors.tolist()
        }
        
        return results
    
    def _calculate_theoretical_deflection(self, beam_energy: float, esa_voltage: float) -> float:
        """Calculate theoretical deflection based on ESA physics."""
        # Simplified ESA deflection model
        # In practice, this would use the specific ESA geometry and physics
        if beam_energy > 0:
            return esa_voltage / beam_energy
        return 0.0
    
    def plot_spatial_mapping(self, regions: List[ImpactRegion], 
                           group_by: str = 'beam_energy',
                           save_path: Optional[str] = None) -> None:
        """
        Create spatial mapping plots showing impact regions.
        
        Args:
            regions: List of impact regions to plot
            group_by: Parameter to group by ('beam_energy', 'esa_voltage', 'rotation_angle')
            save_path: Optional path to save the plot
        """
        if not regions:
            logger.error("No regions to plot")
            return
        
        # Group regions by specified parameter
        groups = {}
        for region in regions:
            if group_by == 'beam_energy':
                key = f"{region.beam_energy:.0f} eV"
            elif group_by == 'esa_voltage':
                key = f"{region.esa_voltage:.0f} V"
            elif group_by == 'rotation_angle':
                if region.is_angle_range and region.rotation_angle_range:
                    key = f"{region.rotation_angle_range[0]:.0f}° to {region.rotation_angle_range[1]:.0f}°"
                elif region.rotation_angle is not None:
                    key = f"{region.rotation_angle:.0f}°"
                else:
                    key = "No angle"
            else:
                key = "All"
            
            if key not in groups:
                groups[key] = []
            groups[key].append(region)
        
        # Create subplot grid
        n_groups = len(groups)
        cols = min(3, n_groups)
        rows = (n_groups + cols - 1) // cols

        fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 4*rows))
        if n_groups == 1:
            axes = [axes]
        elif rows == 1 and cols > 1:
            axes = [axes] if cols == 1 else list(axes)
        else:
            axes = axes.flatten() if rows > 1 else [axes]
        
        # Plot each group
        for i, (group_name, group_regions) in enumerate(groups.items()):
            ax = axes[i] if isinstance(axes, list) else axes
            
            # Create scatter plot of centroids
            x_coords = [r.centroid_x for r in group_regions]
            y_coords = [r.centroid_y for r in group_regions]
            intensities = [r.peak_intensity for r in group_regions]
            
            scatter = ax.scatter(x_coords, y_coords, c=intensities, 
                               s=50, alpha=0.7, cmap='viridis')
            
            # Add colorbar
            plt.colorbar(scatter, ax=ax, label='Peak Intensity')
            
            # Customize plot
            ax.set_title(f'{group_name}\n({len(group_regions)} regions)')
            ax.set_xlabel('X Position (pixels)')
            ax.set_ylabel('Y Position (pixels)')
            ax.set_xlim(0, 1024)
            ax.set_ylim(0, 1024)
            ax.grid(True, alpha=0.3)
            
            # Add region boundaries
            for region in group_regions:
                rect = plt.Rectangle((region.min_x, region.min_y), 
                                   region.max_x - region.min_x,
                                   region.max_y - region.min_y,
                                   fill=False, edgecolor='red', alpha=0.5)
                ax.add_patch(rect)
        
        # Hide unused subplots
        for i in range(n_groups, rows * cols):
            row = i // cols
            col = i % cols
            ax = axes[row, col] if rows > 1 else axes[col]
            ax.set_visible(False)
        
        plt.suptitle(f'Spatial Impact Mapping - Grouped by {group_by.replace("_", " ").title()}', 
                     fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Spatial mapping plot saved to {save_path}")
        
        plt.show()
    
    def generate_esa_report(self, k_factor_results: Dict[str, Any], 
                          regions: List[ImpactRegion],
                          output_path: str = "results/esa_analysis_report.md") -> str:
        """Generate comprehensive ESA analysis report."""
        
        with open(output_path, 'w') as f:
            f.write("# ESA K-Factor Analysis Report\n\n")
            f.write("**K-Factor Definition:** K = Beam Energy (eV) / |ESA Voltage (V)|\n\n")

            # K-factor results
            if "error" not in k_factor_results:
                f.write("## K-Factor Estimation Results\n\n")
                f.write(f"**Mean K-Factor:** {k_factor_results['k_factor_mean']:.2f} eV/V\n")
                f.write(f"**Standard Deviation:** {k_factor_results['k_factor_std']:.2f} eV/V\n")
                f.write(f"**Median K-Factor:** {k_factor_results['k_factor_median']:.2f} eV/V\n")
                f.write(f"**Range:** {k_factor_results['k_factor_range'][0]:.2f} to {k_factor_results['k_factor_range'][1]:.2f} eV/V\n")
                f.write(f"**Number of Measurements:** {k_factor_results['num_measurements']}\n\n")

                # Add individual k-factor calculations
                if k_factor_results.get('measurements'):
                    f.write("### Individual K-Factor Calculations\n\n")
                    f.write("| File | Beam Energy (eV) | ESA Voltage (V) | K-Factor (eV/V) |\n")
                    f.write("|------|------------------|-----------------|------------------|\n")
                    for measurement in k_factor_results['measurements']:
                        region = measurement.impact_region
                        k_val = measurement.k_factor_estimate or 0
                        f.write(f"| {region.filename} | {region.beam_energy:.0f} | {region.esa_voltage:.0f} | {k_val:.2f} |\n")
                    f.write("\n")
            else:
                f.write("## K-Factor Estimation\n\n")
                f.write(f"**Error:** {k_factor_results['error']}\n\n")
            
            # Spatial mapping summary
            f.write("## Spatial Impact Region Analysis\n\n")
            f.write(f"**Total Regions Analyzed:** {len(regions)}\n\n")
            
            # Group by experimental conditions
            beam_energies = set(r.beam_energy for r in regions)
            esa_voltages = set(r.esa_voltage for r in regions)
            rotation_angles = set(r.rotation_angle for r in regions if r.rotation_angle is not None)
            
            f.write(f"**Beam Energies:** {sorted(beam_energies)} eV\n")
            f.write(f"**ESA Voltages:** {sorted(esa_voltages)} V\n")
            f.write(f"**Rotation Angles:** {sorted(rotation_angles)}°\n\n")
            
            # Detailed region analysis
            f.write("## Detailed Region Analysis\n\n")
            f.write("| File | Beam Energy | ESA Voltage | Rotation | Centroid (X,Y) | Peak Intensity | SNR | Range? |\n")
            f.write("|------|-------------|-------------|----------|----------------|----------------|-----|--------|\n")

            for region in sorted(regions, key=lambda r: (r.beam_energy, r.esa_voltage)):
                if region.is_angle_range and region.rotation_angle_range:
                    angle_str = f"{region.rotation_angle_range[0]:.0f}° to {region.rotation_angle_range[1]:.0f}°"
                    range_str = "Yes"
                elif region.rotation_angle is not None:
                    angle_str = f"{region.rotation_angle:.0f}°"
                    range_str = "No"
                else:
                    angle_str = "N/A"
                    range_str = "N/A"

                f.write(f"| {region.filename} | {region.beam_energy:.0f} eV | {region.esa_voltage:.0f} V | "
                       f"{angle_str} | ({region.centroid_x:.1f}, {region.centroid_y:.1f}) | "
                       f"{region.peak_intensity:.3f} | {region.signal_to_noise:.2f} | {range_str} |\n")
        
        logger.info(f"ESA analysis report saved to {output_path}")
        return output_path


def main():
    """Main function for ESA analysis."""
    analyzer = ESAAnalyzer()
    
    # Discover FITS/MAP files
    all_files = analyzer.data_manager.discover_files()
    fits_files = [f for f in all_files if f.is_fits_or_map]
    
    print(f"Analyzing {len(fits_files)} FITS/MAP files for ESA characteristics...")
    
    # Analyze impact regions
    regions = analyzer.analyze_impact_regions(fits_files)
    print(f"Found {len(regions)} valid impact regions")
    
    if regions:
        # Estimate k-factor
        k_factor_results = analyzer.estimate_k_factor(regions)
        
        # Create spatial mapping plots
        analyzer.plot_spatial_mapping(regions, group_by='beam_energy')
        analyzer.plot_spatial_mapping(regions, group_by='esa_voltage')
        
        # Generate report
        report_path = analyzer.generate_esa_report(k_factor_results, regions)
        print(f"Analysis complete. Report saved to: {report_path}")
        
        # Print summary
        if "error" not in k_factor_results:
            print(f"\nK-Factor Estimation:")
            print(f"  Mean: {k_factor_results['k_factor_mean']:.4f}")
            print(f"  Std:  {k_factor_results['k_factor_std']:.4f}")
            print(f"  Range: {k_factor_results['k_factor_range'][0]:.4f} - {k_factor_results['k_factor_range'][1]:.4f}")
    else:
        print("No valid regions found for analysis")


if __name__ == "__main__":
    main()
