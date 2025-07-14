#!/usr/bin/env python3
"""
Test runner for the XDL Processing project.

This script runs all unit tests and generates a test report.

Author: XDL Processing Project
"""

import unittest
import sys
import os
import time
from io import StringIO


def discover_and_run_tests():
    """Discover and run all tests in the tests directory."""
    
    # Add src directory to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    
    # Discover tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'tests')
    
    if not os.path.exists(start_dir):
        print(f"Tests directory not found: {start_dir}")
        return False
    
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Count tests
    test_count = suite.countTestCases()
    print(f"Discovered {test_count} tests")
    
    if test_count == 0:
        print("No tests found!")
        return False
    
    # Run tests with detailed output
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
        buffer=True
    )
    
    print("\nRunning tests...")
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # Print results
    output = stream.getvalue()
    print(output)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"Time: {end_time - start_time:.2f} seconds")
    
    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Error:')[-1].strip()}")
    
    if result.skipped:
        print(f"\nSKIPPED ({len(result.skipped)}):")
        for test, reason in result.skipped:
            print(f"- {test}: {reason}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\nSuccess rate: {success_rate:.1f}%")
    
    if result.wasSuccessful():
        print("✅ All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False


def run_specific_test(test_module):
    """Run a specific test module."""
    
    # Add src directory to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    
    try:
        # Import the test module
        module = __import__(f"tests.{test_module}", fromlist=[test_module])
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except ImportError as e:
        print(f"Error importing test module '{test_module}': {e}")
        return False


def main():
    """Main function."""
    
    if len(sys.argv) > 1:
        # Run specific test
        test_module = sys.argv[1]
        if test_module.startswith('test_'):
            test_module = test_module[5:]  # Remove 'test_' prefix
        if test_module.endswith('.py'):
            test_module = test_module[:-3]  # Remove '.py' suffix
        
        print(f"Running specific test: test_{test_module}")
        success = run_specific_test(f"test_{test_module}")
    else:
        # Run all tests
        print("Running all tests...")
        success = discover_and_run_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
