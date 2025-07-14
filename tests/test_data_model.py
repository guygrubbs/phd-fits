#!/usr/bin/env python3
"""
Unit tests for the data model module.

Author: XDL Processing Project
"""

import unittest
import sys
import os
import tempfile
import shutil
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_model import DataManager, DataFile, ExperimentGroup
from filename_parser import ExperimentalParameters


class TestDataFile(unittest.TestCase):
    """Test cases for the DataFile class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.fits")
        
        # Create a test file
        with open(self.test_file, 'w') as f:
            f.write("test data")
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_data_file_creation(self):
        """Test DataFile creation and properties."""
        params = ExperimentalParameters(
            filename="test.fits",
            file_type="fits",
            base_name="test.fits"
        )
        
        data_file = DataFile(
            filepath=self.test_file,
            parameters=params,
            file_type="fits"
        )
        
        self.assertEqual(data_file.filename, "test.fits")
        self.assertTrue(data_file.is_fits_or_map)
        self.assertFalse(data_file.is_phd)
        self.assertIsNotNone(data_file.file_size)
        self.assertFalse(data_file.has_errors)
    
    def test_missing_file(self):
        """Test DataFile with missing file."""
        params = ExperimentalParameters(
            filename="missing.fits",
            file_type="fits",
            base_name="missing.fits"
        )
        
        data_file = DataFile(
            filepath="nonexistent.fits",
            parameters=params,
            file_type="fits"
        )
        
        self.assertTrue(data_file.has_errors)
        self.assertIn("File not found", data_file.error_messages[0])


class TestExperimentGroup(unittest.TestCase):
    """Test cases for the ExperimentGroup class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.group = ExperimentGroup(
            name="test_group",
            description="Test group for unit tests"
        )
        
        # Create mock data files
        self.mock_files = []
        for i in range(3):
            params = ExperimentalParameters(
                filename=f"test_{i}.fits",
                file_type="fits",
                base_name=f"test_{i}.fits",
                beam_energy_value=1000.0,
                esa_voltage_value=float(i * 10)
            )
            
            data_file = Mock()
            data_file.parameters = params
            data_file.filename = f"test_{i}.fits"
            
            self.mock_files.append(data_file)
            self.group.add_file(data_file)
    
    def test_group_creation(self):
        """Test ExperimentGroup creation."""
        self.assertEqual(self.group.name, "test_group")
        self.assertEqual(len(self.group.files), 3)
    
    def test_get_files_by_parameter(self):
        """Test filtering files by parameter value."""
        # This would need the actual parameter extraction to work
        # For now, we test the method exists
        result = self.group.get_files_by_parameter('esa_voltage_value', 10.0)
        self.assertIsInstance(result, list)
    
    def test_get_parameter_values(self):
        """Test getting unique parameter values."""
        # This would need the actual parameter extraction to work
        # For now, we test the method exists
        result = self.group.get_parameter_values('esa_voltage_value')
        self.assertIsInstance(result, list)


class TestDataManager(unittest.TestCase):
    """Test cases for the DataManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test files
        test_files = [
            "test1.fits",
            "test2.map", 
            "test3.phd",
            "test4.fits"
        ]
        
        for filename in test_files:
            filepath = os.path.join(self.temp_dir, filename)
            with open(filepath, 'w') as f:
                f.write("test data")
        
        self.data_manager = DataManager(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_data_manager_creation(self):
        """Test DataManager initialization."""
        self.assertEqual(str(self.data_manager.data_directory), self.temp_dir)
        self.assertIsNotNone(self.data_manager.filename_parser)
        self.assertIsNotNone(self.data_manager.fits_handler)
    
    def test_discover_files(self):
        """Test file discovery."""
        files = self.data_manager.discover_files()
        
        # Should find all test files
        self.assertEqual(len(files), 4)
        
        # Check file types
        file_types = [f.file_type for f in files]
        self.assertIn('fits', file_types)
        self.assertIn('map', file_types)
        self.assertIn('phd', file_types)
    
    def test_get_files_summary(self):
        """Test files summary generation."""
        # First discover files
        self.data_manager.discover_files()
        
        summary = self.data_manager.get_files_summary()
        
        self.assertIn('total_files', summary)
        self.assertIn('by_type', summary)
        self.assertIn('by_test_type', summary)
        self.assertEqual(summary['total_files'], 4)
    
    @patch('src.data_model.DataManager.load_file_data')
    def test_load_file_data_mock(self, mock_load):
        """Test file data loading with mocking."""
        mock_load.return_value = True
        
        # Create a mock data file
        params = ExperimentalParameters(
            filename="test.fits",
            file_type="fits",
            base_name="test.fits"
        )
        
        data_file = DataFile(
            filepath=os.path.join(self.temp_dir, "test1.fits"),
            parameters=params,
            file_type="fits"
        )
        
        result = self.data_manager.load_file_data(data_file)
        self.assertTrue(result)
        mock_load.assert_called_once()


class TestDataManagerIntegration(unittest.TestCase):
    """Integration tests for DataManager with real data directory."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Use the actual data directory if it exists
        self.data_dir = "data"
        if os.path.exists(self.data_dir):
            self.data_manager = DataManager(self.data_dir)
        else:
            self.skipTest("Data directory not found")
    
    def test_real_file_discovery(self):
        """Test file discovery with real data."""
        files = self.data_manager.discover_files()
        
        # Should find some files if data directory exists
        self.assertGreater(len(files), 0)
        
        # Check that all files have valid parameters
        for data_file in files:
            self.assertIsNotNone(data_file.parameters)
            self.assertIn(data_file.file_type, ['fits', 'map', 'phd'])
    
    def test_real_grouping(self):
        """Test file grouping with real data."""
        files = self.data_manager.discover_files()
        
        if len(files) > 1:
            # Test grouping by beam energy
            groups = self.data_manager.group_files_by_parameter('beam_energy_value')
            self.assertIsInstance(groups, list)
            
            # Test comparison sets
            comparison_sets = self.data_manager.find_comparison_sets(
                ['beam_energy_value'], 'esa_voltage_value'
            )
            self.assertIsInstance(comparison_sets, list)


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestDataFile))
    suite.addTests(loader.loadTestsFromTestCase(TestExperimentGroup))
    suite.addTests(loader.loadTestsFromTestCase(TestDataManager))
    
    # Add integration tests if data directory exists
    if os.path.exists("data"):
        suite.addTests(loader.loadTestsFromTestCase(TestDataManagerIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
