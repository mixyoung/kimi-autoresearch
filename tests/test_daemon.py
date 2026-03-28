#!/usr/bin/env python3
"""Tests for autoresearch_daemon.py"""
import unittest
import sys
import os
import tempfile
import json
import io
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from autoresearch_daemon import (
    load_daemon_state, save_daemon_state, generate_daemon_prompt,
    cmd_start, cmd_status, cmd_pause, cmd_resume, cmd_stop, main,
    DAEMON_STATE_FILE
)


class TestLoadDaemonState(unittest.TestCase):
    """Test load_daemon_state function."""
    
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
    
    def test_load_no_file(self):
        """Test loading when no state file exists."""
        result = load_daemon_state()
        
        self.assertEqual(result['status'], 'stopped')
        self.assertIsNone(result['start_time'])
        self.assertEqual(result['current_iteration'], 0)
    
    def test_load_with_file(self):
        """Test loading from existing file."""
        state = {
            'status': 'running',
            'current_iteration': 5,
            'max_iterations': 100
        }
        with open(DAEMON_STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        result = load_daemon_state()
        
        self.assertEqual(result['status'], 'running')
        self.assertEqual(result['current_iteration'], 5)


class TestSaveDaemonState(unittest.TestCase):
    """Test save_daemon_state function."""
    
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
    
    def test_save_state(self):
        """Test saving daemon state."""
        state = {
            'status': 'running',
            'current_iteration': 10
        }
        
        save_daemon_state(state)
        
        self.assertTrue(os.path.exists(DAEMON_STATE_FILE))
        
        with open(DAEMON_STATE_FILE, 'r') as f:
            saved = json.load(f)
            self.assertEqual(saved['status'], 'running')
            self.assertEqual(saved['current_iteration'], 10)


class TestGenerateDaemonPrompt(unittest.TestCase):
    """Test generate_daemon_prompt function."""
    
    def test_prompt_generation(self):
        """Test generating daemon prompt."""
        config = {
            'goal': 'Reduce type errors',
            'scope': 'src/**/*.ts',
            'verify': 'tsc --noEmit',
            'direction': 'lower',
            'iterations': 50,
            'loop_control': {
                'max_steps_per_turn': 30,
                'max_retries_per_step': 2,
                'max_ralph_iterations': 100
            },
            'agent_config': None
        }
        
        prompt = generate_daemon_prompt(config)
        
        self.assertIn('Reduce type errors', prompt)
        self.assertIn('src/**/*.ts', prompt)
        self.assertIn('tsc --noEmit', prompt)
        self.assertIn('Ralph Loop Protocol', prompt)
        self.assertIn('<choice>STOP</choice>', prompt)
    
    def test_prompt_with_agent(self):
        """Test generating prompt with agent config (lines 65-66)."""
        config = {
            'goal': 'Test',
            'scope': '.',
            'verify': '',
            'direction': 'lower',
            'iterations': 10,
            'loop_control': {},
            'agent_config': {'agent': 'okabe', 'agent_file': None}
        }
        
        prompt = generate_daemon_prompt(config)
        
        self.assertIn('okabe', prompt)
    
    def test_prompt_with_agent_file(self):
        """Test generating prompt with agent file (lines 67-68)."""
        config = {
            'goal': 'Test',
            'scope': '.',
            'verify': '',
            'direction': 'lower',
            'iterations': 10,
            'loop_control': {},
            'agent_config': {'agent': None, 'agent_file': '/path/to/agent.json'}
        }
        
        prompt = generate_daemon_prompt(config)
        
        self.assertIn('agent.json', prompt)


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
    
    def test_start_new_daemon(self):
        """Test starting a new daemon."""
        args = MagicMock()
        args.goal = 'Test goal'
        args.scope = '.'
        args.verify = 'echo test'
        args.direction = 'lower'
        args.iterations = 10
        args.target = None
        args.max_steps_per_turn = 50
        args.max_retries_per_step = 3
        args.max_ralph_iterations = 0
        args.agent = None
        args.agent_file = None
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_start(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Autoresearch Daemon', output)
        self.assertIn('Test goal', output)
        
        # Check state was saved
        state = load_daemon_state()
        self.assertEqual(state['status'], 'running')
        self.assertEqual(state['max_iterations'], 10)
    
    def test_start_when_running(self):
        """Test starting when already running."""
        # Set up running state
        state = {'status': 'running', 'current_iteration': 5, 'max_iterations': 100}
        with open(DAEMON_STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        args = MagicMock()
        args.goal = 'Test'
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_start(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 1)
        self.assertIn('already running', output)
    
    def test_start_with_agent(self):
        """Test starting daemon with agent config (lines 225-226)."""
        args = MagicMock()
        args.goal = 'Test goal'
        args.scope = '.'
        args.verify = 'echo test'
        args.direction = 'lower'
        args.iterations = 10
        args.target = None
        args.max_steps_per_turn = 50
        args.max_retries_per_step = 3
        args.max_ralph_iterations = 0
        args.agent = 'okabe'
        args.agent_file = None
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_start(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        
        # Check state was saved with agent config
        state = load_daemon_state()
        self.assertEqual(state['config']['agent_config']['agent'], 'okabe')
    
    def test_start_with_agent_file(self):
        """Test starting daemon with agent file (lines 227-228)."""
        args = MagicMock()
        args.goal = 'Test goal'
        args.scope = '.'
        args.verify = 'echo test'
        args.direction = 'lower'
        args.iterations = 10
        args.target = None
        args.max_steps_per_turn = 50
        args.max_retries_per_step = 3
        args.max_ralph_iterations = 0
        args.agent = None
        args.agent_file = '/path/to/custom_agent.json'
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_start(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        
        # Check state was saved with agent file config
        state = load_daemon_state()
        self.assertEqual(state['config']['agent_config']['agent_file'], '/path/to/custom_agent.json')


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
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_status(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('stopped', output)
    
    def test_status_running(self):
        """Test status when running."""
        state = {
            'status': 'running',
            'current_iteration': 5,
            'max_iterations': 100,
            'config': {'goal': 'Test goal'}
        }
        with open(DAEMON_STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_status(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('running', output)
        self.assertIn('Test goal', output)
    
    def test_status_with_start_time_and_task_id(self):
        """Test status with start_time and task_id (lines 283, 286)."""
        state = {
            'status': 'running',
            'current_iteration': 5,
            'max_iterations': 100,
            'start_time': '2024-01-01T12:00:00',
            'task_id': 'task-12345',
            'config': {'goal': 'Test goal'}
        }
        with open(DAEMON_STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_status(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('2024-01-01', output)
        self.assertIn('task-12345', output)
    
    def test_status_with_log_file(self):
        """Test status with log file display (lines 299-304)."""
        state = {
            'status': 'running',
            'current_iteration': 5,
            'max_iterations': 100,
            'config': {'goal': 'Test goal'}
        }
        with open(DAEMON_STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        # Create log file
        with open('autoresearch-daemon.log', 'w') as f:
            f.write('Line 1\n')
            f.write('Line 2\n')
            f.write('Line 3\n')
        
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_status(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Line 3', output)


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
    
    def test_pause_running(self):
        """Test pausing a running daemon."""
        state = {'status': 'running', 'current_iteration': 5}
        with open(DAEMON_STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_pause(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('paused', output)
        
        state = load_daemon_state()
        self.assertEqual(state['status'], 'paused')
    
    def test_pause_not_running(self):
        """Test pausing when not running."""
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
    
    def test_resume_paused(self):
        """Test resuming a paused daemon."""
        state = {'status': 'paused', 'current_iteration': 5}
        with open(DAEMON_STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_resume(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('resumed', output)
        
        state = load_daemon_state()
        self.assertEqual(state['status'], 'running')
    
    def test_resume_not_paused(self):
        """Test resuming when not paused."""
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_resume(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 1)
        self.assertIn('not paused', output)


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
    
    def test_stop(self):
        """Test stopping daemon."""
        state = {'status': 'running', 'task_id': '123'}
        with open(DAEMON_STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_stop(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('stopped', output)
        
        state = load_daemon_state()
        self.assertEqual(state['status'], 'stopped')
        self.assertIsNone(state['task_id'])


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
    
    def test_main_status(self):
        """Test main with status command."""
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_daemon.py', 'status']
            try:
                main()
            except SystemExit as e:
                self.assertEqual(e.code, 0)
        finally:
            sys.argv = old_argv
    
    def test_main_no_command(self):
        """Test main with no command."""
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_daemon.py']
            try:
                main()
            except SystemExit as e:
                self.assertEqual(e.code, 1)
        finally:
            sys.argv = old_argv


class TestMainBlock(unittest.TestCase):
    """Test __main__ block execution."""
    
    @patch('autoresearch_daemon.main')
    def test_main_block(self, mock_main):
        """Test that __main__ block calls main() (line 419)."""
        mock_main.return_value = None
        
        # Simulate running as __main__
        import importlib.util
        spec = importlib.util.spec_from_file_location("__main__", os.path.join(
            os.path.dirname(__file__), '..', 'scripts', 'autoresearch_daemon.py'))
        module = importlib.util.module_from_spec(spec)
        
        # Should call main() and exit
        try:
            spec.loader.exec_module(module)
        except SystemExit:
            pass  # Expected


if __name__ == '__main__':
    unittest.main()
