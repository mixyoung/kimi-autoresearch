#!/usr/bin/env python3
"""Tests for autoresearch_exec.py"""
import unittest
import sys
import os
import tempfile
import shutil
import json
import io
import stat
import time
from unittest.mock import patch, MagicMock, mock_open

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from autoresearch_exec import (
    Colors, log, run_command, extract_number, init_run, get_baseline,
    run_iteration, exec_loop, exec_check, main
)


class TestColors(unittest.TestCase):
    """Test Colors class."""
    
    def test_colors_defined(self):
        """Test all color codes are defined."""
        self.assertEqual(Colors.GREEN, '\033[92m')
        self.assertEqual(Colors.YELLOW, '\033[93m')
        self.assertEqual(Colors.RED, '\033[91m')
        self.assertEqual(Colors.BLUE, '\033[94m')
        self.assertEqual(Colors.END, '\033[0m')


class TestLog(unittest.TestCase):
    """Test log function."""
    
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_log_info(self, mock_stderr):
        """Test info level logging."""
        log('Test message')
        output = mock_stderr.getvalue()
        self.assertIn('INFO', output)
        self.assertIn('Test message', output)
    
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_log_error(self, mock_stderr):
        """Test error level logging."""
        log('Error message', 'error')
        output = mock_stderr.getvalue()
        self.assertIn('ERROR', output)
        self.assertIn('Error message', output)
    
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_log_warn(self, mock_stderr):
        """Test warn level logging."""
        log('Warning message', 'warn')
        output = mock_stderr.getvalue()
        self.assertIn('WARN', output)
        self.assertIn('Warning message', output)
    
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_log_success(self, mock_stderr):
        """Test success level logging."""
        log('Success message', 'success')
        output = mock_stderr.getvalue()
        self.assertIn('SUCCESS', output)
        self.assertIn('Success message', output)
    
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_log_timestamp(self, mock_stderr):
        """Test that log includes timestamp."""
        log('Test message')
        output = mock_stderr.getvalue()
        # Should contain ISO format timestamp with T
        self.assertIn('T', output)


class TestRunCommand(unittest.TestCase):
    """Test run_command function."""
    
    @patch('subprocess.run')
    def test_run_command_success(self, mock_run):
        """Test successful command execution."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='output',
            stderr=''
        )
        
        code, output = run_command('echo hello')
        
        self.assertEqual(code, 0)
        self.assertEqual(output, 'output')
    
    @patch('subprocess.run')
    def test_run_command_failure(self, mock_run):
        """Test failed command execution."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='',
            stderr='error output'
        )
        
        code, output = run_command('false')
        
        self.assertEqual(code, 1)
        self.assertEqual(output, 'error output')
    
    @patch('subprocess.run')
    def test_run_command_timeout(self, mock_run):
        """Test command timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd='test', timeout=300)
        
        code, output = run_command('sleep 1000')
        
        self.assertEqual(code, -1)
        self.assertIn('timed out', output)
        self.assertIn('300', output)
    
    @patch('subprocess.run')
    def test_run_command_exception(self, mock_run):
        """Test command that raises exception."""
        mock_run.side_effect = Exception('Command failed')
        
        code, output = run_command('invalid')
        
        self.assertEqual(code, -1)
        self.assertIn('Command failed', output)
    
    @patch('subprocess.run')
    def test_run_command_with_custom_timeout(self, mock_run):
        """Test command with custom timeout."""
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        
        run_command('echo test', timeout=60)
        
        call_kwargs = mock_run.call_args[1]
        self.assertEqual(call_kwargs['timeout'], 60)


class TestExtractNumber(unittest.TestCase):
    """Test extract_number function."""
    
    def test_extract_percentage(self):
        """Test extracting percentage."""
        result = extract_number('Coverage: 85.5%')
        self.assertEqual(result, 85.5)
    
    def test_extract_integer(self):
        """Test extracting integer."""
        result = extract_number('Errors: 42')
        self.assertEqual(result, 42.0)
    
    def test_extract_float(self):
        """Test extracting float."""
        result = extract_number('Time: 3.14159')
        self.assertEqual(result, 3.14159)
    
    def test_extract_no_number(self):
        """Test when no number present."""
        result = extract_number('No numbers here')
        self.assertIsNone(result)
    
    def test_extract_empty_string(self):
        """Test with empty string."""
        result = extract_number('')
        self.assertIsNone(result)
    
    def test_extract_multiple_numbers(self):
        """Test extracting first number when multiple present."""
        result = extract_number('Files: 10, Coverage: 85%')
        # Should match percentage first if present
        self.assertEqual(result, 85.0)
    
    def test_extract_value_error(self):
        """Test handling of ValueError during float conversion."""
        # This covers lines 71-72 in autoresearch_exec.py
        # We need to trigger a ValueError in the float conversion
        # by mocking re.search to return a group that can't be converted
        import re
        original_search = re.search
        
        def mock_search(*args, **kwargs):
            match = original_search(*args, **kwargs)
            if match and args[0] == r'(\d+\.?\d*)':
                # Create a mock match that returns invalid float string
                class MockMatch:
                    def group(self, n):
                        return 'not_a_number'
                return MockMatch()
            return match
        
        with patch('re.search', side_effect=mock_search):
            result = extract_number('Value: 42')
            self.assertIsNone(result)


class TestInitRun(unittest.TestCase):
    """Test init_run function."""
    
    @patch('subprocess.run')
    def test_init_run_success(self, mock_run):
        """Test successful init."""
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        
        config = {
            'goal': 'Test goal',
            'metric': 'Test metric',
            'verify': 'test verify',
            'direction': 'lower',
            'mode': 'loop'
        }
        
        result = init_run(config)
        
        self.assertTrue(result)
    
    @patch('subprocess.run')
    def test_init_run_failure(self, mock_run):
        """Test failed init."""
        mock_run.return_value = MagicMock(returncode=1, stdout='', stderr='Init error')
        
        config = {
            'goal': 'Test goal',
            'metric': 'Test metric',
            'verify': 'test verify',
            'direction': 'lower'
        }
        
        result = init_run(config)
        
        self.assertFalse(result)
    
    @patch('subprocess.run')
    def test_init_run_with_optional_args(self, mock_run):
        """Test init with optional args."""
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        
        config = {
            'goal': 'Test goal',
            'metric': 'Test metric',
            'verify': 'test verify',
            'direction': 'lower',
            'mode': 'debug',
            'scope': 'src/',
            'guard': 'npm test',
            'iterations': 10
        }
        
        result = init_run(config)
        
        self.assertTrue(result)
        # Verify the command includes optional args
        call_args = mock_run.call_args[0][0]
        self.assertIn('--scope', call_args)
        self.assertIn('src/', call_args)
    
    @patch('subprocess.run')
    def test_init_run_exception(self, mock_run):
        """Test init that raises exception."""
        mock_run.side_effect = Exception('Init failed')
        
        config = {
            'goal': 'Test goal',
            'metric': 'Test metric',
            'verify': 'test verify',
            'direction': 'lower'
        }
        
        result = init_run(config)
        
        self.assertFalse(result)


class TestGetBaseline(unittest.TestCase):
    """Test get_baseline function."""
    
    @patch('autoresearch_exec.run_command')
    def test_get_baseline_success(self, mock_run):
        """Test successful baseline extraction."""
        mock_run.return_value = (0, 'Coverage: 75.5%')
        
        success, metric = get_baseline('npm test')
        
        self.assertTrue(success)
        self.assertEqual(metric, 75.5)
    
    @patch('autoresearch_exec.run_command')
    def test_get_baseline_command_fails(self, mock_run):
        """Test when verify command fails."""
        mock_run.return_value = (1, 'Error output')
        
        success, metric = get_baseline('npm test')
        
        self.assertFalse(success)
        self.assertEqual(metric, 0)
    
    @patch('autoresearch_exec.run_command')
    def test_get_baseline_no_number(self, mock_run):
        """Test when no number can be extracted."""
        mock_run.return_value = (0, 'No numbers here')
        
        success, metric = get_baseline('npm test')
        
        self.assertFalse(success)
        self.assertEqual(metric, 0)


class TestRunIteration(unittest.TestCase):
    """Test run_iteration function."""
    
    @patch('autoresearch_exec.run_command')
    def test_run_iteration_keep(self, mock_run):
        """Test iteration that should be kept."""
        mock_run.return_value = (0, 'Coverage: 80%')
        
        config = {
            'verify': 'npm test',
            'direction': 'lower',
            'guard': None
        }
        baseline = 85.0
        
        result = run_iteration(1, config, baseline)
        
        self.assertEqual(result['status'], 'keep')
        self.assertEqual(result['metric'], 80.0)
        self.assertEqual(result['delta'], -5.0)
    
    @patch('autoresearch_exec.run_command')
    def test_run_iteration_discard_not_improved(self, mock_run):
        """Test iteration that should be discarded (not improved)."""
        mock_run.return_value = (0, 'Coverage: 80%')
        
        config = {
            'verify': 'npm test',
            'direction': 'higher',
            'guard': None
        }
        baseline = 85.0
        
        result = run_iteration(1, config, baseline)
        
        self.assertEqual(result['status'], 'discard')
        self.assertEqual(result['reason'], 'Did not improve')
    
    @patch('autoresearch_exec.run_command')
    def test_run_iteration_discard_guard_failed(self, mock_run):
        """Test iteration discarded due to guard failure."""
        # First call is verify (returns success with metric)
        # Second call is guard (returns failure)
        mock_run.side_effect = [
            (0, 'Coverage: 80%'),
            (1, 'Tests failed')
        ]
        
        config = {
            'verify': 'npm test',
            'direction': 'lower',
            'guard': 'npm test'
        }
        baseline = 85.0
        
        result = run_iteration(1, config, baseline)
        
        self.assertEqual(result['status'], 'discard')
        self.assertEqual(result['reason'], 'Guard failed')
    
    @patch('autoresearch_exec.run_command')
    def test_run_iteration_crash_no_metric(self, mock_run):
        """Test iteration crash when metric can't be extracted."""
        mock_run.return_value = (0, 'No parseable output')
        
        config = {
            'verify': 'npm test',
            'direction': 'lower'
        }
        baseline = 85.0
        
        result = run_iteration(1, config, baseline)
        
        self.assertEqual(result['status'], 'crash')
        self.assertEqual(result['reason'], 'Could not extract metric')


class TestExecLoop(unittest.TestCase):
    """Test exec_loop function."""
    
    @patch('autoresearch_exec.init_run')
    def test_exec_loop_init_fails(self, mock_init):
        """Test when init fails."""
        mock_init.return_value = False
        
        config = {'goal': 'Test', 'metric': 'coverage', 'verify': 'test'}
        
        result = exec_loop(config)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['exit_code'], 3)
    
    @patch('autoresearch_exec.get_baseline')
    @patch('autoresearch_exec.init_run')
    @patch('autoresearch_exec.run_command')
    def test_exec_loop_health_check_fails(self, mock_run, mock_init, mock_baseline):
        """Test when health check fails."""
        mock_init.return_value = True
        mock_run.return_value = (1, 'Health check failed')
        
        config = {'goal': 'Test', 'metric': 'coverage', 'verify': 'test'}
        
        result = exec_loop(config)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Health check failed')
    
    @patch('autoresearch_exec.get_baseline')
    @patch('autoresearch_exec.init_run')
    @patch('autoresearch_exec.run_command')
    def test_exec_loop_baseline_fails(self, mock_run, mock_init, mock_baseline):
        """Test when baseline fails."""
        mock_init.return_value = True
        mock_run.return_value = (0, 'Health OK')
        mock_baseline.return_value = (False, 0)
        
        config = {'goal': 'Test', 'metric': 'coverage', 'verify': 'test'}
        
        result = exec_loop(config)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Baseline failed')
    
    @patch('autoresearch_exec.get_baseline')
    @patch('autoresearch_exec.init_run')
    @patch('autoresearch_exec.run_command')
    def test_exec_loop_success(self, mock_run, mock_init, mock_baseline):
        """Test successful exec loop."""
        mock_init.return_value = True
        mock_run.side_effect = [
            (0, 'Health OK'),  # health check
            (0, 'Coverage: 80%')  # iteration verify
        ]
        mock_baseline.return_value = (True, 85.0)
        
        config = {
            'goal': 'Test',
            'metric': 'coverage',
            'verify': 'npm test',
            'direction': 'lower',
            'iterations': 1
        }
        
        result = exec_loop(config)
        
        self.assertTrue(result['success'])
        self.assertIn('summary', result)
        self.assertEqual(result['summary']['baseline'], 85.0)
    
    @patch('autoresearch_exec.get_baseline')
    @patch('autoresearch_exec.init_run')
    @patch('autoresearch_exec.run_command')
    def test_exec_loop_target_reached(self, mock_run, mock_init, mock_baseline):
        """Test exec loop when target is reached."""
        mock_init.return_value = True
        mock_run.side_effect = [
            (0, 'Health OK'),  # health check
            (0, 'Coverage: 70%')  # iteration verify - below target
        ]
        mock_baseline.return_value = (True, 85.0)
        
        config = {
            'goal': 'Test',
            'metric': 'coverage',
            'verify': 'npm test',
            'direction': 'lower',
            'iterations': 10,
            'target': 75.0
        }
        
        result = exec_loop(config)
        
        self.assertTrue(result['success'])
    
    @patch('autoresearch_exec.get_baseline')
    @patch('autoresearch_exec.init_run')
    @patch('autoresearch_exec.run_command')
    def test_exec_loop_target_reached_higher(self, mock_run, mock_init, mock_baseline):
        """Test exec loop when target is reached with higher direction (lines 227-229)."""
        mock_init.return_value = True
        mock_run.side_effect = [
            (0, 'Health OK'),  # health check
            (0, 'Coverage: 90%')  # iteration verify - above target
        ]
        mock_baseline.return_value = (True, 85.0)
        
        config = {
            'goal': 'Test',
            'metric': 'coverage',
            'verify': 'npm test',
            'direction': 'higher',
            'iterations': 10,
            'target': 88.0
        }
        
        result = exec_loop(config)
        
        self.assertTrue(result['success'])
    
    @patch('autoresearch_exec.get_baseline')
    @patch('autoresearch_exec.init_run')
    @patch('autoresearch_exec.run_command')
    def test_exec_loop_discard_count(self, mock_run, mock_init, mock_baseline):
        """Test exec loop tracking discard count (lines 219-220)."""
        mock_init.return_value = True
        mock_run.side_effect = [
            (0, 'Health OK'),  # health check
            (0, 'Coverage: 80%'),  # iteration verify - worse (higher direction: 80 < 85)
        ]
        mock_baseline.return_value = (True, 85.0)
        
        config = {
            'goal': 'Test',
            'metric': 'coverage',
            'verify': 'npm test',
            'direction': 'higher',  # Higher is better, but we got 80 < 85 (worse)
            'iterations': 1
        }
        
        result = exec_loop(config)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['summary']['discarded'], 1)


class TestExecCheck(unittest.TestCase):
    """Test exec_check function."""
    
    @patch('autoresearch_exec.get_baseline')
    def test_exec_check_pass_higher(self, mock_baseline):
        """Test check mode that passes with higher direction."""
        mock_baseline.return_value = (True, 85.0)
        
        config = {
            'verify': 'npm test',
            'threshold': 80.0,
            'direction': 'higher'
        }
        
        result = exec_check(config)
        
        self.assertTrue(result['success'])
        self.assertTrue(result['passed'])
        self.assertEqual(result['metric'], 85.0)
    
    @patch('autoresearch_exec.get_baseline')
    def test_exec_check_fail_higher(self, mock_baseline):
        """Test check mode that fails with higher direction."""
        mock_baseline.return_value = (True, 75.0)
        
        config = {
            'verify': 'npm test',
            'threshold': 80.0,
            'direction': 'higher'
        }
        
        result = exec_check(config)
        
        self.assertFalse(result['success'])
        self.assertFalse(result['passed'])
    
    @patch('autoresearch_exec.get_baseline')
    def test_exec_check_pass_lower(self, mock_baseline):
        """Test check mode that passes with lower direction."""
        mock_baseline.return_value = (75.0)
        mock_baseline.return_value = (True, 75.0)
        
        config = {
            'verify': 'npm test',
            'threshold': 80.0,
            'direction': 'lower'
        }
        
        result = exec_check(config)
        
        self.assertTrue(result['success'])
        self.assertTrue(result['passed'])
    
    @patch('autoresearch_exec.get_baseline')
    def test_exec_check_baseline_fails(self, mock_baseline):
        """Test check mode when baseline fails."""
        mock_baseline.return_value = (False, 0)
        
        config = {'verify': 'npm test'}
        
        result = exec_check(config)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['exit_code'], 3)
    
    @patch('autoresearch_exec.get_baseline')
    def test_exec_check_default_threshold(self, mock_baseline):
        """Test check mode with default threshold."""
        mock_baseline.return_value = (True, 5.0)
        
        config = {
            'verify': 'npm test',
            'direction': 'lower'
        }
        
        result = exec_check(config)
        
        self.assertFalse(result['passed'])  # 5.0 > 0 (default threshold)


class TestMain(unittest.TestCase):
    """Test main function."""
    
    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        os.chdir(self.old_cwd)
        
        def on_rm_error(func, path, exc_info):
            os.chmod(path, stat.S_IWRITE)
            try:
                func(path)
            except:
                pass
        
        shutil.rmtree(self.temp_dir, onerror=on_rm_error)
    
    @patch('autoresearch_exec.exec_loop')
    def test_main_optimize_mode(self, mock_exec_loop):
        """Test main with optimize mode."""
        mock_exec_loop.return_value = {'success': True, 'exit_code': 0}
        
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.argv', [
                'autoresearch_exec',
                '--mode', 'optimize',
                '--goal', 'Test goal',
                '--metric', 'coverage',
                '--verify', 'npm test',
                '--direction', 'lower'
            ]):
                main()
        
        self.assertEqual(cm.exception.code, 0)
    
    @patch('autoresearch_exec.exec_check')
    def test_main_check_mode(self, mock_exec_check):
        """Test main with check mode."""
        mock_exec_check.return_value = {'success': True, 'exit_code': 0}
        
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.argv', [
                'autoresearch_exec',
                '--mode', 'check',
                '--verify', 'npm test'
            ]):
                main()
        
        self.assertEqual(cm.exception.code, 0)
    
    def test_main_missing_required_optimize(self):
        """Test main with missing required fields for optimize."""
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.argv', [
                'autoresearch_exec',
                '--mode', 'optimize',
                '--goal', 'Test'  # Missing metric and verify
            ]):
                main()
        
        self.assertEqual(cm.exception.code, 3)
    
    def test_main_missing_required_check(self):
        """Test main with missing required fields for check."""
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.argv', [
                'autoresearch_exec',
                '--mode', 'check'
                # Missing verify
            ]):
                main()
        
        self.assertEqual(cm.exception.code, 3)
    
    @patch('autoresearch_exec.exec_loop')
    def test_main_config_file(self, mock_exec_loop):
        """Test main with config file."""
        mock_exec_loop.return_value = {'success': True, 'exit_code': 0}
        
        # Create config file
        config = {
            'goal': 'Test goal',
            'metric': 'coverage',
            'verify': 'npm test',
            'direction': 'lower'
        }
        with open('config.json', 'w') as f:
            json.dump(config, f)
        
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.argv', [
                'autoresearch_exec',
                '--mode', 'optimize',
                '--config', 'config.json'
            ]):
                main()
        
        self.assertEqual(cm.exception.code, 0)
    
    @patch('autoresearch_exec.exec_loop')
    def test_main_output_json(self, mock_exec_loop):
        """Test main with JSON output file."""
        mock_exec_loop.return_value = {
            'success': True,
            'exit_code': 0,
            'summary': {'baseline': 100}
        }
        
        with self.assertRaises(SystemExit):
            with patch('sys.argv', [
                'autoresearch_exec',
                '--mode', 'optimize',
                '--goal', 'Test',
                '--metric', 'coverage',
                '--verify', 'test',
                '--direction', 'lower',
                '--output-json', 'result.json'
            ]):
                main()
        
        # Check that output file was created
        self.assertTrue(os.path.exists('result.json'))
        with open('result.json', 'r') as f:
            result = json.load(f)
            self.assertTrue(result['success'])


# Import subprocess for the TimeoutExpired exception
import subprocess


class TestMainBlock(unittest.TestCase):
    """Test __main__ block execution."""
    
    @patch('autoresearch_exec.main')
    def test_main_block(self, mock_main):
        """Test that __main__ block calls main()."""
        mock_main.return_value = None
        
        # Simulate running as __main__
        import importlib.util
        spec = importlib.util.spec_from_file_location("__main__", os.path.join(
            os.path.dirname(__file__), '..', 'scripts', 'autoresearch_exec.py'))
        module = importlib.util.module_from_spec(spec)
        
        # Should call main() and exit
        try:
            spec.loader.exec_module(module)
        except SystemExit:
            pass  # Expected


if __name__ == '__main__':
    unittest.main()
