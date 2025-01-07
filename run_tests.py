import unittest
import sys
import os
import argparse

def discover_tests(pattern='test_*.py'):
    """Discover and return test suite."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    loader = unittest.TestLoader()
    start_dir = os.path.join(project_root, 'tests')
    return loader.discover(start_dir, pattern=pattern)

def run_unit_tests():
    """Run unit tests only."""
    suite = discover_tests(pattern='test_[!_]*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

def run_integration_tests():
    """Run integration tests only."""
    suite = discover_tests(pattern='test_*_integration.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

def run_all_tests():
    """Run both unit and integration tests."""
    unit_suite = discover_tests(pattern='test_[!_]*.py')
    integration_suite = discover_tests(pattern='test_*_integration.py')
    
    suite = unittest.TestSuite([unit_suite, integration_suite])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run BookChat tests')
    parser.add_argument('--type', choices=['unit', 'integration', 'all'],
                      default='unit',
                      help='Type of tests to run (default: unit)')
    
    args = parser.parse_args()
    
    if args.type == 'unit':
        print("\nRunning unit tests...")
        success = run_unit_tests()
    elif args.type == 'integration':
        print("\nRunning integration tests...")
        success = run_integration_tests()
    else:  # all
        print("\nRunning all tests...")
        success = run_all_tests()
    
    sys.exit(0 if success else 1)
