#!/usr/bin/env python3
"""Tests for autoresearch_commit_gate.py"""
import unittest
import sys
import os
import tempfile
import json
import io
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from autoresearch_commit_gate import (
    run_git, is_git_repo, get_git_status, check_scope_safety,
    commit_gate_check, main
)


class TestRunGit(unittest.TestCase):
    """Test run_git function."""
    
    @patch('subprocess.run')
    def test_run_git_success(self, mock_run):
        """Test running git command successfully."""
        mock_run.return_value = MagicMock(returncode=0, stdout='output', stderr='')
        
        code, output = run_git(['status'])
        
        self.assertEqual(code, 0)
        self.assertEqual(output, 'output')
    
    @patch('subprocess.run')
    def test_run_git_failure(self, mock_run):
        """Test running git command that fails."""
        mock_run.return_value = MagicMock(returncode=1, stdout='', stderr='error')
        
        code, output = run_git(['status'])
        
        self.assertEqual(code, 1)
        self.assertEqual(output, 'error')
    
    @patch('subprocess.run', side_effect=Exception('Timeout'))
    def test_run_git_exception(self, mock_run):
        """Test running git command that raises exception."""
        code, output = run_git(['status'])
        
        self.assertEqual(code, -1)
        self.assertIn('Timeout', output)


class TestIsGitRepo(unittest.TestCase):
    """Test is_git_repo function."""
    
    @patch('autoresearch_commit_gate.run_git')
    def test_is_git_repo_true(self, mock_run_git):
        """Test detecting a git repo."""
        mock_run_git.return_value = (0, '.git')
        
        result = is_git_repo()
        
        self.assertTrue(result)
    
    @patch('autoresearch_commit_gate.run_git')
    def test_is_git_repo_false(self, mock_run_git):
        """Test detecting non-git directory."""
        mock_run_git.return_value = (1, 'Not a git repo')
        
        result = is_git_repo()
        
        self.assertFalse(result)


class TestGetGitStatus(unittest.TestCase):
    """Test get_git_status function."""
    
    @patch('autoresearch_commit_gate.is_git_repo')
    def test_not_a_repo(self, mock_is_repo):
        """Test status for non-repo."""
        mock_is_repo.return_value = False
        
        status = get_git_status()
        
        self.assertFalse(status['is_repo'])
        self.assertIn('Not a git repository', status['errors'])
    
    @patch('autoresearch_commit_gate.run_git')
    @patch('autoresearch_commit_gate.is_git_repo')
    def test_detached_head(self, mock_is_repo, mock_run_git):
        """Test status with detached HEAD."""
        mock_is_repo.return_value = True
        mock_run_git.side_effect = [
            (1, ''),  # symbolic-ref fails (detached)
            (0, ''),  # status --porcelain
        ]
        
        status = get_git_status()
        
        self.assertTrue(status['is_repo'])
        self.assertTrue(status['is_detached'])
        self.assertFalse(status['can_commit'])
    
    @patch('autoresearch_commit_gate.run_git')
    @patch('autoresearch_commit_gate.is_git_repo')
    def test_normal_repo(self, mock_is_repo, mock_run_git):
        """Test status for normal repo."""
        mock_is_repo.return_value = True
        mock_run_git.side_effect = [
            (0, 'main'),  # symbolic-ref returns branch
            (0, ' M file.txt'),  # status --porcelain
        ]
        
        status = get_git_status()
        
        self.assertTrue(status['is_repo'])
        self.assertEqual(status['branch'], 'main')
        self.assertFalse(status['is_detached'])
        self.assertTrue(status['has_changes'])


class TestCheckScopeSafety(unittest.TestCase):
    """Test check_scope_safety function."""
    
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
    
    def test_scope_no_files(self):
        """Test scope with no matching files."""
        result = check_scope_safety('*.nonexistent')
        
        self.assertFalse(result['exists'])
        self.assertIn('No files match scope', result['errors'][0])
    
    def test_scope_with_files(self):
        """Test scope with matching files."""
        # Create test files
        with open('test1.py', 'w') as f:
            f.write('test')
        with open('test2.py', 'w') as f:
            f.write('test')
        
        result = check_scope_safety('*.py')
        
        self.assertTrue(result['exists'])
        self.assertEqual(len(result['files']), 2)
        self.assertTrue(result['is_safe'])
    
    def test_scope_with_protected_files(self):
        """Test scope with protected files."""
        # Create a test file with protected pattern
        os.makedirs('test_dir', exist_ok=True)
        with open('test_dir/test.py', 'w') as f:
            f.write('test')
        
        # Test with pattern that includes the file
        result = check_scope_safety('test_dir/*.py')
        
        self.assertTrue(result['exists'])
        # The function only warns for actual protected patterns in the files list
        # Since we're not checking .git/config, no warnings should be generated


class TestCommitGateCheck(unittest.TestCase):
    """Test commit_gate_check function."""
    
    @patch('autoresearch_commit_gate.get_git_status')
    def test_not_a_repo(self, mock_get_status):
        """Test when not in a git repo."""
        mock_get_status.return_value = {
            'is_repo': False,
            'errors': ['Not a git repository']
        }
        
        result = commit_gate_check()
        
        self.assertFalse(result['passed'])
        self.assertTrue(any('not a git repository' in e.lower() for e in result['errors']))
    
    @patch('autoresearch_commit_gate.get_git_status')
    def test_cannot_commit(self, mock_get_status):
        """Test when repo can't commit."""
        mock_get_status.return_value = {
            'is_repo': True,
            'can_commit': False,
            'errors': ['Detached HEAD']
        }
        
        result = commit_gate_check()
        
        self.assertFalse(result['passed'])
        self.assertIn('Detached HEAD', result['errors'])
    
    @patch('autoresearch_commit_gate.get_git_status')
    def test_can_commit(self, mock_get_status):
        """Test when repo can commit."""
        mock_get_status.return_value = {
            'is_repo': True,
            'can_commit': True,
            'branch': 'main',
            'errors': []
        }
        
        result = commit_gate_check()
        
        self.assertTrue(result['passed'])
    
    @patch('autoresearch_commit_gate.get_git_status')
    def test_strict_mode(self, mock_get_status):
        """Test strict mode with warnings."""
        mock_get_status.return_value = {
            'is_repo': True,
            'can_commit': True,
            'branch': 'main',
            'errors': []
        }
        
        # Mock scope check to return warnings
        with patch('autoresearch_commit_gate.check_scope_safety') as mock_scope:
            mock_scope.return_value = {
                'is_safe': True,
                'warnings': ['Some warning']
            }
            
            result = commit_gate_check(scope='*.py', strict=True)
            
            self.assertFalse(result['passed'])
            self.assertTrue(any('WARNING (strict mode)' in e for e in result['errors']))


class TestMain(unittest.TestCase):
    """Test main function."""
    
    @patch('autoresearch_commit_gate.commit_gate_check')
    def test_main_passed(self, mock_check):
        """Test main when check passes."""
        mock_check.return_value = {
            'passed': True,
            'primary_repo': {'branch': 'main', 'can_commit': True},
            'scope_check': {},
            'companion_repos': {},
            'errors': [],
            'warnings': []
        }
        
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_commit_gate.py']
            result = main()
            self.assertEqual(result, 0)
        finally:
            sys.argv = old_argv
    
    @patch('autoresearch_commit_gate.commit_gate_check')
    def test_main_failed(self, mock_check):
        """Test main when check fails."""
        mock_check.return_value = {
            'passed': False,
            'primary_repo': {'branch': None},
            'scope_check': {},
            'companion_repos': {},
            'errors': ['Not a repo'],
            'warnings': []
        }
        
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_commit_gate.py']
            result = main()
            self.assertEqual(result, 1)
        finally:
            sys.argv = old_argv
    
    @patch('autoresearch_commit_gate.commit_gate_check')
    def test_main_json_output(self, mock_check):
        """Test main with JSON output."""
        mock_check.return_value = {
            'passed': True,
            'primary_repo': {},
            'errors': [],
            'warnings': []
        }
        
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_commit_gate.py', '--json']
            result = main()
            self.assertEqual(result, 0)
        finally:
            sys.argv = old_argv


if __name__ == '__main__':
    unittest.main()
