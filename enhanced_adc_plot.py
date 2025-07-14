#!/usr/bin/env python3
"""
Enhanced ADC Analysis Script

This script provides improved ADC (Pulse Height Distribution) analysis with:
- Automatic file discovery and parameter extraction
- Smart file grouping and filtering
- Parameter-based labeling
- Robust error handling
- Multiple analysis modes

Author: XDL Processing Project
"""

import sys
import os
import argparse
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

# Add src directory to path for imports
sys.path.append('src')
from data_model import DataManager, DataFile, ExperimentGroup
from filename_parser import ExperimentalParameters

# Configure matplotlib backend
matplotlib.use('Qt5Agg')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class EnhancedADCAnalyzer:
    """Enhanced ADC analysis with automatic file management and smart grouping."""
    
    def __init__(self, data_directory: str = "data"):
        """Initialize the analyzer with data directory."""
        self.data_manager = DataManager(data_directory)
        self.adc_bin_range = (11, 245)  # Default ADC bin range for analysis
        
    def discover_phd_files(self) -> List[DataFile]:
        """Discover all PHD files in the data directory."""
        all_files = self.data_manager.discover_files()
        phd_files = [f for f in all_files if f.is_phd]
        logger.info(f"Found {len(phd_files)} PHD files")
        return phd_files
    
    def load_phd_data(self, data_file: DataFile) -> Optional[Dict[str, np.ndarray]]:
        """Load PHD data from a file."""
        if not self.data_manager.load_file_data(data_file):
            logger.error(f"Failed to load data from {data_file.filename}")
            return None
        return data_file.phd_data
    
    def process_phd_data(self, adc_bins: np.ndarray, counts: np.ndarray,
                        bin_range: Optional[Tuple[int, int]] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Process PHD data with filtering and normalization.
        
        Args:
            adc_bins: Array of ADC bin values
            counts: Array of count values
            bin_range: Tuple of (min_bin, max_bin) for filtering
            
        Returns:
            Tuple of (filtered_bins, normalized_counts)
        """
        if bin_range is None:
            bin_range = self.adc_bin_range
        
        # Create a copy to avoid modifying original data
        bins = adc_bins.copy()
        counts_copy = counts.copy()
        
        # Filter data to specified range
        mask = (bins >= bin_range[0]) & (bins <= bin_range[1])
        filtered_bins = bins[mask]
        filtered_counts = counts_copy[mask]
        
        if len(filtered_counts) == 0:
            logger.warning(f"No data in range {bin_range}")
            return bins, counts_copy
        
        # Calculate area under curve for normalization
        area = np.trapz(filtered_counts, filtered_bins)
        
        if area == 0:
            logger.warning("Area under curve is zero, cannot normalize")
            return bins, counts_copy
        
        # Normalize so area under curve equals 1
        normalized_counts = counts_copy / area
        
        return bins, normalized_counts
    
    def generate_smart_label(self, data_file: DataFile) -> str:
        """Generate a smart label based on extracted parameters."""
        params = data_file.parameters
        label_parts = []
        
        # Add beam energy if available
        if params.beam_energy_value:
            label_parts.append(f"{params.beam_energy_value:.0f}eV")
        
        # Add ESA voltage if available
        if params.esa_voltage_value:
            label_parts.append(f"ESA{params.esa_voltage_value:.0f}V")
        
        # Add inner angle if available
        if params.inner_angle_value:
            label_parts.append(f"Angle{params.inner_angle_value:.0f}°")
        
        # Add horizontal value if available
        if params.horizontal_value_num:
            label_parts.append(f"Hor{params.horizontal_value_num:.0f}")
        
        # Add test type if no other parameters
        if not label_parts and params.test_type != 'unknown':
            label_parts.append(params.test_type)
        
        # Fall back to filename if no parameters extracted
        if not label_parts:
            label_parts.append(Path(data_file.filename).stem)
        
        return " ".join(label_parts)
    
    def plot_phd_comparison(self, files: List[DataFile], title: str = "PHD Comparison",
                           custom_labels: Optional[Dict[str, str]] = None,
                           save_path: Optional[str] = None) -> None:
        """
        Plot PHD data comparison for multiple files.
        
        Args:
            files: List of DataFile objects to plot
            title: Plot title
            custom_labels: Optional dictionary mapping filenames to custom labels
            save_path: Optional path to save the plot
        """
        plt.figure(figsize=(12, 8))
        
        colors = plt.cm.tab10(np.linspace(0, 1, len(files)))
        
        for i, data_file in enumerate(files):
            # Load data
            phd_data = self.load_phd_data(data_file)
            if phd_data is None:
                continue
            
            # Process data
            bins, normalized_counts = self.process_phd_data(
                phd_data['adc_bins'], phd_data['counts']
            )
            
            # Generate label
            if custom_labels and data_file.filename in custom_labels:
                label = custom_labels[data_file.filename]
            else:
                label = self.generate_smart_label(data_file)
            
            # Plot
            plt.plot(bins, normalized_counts, label=label, color=colors[i], linewidth=2)
        
        # Customize plot
        plt.title(title, fontsize=16, fontweight='bold')
        plt.xlabel("ADC Bin", fontsize=14)
        plt.ylabel("Normalized Count (Area = 1)", fontsize=14)
        plt.legend(fontsize=10, loc='best')
        plt.grid(True, alpha=0.3)
        plt.xlim(self.adc_bin_range)
        
        # Add range annotation
        plt.axvspan(self.adc_bin_range[0], self.adc_bin_range[1], 
                   alpha=0.1, color='gray', label=f'Analysis Range: {self.adc_bin_range}')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Plot saved to {save_path}")
        
        plt.show()
    
    def analyze_by_parameter(self, parameter: str, parameter_values: Optional[List] = None) -> None:
        """
        Analyze PHD files grouped by a specific parameter.
        
        Args:
            parameter: Parameter name to group by (e.g., 'esa_voltage_value')
            parameter_values: Optional list of specific parameter values to include
        """
        phd_files = self.discover_phd_files()
        
        if not phd_files:
            logger.error("No PHD files found")
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
            phd_files_in_group = [f for f in group.files if f.is_phd]
            
            if phd_files_in_group:
                param_value = group.common_parameters[parameter]
                title = f"PHD Analysis - {parameter} = {param_value}"
                self.plot_phd_comparison(phd_files_in_group, title=title)
    
    def analyze_comparison_set(self, fixed_parameters: List[str], varying_parameter: str) -> None:
        """
        Analyze comparison sets where some parameters are fixed and one varies.
        
        Args:
            fixed_parameters: Parameters that should be constant
            varying_parameter: Parameter that should vary
        """
        phd_files = self.discover_phd_files()
        
        if not phd_files:
            logger.error("No PHD files found")
            return
        
        # Find comparison sets
        comparison_sets = self.data_manager.find_comparison_sets(fixed_parameters, varying_parameter)
        
        if not comparison_sets:
            logger.error(f"No comparison sets found")
            return
        
        for group in comparison_sets:
            phd_files_in_group = [f for f in group.files if f.is_phd]
            
            if len(phd_files_in_group) > 1:
                # Create descriptive title
                fixed_desc = ", ".join([f"{p}={group.common_parameters[p]}" 
                                      for p in fixed_parameters 
                                      if group.common_parameters[p] is not None])
                title = f"PHD Comparison - {fixed_desc}, varying {varying_parameter}"
                
                self.plot_phd_comparison(phd_files_in_group, title=title)
    
    def interactive_file_selection(self) -> None:
        """Interactive mode for file selection and analysis."""
        phd_files = self.discover_phd_files()
        
        if not phd_files:
            logger.error("No PHD files found")
            return
        
        print(f"\nFound {len(phd_files)} PHD files:")
        for i, file in enumerate(phd_files):
            label = self.generate_smart_label(file)
            print(f"{i+1:2d}. {file.filename} ({label})")
        
        print("\nEnter file numbers to analyze (comma-separated, e.g., 1,3,5):")
        try:
            selection = input("Selection: ").strip()
            if not selection:
                return
            
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            selected_files = [phd_files[i] for i in indices if 0 <= i < len(phd_files)]
            
            if selected_files:
                self.plot_phd_comparison(selected_files, title="Selected PHD Files Comparison")
            else:
                print("No valid files selected")
                
        except (ValueError, IndexError) as e:
            print(f"Invalid selection: {e}")


def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(description="Enhanced ADC/PHD Analysis Tool")
    parser.add_argument("--data-dir", default="data", help="Data directory path")
    parser.add_argument("--mode", choices=['interactive', 'auto', 'parameter', 'comparison'], 
                       default='interactive', help="Analysis mode")
    parser.add_argument("--parameter", help="Parameter to group by (for parameter mode)")
    parser.add_argument("--parameter-values", nargs='+', help="Specific parameter values to include")
    parser.add_argument("--fixed-params", nargs='+', help="Fixed parameters for comparison mode")
    parser.add_argument("--varying-param", help="Varying parameter for comparison mode")
    parser.add_argument("--bin-range", nargs=2, type=int, default=[11, 245], 
                       help="ADC bin range for analysis")
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = EnhancedADCAnalyzer(args.data_dir)
    analyzer.adc_bin_range = tuple(args.bin_range)
    
    # Run analysis based on mode
    if args.mode == 'interactive':
        analyzer.interactive_file_selection()
    elif args.mode == 'auto':
        # Automatic analysis of all files
        phd_files = analyzer.discover_phd_files()
        if phd_files:
            analyzer.plot_phd_comparison(phd_files, title="All PHD Files")
    elif args.mode == 'parameter':
        if not args.parameter:
            logger.error("Parameter mode requires --parameter argument")
            return
        analyzer.analyze_by_parameter(args.parameter, args.parameter_values)
    elif args.mode == 'comparison':
        if not args.fixed_params or not args.varying_param:
            logger.error("Comparison mode requires --fixed-params and --varying-param arguments")
            return
        analyzer.analyze_comparison_set(args.fixed_params, args.varying_param)


if __name__ == "__main__":
    main()
