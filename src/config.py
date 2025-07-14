"""
Configuration Management Module

This module provides configuration management for the XDL Processing project,
including default settings, user preferences, and logging configuration.

Author: XDL Processing Project
"""

import os
import json
import logging
import logging.config
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict
import yaml


@dataclass
class AnalysisConfig:
    """Configuration for analysis parameters."""
    
    # ADC/PHD Analysis
    adc_bin_range: tuple = (11, 245)
    adc_normalization_mode: str = 'area'  # 'area', 'peak', 'none'
    
    # FITS/Map Analysis
    fits_contrast_range: tuple = (1, 99)  # Percentile range
    fits_normalization_mode: str = 'percentile'  # 'percentile', 'minmax', 'none', 'global'
    default_colormap: str = 'viridis'
    
    # File filtering
    min_data_density: float = 0.0  # Minimum fraction of non-zero pixels
    include_empty_files: bool = False
    max_file_size_mb: float = 100.0  # Maximum file size to process
    
    # Comparison analysis
    min_group_size: int = 2
    correlation_threshold: float = 0.5
    
    # Output settings
    figure_dpi: int = 300
    figure_format: str = 'png'
    save_intermediate_results: bool = True


@dataclass
class PathConfig:
    """Configuration for file paths and directories."""
    
    data_directory: str = "data"
    output_directory: str = "results"
    cache_directory: str = "cache"
    log_directory: str = "logs"
    config_directory: str = "config"
    
    # File patterns
    fits_pattern: str = "*.fits"
    map_pattern: str = "*.map"
    phd_pattern: str = "*.phd"


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    
    # File logging
    log_to_file: bool = True
    log_file_max_size: int = 10 * 1024 * 1024  # 10 MB
    log_file_backup_count: int = 5
    
    # Console logging
    log_to_console: bool = True
    console_level: str = "INFO"


@dataclass
class XDLConfig:
    """Main configuration class combining all settings."""
    
    analysis: AnalysisConfig = None
    paths: PathConfig = None
    logging: LoggingConfig = None
    
    def __post_init__(self):
        if self.analysis is None:
            self.analysis = AnalysisConfig()
        if self.paths is None:
            self.paths = PathConfig()
        if self.logging is None:
            self.logging = LoggingConfig()


class ConfigManager:
    """Manages configuration loading, saving, and validation."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self.config_file = config_file or "config/xdl_config.yaml"
        self.config = XDLConfig()
        
        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        # Load configuration if file exists
        if os.path.exists(self.config_file):
            self.load_config()
        else:
            # Save default configuration
            self.save_config()
    
    def load_config(self) -> XDLConfig:
        """Load configuration from file."""
        try:
            with open(self.config_file, 'r') as f:
                if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                    config_data = yaml.safe_load(f)
                else:
                    config_data = json.load(f)
            
            # Convert nested dictionaries to dataclass instances
            if 'analysis' in config_data:
                self.config.analysis = AnalysisConfig(**config_data['analysis'])
            if 'paths' in config_data:
                self.config.paths = PathConfig(**config_data['paths'])
            if 'logging' in config_data:
                self.config.logging = LoggingConfig(**config_data['logging'])
            
            logging.info(f"Configuration loaded from {self.config_file}")
            
        except Exception as e:
            logging.error(f"Error loading configuration: {e}")
            logging.info("Using default configuration")
        
        return self.config
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            config_data = {
                'analysis': asdict(self.config.analysis),
                'paths': asdict(self.config.paths),
                'logging': asdict(self.config.logging)
            }
            
            with open(self.config_file, 'w') as f:
                if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                    yaml.dump(config_data, f, default_flow_style=False, indent=2)
                else:
                    json.dump(config_data, f, indent=2)
            
            logging.info(f"Configuration saved to {self.config_file}")
            
        except Exception as e:
            logging.error(f"Error saving configuration: {e}")
    
    def update_config(self, section: str, **kwargs) -> None:
        """
        Update configuration section with new values.
        
        Args:
            section: Configuration section ('analysis', 'paths', 'logging')
            **kwargs: Key-value pairs to update
        """
        if section == 'analysis':
            for key, value in kwargs.items():
                if hasattr(self.config.analysis, key):
                    setattr(self.config.analysis, key, value)
        elif section == 'paths':
            for key, value in kwargs.items():
                if hasattr(self.config.paths, key):
                    setattr(self.config.paths, key, value)
        elif section == 'logging':
            for key, value in kwargs.items():
                if hasattr(self.config.logging, key):
                    setattr(self.config.logging, key, value)
        else:
            raise ValueError(f"Unknown configuration section: {section}")
        
        # Save updated configuration
        self.save_config()
    
    def setup_logging(self) -> None:
        """Set up logging based on configuration."""
        log_config = self.config.logging
        
        # Create logs directory
        os.makedirs(self.config.paths.log_directory, exist_ok=True)
        
        # Configure logging
        logging_dict = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': log_config.format,
                    'datefmt': log_config.date_format
                }
            },
            'handlers': {},
            'root': {
                'level': log_config.level,
                'handlers': []
            }
        }
        
        # Console handler
        if log_config.log_to_console:
            logging_dict['handlers']['console'] = {
                'class': 'logging.StreamHandler',
                'level': log_config.console_level,
                'formatter': 'standard',
                'stream': 'ext://sys.stdout'
            }
            logging_dict['root']['handlers'].append('console')
        
        # File handler
        if log_config.log_to_file:
            log_file = os.path.join(self.config.paths.log_directory, 'xdl_processing.log')
            logging_dict['handlers']['file'] = {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': log_config.level,
                'formatter': 'standard',
                'filename': log_file,
                'maxBytes': log_config.log_file_max_size,
                'backupCount': log_config.log_file_backup_count
            }
            logging_dict['root']['handlers'].append('file')
        
        # Apply configuration
        logging.config.dictConfig(logging_dict)
        
        # Log configuration setup
        logger = logging.getLogger(__name__)
        logger.info("Logging configuration applied")
    
    def create_directories(self) -> None:
        """Create all configured directories."""
        directories = [
            self.config.paths.data_directory,
            self.config.paths.output_directory,
            self.config.paths.cache_directory,
            self.config.paths.log_directory,
            self.config.paths.config_directory
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        logging.info("All configured directories created")
    
    def validate_config(self) -> List[str]:
        """
        Validate configuration and return list of issues.
        
        Returns:
            List of validation error messages
        """
        issues = []
        
        # Validate analysis config
        if self.config.analysis.adc_bin_range[0] >= self.config.analysis.adc_bin_range[1]:
            issues.append("ADC bin range: minimum must be less than maximum")
        
        if not 0 <= self.config.analysis.min_data_density <= 1:
            issues.append("Minimum data density must be between 0 and 1")
        
        if self.config.analysis.min_group_size < 1:
            issues.append("Minimum group size must be at least 1")
        
        # Validate paths
        if not os.path.exists(self.config.paths.data_directory):
            issues.append(f"Data directory does not exist: {self.config.paths.data_directory}")
        
        # Validate logging
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.config.logging.level not in valid_levels:
            issues.append(f"Invalid logging level: {self.config.logging.level}")
        
        return issues


# Global configuration instance
_config_manager = None


def get_config() -> XDLConfig:
    """Get the global configuration instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
        _config_manager.setup_logging()
        _config_manager.create_directories()
    return _config_manager.config


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
        _config_manager.setup_logging()
        _config_manager.create_directories()
    return _config_manager


if __name__ == "__main__":
    # Test configuration management
    config_manager = ConfigManager()
    
    print("Default Configuration:")
    print(f"  ADC bin range: {config_manager.config.analysis.adc_bin_range}")
    print(f"  Data directory: {config_manager.config.paths.data_directory}")
    print(f"  Logging level: {config_manager.config.logging.level}")
    
    # Validate configuration
    issues = config_manager.validate_config()
    if issues:
        print(f"\nConfiguration issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\nConfiguration is valid")
    
    # Test configuration update
    config_manager.update_config('analysis', adc_bin_range=(10, 250))
    print(f"\nUpdated ADC bin range: {config_manager.config.analysis.adc_bin_range}")
    
    print(f"\nConfiguration saved to: {config_manager.config_file}")
