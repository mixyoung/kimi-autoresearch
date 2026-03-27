#!/usr/bin/env python3
"""Tests for autoresearch_launch_gate.py"""
import unittest
import sys
import os
import tempfile
import json
import io
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from autoresearch_launch_gate import (
    check_existing_state, check_results_consistency, decide_launch_action,
    main, STATE_FILE, RESULTS_FILE
)


class TestCheckExistingState(unittest.TestCase):
    """Test check_existing_state function."""
    
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
    
    def test_no_state_file(self):
        """Test when no state file exists."""
        result = check_existing_state()
        
        self.assertEqual(result['can_resume'], False)
        self.assertIn('No state file found', result['reason'])
    
    def test_completed_state(self):
        """Test with completed state."""
        state = {'status': 'completed', 'iteration': 10}
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        result = check_existing_state()
        
        self.assertEqual(result['can_resume'], False)
        self.assertIn('completed', result['reason'])
    
    def test_interrupted_state(self):
        """Test with interrupted state."""
        state = {'status': 'interrupted', 'iteration': 5}
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        result = check_existing_state()
        
        self.assertEqual(result['can_resume'], True)
        self.assertEqual(result['mode'], 'full_resume')
        self.assertIn('interrupted', result['reason'])
        self.assertIn('state', result)
    
    def test_running_state(self):
        """Test with running state."""
        state = {'status': 'running', 'iteration': 3}
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        result = check_existing_state()
        
        self.assertEqual(result['can_resume'], True)
        self.assertEqual(result['mode'], 'mini_wizard')
        self.assertIn('active', result['reason'])
    
    def test_unknown_state(self):
        """Test with unknown status."""
        state = {'status': 'unknown_status', 'iteration': 1}
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        result = check_existing_state()
        
        self.assertEqual(result['can_resume'], True)
        self.assertEqual(result['mode'], 'fallback')
    
    def test_corrupted_state_file(self):
        """Test with corrupted state file."""
        with open(STATE_FILE, 'w') as f:
            f.write('not valid json')
        
        result = check_existing_state()
        
        self.assertEqual(result['can_resume'], False)
        self.assertIn('corrupted', result['reason'])


class TestCheckResultsConsistency(unittest.TestCase):
    """Test check_results_consistency function."""
    
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
    
    def test_no_results_file(self):
        """Test when no results file exists."""
        result = check_results_consistency()
        
        self.assertEqual(result['consistent'], True)
        self.assertEqual(result['results_count'], 0)
    
    def test_consistent_results(self):
        """Test with consistent results."""
        state = {'status': 'running', 'iteration': 2}
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        # iteration 2 means expected 3 results (baseline + 2 iterations)
        with open(RESULTS_FILE, 'w') as f:
            f.write("iteration\tcommit\tmetric\tdelta\tstatus\n")
            f.write("0\tabc\t100\t0\tbaseline\n")
            f.write("1\tdef\t90\t-10\tkeep\n")
            f.write("2\tghi\t85\t-5\tkeep\n")
        
        result = check_results_consistency()
        
        self.assertEqual(result['consistent'], True)
        self.assertEqual(result['results_count'], 3)
        self.assertEqual(result['state_iteration'], 2)
    
    def test_inconsistent_results(self):
        """Test with inconsistent results."""
        state = {'status': 'running', 'iteration': 5}
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        # Only 2 results but iteration is 5
        with open(RESULTS_FILE, 'w') as f:
            f.write("iteration\tcommit\tmetric\tdelta\tstatus\n")
            f.write("0\tabc\t100\t0\tbaseline\n")
            f.write("1\tdef\t90\t-10\tkeep\n")
        
        result = check_results_consistency()
        
        self.assertEqual(result['consistent'], False)
        self.assertIn('Mismatch', result.get('note', ''))


class TestDecideLaunchAction(unittest.TestCase):
    """Test decide_launch_action function."""
    
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
    
    def test_force_fresh(self):
        """Test force fresh start."""
        args = MagicMock()
        args.force_fresh = True
        args.force_resume = False
        
        result = decide_launch_action(args)
        
        self.assertEqual(result['action'], 'fresh')
        self.assertIn('Force fresh', result['reason'])
    
    def test_force_resume_no_state(self):
        """Test force resume with no state."""
        args = MagicMock()
        args.force_fresh = False
        args.force_resume = True
        
        result = decide_launch_action(args)
        
        self.assertEqual(result['action'], 'block')
        self.assertIn('Cannot resume', result['reason'])
    
    def test_force_resume_with_state(self):
        """Test force resume with existing state."""
        state = {'status': 'interrupted', 'iteration': 3}
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        args = MagicMock()
        args.force_fresh = False
        args.force_resume = True
        
        result = decide_launch_action(args)
        
        self.assertEqual(result['action'], 'resume')
        self.assertEqual(result['mode'], 'full_resume')
    
    def test_fresh_start_no_state(self):
        """Test fresh start when no state exists."""
        args = MagicMock()
        args.force_fresh = False
        args.force_resume = False
        
        result = decide_launch_action(args)
        
        self.assertEqual(result['action'], 'fresh')
        self.assertIn('No state file', result['reason'])
    
    def test_resume_with_consistent_state(self):
        """Test resume with consistent state and results."""
        state = {'status': 'interrupted', 'iteration': 1}
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        with open(RESULTS_FILE, 'w') as f:
            f.write("iteration\tcommit\tmetric\tdelta\tstatus\n")
            f.write("0\tabc\t100\t0\tbaseline\n")
            f.write("1\tdef\t90\t-10\tkeep\n")
        
        args = MagicMock()
        args.force_fresh = False
        args.force_resume = False
        
        result = decide_launch_action(args)
        
        self.assertEqual(result['action'], 'resume')
        self.assertIn('state', result)


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
    
    def test_main_check_only_json(self):
        """Test main with check-only and JSON format."""
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_launch_gate.py', '--check-only', '--format', 'json']
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            try:
                main()
            except SystemExit as e:
                pass
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            # Verify JSON output
            data = json.loads(output)
            self.assertIn('state', data)
            self.assertIn('consistency', data)
        finally:
            sys.argv = old_argv
    
    def test_main_check_only_text(self):
        """Test main with check-only and text format."""
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_launch_gate.py', '--check-only', '--format', 'text']
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            try:
                main()
            except SystemExit as e:
                pass
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            self.assertIn('Launch Gate Check', output)
        finally:
            sys.argv = old_argv
    
    def test_main_decide_action_json(self):
        """Test main deciding action with JSON format."""
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_launch_gate.py', '--format', 'json']
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            try:
                main()
            except SystemExit as e:
                self.assertEqual(e.code, 0)  # fresh start returns 0
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            data = json.loads(output)
            self.assertIn('action', data)
            self.assertEqual(data['action'], 'fresh')
        finally:
            sys.argv = old_argv


if __name__ == '__main__':
    unittest.main()
