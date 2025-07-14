#!/usr/bin/env python3
"""
Enhanced Map Visualization Script

This script provides improved map/FITS file visualization with:
- Automatic file discovery and parameter extraction
- Proper FITS file handling with astropy
- Smart file grouping and comparison
- Parameter-based labeling and organization
- Multiple visualization modes
- Robust error handling

Author: XDL Processing Project
"""

import sys
import os
import argparse
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import logging

# Add src directory to path for imports
sys.path.append('src')
from data_model import DataManager, DataFile, ExperimentGroup
from fits_handler import FitsHandler, FitsData
from filename_parser import ExperimentalParameters

# Configure matplotlib backend
matplotlib.use('Qt5Agg')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class EnhancedMapVisualizer:
    """Enhanced map/FITS visualization with automatic file management and smart grouping."""
    
    def __init__(self, data_directory: str = "data"):
        """Initialize the visualizer with data directory."""
        self.data_manager = DataManager(data_directory)
        self.fits_handler = FitsHandler()
        self.default_contrast_range = (1, 99)  # Percentile range for contrast
        self.normalization_mode = 'percentile'  # Default to local normalization for ESA analysis
        self.global_min = None  # For global normalization
        self.global_max = None
        
    def discover_map_files(self) -> List[DataFile]:
        """Discover all FITS and MAP files in the data directory."""
        all_files = self.data_manager.discover_files()
        map_files = [f for f in all_files if f.is_fits_or_map]
        logger.info(f"Found {len(map_files)} FITS/MAP files")
        return map_files
    
    def load_image_data(self, data_file: DataFile) -> Optional[Tuple[np.ndarray, Dict[str, Any]]]:
        """
        Load image data from a FITS or MAP file.

        Returns:
            Tuple of (image_data, metadata) or None if loading fails
        """
        if not self.data_manager.load_file_data(data_file):
            logger.error(f"Failed to load data from {data_file.filename}")
            return None

        if data_file.fits_data and data_file.fits_data.data is not None:
            # Check if file has meaningful data
            non_zero_pixels = np.count_nonzero(data_file.fits_data.data)
            total_pixels = data_file.fits_data.data.size
            data_density = non_zero_pixels / total_pixels if total_pixels > 0 else 0

            metadata = {
                'non_zero_pixels': non_zero_pixels,
                'total_pixels': total_pixels,
                'data_density': data_density,
                'min_value': data_file.fits_data.min_value,
                'max_value': data_file.fits_data.max_value,
                'is_empty': non_zero_pixels == 0,
                'is_sparse': data_density < 0.01  # Less than 1% non-zero
            }

            # Extract and process image data
            image_data = self.fits_handler.extract_image_data(
                data_file.fits_data,
                percentile_range=self.default_contrast_range,
                normalization_mode=self.normalization_mode
            )

            # Apply global normalization if requested
            if self.normalization_mode == 'global' and self.global_min is not None and self.global_max is not None:
                if self.global_max > self.global_min:
                    image_data = (image_data - self.global_min) / (self.global_max - self.global_min)
                    image_data = np.clip(image_data, 0, 1)

            return image_data, metadata

        return None
    
    def generate_smart_title(self, data_file: DataFile) -> str:
        """Generate a smart title based on extracted parameters."""
        params = data_file.parameters
        title_parts = []
        
        # Add test type
        if params.test_type and params.test_type != 'unknown':
            title_parts.append(params.test_type.replace('_', ' ').title())
        
        # Add beam energy if available
        if params.beam_energy_value:
            title_parts.append(f"{params.beam_energy_value:.0f} eV")
        
        # Add ESA voltage if available
        if params.esa_voltage_value:
            title_parts.append(f"ESA {params.esa_voltage_value:.0f}V")
        
        # Add inner angle if available
        if params.inner_angle_value:
            title_parts.append(f"Angle {params.inner_angle_value:.0f}°")
        
        # Add timestamp if available
        if params.datetime_obj:
            title_parts.append(params.datetime_obj.strftime("%Y-%m-%d %H:%M"))
        
        # Fall back to filename if no parameters extracted
        if not title_parts:
            title_parts.append(Path(data_file.filename).stem)
        
        return " - ".join(title_parts)

    def calculate_global_normalization(self, files: List[DataFile]) -> Tuple[float, float]:
        """
        Calculate global min/max values across all files for consistent normalization.

        Args:
            files: List of DataFile objects

        Returns:
            Tuple of (global_min, global_max)
        """
        all_mins = []
        all_maxs = []

        for data_file in files:
            if not self.data_manager.load_file_data(data_file):
                continue

            if data_file.fits_data and data_file.fits_data.data is not None:
                # Only consider non-empty files for global normalization
                if np.count_nonzero(data_file.fits_data.data) > 0:
                    all_mins.append(data_file.fits_data.min_value)
                    all_maxs.append(data_file.fits_data.max_value)

        if all_mins and all_maxs:
            return min(all_mins), max(all_maxs)
        else:
            return 0.0, 1.0  # Default range
    
    def plot_single_map(self, data_file: DataFile, 
                       custom_title: Optional[str] = None,
                       save_path: Optional[str] = None,
                       colormap: str = 'viridis',
                       show_colorbar: bool = True) -> None:
        """
        Plot a single map/FITS file.
        
        Args:
            data_file: DataFile object to plot
            custom_title: Optional custom title
            save_path: Optional path to save the plot
            colormap: Matplotlib colormap name
            show_colorbar: Whether to show colorbar
        """
        # Load image data
        result = self.load_image_data(data_file)
        if result is None:
            logger.error(f"No image data available for {data_file.filename}")
            return

        image_data, metadata = result

        # Check if file is empty or sparse
        if metadata['is_empty']:
            logger.warning(f"File {data_file.filename} contains no data (all zeros)")
        elif metadata['is_sparse']:
            logger.info(f"File {data_file.filename} is sparse ({metadata['data_density']:.1%} non-zero pixels)")
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Display image
        im = ax.imshow(image_data, cmap=colormap, aspect='auto', origin='lower')
        
        # Add colorbar
        if show_colorbar:
            cbar = plt.colorbar(im, ax=ax, label='Intensity [Arbitrary Units]')
        
        # Set title
        title = custom_title if custom_title else self.generate_smart_title(data_file)
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        # Set labels
        ax.set_xlabel('X Pixel', fontsize=12)
        ax.set_ylabel('Y Pixel', fontsize=12)
        
        # Add file info as text
        info_text = f"File: {data_file.filename}\nSize: {image_data.shape}"
        info_text += f"\nNon-zero pixels: {metadata['non_zero_pixels']:,} ({metadata['data_density']:.1%})"
        info_text += f"\nData range: {metadata['min_value']:.1f} - {metadata['max_value']:.1f}"
        info_text += f"\nNormalization: {self.normalization_mode}"

        if metadata['is_empty']:
            info_text += "\n⚠️ EMPTY FILE"
        elif metadata['is_sparse']:
            info_text += "\n⚠️ SPARSE DATA"
        
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes, 
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
               fontsize=9)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Plot saved to {save_path}")
        
        plt.show()
    
    def plot_map_comparison(self, files: List[DataFile], 
                           title: str = "Map Comparison",
                           save_path: Optional[str] = None,
                           colormap: str = 'viridis',
                           max_cols: int = 3) -> None:
        """
        Plot multiple maps in a grid for comparison.
        
        Args:
            files: List of DataFile objects to plot
            title: Overall plot title
            save_path: Optional path to save the plot
            colormap: Matplotlib colormap name
            max_cols: Maximum number of columns in the grid
        """
        if not files:
            logger.error("No files provided for comparison")
            return

        # Set up global normalization if requested
        if self.normalization_mode == 'global':
            self.global_min, self.global_max = self.calculate_global_normalization(files)
            logger.info(f"Global normalization range: {self.global_min:.1f} - {self.global_max:.1f}")

        # Calculate grid dimensions
        n_files = len(files)
        n_cols = min(max_cols, n_files)
        n_rows = (n_files + n_cols - 1) // n_cols
        
        # Create subplots
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(4*n_cols, 4*n_rows))
        if n_files == 1:
            axes = [axes]
        elif n_rows == 1:
            axes = axes.reshape(1, -1)
        
        # Plot each file
        for i, data_file in enumerate(files):
            row = i // n_cols
            col = i % n_cols
            ax = axes[row, col] if n_rows > 1 else axes[col]
            
            # Load image data
            result = self.load_image_data(data_file)
            if result is None:
                ax.text(0.5, 0.5, f"Error loading\n{data_file.filename}",
                       ha='center', va='center', transform=ax.transAxes)
                ax.set_xticks([])
                ax.set_yticks([])
                continue

            image_data, metadata = result

            # Handle empty files
            if metadata['is_empty']:
                ax.text(0.5, 0.5, f"EMPTY FILE\n{data_file.filename}\n(All zeros)",
                       ha='center', va='center', transform=ax.transAxes,
                       bbox=dict(boxstyle='round', facecolor='red', alpha=0.3))
                ax.set_xticks([])
                ax.set_yticks([])
                continue
            
            # Display image
            im = ax.imshow(image_data, cmap=colormap, aspect='auto', origin='lower')
            
            # Set subplot title
            subplot_title = self.generate_smart_title(data_file)
            if len(subplot_title) > 40:  # Truncate long titles
                subplot_title = subplot_title[:37] + "..."
            ax.set_title(subplot_title, fontsize=10)
            
            # Add colorbar for each subplot
            plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            
            # Set labels
            ax.set_xlabel('X Pixel', fontsize=9)
            ax.set_ylabel('Y Pixel', fontsize=9)
        
        # Hide unused subplots
        for i in range(n_files, n_rows * n_cols):
            row = i // n_cols
            col = i % n_cols
            ax = axes[row, col] if n_rows > 1 else axes[col]
            ax.set_visible(False)
        
        # Set overall title
        fig.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Comparison plot saved to {save_path}")
        
        plt.show()
    
    def analyze_by_parameter(self, parameter: str, parameter_values: Optional[List] = None) -> None:
        """
        Analyze map files grouped by a specific parameter.
        
        Args:
            parameter: Parameter name to group by (e.g., 'esa_voltage_value')
            parameter_values: Optional list of specific parameter values to include
        """
        map_files = self.discover_map_files()
        
        if not map_files:
            logger.error("No FITS/MAP files found")
            return
        
        # Group files by parameter
        groups = self.data_manager.group_files_by_parameter(parameter, min_group_size=1)
        
        if not groups:
            logger.error(f"No groups found for parameter '{parameter}'")
            return
        
        # Filter by specific values if provided
        if parameter_values:
            groups = [g for g in groups if g.common_parameters[parameter] in parameter_values]
        
        for group in groups:
            map_files_in_group = [f for f in group.files if f.is_fits_or_map]
            
            if map_files_in_group:
                param_value = group.common_parameters[parameter]
                title = f"Map Analysis - {parameter} = {param_value}"
                
                if len(map_files_in_group) == 1:
                    self.plot_single_map(map_files_in_group[0], custom_title=title)
                else:
                    self.plot_map_comparison(map_files_in_group, title=title)
    
    def analyze_comparison_set(self, fixed_parameters: List[str], varying_parameter: str) -> None:
        """
        Analyze comparison sets where some parameters are fixed and one varies.
        
        Args:
            fixed_parameters: Parameters that should be constant
            varying_parameter: Parameter that should vary
        """
        map_files = self.discover_map_files()
        
        if not map_files:
            logger.error("No FITS/MAP files found")
            return
        
        # Find comparison sets
        comparison_sets = self.data_manager.find_comparison_sets(fixed_parameters, varying_parameter)
        
        if not comparison_sets:
            logger.error(f"No comparison sets found")
            return
        
        for group in comparison_sets:
            map_files_in_group = [f for f in group.files if f.is_fits_or_map]
            
            if len(map_files_in_group) > 1:
                # Create descriptive title
                fixed_desc = ", ".join([f"{p}={group.common_parameters[p]}" 
                                      for p in fixed_parameters 
                                      if group.common_parameters[p] is not None])
                title = f"Map Comparison - {fixed_desc}, varying {varying_parameter}"
                
                self.plot_map_comparison(map_files_in_group, title=title)
    
    def interactive_file_selection(self) -> None:
        """Interactive mode for file selection and visualization."""
        map_files = self.discover_map_files()
        
        if not map_files:
            logger.error("No FITS/MAP files found")
            return
        
        print(f"\nFound {len(map_files)} FITS/MAP files:")
        for i, file in enumerate(map_files):
            title = self.generate_smart_title(file)
            print(f"{i+1:2d}. {file.filename} ({title})")
        
        print("\nEnter file numbers to visualize (comma-separated, e.g., 1,3,5):")
        print("Or enter 'single X' to view file X individually:")
        try:
            selection = input("Selection: ").strip()
            if not selection:
                return
            
            if selection.startswith('single '):
                # Single file mode
                index = int(selection.split()[1]) - 1
                if 0 <= index < len(map_files):
                    self.plot_single_map(map_files[index])
                else:
                    print("Invalid file number")
            else:
                # Multiple file comparison mode
                indices = [int(x.strip()) - 1 for x in selection.split(',')]
                selected_files = [map_files[i] for i in indices if 0 <= i < len(map_files)]
                
                if selected_files:
                    if len(selected_files) == 1:
                        self.plot_single_map(selected_files[0])
                    else:
                        self.plot_map_comparison(selected_files, title="Selected Files Comparison")
                else:
                    print("No valid files selected")
                    
        except (ValueError, IndexError) as e:
            print(f"Invalid selection: {e}")


def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(description="Enhanced Map/FITS Visualization Tool")
    parser.add_argument("--data-dir", default="data", help="Data directory path")
    parser.add_argument("--mode", choices=['interactive', 'auto', 'parameter', 'comparison'], 
                       default='interactive', help="Visualization mode")
    parser.add_argument("--parameter", help="Parameter to group by (for parameter mode)")
    parser.add_argument("--parameter-values", nargs='+', help="Specific parameter values to include")
    parser.add_argument("--fixed-params", nargs='+', help="Fixed parameters for comparison mode")
    parser.add_argument("--varying-param", help="Varying parameter for comparison mode")
    parser.add_argument("--colormap", default="viridis", help="Matplotlib colormap name")
    parser.add_argument("--contrast-range", nargs=2, type=float, default=[1, 99],
                       help="Percentile range for contrast enhancement")
    parser.add_argument("--normalization", choices=['percentile', 'minmax', 'none', 'global'],
                       default='percentile', help="Normalization mode for image display")
    parser.add_argument("--show-empty", action='store_true',
                       help="Include empty files in analysis")
    parser.add_argument("--min-density", type=float, default=0.0,
                       help="Minimum data density (fraction of non-zero pixels) to include files")
    
    args = parser.parse_args()
    
    # Initialize visualizer
    visualizer = EnhancedMapVisualizer(args.data_dir)
    visualizer.default_contrast_range = tuple(args.contrast_range)
    visualizer.normalization_mode = args.normalization
    
    # Run visualization based on mode
    if args.mode == 'interactive':
        visualizer.interactive_file_selection()
    elif args.mode == 'auto':
        # Automatic visualization of all files (limited to first few)
        map_files = visualizer.discover_map_files()
        if map_files:
            # Show first 6 files to avoid overwhelming display
            files_to_show = map_files[:6]
            visualizer.plot_map_comparison(files_to_show, title="Sample FITS/MAP Files")
    elif args.mode == 'parameter':
        if not args.parameter:
            logger.error("Parameter mode requires --parameter argument")
            return
        visualizer.analyze_by_parameter(args.parameter, args.parameter_values)
    elif args.mode == 'comparison':
        if not args.fixed_params or not args.varying_param:
            logger.error("Comparison mode requires --fixed-params and --varying-param arguments")
            return
        visualizer.analyze_comparison_set(args.fixed_params, args.varying_param)


if __name__ == "__main__":
    main()
