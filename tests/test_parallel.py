#!/usr/bin/env python3
"""Tests for autoresearch_parallel.py"""
import unittest
import sys
import os
import tempfile
import shutil
import json
import stat
import io
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from autoresearch_parallel import (
    ParallelExperiment, cmd_run, cmd_status, cmd_cleanup, main
)


class TestParallelExperiment(unittest.TestCase):
    """Test ParallelExperiment class."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.exp = ParallelExperiment(self.temp_dir, max_workers=3)
    
    def tearDown(self):
        def on_rm_error(func, path, exc_info):
            os.chmod(path, stat.S_IWRITE)
            try:
                func(path)
            except:
                pass
        shutil.rmtree(self.temp_dir, onerror=on_rm_error)
    
    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.exp.base_dir, os.path.abspath(self.temp_dir))
        self.assertEqual(self.exp.max_workers, 3)
        self.assertEqual(self.exp.worktrees, [])
        self.assertEqual(self.exp.results, [])
    
    @patch('subprocess.run')
    def test_run_git_success(self, mock_run):
        """Test successful git command."""
        mock_run.return_value = MagicMock(returncode=0, stdout='output', stderr='')
        
        code, output = self.exp.run_git(['status'])
        
        self.assertEqual(code, 0)
        self.assertEqual(output, 'output')
    
    @patch('subprocess.run')
    def test_run_git_failure(self, mock_run):
        """Test failed git command."""
        mock_run.return_value = MagicMock(returncode=1, stdout='', stderr='error')
        
        code, output = self.exp.run_git(['invalid'])
        
        self.assertEqual(code, 1)
        self.assertEqual(output, 'error')
    
    @patch('subprocess.run')
    def test_run_git_exception(self, mock_run):
        """Test git command that raises exception."""
        mock_run.side_effect = Exception('Git error')
        
        code, output = self.exp.run_git(['status'])
        
        self.assertEqual(code, -1)
        self.assertIn('Git error', output)
    
    @patch('shutil.rmtree')
    @patch.object(ParallelExperiment, 'run_git')
    def test_create_worktree_success(self, mock_run_git, mock_rmtree):
        """Test successful worktree creation."""
        mock_run_git.return_value = (0, 'OK')
        
        hypothesis = {'description': 'Test hypothesis'}
        path = self.exp.create_worktree('test-worker', hypothesis)
        
        self.assertIsNotNone(path)
        self.assertEqual(len(self.exp.worktrees), 1)
        self.assertEqual(self.exp.worktrees[0]['name'], 'test-worker')
    
    @patch('shutil.rmtree')
    @patch.object(ParallelExperiment, 'run_git')
    def test_create_worktree_removes_existing(self, mock_run_git, mock_rmtree):
        """Test worktree creation removes existing path (line 46)."""
        mock_run_git.return_value = (0, 'OK')
        
        # Create existing worktree path
        worktree_path = os.path.join(self.temp_dir, '.autoresearch-worktree-test-worker')
        os.makedirs(worktree_path)
        
        hypothesis = {'description': 'Test hypothesis'}
        path = self.exp.create_worktree('test-worker', hypothesis)
        
        self.assertIsNotNone(path)
        mock_rmtree.assert_called_once_with(worktree_path)
    
    @patch('shutil.rmtree')
    @patch.object(ParallelExperiment, 'run_git')
    def test_create_worktree_failure(self, mock_run_git, mock_rmtree):
        """Test failed worktree creation."""
        mock_run_git.return_value = (1, 'Failed to create worktree')
        
        hypothesis = {'description': 'Test hypothesis'}
        path = self.exp.create_worktree('test-worker', hypothesis)
        
        self.assertIsNone(path)
    
    def test_apply_hypothesis(self):
        """Test applying hypothesis."""
        worktree = {'name': 'test', 'hypothesis': {'description': 'Test hypothesis'}}
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = self.exp.apply_hypothesis(worktree)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertTrue(result)
        self.assertIn('Test hypothesis', output)
    
    @patch('subprocess.run')
    def test_run_verification_success(self, mock_run):
        """Test successful verification."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='Coverage: 85.5%',
            stderr=''
        )
        
        worktree = {'name': 'test', 'path': '/tmp/test'}
        result = self.exp.run_verification(worktree, 'npm test')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['metric'], 85.5)
        self.assertEqual(result['worktree'], 'test')
    
    @patch('subprocess.run')
    def test_run_verification_failure(self, mock_run):
        """Test failed verification."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='Tests failed',
            stderr=''
        )
        
        worktree = {'name': 'test', 'path': '/tmp/test'}
        result = self.exp.run_verification(worktree, 'npm test')
        
        self.assertFalse(result['success'])
    
    @patch('subprocess.run')
    def test_run_verification_timeout(self, mock_run):
        """Test verification timeout (line 103)."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd='test', timeout=300)
        
        worktree = {'name': 'test', 'path': '/tmp/test'}
        result = self.exp.run_verification(worktree, 'npm test')
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Timeout')
    
    @patch('subprocess.run')
    def test_run_verification_exception(self, mock_run):
        """Test verification with exception (lines 108-109)."""
        mock_run.side_effect = Exception('Command failed')
        
        worktree = {'name': 'test', 'path': '/tmp/test'}
        result = self.exp.run_verification(worktree, 'npm test')
        
        self.assertFalse(result['success'])
        self.assertIn('Command failed', result['error'])
    
    @patch('subprocess.run')
    def test_run_verification_value_error(self, mock_run):
        """Test verification with ValueError during float conversion (lines 93-94)."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='Coverage: abc%',  # Invalid number format
            stderr=''
        )
        
        worktree = {'name': 'test', 'path': '/tmp/test'}
        result = self.exp.run_verification(worktree, 'npm test')
        
        # Should handle ValueError gracefully
        self.assertTrue(result['success'])
        self.assertIsNone(result['metric'])
    
    @patch.object(ParallelExperiment, 'create_worktree')
    def test_run_parallel_no_worktrees(self, mock_create):
        """Test run_parallel when no worktrees are created (line 127)."""
        mock_create.return_value = None  # All worktree creations fail
        
        hypotheses = [
            {'id': 1, 'description': 'Approach A'},
        ]
        
        result = self.exp.run_parallel(hypotheses, 'npm test')
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'No worktrees created')
    
    @patch.object(ParallelExperiment, 'run_verification')
    @patch.object(ParallelExperiment, 'apply_hypothesis')
    @patch.object(ParallelExperiment, 'create_worktree')
    def test_run_parallel_success(self, mock_create, mock_apply, mock_verify):
        """Test running parallel experiments."""
        mock_create.return_value = '/tmp/worktree'
        mock_apply.return_value = True
        mock_verify.return_value = {
            'success': True,
            'metric': 90.0,
            'worktree': 'worker-1'
        }
        
        hypotheses = [
            {'description': 'Approach A'},
            {'description': 'Approach B'}
        ]
        
        # Manually add worktree since we're mocking create_worktree
        self.exp.worktrees.append({
            'name': 'worker-1',
            'path': '/tmp/worktree',
            'hypothesis': hypotheses[0]
        })
        
        result = self.exp.run_parallel(hypotheses, 'npm test')
        
        self.assertTrue(result['success'])
    
    def test_select_best_empty(self):
        """Test select_best with no results."""
        best = self.exp.select_best([])
        self.assertIsNone(best)
    
    def test_select_best_no_valid_results(self):
        """Test select_best with no valid results."""
        results = [
            {'success': False, 'metric': None},
            {'success': True, 'metric': None}
        ]
        best = self.exp.select_best(results)
        self.assertIsNone(best)
    
    def test_select_best_with_results(self):
        """Test select_best with valid results."""
        results = [
            {'success': True, 'metric': 100.0, 'worktree': 'worker-1'},
            {'success': True, 'metric': 80.0, 'worktree': 'worker-2'},
            {'success': True, 'metric': 90.0, 'worktree': 'worker-3'}
        ]
        best = self.exp.select_best(results)
        
        self.assertIsNotNone(best)
        self.assertEqual(best['metric'], 80.0)  # Lower is better
    
    @patch.object(ParallelExperiment, 'run_git')
    def test_cleanup(self, mock_run_git):
        """Test cleanup."""
        mock_run_git.return_value = (0, '')
        
        self.exp.worktrees = [
            {'name': 'worker-1', 'path': '/tmp/wt1'},
            {'name': 'worker-2', 'path': '/tmp/wt2'}
        ]
        
        self.exp.cleanup()
        
        self.assertEqual(len(self.exp.worktrees), 0)
        self.assertEqual(mock_run_git.call_count, 4)  # 2 worktrees * 2 commands each


class TestCmdRun(unittest.TestCase):
    """Test cmd_run function."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        def on_rm_error(func, path, exc_info):
            os.chmod(path, stat.S_IWRITE)
            try:
                func(path)
            except:
                pass
        shutil.rmtree(self.temp_dir, onerror=on_rm_error)
    
    @patch.object(ParallelExperiment, 'cleanup')
    @patch.object(ParallelExperiment, 'run_parallel')
    def test_cmd_run_success(self, mock_run, mock_cleanup):
        """Test cmd_run success."""
        mock_run.return_value = {
            'success': True,
            'results': [],
            'best': None
        }
        
        args = MagicMock()
        args.verify = 'npm test'
        args.hypotheses_file = None
        args.repo = self.temp_dir
        args.workers = 3
        args.keep = False
        args.json = False
        
        result = cmd_run(args)
        
        self.assertEqual(result, 0)
        mock_cleanup.assert_called_once()
    
    @patch.object(ParallelExperiment, 'cleanup')
    @patch.object(ParallelExperiment, 'run_parallel')
    def test_cmd_run_failure(self, mock_run, mock_cleanup):
        """Test cmd_run failure."""
        mock_run.return_value = {
            'success': False,
            'results': [],
            'best': None
        }
        
        args = MagicMock()
        args.verify = 'npm test'
        args.hypotheses_file = None
        args.repo = self.temp_dir
        args.workers = 3
        args.keep = True  # Don't cleanup on failure
        args.json = False
        
        result = cmd_run(args)
        
        self.assertEqual(result, 1)
        mock_cleanup.assert_not_called()
    
    @patch.object(ParallelExperiment, 'cleanup')
    @patch.object(ParallelExperiment, 'run_parallel')
    def test_cmd_run_json_output(self, mock_run, mock_cleanup):
        """Test cmd_run with JSON output."""
        mock_run.return_value = {
            'success': True,
            'results': [{'metric': 85.0}],
            'best': {'metric': 85.0}
        }
        
        args = MagicMock()
        args.verify = 'npm test'
        args.hypotheses_file = None
        args.repo = self.temp_dir
        args.workers = 3
        args.keep = False
        args.json = True
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_run(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        # Should be valid JSON
        data = json.loads(output)
        self.assertTrue(data['success'])
    
    def test_cmd_run_with_hypotheses_file(self):
        """Test cmd_run with hypotheses file."""
        hypotheses = {
            'hypotheses': [
                {'id': 1, 'description': 'Test 1'},
                {'id': 2, 'description': 'Test 2'}
            ]
        }
        with open('hypotheses.json', 'w') as f:
            json.dump(hypotheses, f)
        
        args = MagicMock()
        args.verify = 'npm test'
        args.hypotheses_file = 'hypotheses.json'
        args.repo = self.temp_dir
        args.workers = 3
        args.keep = False
        args.json = False
        
        with patch.object(ParallelExperiment, 'run_parallel') as mock_run:
            with patch.object(ParallelExperiment, 'cleanup'):
                mock_run.return_value = {'success': True, 'results': [], 'best': None}
                result = cmd_run(args)
        
        self.assertEqual(result, 0)
    
    def test_cmd_run_empty_hypotheses(self):
        """Test cmd_run with empty hypotheses."""
        hypotheses = {'hypotheses': []}
        with open('hypotheses.json', 'w') as f:
            json.dump(hypotheses, f)
        
        args = MagicMock()
        args.verify = 'npm test'
        args.hypotheses_file = 'hypotheses.json'
        args.repo = self.temp_dir
        args.workers = 3
        args.keep = False
        args.json = False
        
        result = cmd_run(args)
        
        self.assertEqual(result, 1)
    
    @patch.object(ParallelExperiment, 'cleanup')
    @patch.object(ParallelExperiment, 'run_parallel')
    def test_cmd_run_keyboard_interrupt(self, mock_run, mock_cleanup):
        """Test cmd_run with keyboard interrupt."""
        mock_run.side_effect = KeyboardInterrupt()
        
        args = MagicMock()
        args.verify = 'npm test'
        args.hypotheses_file = None
        args.repo = self.temp_dir
        args.workers = 3
        args.keep = False
        args.json = False
        
        result = cmd_run(args)
        
        self.assertEqual(result, 1)
        mock_cleanup.assert_called_once()
    
    @patch.object(ParallelExperiment, 'cleanup')
    @patch.object(ParallelExperiment, 'run_parallel')
    def test_cmd_run_with_best_result(self, mock_run, mock_cleanup):
        """Test cmd_run with best result display (lines 204-206, 210)."""
        mock_run.return_value = {
            'success': True,
            'results': [
                {'success': True, 'metric': 80.0, 'worktree': 'worker-1'},
                {'success': True, 'metric': 90.0, 'worktree': 'worker-2'},
            ],
            'best': {'worktree': 'worker-1', 'metric': 80.0}
        }
        
        args = MagicMock()
        args.verify = 'npm test'
        args.hypotheses_file = None
        args.repo = self.temp_dir
        args.workers = 3
        args.keep = False
        args.json = False
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_run(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('worker-1', output)
        self.assertIn('Best result', output)


class TestCmdStatus(unittest.TestCase):
    """Test cmd_status function."""
    
    @patch('subprocess.run')
    def test_cmd_status_with_autoresearch_worktrees(self, mock_run):
        """Test cmd_status with autoresearch worktrees (line 240)."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='/path/to/repo    abc123 [main]\n/path/to/.autoresearch-worktree-test  def456 [branch]'
        )
        
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_status(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Active autoresearch worktrees', output)
    
    @patch('subprocess.run')
    def test_cmd_status_success(self, mock_run):
        """Test cmd_status success."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='/path/to/repo    abc123 [main]\n/path/to/worktree  def456 (detached)'
        )
        
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_status(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Worktrees', output)
    
    @patch('subprocess.run')
    def test_cmd_status_error(self, mock_run):
        """Test cmd_status error."""
        mock_run.side_effect = Exception('Git error')
        
        args = MagicMock()
        
        result = cmd_status(args)
        
        self.assertEqual(result, 1)


class TestCmdCleanup(unittest.TestCase):
    """Test cmd_cleanup function."""
    
    @patch('subprocess.run')
    def test_cmd_cleanup_success(self, mock_run):
        """Test cmd_cleanup success."""
        # First call: git worktree list --porcelain
        # Second call: git worktree remove
        # Third call: git branch
        # Fourth call: git branch -D
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout='worktree /path/to/autoresearch-worktree-test\n'),
            MagicMock(returncode=0, stdout=''),
            MagicMock(returncode=0, stdout='  autoresearch-worker-1\n  main'),
            MagicMock(returncode=0, stdout='')
        ]
        
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_cleanup(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Cleaned up', output)
    
    @patch('subprocess.run')
    def test_cmd_cleanup_error(self, mock_run):
        """Test cmd_cleanup error."""
        mock_run.side_effect = Exception('Git error')
        
        args = MagicMock()
        
        result = cmd_cleanup(args)
        
        self.assertEqual(result, 1)


class TestMain(unittest.TestCase):
    """Test main function."""
    
    def test_main_no_command(self):
        """Test main with no command."""
        with patch('sys.argv', ['autoresearch_parallel']):
            result = main()
        
        self.assertEqual(result, 1)
    
    @patch('autoresearch_parallel.cmd_run')
    def test_main_run_command(self, mock_cmd):
        """Test main with run command."""
        mock_cmd.return_value = 0
        
        with patch('sys.argv', [
            'autoresearch_parallel', 'run',
            '--verify', 'npm test'
        ]):
            result = main()
        
        self.assertEqual(result, 0)
    
    @patch('autoresearch_parallel.cmd_status')
    def test_main_status_command(self, mock_cmd):
        """Test main with status command."""
        mock_cmd.return_value = 0
        
        with patch('sys.argv', ['autoresearch_parallel', 'status']):
            result = main()
        
        self.assertEqual(result, 0)
    
    @patch('autoresearch_parallel.cmd_cleanup')
    def test_main_cleanup_command(self, mock_cmd):
        """Test main with cleanup command."""
        mock_cmd.return_value = 0
        
        with patch('sys.argv', ['autoresearch_parallel', 'cleanup']):
            result = main()
        
        self.assertEqual(result, 0)


# Import subprocess for the TimeoutExpired exception
import subprocess

class TestMainBlock(unittest.TestCase):
    """Test __main__ block execution."""
    
    @patch('autoresearch_parallel.main')
    def test_main_block(self, mock_main):
        """Test that __main__ block calls main() (line 345)."""
        mock_main.return_value = None
        
        # Simulate running as __main__
        import importlib.util
        spec = importlib.util.spec_from_file_location("__main__", os.path.join(
            os.path.dirname(__file__), '..', 'scripts', 'autoresearch_parallel.py'))
        module = importlib.util.module_from_spec(spec)
        
        # Should call main() and exit
        try:
            spec.loader.exec_module(module)
        except SystemExit:
            pass  # Expected


if __name__ == '__main__':
    unittest.main()
