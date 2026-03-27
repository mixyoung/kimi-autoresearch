#!/usr/bin/env python3
"""Tests for autoresearch_background.py"""
import unittest
import sys
import os
import tempfile
import json
import io
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from autoresearch_background import (
    load_runtime, save_runtime, load_state, is_process_running,
    cmd_status, cmd_start, cmd_stop, cmd_pause, cmd_resume, cmd_log,
    main, RUNTIME_FILE, STATE_FILE
)


class TestLoadRuntime(unittest.TestCase):
    """Test load_runtime function."""
    
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
    
    def test_load_runtime_no_file(self):
        """Test loading runtime when no file exists."""
        result = load_runtime()
        
        self.assertEqual(result['status'], 'stopped')
        self.assertIsNone(result['pid'])
        self.assertIsNone(result['start_time'])
        self.assertEqual(result['iterations_completed'], 0)
        self.assertEqual(result['errors'], [])
    
    def test_load_runtime_with_file(self):
        """Test loading runtime from file."""
        runtime = {
            'status': 'running',
            'pid': 1234,
            'iterations_completed': 5,
            'errors': []
        }
        with open(RUNTIME_FILE, 'w') as f:
            json.dump(runtime, f)
        
        result = load_runtime()
        
        self.assertEqual(result['status'], 'running')
        self.assertEqual(result['pid'], 1234)
        self.assertEqual(result['iterations_completed'], 5)
    
    def test_load_runtime_corrupted(self):
        """Test loading runtime from corrupted file."""
        with open(RUNTIME_FILE, 'w') as f:
            f.write('not valid json')
        
        result = load_runtime()
        
        self.assertEqual(result['status'], 'stopped')


class TestSaveRuntime(unittest.TestCase):
    """Test save_runtime function."""
    
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
    
    def test_save_runtime(self):
        """Test saving runtime state."""
        runtime = {'status': 'running', 'pid': 1234}
        
        save_runtime(runtime)
        
        self.assertTrue(os.path.exists(RUNTIME_FILE))
        
        with open(RUNTIME_FILE, 'r') as f:
            saved = json.load(f)
            self.assertEqual(saved['status'], 'running')
            self.assertEqual(saved['pid'], 1234)
            self.assertIn('last_update', saved)


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
        state = {'iteration': 5, 'config': {'goal': 'Test'}}
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        result = load_state()
        
        self.assertEqual(result['iteration'], 5)
        self.assertEqual(result['config']['goal'], 'Test')


class TestIsProcessRunning(unittest.TestCase):
    """Test is_process_running function."""
    
    def test_none_pid(self):
        """Test with None pid."""
        result = is_process_running(None)
        self.assertFalse(result)
    
    @patch('subprocess.run')
    def test_running_on_windows(self, mock_run):
        """Test checking running process on Windows."""
        mock_run.return_value = MagicMock(stdout='test.exe 1234 Console', stderr='')
        
        with patch.object(sys, 'platform', 'win32'):
            result = is_process_running(1234)
        
        self.assertTrue(result)
    
    @patch('subprocess.run')
    def test_not_running_on_windows(self, mock_run):
        """Test checking non-running process on Windows."""
        mock_run.return_value = MagicMock(stdout='INFO: No tasks', stderr='')
        
        with patch.object(sys, 'platform', 'win32'):
            result = is_process_running(9999)
        
        self.assertFalse(result)
    
    @patch('os.kill')
    def test_running_on_unix(self, mock_kill):
        """Test checking running process on Unix."""
        with patch.object(sys, 'platform', 'linux'):
            result = is_process_running(1234)
        
        self.assertTrue(result)
    
    @patch('os.kill', side_effect=OSError())
    def test_not_running_on_unix(self, mock_kill):
        """Test checking non-running process on Unix."""
        with patch.object(sys, 'platform', 'linux'):
            result = is_process_running(9999)
        
        self.assertFalse(result)


class TestCmdStatus(unittest.TestCase):
    """Test cmd_status function."""
    
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
    
    def test_status_stopped(self):
        """Test status when stopped."""
        runtime = {'status': 'stopped', 'pid': None}
        with open(RUNTIME_FILE, 'w') as f:
            json.dump(runtime, f)
        
        args = MagicMock()
        args.json = False
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_status(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('stopped', output)
    
    def test_status_json_output(self):
        """Test status with JSON output."""
        runtime = {'status': 'stopped', 'pid': None, 'iterations_completed': 0}
        with open(RUNTIME_FILE, 'w') as f:
            json.dump(runtime, f)
        
        args = MagicMock()
        args.json = True
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_status(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        data = json.loads(output)
        self.assertIn('status', data)
        self.assertIn('iterations_completed', data)


class TestCmdStart(unittest.TestCase):
    """Test cmd_start function."""
    
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
    
    def test_start_when_not_running(self):
        """Test start when not already running."""
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_start(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Starting', output)
        
        # Check runtime file was created
        runtime = load_runtime()
        self.assertEqual(runtime['status'], 'running')
    
    def test_start_when_already_running(self):
        """Test start when already running."""
        runtime = {'status': 'running', 'pid': 1234}
        with open(RUNTIME_FILE, 'w') as f:
            json.dump(runtime, f)
        
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_start(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 1)
        self.assertIn('already running', output)


class TestCmdStop(unittest.TestCase):
    """Test cmd_stop function."""
    
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
    
    def test_stop_when_not_running(self):
        """Test stop when not running."""
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_stop(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('not running', output)
    
    def test_stop_when_running(self):
        """Test stop when running."""
        runtime = {'status': 'running', 'pid': None}
        with open(RUNTIME_FILE, 'w') as f:
            json.dump(runtime, f)
        
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_stop(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('stopped', output)
        
        runtime = load_runtime()
        self.assertEqual(runtime['status'], 'stopped')
        self.assertIsNone(runtime['pid'])


class TestCmdPause(unittest.TestCase):
    """Test cmd_pause function."""
    
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
    
    def test_pause_when_running(self):
        """Test pause when running."""
        runtime = {'status': 'running', 'pid': None}
        with open(RUNTIME_FILE, 'w') as f:
            json.dump(runtime, f)
        
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_pause(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('paused', output)
        
        runtime = load_runtime()
        self.assertEqual(runtime['status'], 'paused')
    
    def test_pause_when_not_running(self):
        """Test pause when not running."""
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_pause(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 1)
        self.assertIn('not running', output)


class TestCmdResume(unittest.TestCase):
    """Test cmd_resume function."""
    
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
    
    def test_resume_when_paused(self):
        """Test resume when paused."""
        runtime = {'status': 'paused', 'pid': None}
        with open(RUNTIME_FILE, 'w') as f:
            json.dump(runtime, f)
        
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_resume(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('resumed', output)
        
        runtime = load_runtime()
        self.assertEqual(runtime['status'], 'running')
    
    def test_resume_when_not_paused(self):
        """Test resume when not paused."""
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_resume(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 1)
        self.assertIn('not paused', output)


class TestCmdLog(unittest.TestCase):
    """Test cmd_log function."""
    
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
    
    def test_log_no_errors(self):
        """Test log when no errors exist."""
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_log(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('No errors', output)
    
    def test_log_with_errors(self):
        """Test log with errors."""
        runtime = {
            'status': 'running',
            'errors': [
                {'timestamp': '2024-01-01', 'iteration': 1, 'message': 'Error 1'},
                {'timestamp': '2024-01-02', 'iteration': 2, 'message': 'Error 2'}
            ]
        }
        with open(RUNTIME_FILE, 'w') as f:
            json.dump(runtime, f)
        
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_log(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Recent Errors', output)
        self.assertIn('Error 1', output)
        self.assertIn('Error 2', output)


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
    
    @patch('autoresearch_background.sys.argv', ['autoresearch_background.py', 'status'])
    def test_main_status(self):
        """Test main with status command."""
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        try:
            main()
        except SystemExit as e:
            self.assertEqual(e.code, 0)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertIn('Autoresearch Background Runtime Status', output)
    
    @patch('autoresearch_background.sys.argv', ['autoresearch_background.py', 'start'])
    def test_main_start(self):
        """Test main with start command."""
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        try:
            main()
        except SystemExit as e:
            self.assertEqual(e.code, 0)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertIn('Starting', output)
    
    @patch('autoresearch_background.sys.argv', ['autoresearch_background.py'])
    def test_main_no_command(self):
        """Test main with no command."""
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        try:
            main()
        except SystemExit as e:
            self.assertEqual(e.code, 1)


if __name__ == '__main__':
    unittest.main()
