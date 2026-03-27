#!/usr/bin/env python3
"""
Test runner for kimi-autoresearch v2.0

Usage:
    python tests/run_tests.py              # Run all tests
    python tests/run_tests.py -v           # Run with verbose output
    python tests/run_tests.py test_ralph   # Run specific test file
"""
import sys
import os
import unittest
import argparse

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


def run_all_tests(verbose=False):
    """Run all test suites."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Discover all tests in the tests directory
    start_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        discovered = loader.discover(start_dir, pattern='test_*.py')
        suite.addTests(discovered)
    except Exception as e:
        print(f"Warning: Some tests could not be loaded: {e}")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_specific_test(test_name, verbose=False):
    """Run a specific test file."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    test_file = os.path.join(os.path.dirname(__file__), f'{test_name}.py')
    
    if not os.path.exists(test_file):
        print(f"Error: Test file '{test_file}' not found")
        return False
    
    try:
        discovered = loader.loadTestsFromName(test_name)
        suite.addTests(discovered)
    except Exception as e:
        print(f"Error loading test '{test_name}': {e}")
        return False
    
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def main():
    parser = argparse.ArgumentParser(description='Run kimi-autoresearch tests')
    parser.add_argument('test', nargs='?', help='Specific test file to run (e.g., test_ralph)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  Kimi Autoresearch Test Suite v2.0")
    print("=" * 60)
    print()
    
    if args.test:
        success = run_specific_test(args.test, args.verbose)
    else:
        success = run_all_tests(args.verbose)
    
    print()
    print("=" * 60)
    if success:
        print("  ✓ All tests passed!")
    else:
        print("  ✗ Some tests failed")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
