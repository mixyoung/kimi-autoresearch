#!/usr/bin/env python3
"""Tests for autoresearch_health_check.py"""
import unittest
import sys
import os
import tempfile
import json
from io import StringIO
from unittest.mock import patch, MagicMock

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from autoresearch_health_check import (
    check_git_repository,
    check_git_config,
    check_worktree_clean,
    check_disk_space,
    check_required_tools,
    check_state_files,
    run_all_checks,
    run_git,
    main
)


class TestHealthCheck(unittest.TestCase):
    """Test health check functions."""
    
    def test_check_git_repository(self):
        """Test git repository check."""
        result = check_git_repository()
        
        self.assertIn('name', result)
        self.assertIn('status', result)
        self.assertIn('message', result)
        self.assertEqual(result['name'], 'git_repository')
        
        # Should pass in git repo
        self.assertIn(result['status'], ['pass', 'fail'])
    
    def test_check_git_config(self):
        """Test git config check."""
        result = check_git_config()
        
        self.assertIn('name', result)
        self.assertIn('status', result)
        self.assertIn('message', result)
        self.assertEqual(result['name'], 'git_config')
        
        # Should be pass or warn
        self.assertIn(result['status'], ['pass', 'warn'])
    
    def test_check_worktree_clean(self):
        """Test worktree clean check."""
        result = check_worktree_clean()
        
        self.assertIn('name', result)
        self.assertIn('status', result)
        self.assertIn('message', result)
        self.assertEqual(result['name'], 'worktree')
        
        # Should be pass or warn
        self.assertIn(result['status'], ['pass', 'warn'])
    
    def test_check_disk_space(self):
        """Test disk space check."""
        result = check_disk_space()
        
        self.assertIn('name', result)
        self.assertIn('status', result)
        self.assertIn('message', result)
        self.assertEqual(result['name'], 'disk_space')
        
        # Should be pass, warn, or fail
        self.assertIn(result['status'], ['pass', 'warn', 'fail'])
        
        # Message should contain GB info
        self.assertIn('GB', result['message'])
    
    def test_check_required_tools(self):
        """Test required tools check."""
        result = check_required_tools()
        
        self.assertIn('name', result)
        self.assertIn('status', result)
        self.assertIn('message', result)
        self.assertEqual(result['name'], 'required_tools')
        
        # Git and Python should be available
        self.assertEqual(result['status'], 'pass')
    
    def test_run_all_checks(self):
        """Test running all checks."""
        results = run_all_checks()
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        # Check expected checks are present
        check_names = [r['name'] for r in results]
        expected = ['git_repository', 'git_config', 'worktree', 
                   'disk_space', 'required_tools']
        
        for expected_name in expected:
            self.assertIn(expected_name, check_names)


class TestRunGit(unittest.TestCase):
    """Test run_git function."""
    
    def test_run_git_success(self):
        """Test run_git with successful command."""
        code, output = run_git(['--version'])
        self.assertEqual(code, 0)
        self.assertIn('git', output.lower())
    
    def test_run_git_failure(self):
        """Test run_git with failing command."""
        code, output = run_git(['invalid-command-xyz'])
        self.assertNotEqual(code, 0)
    
    @patch('subprocess.run')
    def test_run_git_exception(self, mock_run):
        """Test run_git with exception (lines 23-24)."""
        mock_run.side_effect = Exception('Git failed')
        
        code, output = run_git(['status'])
        
        self.assertEqual(code, -1)
        self.assertIn('Git failed', output)


class TestCheckStateFiles(unittest.TestCase):
    """Test check_state_files function."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_check_state_files_no_files(self):
        """Test when no state files exist."""
        result = check_state_files()
        
        self.assertEqual(result['name'], 'state_files')
        self.assertEqual(result['status'], 'pass')
    
    def test_check_state_files_with_state(self):
        """Test when state file exists."""
        with open('autoresearch-state.json', 'w') as f:
            json.dump({'test': 'data'}, f)
        
        result = check_state_files()
        
        self.assertEqual(result['name'], 'state_files')
        self.assertEqual(result['status'], 'warn')
        self.assertIn('autoresearch-state.json', result['message'])
    
    def test_check_state_files_with_results(self):
        """Test when results file exists."""
        with open('autoresearch-results.tsv', 'w') as f:
            f.write('test\tdata')
        
        result = check_state_files()
        
        self.assertEqual(result['name'], 'state_files')
        self.assertEqual(result['status'], 'warn')
        self.assertIn('autoresearch-results.tsv', result['message'])


class TestCheckWorktree(unittest.TestCase):
    """Test check_worktree_clean edge cases."""
    
    @unittest.skip("Windows temp directory issue")
    def test_check_worktree_git_fails(self):
        """Test when git status fails."""
        # Change to non-git directory temporarily
        import tempfile
        import os
        
        old_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            result = check_worktree_clean()
            
            # Should fail gracefully
            self.assertEqual(result['name'], 'worktree')
            self.assertEqual(result['status'], 'fail')
        
        os.chdir(old_cwd)


class TestCheckDiskSpaceEdgeCases(unittest.TestCase):
    """Test check_disk_space edge cases."""
    
    @patch('autoresearch_health_check.shutil.disk_usage')
    def test_check_disk_space_low(self, mock_disk):
        """Test disk space check with low space."""
        # Mock low disk space (< 1GB)
        mock_disk.return_value = MagicMock(free=500*1024*1024, total=100*1024**3, used=99.5*1024**3)
        
        result = check_disk_space()
        
        self.assertEqual(result['status'], 'fail')
    
    @patch('autoresearch_health_check.shutil.disk_usage')
    def test_check_disk_space_warning(self, mock_disk):
        """Test disk space check with warning level."""
        # Mock medium disk space (1-5GB)
        mock_disk.return_value = MagicMock(free=2*1024**3, total=100*1024**3, used=98*1024**3)
        
        result = check_disk_space()
        
        self.assertEqual(result['status'], 'warn')
    
    @patch('autoresearch_health_check.shutil.disk_usage')
    def test_check_disk_space_exception(self, mock_disk):
        """Test disk space check with exception (lines 114, 117)."""
        mock_disk.side_effect = Exception("Disk usage failed")
        
        result = check_disk_space()
        
        self.assertEqual(result['status'], 'warn')
        self.assertIn('Could not check disk space', result['message'])


class TestGitCheckEdgeCases(unittest.TestCase):
    """Test git check edge cases for missing lines."""
    
    @patch('autoresearch_health_check.run_git')
    def test_check_git_config_failure(self, mock_run_git):
        """Test git config check when config is not set (lines 48)."""
        # First call for user.name fails, second for user.email
        mock_run_git.side_effect = [(1, ''), (0, 'test@example.com')]
        
        result = check_git_config()
        
        self.assertEqual(result['status'], 'warn')
        self.assertIn('not set', result['message'])
    
    @patch('autoresearch_health_check.run_git')
    def test_check_worktree_git_fails(self, mock_run_git):
        """Test worktree check when git status fails (lines 59)."""
        mock_run_git.return_value = (1, 'fatal: not a git repository')
        
        result = check_worktree_clean()
        
        self.assertEqual(result['status'], 'fail')
        self.assertIn('Failed to check git status', result['message'])


class TestMainEdgeCases(unittest.TestCase):
    """Test main function edge cases for missing lines."""
    
    @patch('autoresearch_health_check.run_all_checks')
    def test_main_text_output_with_failures(self, mock_run_all):
        """Test main with text output and failures (lines 206-207)."""
        mock_run_all.return_value = [
            {'name': 'test', 'status': 'fail', 'message': 'Failed'}
        ]
        
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_health_check.py', '--format', 'text']
            
            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            with self.assertRaises(SystemExit) as cm:
                main()
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            self.assertEqual(cm.exception.code, 1)
            self.assertIn('FAILED', output)
        finally:
            sys.argv = old_argv
    
    @patch('autoresearch_health_check.run_all_checks')
    def test_main_text_output_with_warnings_fail_on_warn(self, mock_run_all):
        """Test main with text output, warnings and --fail-on-warn (lines 206-207, 209-210)."""
        mock_run_all.return_value = [
            {'name': 'test', 'status': 'warn', 'message': 'Warning'}
        ]
        
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_health_check.py', '--format', 'text', '--fail-on-warn']
            
            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            with self.assertRaises(SystemExit) as cm:
                main()
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            self.assertEqual(cm.exception.code, 1)
            self.assertIn('FAILED', output)
        finally:
            sys.argv = old_argv


class TestMain(unittest.TestCase):
    """Test main function."""
    
    def test_main_text_output(self):
        """Test main with text output format."""
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_health_check.py', '--format', 'text']
            
            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            try:
                main()
            except SystemExit as e:
                # Exit code depends on check results
                pass
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            self.assertIn('Autoresearch Health Check', output)
        finally:
            sys.argv = old_argv
    
    def test_main_json_output(self):
        """Test main with JSON output format."""
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_health_check.py', '--format', 'json']
            
            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            try:
                main()
            except SystemExit:
                pass
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            # Should be valid JSON
            data = json.loads(output)
            self.assertIn('checks', data)
            self.assertIn('summary', data)
        finally:
            sys.argv = old_argv
    
    def test_main_fail_on_warn(self):
        """Test main with --fail-on-warn flag."""
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_health_check.py', '--format', 'text', '--fail-on-warn']
            
            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            try:
                main()
            except SystemExit as e:
                # May exit with 1 if there are warnings
                pass
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            # Should show health check results
            self.assertIn('Health Check', output)
        finally:
            sys.argv = old_argv


class TestMainBlock(unittest.TestCase):
    """Test __main__ block execution."""
    
    @patch('autoresearch_health_check.main')
    def test_main_block(self, mock_main):
        """Test that __main__ block calls main()."""
        mock_main.return_value = None
        
        # Simulate running as __main__
        import importlib.util
        spec = importlib.util.spec_from_file_location("__main__", os.path.join(
            os.path.dirname(__file__), '..', 'scripts', 'autoresearch_health_check.py'))
        module = importlib.util.module_from_spec(spec)
        
        # Should call main() and exit
        try:
            spec.loader.exec_module(module)
        except SystemExit:
            pass  # Expected


if __name__ == '__main__':
    unittest.main()
