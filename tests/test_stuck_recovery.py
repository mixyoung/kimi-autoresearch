#!/usr/bin/env python3
"""Tests for autoresearch_stuck_recovery.py"""
import unittest
import sys
import os
import tempfile
import json
import io
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from autoresearch_stuck_recovery import (
    load_state, load_results, analyze_stuck_pattern, generate_recovery_suggestions,
    should_trigger_web_search, cmd_check, cmd_trigger, cmd_simulate, main
)


class TestLoadState(unittest.TestCase):
    """Test load_state function."""
    
    def setUp(self):
        """Create temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        os.chdir(self.old_cwd)
        import shutil
        import stat
        
        def on_rm_error(func, path, exc_info):
            os.chmod(path, stat.S_IWRITE)
            try:
                func(path)
            except:
                pass
        
        shutil.rmtree(self.temp_dir, onerror=on_rm_error)
    
    def test_load_state_no_file(self):
        """Test loading state when no file exists."""
        result = load_state()
        self.assertEqual(result, {})
    
    def test_load_state_with_file(self):
        """Test loading state from file."""
        state = {'iteration': 5, 'consecutive_discards': 2}
        with open('autoresearch-state.json', 'w') as f:
            json.dump(state, f)
        
        result = load_state()
        
        self.assertEqual(result['iteration'], 5)
        self.assertEqual(result['consecutive_discards'], 2)
    
    def test_load_state_corrupted(self):
        """Test loading corrupted state file."""
        with open('autoresearch-state.json', 'w') as f:
            f.write('not valid json')
        
        result = load_state()
        
        self.assertEqual(result, {})


class TestLoadResults(unittest.TestCase):
    """Test load_results function."""
    
    def setUp(self):
        """Create temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        os.chdir(self.old_cwd)
        import shutil
        import stat
        
        def on_rm_error(func, path, exc_info):
            os.chmod(path, stat.S_IWRITE)
            try:
                func(path)
            except:
                pass
        
        shutil.rmtree(self.temp_dir, onerror=on_rm_error)
    
    def test_load_results_no_file(self):
        """Test loading results when no file exists."""
        result = load_results()
        self.assertEqual(result, [])
    
    def test_load_results_with_file(self):
        """Test loading results from file."""
        with open('autoresearch-results.tsv', 'w') as f:
            f.write("iteration\tcommit\tmetric\tdelta\tstatus\n")
            f.write("0\tabc\t100\t0\tbaseline\n")
            f.write("1\tdef\t90\t-10\tkeep\n")
        
        result = load_results()
        
        self.assertEqual(len(result), 2)


class TestAnalyzeStuckPattern(unittest.TestCase):
    """Test analyze_stuck_pattern function."""
    
    def test_not_stuck(self):
        """Test when not stuck."""
        state = {'consecutive_discards': 0, 'pivot_count': 0}
        results = []
        
        analysis = analyze_stuck_pattern(state, results)
        
        self.assertFalse(analysis['is_stuck'])
        self.assertEqual(analysis['action'], 'continue')
    
    def test_refine_needed(self):
        """Test when refine is needed."""
        state = {'consecutive_discards': 3, 'pivot_count': 0}
        results = []
        
        analysis = analyze_stuck_pattern(state, results)
        
        self.assertFalse(analysis['is_stuck'])
        self.assertEqual(analysis['action'], 'refine')
    
    def test_pivot_needed(self):
        """Test when pivot is needed."""
        state = {'consecutive_discards': 5, 'pivot_count': 0}
        results = []
        
        analysis = analyze_stuck_pattern(state, results)
        
        self.assertTrue(analysis['is_stuck'])
        self.assertEqual(analysis['action'], 'pivot')
    
    def test_search_needed(self):
        """Test when search is needed."""
        state = {
            'consecutive_discards': 5,
            'pivot_count': 2,
            'config': {'goal': 'Optimize'},
            'strategy': 'caching',
            'last_error': 'Timeout error'
        }
        results = []
        
        analysis = analyze_stuck_pattern(state, results)
        
        self.assertTrue(analysis['is_stuck'])
        self.assertEqual(analysis['action'], 'search')
        self.assertIn('search_query', analysis)
        self.assertIn('Timeout', analysis['search_query'])


class TestGenerateRecoverySuggestions(unittest.TestCase):
    """Test generate_recovery_suggestions function."""
    
    def test_refine_suggestions(self):
        """Test suggestions for refine action."""
        analysis = {
            'action': 'refine',
            'context': {'goal': 'Test'}
        }
        
        suggestions = generate_recovery_suggestions(analysis)
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
    
    def test_pivot_suggestions(self):
        """Test suggestions for pivot action."""
        analysis = {
            'action': 'pivot',
            'context': {'goal': 'Test'}
        }
        
        suggestions = generate_recovery_suggestions(analysis)
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
    
    def test_search_suggestions(self):
        """Test suggestions for search action."""
        analysis = {
            'action': 'search',
            'search_query': 'how to optimize python',
            'context': {'goal': 'Test'}
        }
        
        suggestions = generate_recovery_suggestions(analysis)
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
        # Should include the search query in suggestions
        self.assertTrue(any('how to optimize python' in s for s in suggestions))


class TestShouldTriggerWebSearch(unittest.TestCase):
    """Test should_trigger_web_search function."""
    
    @patch('autoresearch_stuck_recovery.load_state')
    @patch('autoresearch_stuck_recovery.load_results')
    def test_not_stuck(self, mock_load_results, mock_load_state):
        """Test when not stuck enough."""
        mock_load_state.return_value = {'consecutive_discards': 2, 'pivot_count': 0}
        mock_load_results.return_value = []
        
        should_search, analysis = should_trigger_web_search(auto_trigger=True)
        
        self.assertFalse(should_search)
        self.assertFalse(analysis['is_stuck'])
    
    @patch('autoresearch_stuck_recovery.load_state')
    @patch('autoresearch_stuck_recovery.load_results')
    def test_stuck_but_no_auto_trigger(self, mock_load_results, mock_load_state):
        """Test when stuck but auto_trigger is False."""
        mock_load_state.return_value = {
            'consecutive_discards': 5,
            'pivot_count': 2,
            'config': {},
            'strategy': '',
            'last_error': ''
        }
        mock_load_results.return_value = []
        
        should_search, analysis = should_trigger_web_search(auto_trigger=False)
        
        self.assertFalse(should_search)  # Should be False because auto_trigger is False
        self.assertTrue(analysis['is_stuck'])
    
    @patch('autoresearch_stuck_recovery.load_state')
    @patch('autoresearch_stuck_recovery.load_results')
    def test_should_trigger(self, mock_load_results, mock_load_state):
        """Test when should trigger search."""
        mock_load_state.return_value = {
            'consecutive_discards': 5,
            'pivot_count': 2,
            'config': {'goal': 'Test'},
            'strategy': 'test',
            'last_error': 'error'
        }
        mock_load_results.return_value = []
        
        should_search, analysis = should_trigger_web_search(auto_trigger=True)
        
        self.assertTrue(should_search)
        self.assertTrue(analysis['is_stuck'])
        self.assertEqual(analysis['action'], 'search')


class TestCmdCheck(unittest.TestCase):
    """Test cmd_check function."""
    
    @patch('autoresearch_stuck_recovery.load_state')
    @patch('autoresearch_stuck_recovery.load_results')
    def test_check_not_stuck(self, mock_load_results, mock_load_state):
        """Test check when not stuck."""
        mock_load_state.return_value = {'consecutive_discards': 1, 'pivot_count': 0}
        mock_load_results.return_value = []
        
        args = MagicMock()
        args.json = False
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_check(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Not stuck', output)
    
    @patch('autoresearch_stuck_recovery.load_state')
    @patch('autoresearch_stuck_recovery.load_results')
    def test_check_stuck(self, mock_load_results, mock_load_state):
        """Test check when stuck."""
        mock_load_state.return_value = {
            'consecutive_discards': 5,
            'pivot_count': 2,
            'config': {'goal': 'Test'},
            'strategy': 'test',
            'last_error': 'error'
        }
        mock_load_results.return_value = []
        
        args = MagicMock()
        args.json = False
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_check(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 2)
        self.assertIn('STUCK DETECTED', output)


class TestCmdTrigger(unittest.TestCase):
    """Test cmd_trigger function."""
    
    @patch('autoresearch_stuck_recovery.load_state')
    @patch('autoresearch_stuck_recovery.load_results')
    def test_trigger_not_stuck(self, mock_load_results, mock_load_state):
        """Test trigger when not stuck enough."""
        mock_load_state.return_value = {'consecutive_discards': 2, 'pivot_count': 0}
        mock_load_results.return_value = []
        
        args = MagicMock()
        args.json = False
        args.quiet = False
        args.output = None
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_trigger(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Not stuck enough', output)


class TestCmdSimulate(unittest.TestCase):
    """Test cmd_simulate function."""
    
    def test_simulate(self):
        """Test simulate command."""
        args = MagicMock()
        args.discards = None
        args.pivots = None
        args.query = None
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_simulate(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        data = json.loads(output)
        self.assertTrue(data['triggered'])
        self.assertIn('SIMULATION', data['note'])


class TestMain(unittest.TestCase):
    """Test main function."""
    
    def test_main_check(self):
        """Test main with check command."""
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_stuck_recovery.py', 'check']
            result = main()
            # Result depends on state file existence
            self.assertIn(result, [0, 2])
        finally:
            sys.argv = old_argv
    
    def test_main_simulate(self):
        """Test main with simulate command."""
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_stuck_recovery.py', 'simulate']
            result = main()
            self.assertEqual(result, 0)
        finally:
            sys.argv = old_argv
    
    def test_main_no_command(self):
        """Test main with no command."""
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_stuck_recovery.py']
            result = main()
            self.assertEqual(result, 1)
        finally:
            sys.argv = old_argv


if __name__ == '__main__':
    unittest.main()
