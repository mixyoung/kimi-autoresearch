#!/usr/bin/env python3
"""
Test suite for autoresearch daemon and core functionality
"""

import json
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


class TestDaemonState(unittest.TestCase):
    """Test daemon state management"""
    
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()
    
    def test_state_file_creation(self):
        """Test state file is created"""
        from autoresearch_init_run import init_state
        
        config = {
            'goal': 'Test goal',
            'scope': 'src/',
            'metric': 'test',
            'verify': 'echo 1',
            'guard': '',
            'direction': 'lower',
            'max_iterations': 10,
            'mode': 'loop'
        }
        
        init_state(config)
        
        self.assertTrue(os.path.exists('autoresearch-state.json'))
        
        with open('autoresearch-state.json', 'r') as f:
            state = json.load(f)
        
        self.assertEqual(state['config']['goal'], 'Test goal')
        self.assertEqual(state['iteration'], 0)
        self.assertEqual(state['status'], 'initialized')


class TestDecisionLogic(unittest.TestCase):
    """Test decision making"""
    
    def test_decide_keep_improved(self):
        """Test keep decision when improved"""
        from autoresearch_decision import decide_keep_discard
        
        result = decide_keep_discard(
            current_metric=40,
            baseline=50,
            direction='lower',
            guard_passed=True
        )
        
        self.assertEqual(result['decision'], 'keep')
        self.assertIn('improved', result['reason'])
    
    def test_decide_discard_worse(self):
        """Test discard decision when worse"""
        from autoresearch_decision import decide_keep_discard
        
        result = decide_keep_discard(
            current_metric=60,
            baseline=50,
            direction='lower',
            guard_passed=True
        )
        
        self.assertEqual(result['decision'], 'discard')
        self.assertIn('did not improve', result['reason'])
    
    def test_decide_rework_guard_failed(self):
        """Test rework when guard failed"""
        from autoresearch_decision import decide_keep_discard
        
        result = decide_keep_discard(
            current_metric=40,
            baseline=50,
            direction='lower',
            guard_passed=False
        )
        
        self.assertEqual(result['decision'], 'rework')


class TestStuckDetection(unittest.TestCase):
    """Test stuck pattern detection"""
    
    def test_not_stuck(self):
        """Test not stuck with few discards"""
        from autoresearch_decision import check_stuck_pattern
        
        state = {
            'consecutive_discards': 2,
            'pivot_count': 0
        }
        
        result = check_stuck_pattern(state)
        
        self.assertEqual(result['action'], 'continue')
    
    def test_refine(self):
        """Test refine action"""
        from autoresearch_decision import check_stuck_pattern
        
        state = {
            'consecutive_discards': 3,
            'pivot_count': 0
        }
        
        result = check_stuck_pattern(state)
        
        self.assertEqual(result['action'], 'refine')
    
    def test_pivot(self):
        """Test pivot action"""
        from autoresearch_decision import check_stuck_pattern
        
        state = {
            'consecutive_discards': 5,
            'pivot_count': 0
        }
        
        result = check_stuck_pattern(state)
        
        self.assertEqual(result['action'], 'pivot')
    
    def test_search(self):
        """Test web search action"""
        from autoresearch_decision import check_stuck_pattern
        
        state = {
            'consecutive_discards': 5,
            'pivot_count': 2
        }
        
        result = check_stuck_pattern(state)
        
        self.assertEqual(result['action'], 'search')


class TestBaselining(unittest.TestCase):
    """Test baseline measurement"""
    
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()
    
    def test_get_baseline_number(self):
        """Test extracting number from command output"""
        from get_baseline import extract_number
        
        # Should extract number from various formats
        self.assertEqual(extract_number("Error count: 42"), 42)
        self.assertEqual(extract_number("42 errors found"), 42)
        self.assertEqual(extract_number("Coverage: 85.5%"), 85.5)
    
    def test_get_baseline_none(self):
        """Test when no number found"""
        from get_baseline import extract_number
        
        result = extract_number("No errors")
        self.assertIsNone(result)


class TestLogging(unittest.TestCase):
    """Test result logging"""
    
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()
    
    def test_log_result_creates_file(self):
        """Test that logging creates results file"""
        from log_result import log_result
        
        log_result(
            iteration=1,
            commit='abc123',
            metric=42,
            delta=-5,
            status='keep',
            description='Test fix'
        )
        
        self.assertTrue(os.path.exists('autoresearch-results.tsv'))
    
    def test_log_result_content(self):
        """Test logged result content"""
        from log_result import log_result
        
        log_result(
            iteration=1,
            commit='abc123',
            metric=42,
            delta=-5,
            status='keep',
            description='Test fix'
        )
        
        with open('autoresearch-results.tsv', 'r') as f:
            content = f.read()
        
        self.assertIn('abc123', content)
        self.assertIn('42', content)
        self.assertIn('keep', content)


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDaemonState))
    suite.addTests(loader.loadTestsFromTestCase(TestDecisionLogic))
    suite.addTests(loader.loadTestsFromTestCase(TestStuckDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestBaselining))
    suite.addTests(loader.loadTestsFromTestCase(TestLogging))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
