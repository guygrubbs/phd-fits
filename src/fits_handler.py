"""
FITS File Handler Module

This module provides robust FITS file reading and processing capabilities
for the XDL Processing project using astropy.

Author: XDL Processing Project
"""

import os
import numpy as np
import logging
from typing import Dict, Optional, Tuple, Any, List
from dataclasses import dataclass
from astropy.io import fits
from astropy.io.fits.verify import VerifyError


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FitsData:
    """Data class to hold FITS file information and data."""

    filename: str
    header: Dict[str, Any] = None
    data: Optional[np.ndarray] = None
    shape: Optional[Tuple[int, ...]] = None
    dtype: Optional[str] = None
    
    # Image statistics
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None
    std_value: Optional[float] = None
    
    # File info
    file_size: Optional[int] = None
    num_hdus: Optional[int] = None
    
    # Error info
    has_errors: bool = False
    error_messages: List[str] = None
    
    def __post_init__(self):
        if self.error_messages is None:
            self.error_messages = []
        if self.header is None:
            self.header = {}


class FitsHandler:
    """Handler for reading and processing FITS files."""
    
    def __init__(self, verify_checksums: bool = False, ignore_missing_end: bool = True):
        """
        Initialize the FITS handler.
        
        Args:
            verify_checksums: Whether to verify FITS checksums
            ignore_missing_end: Whether to ignore missing END cards
        """
        self.verify_checksums = verify_checksums
        self.ignore_missing_end = ignore_missing_end
        
    def read_fits_file(self, filepath: str, hdu_index: int = 0) -> FitsData:
        """
        Read a FITS file and return structured data.
        
        Args:
            filepath: Path to the FITS file
            hdu_index: Index of the HDU to read (default: 0 for primary HDU)
            
        Returns:
            FitsData object containing file information and data
        """
        fits_data = FitsData(filename=os.path.basename(filepath))
        
        try:
            # Get file size
            if os.path.exists(filepath):
                fits_data.file_size = os.path.getsize(filepath)
            
            # Open FITS file with error handling
            with fits.open(filepath, 
                          ignore_missing_end=self.ignore_missing_end,
                          checksum=self.verify_checksums) as hdul:
                
                fits_data.num_hdus = len(hdul)
                
                # Check if requested HDU exists
                if hdu_index >= len(hdul):
                    error_msg = f"HDU index {hdu_index} not found. File has {len(hdul)} HDUs."
                    fits_data.error_messages.append(error_msg)
                    fits_data.has_errors = True
                    logger.warning(error_msg)
                    return fits_data
                
                hdu = hdul[hdu_index]
                
                # Extract header information
                fits_data.header = dict(hdu.header)
                
                # Extract data if available
                if hdu.data is not None:
                    fits_data.data = hdu.data.copy()
                    fits_data.shape = fits_data.data.shape
                    fits_data.dtype = str(fits_data.data.dtype)
                    
                    # Calculate statistics for numeric data
                    if np.issubdtype(fits_data.data.dtype, np.number):
                        fits_data.min_value = float(np.min(fits_data.data))
                        fits_data.max_value = float(np.max(fits_data.data))
                        fits_data.mean_value = float(np.mean(fits_data.data))
                        fits_data.std_value = float(np.std(fits_data.data))
                else:
                    logger.warning(f"No data found in HDU {hdu_index} of {filepath}")
                    
        except FileNotFoundError:
            error_msg = f"File not found: {filepath}"
            fits_data.error_messages.append(error_msg)
            fits_data.has_errors = True
            logger.error(error_msg)
            
        except VerifyError as e:
            error_msg = f"FITS verification error: {str(e)}"
            fits_data.error_messages.append(error_msg)
            fits_data.has_errors = True
            logger.error(error_msg)
            
        except Exception as e:
            error_msg = f"Error reading FITS file: {str(e)}"
            fits_data.error_messages.append(error_msg)
            fits_data.has_errors = True
            logger.error(error_msg)
            
        return fits_data
    
    def read_fits_header_only(self, filepath: str, hdu_index: int = 0) -> Dict[str, Any]:
        """
        Read only the header from a FITS file for quick metadata access.
        
        Args:
            filepath: Path to the FITS file
            hdu_index: Index of the HDU to read
            
        Returns:
            Dictionary containing header keywords and values
        """
        try:
            with fits.open(filepath, 
                          ignore_missing_end=self.ignore_missing_end,
                          checksum=self.verify_checksums) as hdul:
                
                if hdu_index >= len(hdul):
                    logger.warning(f"HDU index {hdu_index} not found in {filepath}")
                    return {}
                
                return dict(hdul[hdu_index].header)
                
        except Exception as e:
            logger.error(f"Error reading FITS header from {filepath}: {str(e)}")
            return {}
    
    def get_fits_info(self, filepath: str) -> Dict[str, Any]:
        """
        Get basic information about a FITS file without loading data.
        
        Args:
            filepath: Path to the FITS file
            
        Returns:
            Dictionary with file information
        """
        info = {
            'filename': os.path.basename(filepath),
            'filepath': filepath,
            'file_size': None,
            'num_hdus': 0,
            'hdus_info': [],
            'has_errors': False,
            'error_messages': []
        }
        
        try:
            if os.path.exists(filepath):
                info['file_size'] = os.path.getsize(filepath)
            
            with fits.open(filepath, 
                          ignore_missing_end=self.ignore_missing_end,
                          checksum=self.verify_checksums) as hdul:
                
                info['num_hdus'] = len(hdul)
                
                for i, hdu in enumerate(hdul):
                    hdu_info = {
                        'index': i,
                        'type': type(hdu).__name__,
                        'name': hdu.name,
                        'shape': hdu.data.shape if hdu.data is not None else None,
                        'dtype': str(hdu.data.dtype) if hdu.data is not None else None,
                        'header_keys': len(hdu.header)
                    }
                    info['hdus_info'].append(hdu_info)
                    
        except Exception as e:
            info['has_errors'] = True
            info['error_messages'].append(str(e))
            logger.error(f"Error getting FITS info for {filepath}: {str(e)}")
            
        return info
    
    def extract_image_data(self, fits_data: FitsData,
                          percentile_range: Tuple[float, float] = (1, 99),
                          normalization_mode: str = 'percentile') -> Optional[np.ndarray]:
        """
        Extract and process image data with various normalization options.

        Args:
            fits_data: FitsData object containing the data
            percentile_range: Percentile range for contrast enhancement
            normalization_mode: 'percentile', 'minmax', 'none', or 'global'

        Returns:
            Processed image data or None if no data available
        """
        if fits_data.data is None or fits_data.has_errors:
            return None

        data = fits_data.data.copy()

        # Handle different data shapes
        if len(data.shape) == 2:
            # 2D image data
            image_data = data
        elif len(data.shape) == 3 and data.shape[0] == 1:
            # 3D data with single slice
            image_data = data[0]
        else:
            logger.warning(f"Unexpected data shape: {data.shape}")
            return None

        # Apply normalization based on mode
        if np.issubdtype(image_data.dtype, np.number) and normalization_mode != 'none':
            if normalization_mode == 'percentile':
                # Percentile-based normalization (default)
                p_low, p_high = np.percentile(image_data, percentile_range)
                image_data = np.clip(image_data, p_low, p_high)
                if p_high > p_low:
                    image_data = (image_data - p_low) / (p_high - p_low)
            elif normalization_mode == 'minmax':
                # Min-max normalization
                min_val, max_val = np.min(image_data), np.max(image_data)
                if max_val > min_val:
                    image_data = (image_data - min_val) / (max_val - min_val)
            elif normalization_mode == 'global':
                # Global normalization (caller must provide global min/max)
                # This will be handled by the calling function
                pass

        return image_data
    
    def read_legacy_map_file(self, filepath: str) -> Optional[np.ndarray]:
        """
        Read legacy .map files that contain FITS-format data.
        This handles the specific format used in the original map_plot.py.
        
        Args:
            filepath: Path to the .map file
            
        Returns:
            Image data array or None if reading fails
        """
        try:
            # Read the file as binary
            with open(filepath, 'rb') as f:
                data = f.read()
            
            # Skip the FITS header (2880 bytes)
            header_size = 2880
            if len(data) < header_size:
                logger.error(f"File {filepath} too small to contain FITS header")
                return None
            
            # Extract binary data
            binary_data = data[header_size:]
            
            # Convert to 16-bit integers (big-endian)
            image_data = np.frombuffer(binary_data, dtype='>u2')
            
            # Reshape to 1024x1024 (assuming this is the expected size)
            expected_size = 1024 * 1024
            if len(image_data) >= expected_size:
                image_data = image_data[:expected_size].reshape(1024, 1024)
                return image_data
            else:
                logger.warning(f"Insufficient data in {filepath}: got {len(image_data)}, expected {expected_size}")
                return None
                
        except Exception as e:
            logger.error(f"Error reading legacy map file {filepath}: {str(e)}")
            return None


def read_fits_file(filepath: str, hdu_index: int = 0) -> FitsData:
    """
    Convenience function to read a FITS file.
    
    Args:
        filepath: Path to the FITS file
        hdu_index: Index of the HDU to read
        
    Returns:
        FitsData object
    """
    handler = FitsHandler()
    return handler.read_fits_file(filepath, hdu_index)


def get_fits_info(filepath: str) -> Dict[str, Any]:
    """
    Convenience function to get FITS file information.
    
    Args:
        filepath: Path to the FITS file
        
    Returns:
        Dictionary with file information
    """
    handler = FitsHandler()
    return handler.get_fits_info(filepath)


if __name__ == "__main__":
    # Test the FITS handler with sample files
    import glob
    
    data_dir = "data"
    fits_files = glob.glob(os.path.join(data_dir, "*.fits"))[:3]  # Test first 3 files
    
    handler = FitsHandler()
    
    for filepath in fits_files:
        print(f"\nTesting: {os.path.basename(filepath)}")
        
        # Get file info
        info = handler.get_fits_info(filepath)
        print(f"  HDUs: {info['num_hdus']}")
        print(f"  File size: {info['file_size']} bytes")
        
        # Read the file
        fits_data = handler.read_fits_file(filepath)
        if not fits_data.has_errors:
            print(f"  Data shape: {fits_data.shape}")
            print(f"  Data type: {fits_data.dtype}")
            if fits_data.min_value is not None:
                print(f"  Value range: {fits_data.min_value:.2f} - {fits_data.max_value:.2f}")
        else:
            print(f"  Errors: {fits_data.error_messages}")
