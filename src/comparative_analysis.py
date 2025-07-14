"""
Comparative Analysis Tools Module

This module provides tools for automatically grouping and comparing experimental
data files with similar parameters while holding certain variables constant.

Author: XDL Processing Project
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any, Union
from dataclasses import dataclass
import logging
from pathlib import Path

from data_model import DataManager, DataFile, ExperimentGroup
from filename_parser import ExperimentalParameters
from fits_handler import FitsHandler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ComparisonResult:
    """Results from a comparative analysis."""
    
    group_name: str
    description: str
    files: List[DataFile]
    fixed_parameters: Dict[str, Any]
    varying_parameter: str
    varying_values: List[Any]
    
    # Analysis results
    statistics: Optional[Dict[str, Any]] = None
    plots_generated: List[str] = None
    
    def __post_init__(self):
        if self.plots_generated is None:
            self.plots_generated = []


class ComparativeAnalyzer:
    """Tool for performing comparative analysis of experimental data."""
    
    def __init__(self, data_directory: str = "data"):
        """Initialize the comparative analyzer."""
        self.data_manager = DataManager(data_directory)
        self.fits_handler = FitsHandler()
        
        # Common parameter combinations for analysis
        self.common_comparisons = {
            'beam_energy_sweep': {
                'fixed': ['esa_voltage_value', 'inner_angle_value'],
                'varying': 'beam_energy_value',
                'description': 'Compare different beam energies with fixed ESA voltage and angle'
            },
            'voltage_sweep': {
                'fixed': ['beam_energy_value', 'inner_angle_value'],
                'varying': 'esa_voltage_value',
                'description': 'Compare different ESA voltages with fixed beam energy and angle'
            },
            'angle_sweep': {
                'fixed': ['beam_energy_value', 'esa_voltage_value'],
                'varying': 'inner_angle_value',
                'description': 'Compare different angles with fixed beam energy and ESA voltage'
            },
            'temporal_analysis': {
                'fixed': ['beam_energy_value', 'esa_voltage_value', 'inner_angle_value'],
                'varying': 'datetime_obj',
                'description': 'Compare measurements over time with fixed experimental parameters'
            }
        }
    
    def discover_comparison_opportunities(self) -> Dict[str, List[ExperimentGroup]]:
        """
        Automatically discover opportunities for comparative analysis.
        
        Returns:
            Dictionary mapping comparison types to available groups
        """
        # Discover all files
        all_files = self.data_manager.discover_files()
        logger.info(f"Analyzing {len(all_files)} files for comparison opportunities")
        
        opportunities = {}
        
        for comp_name, comp_config in self.common_comparisons.items():
            # Find comparison sets for this configuration
            comparison_groups = self.data_manager.find_comparison_sets(
                comp_config['fixed'], 
                comp_config['varying']
            )
            
            if comparison_groups:
                opportunities[comp_name] = comparison_groups
                logger.info(f"Found {len(comparison_groups)} groups for {comp_name}")
        
        return opportunities
    
    def analyze_phd_comparison(self, group: ExperimentGroup) -> ComparisonResult:
        """
        Perform comparative analysis on PHD files within a group.
        
        Args:
            group: ExperimentGroup containing files to compare
            
        Returns:
            ComparisonResult with analysis outcomes
        """
        # Filter to PHD files only
        phd_files = [f for f in group.files if f.is_phd]
        
        if len(phd_files) < 2:
            logger.warning(f"Group {group.name} has insufficient PHD files for comparison")
            return None
        
        # Create comparison result
        result = ComparisonResult(
            group_name=group.name,
            description=group.description,
            files=phd_files,
            fixed_parameters=group.common_parameters,
            varying_parameter=group.varying_parameters[0] if group.varying_parameters else 'unknown',
            varying_values=group.get_parameter_values(group.varying_parameters[0]) if group.varying_parameters else []
        )
        
        # Load and analyze PHD data
        phd_data_sets = []
        labels = []
        
        for data_file in phd_files:
            if self.data_manager.load_file_data(data_file):
                phd_data_sets.append(data_file.phd_data)
                
                # Generate label based on varying parameter
                if result.varying_parameter != 'unknown':
                    param_value = getattr(data_file.parameters, result.varying_parameter, 'N/A')
                    if result.varying_parameter == 'datetime_obj' and param_value:
                        labels.append(param_value.strftime('%Y-%m-%d %H:%M'))
                    else:
                        labels.append(f"{result.varying_parameter}={param_value}")
                else:
                    labels.append(Path(data_file.filename).stem)
        
        # Calculate statistics
        result.statistics = self._calculate_phd_statistics(phd_data_sets, labels)
        
        return result
    
    def analyze_fits_comparison(self, group: ExperimentGroup) -> ComparisonResult:
        """
        Perform comparative analysis on FITS/MAP files within a group.
        
        Args:
            group: ExperimentGroup containing files to compare
            
        Returns:
            ComparisonResult with analysis outcomes
        """
        # Filter to FITS/MAP files only
        fits_files = [f for f in group.files if f.is_fits_or_map]
        
        if len(fits_files) < 2:
            logger.warning(f"Group {group.name} has insufficient FITS/MAP files for comparison")
            return None
        
        # Create comparison result
        result = ComparisonResult(
            group_name=group.name,
            description=group.description,
            files=fits_files,
            fixed_parameters=group.common_parameters,
            varying_parameter=group.varying_parameters[0] if group.varying_parameters else 'unknown',
            varying_values=group.get_parameter_values(group.varying_parameters[0]) if group.varying_parameters else []
        )
        
        # Load and analyze FITS data
        image_stats = []
        
        for data_file in fits_files:
            if self.data_manager.load_file_data(data_file):
                if data_file.fits_data and data_file.fits_data.data is not None:
                    stats = {
                        'filename': data_file.filename,
                        'min_value': data_file.fits_data.min_value,
                        'max_value': data_file.fits_data.max_value,
                        'mean_value': data_file.fits_data.mean_value,
                        'std_value': data_file.fits_data.std_value,
                        'non_zero_pixels': np.count_nonzero(data_file.fits_data.data),
                        'total_pixels': data_file.fits_data.data.size
                    }
                    
                    # Add varying parameter value
                    if result.varying_parameter != 'unknown':
                        param_value = getattr(data_file.parameters, result.varying_parameter, None)
                        stats['varying_param_value'] = param_value
                    
                    image_stats.append(stats)
        
        # Calculate comparative statistics
        result.statistics = self._calculate_fits_statistics(image_stats, result.varying_parameter)
        
        return result
    
    def _calculate_phd_statistics(self, phd_data_sets: List[Dict], labels: List[str]) -> Dict[str, Any]:
        """Calculate statistics for PHD data comparison."""
        stats = {
            'num_files': len(phd_data_sets),
            'labels': labels,
            'peak_positions': [],
            'peak_heights': [],
            'total_counts': [],
            'mean_adc': [],
            'std_adc': []
        }
        
        for i, phd_data in enumerate(phd_data_sets):
            if phd_data and 'adc_bins' in phd_data and 'counts' in phd_data:
                bins = phd_data['adc_bins']
                counts = phd_data['counts']
                
                # Find peak position
                peak_idx = np.argmax(counts)
                stats['peak_positions'].append(bins[peak_idx])
                stats['peak_heights'].append(counts[peak_idx])
                
                # Calculate total counts
                stats['total_counts'].append(np.sum(counts))
                
                # Calculate weighted mean and std
                total_counts = np.sum(counts)
                if total_counts > 0:
                    mean_adc = np.sum(bins * counts) / total_counts
                    variance = np.sum(counts * (bins - mean_adc)**2) / total_counts
                    std_adc = np.sqrt(variance)
                    stats['mean_adc'].append(mean_adc)
                    stats['std_adc'].append(std_adc)
                else:
                    stats['mean_adc'].append(0)
                    stats['std_adc'].append(0)
        
        return stats
    
    def _calculate_fits_statistics(self, image_stats: List[Dict], varying_parameter: str) -> Dict[str, Any]:
        """Calculate statistics for FITS data comparison."""
        if not image_stats:
            return {}
        
        # Create DataFrame for easier analysis
        df = pd.DataFrame(image_stats)
        
        stats = {
            'num_files': len(image_stats),
            'varying_parameter': varying_parameter,
            'summary_stats': {}
        }
        
        # Calculate summary statistics for each metric
        numeric_columns = ['min_value', 'max_value', 'mean_value', 'std_value', 'non_zero_pixels']
        
        for col in numeric_columns:
            if col in df.columns:
                stats['summary_stats'][col] = {
                    'mean': df[col].mean(),
                    'std': df[col].std(),
                    'min': df[col].min(),
                    'max': df[col].max()
                }
        
        # Add correlation analysis if varying parameter is numeric
        if 'varying_param_value' in df.columns:
            try:
                varying_values = pd.to_numeric(df['varying_param_value'], errors='coerce')
                if not varying_values.isna().all():
                    correlations = {}
                    for col in numeric_columns:
                        if col in df.columns:
                            corr = varying_values.corr(df[col])
                            if not np.isnan(corr):
                                correlations[col] = corr
                    stats['correlations'] = correlations
            except:
                pass  # Skip correlation analysis if conversion fails
        
        return stats
    
    def generate_comparison_report(self, results: List[ComparisonResult], 
                                 output_dir: str = "results") -> str:
        """
        Generate a comprehensive comparison report.
        
        Args:
            results: List of ComparisonResult objects
            output_dir: Directory to save the report
            
        Returns:
            Path to the generated report file
        """
        os.makedirs(output_dir, exist_ok=True)
        report_path = os.path.join(output_dir, "comparative_analysis_report.md")
        
        with open(report_path, 'w') as f:
            f.write("# Comparative Analysis Report\n\n")
            f.write(f"Generated from {sum(len(r.files) for r in results)} files across {len(results)} comparison groups.\n\n")
            
            for i, result in enumerate(results, 1):
                f.write(f"## {i}. {result.group_name}\n\n")
                f.write(f"**Description:** {result.description}\n\n")
                f.write(f"**Files analyzed:** {len(result.files)}\n\n")
                
                # Fixed parameters
                if result.fixed_parameters:
                    f.write("**Fixed parameters:**\n")
                    for param, value in result.fixed_parameters.items():
                        f.write(f"- {param}: {value}\n")
                    f.write("\n")
                
                # Varying parameter
                f.write(f"**Varying parameter:** {result.varying_parameter}\n")
                f.write(f"**Values:** {', '.join(map(str, result.varying_values))}\n\n")
                
                # Statistics
                if result.statistics:
                    f.write("**Analysis Results:**\n")
                    if 'peak_positions' in result.statistics:
                        # PHD analysis
                        f.write("- Peak positions: " + 
                               ", ".join(f"{p:.1f}" for p in result.statistics['peak_positions']) + "\n")
                        f.write("- Total counts: " + 
                               ", ".join(f"{c:.0f}" for c in result.statistics['total_counts']) + "\n")
                    elif 'summary_stats' in result.statistics:
                        # FITS analysis
                        for metric, stats in result.statistics['summary_stats'].items():
                            f.write(f"- {metric}: mean={stats['mean']:.2f}, std={stats['std']:.2f}\n")
                    f.write("\n")
                
                f.write("---\n\n")
        
        logger.info(f"Comparison report saved to {report_path}")
        return report_path
    
    def run_automatic_analysis(self, output_dir: str = "results") -> List[ComparisonResult]:
        """
        Run automatic comparative analysis on all discovered opportunities.
        
        Args:
            output_dir: Directory to save results
            
        Returns:
            List of ComparisonResult objects
        """
        opportunities = self.discover_comparison_opportunities()
        all_results = []
        
        for comp_type, groups in opportunities.items():
            logger.info(f"Analyzing {comp_type} comparisons...")
            
            for group in groups:
                # Analyze PHD files
                phd_result = self.analyze_phd_comparison(group)
                if phd_result:
                    all_results.append(phd_result)
                
                # Analyze FITS files
                fits_result = self.analyze_fits_comparison(group)
                if fits_result:
                    all_results.append(fits_result)
        
        # Generate report
        if all_results:
            report_path = self.generate_comparison_report(all_results, output_dir)
            logger.info(f"Analysis complete. {len(all_results)} comparisons performed.")
        else:
            logger.warning("No comparison opportunities found.")
        
        return all_results


if __name__ == "__main__":
    # Test the comparative analyzer
    analyzer = ComparativeAnalyzer()
    
    # Discover opportunities
    opportunities = analyzer.discover_comparison_opportunities()
    
    print("Comparison Opportunities Found:")
    for comp_type, groups in opportunities.items():
        print(f"\n{comp_type}: {len(groups)} groups")
        for group in groups[:3]:  # Show first 3 groups
            print(f"  - {group.name}: {len(group.files)} files")
    
    # Run automatic analysis
    results = analyzer.run_automatic_analysis()
    print(f"\nCompleted {len(results)} comparative analyses")
