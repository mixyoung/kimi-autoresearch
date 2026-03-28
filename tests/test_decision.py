#!/usr/bin/env python3
"""Tests for autoresearch_decision.py"""
import unittest
import sys
import os
import tempfile
import json
from io import StringIO
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from autoresearch_decision import (
    decide_keep_discard,
    check_stuck_pattern,
    update_stuck_counters,
    trigger_web_search,
    load_state,
    save_state,
    main
)


class TestDecision(unittest.TestCase):
    """Test decision functions."""
    
    def test_decide_keep_discard_improved_and_guard_passed(self):
        """Test keep decision when improved and guard passed."""
        result = decide_keep_discard(
            current_metric=42.0,
            baseline=50.0,
            direction='lower',
            guard_passed=True
        )
        
        self.assertEqual(result['decision'], 'keep')
        self.assertEqual(result['delta'], -8.0)
    
    def test_decide_keep_discard_improved_but_guard_failed(self):
        """Test rework decision when improved but guard failed."""
        result = decide_keep_discard(
            current_metric=42.0,
            baseline=50.0,
            direction='lower',
            guard_passed=False
        )
        
        self.assertEqual(result['decision'], 'rework')
    
    def test_decide_keep_discard_not_improved(self):
        """Test discard decision when not improved."""
        result = decide_keep_discard(
            current_metric=55.0,
            baseline=50.0,
            direction='lower',
            guard_passed=True
        )
        
        self.assertEqual(result['decision'], 'discard')
        self.assertEqual(result['delta'], 5.0)
    
    def test_decide_keep_discard_higher_direction(self):
        """Test with higher direction."""
        result = decide_keep_discard(
            current_metric=60.0,
            baseline=50.0,
            direction='higher',
            guard_passed=True
        )
        
        self.assertEqual(result['decision'], 'keep')
        self.assertEqual(result['delta'], 10.0)
    
    def test_check_stuck_pattern_not_stuck(self):
        """Test when not stuck."""
        state = {
            'consecutive_discards': 2,
            'pivot_count': 0
        }
        
        result = check_stuck_pattern(state)
        
        self.assertEqual(result['action'], 'continue')
    
    def test_check_stuck_pattern_refine(self):
        """Test refine action."""
        state = {
            'consecutive_discards': 3,
            'pivot_count': 0
        }
        
        result = check_stuck_pattern(state)
        
        self.assertEqual(result['action'], 'refine')
    
    def test_check_stuck_pattern_pivot(self):
        """Test pivot action."""
        state = {
            'consecutive_discards': 5,
            'pivot_count': 1
        }
        
        result = check_stuck_pattern(state)
        
        self.assertEqual(result['action'], 'pivot')
    
    def test_check_stuck_pattern_search(self):
        """Test search action after multiple pivots."""
        state = {
            'consecutive_discards': 5,
            'pivot_count': 2
        }
        
        result = check_stuck_pattern(state)
        
        self.assertEqual(result['action'], 'search')
    
    def test_update_stuck_counters_keep(self):
        """Test counter reset on keep."""
        state = {
            'consecutive_discards': 3
        }
        
        result = update_stuck_counters(state, 'keep')
        
        self.assertEqual(result['consecutive_discards'], 0)
    
    def test_update_stuck_counters_discard(self):
        """Test counter increment on discard."""
        state = {
            'consecutive_discards': 2
        }
        
        result = update_stuck_counters(state, 'discard')
        
        self.assertEqual(result['consecutive_discards'], 3)


class TestTriggerWebSearch(unittest.TestCase):
    """Test trigger_web_search function."""
    
    def test_trigger_web_search_with_context(self):
        """Test web search trigger with context."""
        state = {
            'config': {'goal': 'Reduce type errors', 'metric': 'error_count'},
            'strategy': 'Add type annotations',
            'last_error': 'TypeError: Cannot read property',
            'consecutive_discards': 5,
            'pivot_count': 2
        }
        
        result = trigger_web_search(state)
        
        self.assertTrue(result['triggered'])
        self.assertIn('query', result)
        self.assertEqual(result['action'], 'web_search')
        self.assertIn('context', result)
    
    def test_trigger_web_search_empty_context(self):
        """Test web search trigger with empty context."""
        state = {}
        
        result = trigger_web_search(state)
        
        self.assertTrue(result['triggered'])
        self.assertEqual(result['query'], 'programming best practices')


class TestLoadSaveState(unittest.TestCase):
    """Test load_state and save_state functions."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_state_no_file(self):
        """Test loading state when no file exists."""
        state = load_state()
        
        self.assertEqual(state, {})
    
    def test_load_state_with_file(self):
        """Test loading state from file."""
        test_state = {'iteration': 5, 'baseline': 100}
        with open('autoresearch-state.json', 'w') as f:
            json.dump(test_state, f)
        
        state = load_state()
        
        self.assertEqual(state['iteration'], 5)
        self.assertEqual(state['baseline'], 100)
    
    def test_save_state(self):
        """Test saving state to file."""
        state = {'iteration': 10, 'best': 50}
        
        save_state(state)
        
        self.assertTrue(os.path.exists('autoresearch-state.json'))
        with open('autoresearch-state.json', 'r') as f:
            saved = json.load(f)
        self.assertEqual(saved['iteration'], 10)


class TestMain(unittest.TestCase):
    """Test main CLI function."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_main_decide(self):
        """Test main with decide action."""
        old_argv = sys.argv
        try:
            sys.argv = [
                'autoresearch_decision.py',
                '--action', 'decide',
                '--current', '42',
                '--baseline', '50',
                '--direction', 'lower',
                '--guard-passed', 'True'
            ]
            
            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            main()
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            # Should be valid JSON
            result = json.loads(output)
            self.assertEqual(result['decision'], 'keep')
        finally:
            sys.argv = old_argv
    
    def test_main_decide_missing_args(self):
        """Test main with decide action missing required args."""
        old_argv = sys.argv
        try:
            sys.argv = [
                'autoresearch_decision.py',
                '--action', 'decide',
                '--current', '42'
                # Missing --baseline
            ]
            
            with self.assertRaises(SystemExit):
                main()
        finally:
            sys.argv = old_argv
    
    def test_main_check_stuck(self):
        """Test main with check-stuck action."""
        # Create state file
        state = {
            'consecutive_discards': 5,
            'pivot_count': 2
        }
        with open('autoresearch-state.json', 'w') as f:
            json.dump(state, f)
        
        old_argv = sys.argv
        try:
            sys.argv = [
                'autoresearch_decision.py',
                '--action', 'check-stuck'
            ]
            
            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            main()
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            # Should be valid JSON
            result = json.loads(output)
            self.assertEqual(result['action'], 'search')
        finally:
            sys.argv = old_argv
    
    def test_main_update_counters(self):
        """Test main with update-counters action."""
        # Create state file
        state = {'consecutive_discards': 2}
        with open('autoresearch-state.json', 'w') as f:
            json.dump(state, f)
        
        old_argv = sys.argv
        try:
            sys.argv = [
                'autoresearch_decision.py',
                '--action', 'update-counters',
                '--status', 'discard'
            ]
            
            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            main()
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            # Should be valid JSON
            result = json.loads(output)
            self.assertEqual(result['consecutive_discards'], 3)
        finally:
            sys.argv = old_argv
    
    def test_main_update_counters_missing_status(self):
        """Test main with update-counters missing status."""
        old_argv = sys.argv
        try:
            sys.argv = [
                'autoresearch_decision.py',
                '--action', 'update-counters'
                # Missing --status
            ]
            
            with self.assertRaises(SystemExit):
                main()
        finally:
            sys.argv = old_argv
    
    def test_main_trigger_search(self):
        """Test main with trigger-search action."""
        # Create state file
        state = {
            'config': {'goal': 'Test goal'},
            'consecutive_discards': 5
        }
        with open('autoresearch-state.json', 'w') as f:
            json.dump(state, f)
        
        old_argv = sys.argv
        try:
            sys.argv = [
                'autoresearch_decision.py',
                '--action', 'trigger-search'
            ]
            
            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            main()
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            # Should be valid JSON
            result = json.loads(output)
            self.assertTrue(result['triggered'])
            self.assertEqual(result['action'], 'web_search')
        finally:
            sys.argv = old_argv


if __name__ == '__main__':
    unittest.main()
