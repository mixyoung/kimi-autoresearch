#!/usr/bin/env python3
"""Tests for autoresearch_main.py"""
import unittest
import sys
import os
import tempfile
import shutil
import io
import stat
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from autoresearch_main import (
    run_script, cmd_init, cmd_health, cmd_launch_gate, cmd_decide,
    cmd_baseline, cmd_git, cmd_log, cmd_report, cmd_version, cmd_lang,
    cmd_search, cmd_ralph, main
)


class TestRunScript(unittest.TestCase):
    """Test run_script function."""
    
    @patch('subprocess.run')
    def test_run_script_success(self, mock_run):
        """Test running a script successfully."""
        mock_run.return_value = MagicMock(
            returncode=0, 
            stdout='success output',
            stderr=''
        )
        
        code, output = run_script('test_script.py', ['--arg1', 'value1'])
        
        self.assertEqual(code, 0)
        self.assertEqual(output, 'success output')
        mock_run.assert_called_once()
        # Check that the command includes python and the script
        call_args = mock_run.call_args[0][0]
        self.assertEqual(call_args[0], 'python')
        self.assertIn('test_script.py', call_args[1])
    
    @patch('subprocess.run')
    def test_run_script_failure(self, mock_run):
        """Test running a script that fails."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='',
            stderr='error message'
        )
        
        code, output = run_script('test_script.py', [])
        
        self.assertEqual(code, 1)
        self.assertEqual(output, 'error message')
    
    @patch('subprocess.run')
    def test_run_script_timeout(self, mock_run):
        """Test running a script that times out."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=['python'], timeout=300)
        
        code, output = run_script('test_script.py', [])
        
        self.assertEqual(code, -1)
        self.assertEqual(output, 'Script timed out')
    
    @patch('subprocess.run')
    def test_run_script_exception(self, mock_run):
        """Test running a script that raises exception."""
        mock_run.side_effect = Exception('Unexpected error')
        
        code, output = run_script('test_script.py', [])
        
        self.assertEqual(code, -1)
        self.assertIn('Unexpected error', output)
    
    @patch('subprocess.run')
    def test_run_script_none_output(self, mock_run):
        """Test running a script with None output."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=None,
            stderr=None
        )
        
        code, output = run_script('test_script.py', [])
        
        self.assertEqual(code, 0)
        self.assertEqual(output, '')


class TestCmdInit(unittest.TestCase):
    """Test cmd_init function."""
    
    @patch('autoresearch_main.run_script')
    def test_cmd_init_basic(self, mock_run_script):
        """Test init command with basic args."""
        mock_run_script.return_value = (0, 'Initialized successfully')
        
        args = MagicMock()
        args.goal = 'Test goal'
        args.metric = 'Test metric'
        args.verify = 'test verify'
        args.direction = 'lower'
        args.mode = 'loop'
        args.scope = None
        args.guard = None
        args.iterations = None
        
        result = cmd_init(args)
        
        self.assertEqual(result, 0)
        mock_run_script.assert_called_once()
        call_args = mock_run_script.call_args[0][1]
        self.assertIn('--goal', call_args)
        self.assertIn('Test goal', call_args)
    
    @patch('autoresearch_main.run_script')
    def test_cmd_init_with_optional_args(self, mock_run_script):
        """Test init command with optional args."""
        mock_run_script.return_value = (0, 'Initialized')
        
        args = MagicMock()
        args.goal = 'Test goal'
        args.metric = 'Test metric'
        args.verify = 'test verify'
        args.direction = 'higher'
        args.mode = 'debug'
        args.scope = 'src/'
        args.guard = 'npm test'
        args.iterations = 10
        
        result = cmd_init(args)
        
        self.assertEqual(result, 0)
        call_args = mock_run_script.call_args[0][1]
        self.assertIn('--scope', call_args)
        self.assertIn('src/', call_args)
        self.assertIn('--guard', call_args)
        self.assertIn('--iterations', call_args)


class TestCmdHealth(unittest.TestCase):
    """Test cmd_health function."""
    
    @patch('autoresearch_main.run_script')
    def test_cmd_health_basic(self, mock_run_script):
        """Test health command with no args."""
        mock_run_script.return_value = (0, 'Health OK')
        
        args = MagicMock()
        args.json = False
        args.fail_on_warn = False
        
        result = cmd_health(args)
        
        self.assertEqual(result, 0)
        mock_run_script.assert_called_once_with('autoresearch_health_check.py', [])
    
    @patch('autoresearch_main.run_script')
    def test_cmd_health_with_json(self, mock_run_script):
        """Test health command with JSON format."""
        mock_run_script.return_value = (0, '{"status": "ok"}')
        
        args = MagicMock()
        args.json = True
        args.fail_on_warn = False
        
        result = cmd_health(args)
        
        call_args = mock_run_script.call_args[0][1]
        self.assertIn('--format=json', call_args)
    
    @patch('autoresearch_main.run_script')
    def test_cmd_health_with_fail_on_warn(self, mock_run_script):
        """Test health command with fail-on-warn."""
        mock_run_script.return_value = (0, 'Health OK')
        
        args = MagicMock()
        args.json = False
        args.fail_on_warn = True
        
        result = cmd_health(args)
        
        call_args = mock_run_script.call_args[0][1]
        self.assertIn('--fail-on-warn', call_args)


class TestCmdLaunchGate(unittest.TestCase):
    """Test cmd_launch_gate function."""
    
    @patch('autoresearch_main.run_script')
    def test_cmd_launch_gate_basic(self, mock_run_script):
        """Test launch-gate command."""
        mock_run_script.return_value = (0, 'Resume')
        
        args = MagicMock()
        args.force_fresh = False
        args.force_resume = False
        args.json = False
        
        result = cmd_launch_gate(args)
        
        self.assertEqual(result, 0)
        mock_run_script.assert_called_once_with('autoresearch_launch_gate.py', [])
    
    @patch('autoresearch_main.run_script')
    def test_cmd_launch_gate_force_fresh(self, mock_run_script):
        """Test launch-gate with force-fresh."""
        mock_run_script.return_value = (0, 'Fresh start')
        
        args = MagicMock()
        args.force_fresh = True
        args.force_resume = False
        args.json = False
        
        result = cmd_launch_gate(args)
        
        call_args = mock_run_script.call_args[0][1]
        self.assertIn('--force-fresh', call_args)


class TestCmdDecide(unittest.TestCase):
    """Test cmd_decide function."""
    
    @patch('autoresearch_main.run_script')
    def test_cmd_decide_keep(self, mock_run_script):
        """Test decide command for keep."""
        mock_run_script.return_value = (0, 'keep')
        
        args = MagicMock()
        args.current = 42.0
        args.baseline = 47.0
        args.direction = 'lower'
        args.guard_passed = True
        
        result = cmd_decide(args)
        
        self.assertEqual(result, 0)
        call_args = mock_run_script.call_args[0][1]
        self.assertIn('--action', call_args)
        self.assertIn('decide', call_args)
        self.assertIn('--current', call_args)
        self.assertIn('42.0', call_args)


class TestCmdBaseline(unittest.TestCase):
    """Test cmd_baseline function."""
    
    @patch('autoresearch_main.run_script')
    def test_cmd_baseline_basic(self, mock_run_script):
        """Test baseline command."""
        mock_run_script.return_value = (0, '45')
        
        args = MagicMock()
        args.verify = 'npm test'
        args.parse_number = False
        
        result = cmd_baseline(args)
        
        self.assertEqual(result, 0)
        mock_run_script.assert_called_once_with('get_baseline.py', ['--verify', 'npm test'])
    
    @patch('autoresearch_main.run_script')
    def test_cmd_baseline_parse_number(self, mock_run_script):
        """Test baseline with parse-number."""
        mock_run_script.return_value = (0, '45')
        
        args = MagicMock()
        args.verify = 'npm test'
        args.parse_number = True
        
        result = cmd_baseline(args)
        
        call_args = mock_run_script.call_args[0][1]
        self.assertIn('--parse-number', call_args)


class TestCmdGit(unittest.TestCase):
    """Test cmd_git function."""
    
    @patch('autoresearch_main.run_script')
    def test_cmd_git_check(self, mock_run_script):
        """Test git check command."""
        mock_run_script.return_value = (0, 'Clean')
        
        args = MagicMock()
        args.git_action = 'check'
        args.message = None
        
        result = cmd_git(args)
        
        self.assertEqual(result, 0)
        mock_run_script.assert_called_once_with('check_git.py', ['--action', 'check'])
    
    @patch('autoresearch_main.run_script')
    def test_cmd_git_commit(self, mock_run_script):
        """Test git commit command."""
        mock_run_script.return_value = (0, 'Committed')
        
        args = MagicMock()
        args.git_action = 'commit'
        args.message = 'Test commit'
        
        result = cmd_git(args)
        
        call_args = mock_run_script.call_args[0][1]
        self.assertIn('--message', call_args)
        self.assertIn('Test commit', call_args)


class TestCmdLog(unittest.TestCase):
    """Test cmd_log function."""
    
    @patch('autoresearch_main.run_script')
    def test_cmd_log_basic(self, mock_run_script):
        """Test log command."""
        mock_run_script.return_value = (0, 'Logged')
        
        args = MagicMock()
        args.iteration = 1
        args.commit = 'abc123'
        args.metric = '42'
        args.status = 'keep'
        args.description = 'Fixed types'
        args.delta = '0'
        
        result = cmd_log(args)
        
        self.assertEqual(result, 0)
        call_args = mock_run_script.call_args[0][1]
        self.assertIn('--iteration', call_args)
        self.assertIn('1', call_args)
        self.assertIn('--commit', call_args)
    
    @patch('autoresearch_main.run_script')
    def test_cmd_log_with_delta(self, mock_run_script):
        """Test log command with delta."""
        mock_run_script.return_value = (0, 'Logged')
        
        args = MagicMock()
        args.iteration = 1
        args.commit = 'abc123'
        args.metric = '42'
        args.status = 'keep'
        args.description = 'Fixed types'
        args.delta = '-5'
        
        result = cmd_log(args)
        
        call_args = mock_run_script.call_args[0][1]
        self.assertIn('--delta', call_args)
        self.assertIn('-5', call_args)


class TestCmdReport(unittest.TestCase):
    """Test cmd_report function."""
    
    @patch('autoresearch_main.run_script')
    def test_cmd_report(self, mock_run_script):
        """Test report command."""
        mock_run_script.return_value = (0, 'Report generated')
        
        args = MagicMock()
        
        result = cmd_report(args)
        
        self.assertEqual(result, 0)
        mock_run_script.assert_called_once_with('generate_report.py', [])


class TestCmdVersion(unittest.TestCase):
    """Test cmd_version function."""
    
    @patch('autoresearch_main.run_script')
    def test_cmd_version_show(self, mock_run_script):
        """Test version show command."""
        mock_run_script.return_value = (0, 'v1.0.0')
        
        args = MagicMock()
        args.version_subcommand = 'show'
        args.value = None
        args.tag = False
        args.no_changelog = False
        
        result = cmd_version(args)
        
        self.assertEqual(result, 0)
        mock_run_script.assert_called_once_with('autoresearch_version.py', ['show'])
    
    @patch('autoresearch_main.run_script')
    def test_cmd_version_bump(self, mock_run_script):
        """Test version bump command."""
        mock_run_script.return_value = (0, 'Bumped to v1.1.0')
        
        args = MagicMock()
        args.version_subcommand = 'bump'
        args.value = 'minor'
        args.tag = True
        args.no_changelog = False
        
        result = cmd_version(args)
        
        call_args = mock_run_script.call_args[0][1]
        self.assertIn('bump', call_args)
        self.assertIn('minor', call_args)
        self.assertIn('--tag', call_args)


class TestCmdLang(unittest.TestCase):
    """Test cmd_lang function."""
    
    @patch('autoresearch_main.set_locale')
    @patch('autoresearch_main.get_locale_name')
    def test_cmd_lang_set_locale(self, mock_get_locale, mock_set_locale):
        """Test setting locale."""
        mock_set_locale.return_value = True
        mock_get_locale.return_value = 'English'
        
        args = MagicMock()
        args.locale = 'en'
        
        result = cmd_lang(args)
        
        self.assertEqual(result, 0)
        mock_set_locale.assert_called_once_with('en')
    
    @patch('autoresearch_main.get_locale_name')
    def test_cmd_lang_get_locale(self, mock_get_locale):
        """Test getting current locale."""
        mock_get_locale.return_value = '中文'
        
        args = MagicMock()
        args.locale = None
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_lang(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('中文', output)


class TestCmdSearch(unittest.TestCase):
    """Test cmd_search function."""
    
    @patch('autoresearch_main.run_script')
    def test_cmd_search_check(self, mock_run_script):
        """Test search check command."""
        mock_run_script.return_value = (0, 'Not stuck')
        
        args = MagicMock()
        args.subcommand = 'check'
        args.state_file = None
        args.force = False
        args.json = False
        
        result = cmd_search(args)
        
        self.assertEqual(result, 0)
        call_args = mock_run_script.call_args[0][1]
        self.assertIn('check', call_args)
    
    @patch('autoresearch_main.run_script')
    def test_cmd_search_query(self, mock_run_script):
        """Test search query command."""
        mock_run_script.return_value = (0, 'Search results')
        
        args = MagicMock()
        args.subcommand = 'query'
        args.goal = 'Fix bug'
        args.error = 'TypeError'
        args.strategy = 'debug'
        args.json = True
        
        result = cmd_search(args)
        
        call_args = mock_run_script.call_args[0][1]
        self.assertIn('search', call_args)
        self.assertIn('--goal', call_args)
        self.assertIn('Fix bug', call_args)
        self.assertIn('--json', call_args)


class TestCmdRalph(unittest.TestCase):
    """Test cmd_ralph function."""
    
    @patch('autoresearch_main.run_script')
    def test_cmd_ralph_set_loop(self, mock_run_script):
        """Test ralph set-loop command."""
        mock_run_script.return_value = (0, 'Loop config set')
        
        args = MagicMock()
        args.ralph_command = 'set-loop'
        args.max_steps = 100
        args.max_retries = 5
        args.max_ralph = 50
        
        result = cmd_ralph(args)
        
        self.assertEqual(result, 0)
        call_args = mock_run_script.call_args[0][1]
        self.assertIn('set-loop', call_args)
        self.assertIn('--max-steps', call_args)
    
    @patch('autoresearch_main.run_script')
    def test_cmd_ralph_status(self, mock_run_script):
        """Test ralph status command."""
        mock_run_script.return_value = (0, 'Status: active')
        
        args = MagicMock()
        args.ralph_command = 'status'
        
        result = cmd_ralph(args)
        
        mock_run_script.assert_called_once_with('autoresearch_ralph.py', ['status'])
    
    @patch('autoresearch_main.run_script')
    def test_cmd_ralph_stop(self, mock_run_script):
        """Test ralph stop command."""
        mock_run_script.return_value = (0, 'Stop signal sent')
        
        args = MagicMock()
        args.ralph_command = 'stop'
        args.reason = 'Manual stop'
        
        result = cmd_ralph(args)
        
        call_args = mock_run_script.call_args[0][1]
        self.assertIn('stop', call_args)
        self.assertIn('--reason', call_args)


class TestMain(unittest.TestCase):
    """Test main function."""
    
    @patch('autoresearch_main.init_locale')
    @patch('autoresearch_main.cmd_init')
    def test_main_no_command(self, mock_cmd_init, mock_init_locale):
        """Test main with no command shows help."""
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.argv', ['autoresearch_main']):
                main()
        
        self.assertEqual(cm.exception.code, 1)
    
    @patch('autoresearch_main.init_locale')
    @patch('autoresearch_main.cmd_health')
    def test_main_health_command(self, mock_cmd_health, mock_init_locale):
        """Test main with health command."""
        mock_cmd_health.return_value = 0
        
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.argv', ['autoresearch_main', 'health']):
                main()
        
        self.assertEqual(cm.exception.code, 0)
        mock_cmd_health.assert_called_once()
    
    @patch('autoresearch_main.init_locale')
    @patch('autoresearch_main.cmd_init')
    def test_main_init_command(self, mock_cmd_init, mock_init_locale):
        """Test main with init command."""
        mock_cmd_init.return_value = 0
        
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.argv', [
                'autoresearch_main', 'init',
                '--goal', 'Test goal',
                '--metric', 'Test metric',
                '--verify', 'test command'
            ]):
                main()
        
        self.assertEqual(cm.exception.code, 0)


# Import subprocess for the TimeoutExpired exception
import subprocess

if __name__ == '__main__':
    unittest.main()
