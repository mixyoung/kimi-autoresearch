#!/usr/bin/env python3
"""
Test suite for autoresearch daemon
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
        # Initialize run
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


class TestResilience(unittest.TestCase):
    """Test session resilience"""
    
    def test_reanchor_trigger(self):
        """Test reanchor trigger conditions"""
        from autoresearch_resilience import ResilienceManager
        
        manager = ResilienceManager()
        manager.last_anchor_iteration = 0
        
        # Should trigger at iteration 10
        should_reanchor, reason = manager.should_reanchor(10)
        self.assertTrue(should_reanchor)
        
        # Should not trigger at iteration 5
        should_reanchor, reason = manager.should_reanchor(5)
        self.assertFalse(should_reanchor)
    
    def test_session_split_trigger(self):
        """Test session split trigger"""
        from autoresearch_resilience import ResilienceManager
        
        manager = ResilienceManager()
        
        # Should trigger at iteration 40
        should_split, reason = manager.should_split_session(40)
        self.assertTrue(should_split)
        
        # Should not trigger at iteration 20
        should_split, reason = manager.should_split_session(20)
        self.assertFalse(should_split)


class TestMonitoring(unittest.TestCase):
    """Test monitoring"""
    
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
        
        # Create sample results
        with open('autoresearch-results.tsv', 'w') as f:
            f.write("iteration\tcommit\tmetric\tdelta\tstatus\tdescription\ttimestamp\n")
            f.write("0\tabc123\t50\t0\tbaseline\tinitial\t2024-01-01\n")
            f.write("1\tdef456\t45\t-5\tkeep\tfix types\t2024-01-01\n")
            f.write("2\tghi789\t48\t+3\tdiscard\twrong approach\t2024-01-01\n")
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()
    
    def test_progress_calculation(self):
        """Test progress calculation"""
        from autoresearch_monitor import ProgressTracker
        
        tracker = ProgressTracker()
        progress = tracker.calculate_progress(tracker.load_results())
        
        self.assertEqual(progress['total_iterations'], 3)
        self.assertEqual(progress['kept'], 1)
        self.assertEqual(progress['discarded'], 1)
        self.assertEqual(progress['baseline'], 50)
        self.assertEqual(progress['current_metric'], 48)


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
        
        # Initialize git repo
        os.system('git init')
        os.system('git config user.email "test@test.com"')
        os.system('git config user.name "Test"')
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()
    
    def test_full_iteration_workflow(self):
        """Test complete iteration workflow"""
        # This is a simplified integration test
        # In practice, this would test the full loop
        pass


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDaemonState))
    suite.addTests(loader.loadTestsFromTestCase(TestDecisionLogic))
    suite.addTests(loader.loadTestsFromTestCase(TestStuckDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestResilience))
    suite.addTests(loader.loadTestsFromTestCase(TestMonitoring))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
