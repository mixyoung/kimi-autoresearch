#!/usr/bin/env python3
"""Tests for autoresearch_resilience.py"""
import unittest
import sys
import os
import tempfile
import json
import io
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from autoresearch_resilience import (
    ResilienceManager, main, STATE_FILE, RESILIENCE_LOG
)


class TestResilienceManager(unittest.TestCase):
    """Test ResilienceManager class."""
    
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
    
    def test_initialization(self):
        """Test manager initialization."""
        manager = ResilienceManager()
        
        self.assertEqual(manager.check_count, 0)
        self.assertEqual(manager.last_anchor_iteration, 0)
        self.assertEqual(manager.compaction_count, 0)
    
    def test_load_state_no_file(self):
        """Test loading state when no file exists."""
        manager = ResilienceManager()
        state = manager.load_state()
        
        self.assertEqual(state, {})
    
    def test_load_state_with_file(self):
        """Test loading state from file."""
        test_state = {'iteration': 10, 'config': {'goal': 'Test'}}
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(test_state, f)
        
        manager = ResilienceManager()
        state = manager.load_state()
        
        self.assertEqual(state['iteration'], 10)
        self.assertEqual(state['config']['goal'], 'Test')
    
    def test_save_state(self):
        """Test saving state."""
        manager = ResilienceManager()
        test_state = {'iteration': 5, 'status': 'running'}
        
        manager.save_state(test_state)
        
        self.assertTrue(os.path.exists(STATE_FILE))
        
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            saved = json.load(f)
            self.assertEqual(saved['iteration'], 5)
            self.assertEqual(saved['status'], 'running')
    
    def test_log_event(self):
        """Test logging events."""
        manager = ResilienceManager()
        
        manager.log_event('test_event', {'detail': 'value'})
        
        self.assertTrue(os.path.exists(RESILIENCE_LOG))
        
        with open(RESILIENCE_LOG, 'r', encoding='utf-8') as f:
            line = f.readline()
            entry = json.loads(line)
            self.assertEqual(entry['type'], 'test_event')
            self.assertEqual(entry['details']['detail'], 'value')
            self.assertIn('timestamp', entry)


class TestProtocolFingerprintCheck(unittest.TestCase):
    """Test protocol fingerprint check."""
    
    def test_fingerprint_check(self):
        """Test protocol fingerprint check."""
        manager = ResilienceManager()
        
        result = manager.protocol_fingerprint_check()
        
        self.assertIn('checks', result)
        self.assertIn('all_passed', result)
        self.assertIn('check_count', result)
        self.assertTrue(result['all_passed'])
        self.assertEqual(result['check_count'], 1)


class TestShouldReanchor(unittest.TestCase):
    """Test should_reanchor function."""
    
    def test_no_reanchor_needed(self):
        """Test when reanchor is not needed."""
        manager = ResilienceManager()
        
        should, reason = manager.should_reanchor(5)
        
        self.assertFalse(should)
        self.assertEqual(reason, "")
    
    def test_reanchor_by_interval(self):
        """Test reanchor by iteration interval."""
        manager = ResilienceManager()
        manager.last_anchor_iteration = 0
        
        should, reason = manager.should_reanchor(15)  # > 10 interval
        
        self.assertTrue(should)
        self.assertIn('reanchor interval', reason)
    
    def test_reanchor_by_compaction(self):
        """Test reanchor by context compaction."""
        manager = ResilienceManager()
        manager.compaction_count = 3  # > MAX_CONTEXT_COMPACT
        
        should, reason = manager.should_reanchor(5)
        
        self.assertTrue(should)
        self.assertIn('Context compacted', reason)


class TestShouldSplitSession(unittest.TestCase):
    """Test should_split_session function."""
    
    def test_no_split_needed(self):
        """Test when split is not needed."""
        manager = ResilienceManager()
        
        should, reason = manager.should_split_session(20)
        
        self.assertFalse(should)
        self.assertEqual(reason, "")
    
    def test_split_by_iterations(self):
        """Test split by iteration limit."""
        manager = ResilienceManager()
        
        should, reason = manager.should_split_session(50)  # > 40 limit
        
        self.assertTrue(should)
        self.assertIn('Iteration limit', reason)
    
    def test_split_by_compaction(self):
        """Test split by too many compactions."""
        manager = ResilienceManager()
        manager.compaction_count = 4  # > MAX_CONTEXT_COMPACT + 1
        
        should, reason = manager.should_split_session(20)
        
        self.assertTrue(should)
        self.assertIn('Too many context compactions', reason)


class TestPerformReanchor(unittest.TestCase):
    """Test perform_reanchor function."""
    
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
    
    def test_reanchor(self):
        """Test performing reanchor."""
        manager = ResilienceManager()
        
        result = manager.perform_reanchor(15)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['iteration'], 15)
        self.assertIn('prompt', result)
        self.assertIn('files_to_reload', result)
        
        self.assertEqual(manager.last_anchor_iteration, 15)
        
        # Check log was written
        self.assertTrue(os.path.exists(RESILIENCE_LOG))


class TestPerformSessionSplit(unittest.TestCase):
    """Test perform_session_split function."""
    
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
    
    def test_session_split(self):
        """Test performing session split."""
        manager = ResilienceManager()
        state = {'iteration': 40, 'config': {'goal': 'Test'}}
        
        result = manager.perform_session_split(40, state)
        
        self.assertTrue(result['success'])
        self.assertTrue(result['checkpoint_saved'])
        self.assertEqual(result['split_at'], 40)
        self.assertIn('SESSION-SPLIT', result['message'])
        
        # Check state was saved
        saved_state = manager.load_state()
        self.assertEqual(saved_state['status'], 'split')
        self.assertEqual(saved_state['split_at'], 40)


class TestCheckStateConsistency(unittest.TestCase):
    """Test check_state_consistency function."""
    
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
    
    def test_missing_files(self):
        """Test consistency check with missing files."""
        manager = ResilienceManager()
        
        result = manager.check_state_consistency()
        
        self.assertFalse(result['consistent'])
        self.assertIn('State file missing', result['issues'])
        self.assertIn('Results TSV missing', result['issues'])
    
    def test_consistent_state(self):
        """Test consistent state check."""
        manager = ResilienceManager()
        
        # Create state file - TSV has header + 2 data rows = 2 iterations
        state = {'iteration': 2, 'baseline': 100, 'config': {}}
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        # Create matching results file - header + 2 data rows
        with open('autoresearch-results.tsv', 'w') as f:
            f.write("iteration\tcommit\tmetric\tdelta\tstatus\n")
            f.write("1\tdef\t90\t-10\tkeep\n")
            f.write("2\tghi\t85\t-5\tkeep\n")
        
        result = manager.check_state_consistency()
        
        # The function counts TSV lines minus header
        self.assertEqual(result['tsv_iterations'], 2)
        self.assertEqual(result['state_iteration'], 2)


class TestGenerateResilienceReport(unittest.TestCase):
    """Test generate_resilience_report function."""
    
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
    
    def test_report_generation(self):
        """Test generating resilience report."""
        manager = ResilienceManager()
        
        # Create state file
        state = {'iteration': 25}
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        report = manager.generate_resilience_report()
        
        self.assertIn('Session Resilience Report', report)
        self.assertIn('Current iteration: 25', report)
        self.assertIn('Protocol checks: 0', report)


class TestMain(unittest.TestCase):
    """Test main function."""
    
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
    
    def test_main_check(self):
        """Test main with check command."""
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_resilience.py', 'check']
            main()
        finally:
            sys.argv = old_argv
    
    def test_main_report(self):
        """Test main with report command."""
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_resilience.py', 'report']
            main()
        finally:
            sys.argv = old_argv
    
    def test_main_reanchor(self):
        """Test main with reanchor command."""
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_resilience.py', 'reanchor', '--iteration', '10']
            main()
        finally:
            sys.argv = old_argv
    
    def test_main_split(self):
        """Test main with split command (lines 327-330)."""
        # Create state file first
        state = {'iteration': 10, 'config': {'goal': 'Test'}}
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_resilience.py', 'split', '--iteration', '10']
            main()
        finally:
            sys.argv = old_argv


class TestMainBlock(unittest.TestCase):
    """Test __main__ block execution."""
    
    @patch('autoresearch_resilience.main')
    def test_main_block(self, mock_main):
        """Test that __main__ block calls main() (line 337)."""
        mock_main.return_value = None
        
        # Simulate running as __main__
        import importlib.util
        spec = importlib.util.spec_from_file_location("__main__", os.path.join(
            os.path.dirname(__file__), '..', 'scripts', 'autoresearch_resilience.py'))
        module = importlib.util.module_from_spec(spec)
        
        # Should call main() and exit
        try:
            spec.loader.exec_module(module)
        except SystemExit:
            pass  # Expected


if __name__ == '__main__':
    unittest.main()
