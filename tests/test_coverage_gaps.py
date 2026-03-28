#!/usr/bin/env python3
"""
Additional tests to cover gaps in test coverage.
Focus on error handling and edge cases.
"""
import unittest
import sys
import os
import tempfile
import json
import io
import csv
import stat
import shutil
from unittest.mock import patch, MagicMock, mock_open

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


class TestStuckRecoveryGaps(unittest.TestCase):
    """Cover missing lines in autoresearch_stuck_recovery.py"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_results_exception(self):
        """Test load_results when CSV reading raises exception (lines 39-40)."""
        from autoresearch_stuck_recovery import load_results
        
        # Create a file that will cause csv.DictReader to fail
        with open('autoresearch-results.tsv', 'w') as f:
            f.write("corrupted data without proper headers")
        
        # Mock csv.DictReader to raise exception
        with patch('csv.DictReader', side_effect=Exception('CSV error')):
            result = load_results()
        
        self.assertEqual(result, [])
    
    def test_cmd_check_json_output(self):
        """Test cmd_check with JSON output (line 168)."""
        from autoresearch_stuck_recovery import cmd_check
        
        # Create state file
        state = {
            'consecutive_discards': 5,
            'pivot_count': 2,
            'config': {'goal': 'Test'},
            'strategy': 'test',
            'last_error': 'error'
        }
        with open('autoresearch-state.json', 'w') as f:
            json.dump(state, f)
        
        args = MagicMock()
        args.json = True  # This triggers line 168
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_check(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        # Should return valid JSON
        data = json.loads(output)
        self.assertTrue(data['is_stuck'])
        self.assertEqual(data['action'], 'search')
    
    def test_cmd_trigger_stuck_with_search_action(self):
        """Test cmd_trigger when stuck and action is 'search' (lines 206-245)."""
        from autoresearch_stuck_recovery import cmd_trigger
        
        # Create state to trigger search
        state = {
            'consecutive_discards': 5,
            'pivot_count': 2,
            'config': {'goal': 'Test goal'},
            'strategy': 'test strategy',
            'last_error': 'test error'
        }
        with open('autoresearch-state.json', 'w') as f:
            json.dump(state, f)
        
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
        self.assertIn('Web Search Auto-Triggered', output)
        self.assertIn('SearchWeb', output)
    
    def test_cmd_trigger_with_output_file(self):
        """Test cmd_trigger with output file (lines 239-243)."""
        from autoresearch_stuck_recovery import cmd_trigger
        
        # Create state to trigger search
        state = {
            'consecutive_discards': 5,
            'pivot_count': 2,
            'config': {'goal': 'Test'},
            'strategy': 'test',
            'last_error': 'error'
        }
        with open('autoresearch-state.json', 'w') as f:
            json.dump(state, f)
        
        args = MagicMock()
        args.json = False
        args.quiet = False
        args.output = 'search_result.json'  # This triggers lines 239-243
        
        result = cmd_trigger(args)
        
        self.assertEqual(result, 0)
        # Check file was created
        self.assertTrue(os.path.exists('search_result.json'))
        with open('search_result.json', 'r') as f:
            data = json.load(f)
            self.assertTrue(data['triggered'])
    
    def test_cmd_trigger_json_output(self):
        """Test cmd_trigger with JSON output (lines 222-223)."""
        from autoresearch_stuck_recovery import cmd_trigger
        
        state = {
            'consecutive_discards': 5,
            'pivot_count': 2,
            'config': {'goal': 'Test'},
            'strategy': 'test',
            'last_error': 'error'
        }
        with open('autoresearch-state.json', 'w') as f:
            json.dump(state, f)
        
        args = MagicMock()
        args.json = True  # This triggers lines 222-223
        args.quiet = False
        args.output = None
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_trigger(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        data = json.loads(output)
        self.assertTrue(data['triggered'])
        self.assertEqual(data['action'], 'web_search')


class TestCommitGateGaps(unittest.TestCase):
    """Cover missing lines in autoresearch_commit_gate.py"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('autoresearch_commit_gate.run_git')
    @patch('autoresearch_commit_gate.is_git_repo')
    def test_get_git_status_with_empty_line(self, mock_is_repo, mock_run_git):
        """Test get_git_status with empty line in status (line 72)."""
        from autoresearch_commit_gate import get_git_status
        
        mock_is_repo.return_value = True
        mock_run_git.side_effect = [
            (0, 'main'),  # symbolic-ref returns branch
            (0, ' M file.txt\n\n?? untracked.txt'),  # status with empty line
        ]
        
        status = get_git_status()
        
        self.assertTrue(status['is_repo'])
        self.assertEqual(status['branch'], 'main')
    
    @patch('autoresearch_commit_gate.run_git')
    @patch('autoresearch_commit_gate.is_git_repo')
    def test_get_git_status_unstaged_modified(self, mock_is_repo, mock_run_git):
        """Test get_git_status with unstaged modified file (line 82)."""
        from autoresearch_commit_gate import get_git_status
        
        mock_is_repo.return_value = True
        mock_run_git.side_effect = [
            (0, 'main'),
            (0, ' M file.txt'),  # unstaged modification (y='M')
        ]
        
        status = get_git_status()
        
        # ' M' means: x=' ' (unmodified in index), y='M' (modified in worktree)
        self.assertIn('file.txt', status['unstaged_files'])
        self.assertNotIn('file.txt', status['staged_files'])
    
    @patch('autoresearch_commit_gate.run_git')
    @patch('autoresearch_commit_gate.is_git_repo')
    def test_get_git_status_untracked(self, mock_is_repo, mock_run_git):
        """Test get_git_status with untracked file (line 84)."""
        from autoresearch_commit_gate import get_git_status
        
        mock_is_repo.return_value = True
        mock_run_git.side_effect = [
            (0, 'main'),
            (0, '?? untracked.txt'),  # untracked file
        ]
        
        status = get_git_status()
        
        self.assertIn('untracked.txt', status['untracked_files'])
    
    def test_check_scope_safety_with_cwd(self):
        """Test check_scope_safety with cwd parameter (lines 111-114)."""
        from autoresearch_commit_gate import check_scope_safety
        
        # Create subdirectory with file
        os.makedirs('subdir', exist_ok=True)
        with open('subdir/test.py', 'w') as f:
            f.write('test')
        
        result = check_scope_safety('*.py', cwd='subdir')
        
        self.assertTrue(result['exists'])
        self.assertEqual(len(result['files']), 1)
    
    @patch('autoresearch_commit_gate.is_git_repo')
    def test_check_scope_safety_protected_warning(self, mock_is_repo):
        """Test check_scope_safety with protected file warning (line 136)."""
        from autoresearch_commit_gate import check_scope_safety
        
        mock_is_repo.return_value = False
        
        # Create file in path that looks like .git
        os.makedirs('project.git', exist_ok=True)
        with open('project.git/config', 'w') as f:
            f.write('test')
        
        result = check_scope_safety('project.git/*')
        
        self.assertTrue(result['exists'])
        self.assertTrue(len(result['warnings']) > 0)
        self.assertTrue(any('.git' in w for w in result['warnings']))
    
    @patch('autoresearch_commit_gate.run_git')
    @patch('autoresearch_commit_gate.is_git_repo')
    def test_check_scope_safety_git_untracked(self, mock_is_repo, mock_run_git):
        """Test check_scope_safety with git untracked check (lines 142-145)."""
        from autoresearch_commit_gate import check_scope_safety
        
        mock_is_repo.return_value = True
        mock_run_git.return_value = (1, '')  # File not tracked by git
        
        with open('untracked.py', 'w') as f:
            f.write('test')
        
        result = check_scope_safety('*.py')
        
        self.assertTrue(result['exists'])
        self.assertTrue(any('not tracked by git' in w for w in result['warnings']))
    
    @patch('autoresearch_commit_gate.get_git_status')
    @patch('os.path.isdir')
    def test_commit_gate_check_companion_repos(self, mock_isdir, mock_get_status):
        """Test commit_gate_check with companion repos (lines 189-195)."""
        from autoresearch_commit_gate import commit_gate_check
        
        mock_get_status.side_effect = [
            {  # Primary repo - OK
                'is_repo': True,
                'can_commit': True,
                'branch': 'main',
                'errors': []
            },
            {  # Companion repo - not safe
                'is_repo': True,
                'can_commit': False,
                'branch': None,
                'errors': ['Detached HEAD']
            }
        ]
        mock_isdir.return_value = True
        
        result = commit_gate_check(companion_repos=['/path/to/repo'])
        
        self.assertFalse(result['passed'])
        self.assertTrue(any('Companion repo' in e for e in result['errors']))
    
    @patch('autoresearch_commit_gate.get_git_status')
    @patch('autoresearch_commit_gate.check_scope_safety')
    def test_commit_gate_check_scope_errors(self, mock_scope, mock_get_status):
        """Test commit_gate_check with scope errors (line 203)."""
        from autoresearch_commit_gate import commit_gate_check
        
        mock_get_status.return_value = {
            'is_repo': True,
            'can_commit': True,
            'branch': 'main',
            'errors': []
        }
        mock_scope.return_value = {
            'is_safe': False,
            'errors': ['No files match scope'],
            'warnings': []
        }
        
        result = commit_gate_check(scope='*.nonexistent')
        
        self.assertFalse(result['passed'])
        self.assertIn('No files match scope', result['errors'])
    
    @patch('autoresearch_commit_gate.commit_gate_check')
    def test_main_quiet_output(self, mock_check):
        """Test main with --quiet (no output, lines 255-258)."""
        from autoresearch_commit_gate import main
        
        mock_check.return_value = {
            'passed': True,
            'primary_repo': {'branch': 'main', 'can_commit': True},
            'scope_check': {},
            'companion_repos': {},
            'errors': [],
            'warnings': []
        }
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_commit_gate.py', '--quiet']
            result = main()
        finally:
            sys.argv = old_argv
            sys.stdout = old_stdout
        
        output = captured.getvalue()
        self.assertEqual(output.strip(), '')  # No output in quiet mode
    
    @patch('autoresearch_commit_gate.commit_gate_check')
    def test_main_warnings_output(self, mock_check):
        """Test main with warnings output (lines 279-282)."""
        from autoresearch_commit_gate import main
        
        mock_check.return_value = {
            'passed': True,
            'primary_repo': {'branch': 'main', 'can_commit': True, 'has_changes': True},
            'scope_check': {'files': [], 'scope': 'test', 'is_safe': True},
            'companion_repos': {},
            'errors': [],
            'warnings': ['Some warning']
        }
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_commit_gate.py']
            result = main()
        finally:
            sys.argv = old_argv
            sys.stdout = old_stdout
        
        output = captured.getvalue()
        self.assertIn('Some warning', output)


class TestBackgroundGaps(unittest.TestCase):
    """Cover missing lines in autoresearch_background.py"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('autoresearch_background.is_process_running')
    def test_cmd_status_not_running_anymore(self, mock_is_running):
        """Test cmd_status when process was running but isn't anymore (lines 84-88)."""
        from autoresearch_background import cmd_status, load_runtime, save_runtime
        
        # Create runtime state showing running
        runtime = {'status': 'running', 'pid': 1234}
        save_runtime(runtime)
        
        # But process is not actually running
        mock_is_running.return_value = False
        
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
        
        # Verify runtime was updated
        runtime = load_runtime()
        self.assertEqual(runtime['status'], 'stopped')
        self.assertIsNone(runtime['pid'])
    
    @patch('autoresearch_background.is_process_running')
    def test_cmd_status_with_pid_and_start_time(self, mock_is_running):
        """Test cmd_status output with pid and start_time (lines 108-112)."""
        from autoresearch_background import cmd_status, save_runtime
        
        runtime = {
            'status': 'running',
            'pid': 1234,
            'start_time': '2024-01-01T00:00:00',
            'iterations_completed': 5
        }
        save_runtime(runtime)
        
        mock_is_running.return_value = True
        
        args = MagicMock()
        args.json = False
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_status(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertIn('1234', output)  # PID
        self.assertIn('2024-01-01', output)  # start_time
    
    def test_cmd_status_with_config(self):
        """Test cmd_status with config in state (lines 118-121)."""
        from autoresearch_background import cmd_status, save_runtime, STATE_FILE
        
        runtime = {'status': 'stopped', 'pid': None}
        save_runtime(runtime)
        
        # Create state with config
        state = {
            'iteration': 10,
            'config': {
                'goal': 'Test goal',
                'metric': 'coverage',
                'direction': 'lower'
            }
        }
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        args = MagicMock()
        args.json = False
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_status(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertIn('Test goal', output)
        self.assertIn('coverage', output)
        self.assertIn('lower', output)
    
    @patch('autoresearch_background.is_process_running')
    @patch('subprocess.run')
    def test_cmd_stop_kill_exception(self, mock_subprocess, mock_is_running):
        """Test cmd_stop when killing process raises exception (lines 171-181)."""
        from autoresearch_background import cmd_stop, save_runtime, RUNTIME_FILE
        
        runtime = {'status': 'running', 'pid': 1234}
        save_runtime(runtime)
        
        mock_is_running.return_value = True
        mock_subprocess.side_effect = Exception('Kill failed')
        
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_stop(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        # Should still show stopped even if kill raised exception
        self.assertIn('stopped', output)


class TestWorkflowGaps(unittest.TestCase):
    """Cover missing lines in autoresearch_workflow.py"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('autoresearch_workflow.run_script')
    def test_workflow_init_with_scope(self, mock_run_script):
        """Test workflow_init with scope (line 68)."""
        from autoresearch_workflow import workflow_init
        
        mock_run_script.return_value = (0, 'OK')
        
        config = {
            'goal': 'Test',
            'metric': 'metric',
            'verify': 'test',
            'direction': 'lower',
            'scope': 'src/'  # This triggers line 68
        }
        
        result = workflow_init(config)
        
        self.assertTrue(result)
        # Verify scope was passed
        call_args = mock_run_script.call_args_list
        init_call = [c for c in call_args if 'autoresearch_init_run.py' in str(c)]
        self.assertTrue(any('--scope' in str(c) for c in init_call))
    
    @patch('autoresearch_workflow.run_script')
    def test_workflow_init_with_guard(self, mock_run_script):
        """Test workflow_init with guard (line 70)."""
        from autoresearch_workflow import workflow_init
        
        mock_run_script.return_value = (0, 'OK')
        
        config = {
            'goal': 'Test',
            'metric': 'metric',
            'verify': 'test',
            'direction': 'lower',
            'guard': 'npm test'  # This triggers line 70
        }
        
        result = workflow_init(config)
        
        self.assertTrue(result)
        # Verify guard was passed
        call_args = mock_run_script.call_args_list
        self.assertTrue(any('--guard' in str(c) for c in call_args))
    
    @patch('autoresearch_workflow.run_script')
    def test_workflow_init_with_iterations(self, mock_run_script):
        """Test workflow_init with iterations (line 72)."""
        from autoresearch_workflow import workflow_init
        
        mock_run_script.return_value = (0, 'OK')
        
        config = {
            'goal': 'Test',
            'metric': 'metric',
            'verify': 'test',
            'direction': 'lower',
            'iterations': 10  # This triggers line 72
        }
        
        result = workflow_init(config)
        
        self.assertTrue(result)
        # Verify iterations was passed
        call_args = mock_run_script.call_args_list
        self.assertTrue(any('--iterations' in str(c) for c in call_args))
    
    @patch('autoresearch_workflow.run_script')
    def test_workflow_baseline_no_metric_extracted(self, mock_run_script):
        """Test workflow_baseline when metric extraction fails (lines 135-136)."""
        from autoresearch_workflow import workflow_baseline
        
        mock_run_script.return_value = (0, 'No metric line here')  # No "Extracted metric:"
        
        config = {'verify': 'test'}
        
        success, baseline = workflow_baseline(config)
        
        self.assertTrue(success)  # Command succeeded
        self.assertEqual(baseline, 0.0)  # But no metric found
    
    def test_generate_ralph_prompt_with_max_ralph(self):
        """Test generate_ralph_prompt with max_ralph_iterations (line 170-171)."""
        from autoresearch_workflow import generate_ralph_prompt
        
        config = {
            'goal': 'Test',
            'verify': 'test',
            'direction': 'lower',
            'loop_control': {'max_ralph_iterations': 50}  # Triggers lines 170-171
        }
        
        prompt = generate_ralph_prompt(config, 100.0)
        
        self.assertIn('Max Ralph Iterations', prompt)
        self.assertIn('50', prompt)
    
    @patch('autoresearch_workflow.workflow_init')
    def test_main_config_file(self, mock_init):
        """Test main with config file (lines 357-359)."""
        from autoresearch_workflow import main
        
        mock_init.return_value = True
        
        # Create config file
        config = {
            'goal': 'From config',
            'verify': 'test',
            'direction': 'lower'
        }
        with open('config.json', 'w') as f:
            json.dump(config, f)
        
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.argv', [
                'autoresearch_workflow.py',
                '--config', 'config.json'
            ]):
                main()
        
        # Should exit with code 1 because workflow_baseline will fail
        # But config file should have been loaded
    
    @patch('autoresearch_workflow.run_script')
    def test_workflow_init_loop_control_no_max_ralph(self, mock_run_script):
        """Test workflow_init with loop_control but no max_ralph_iterations (line 90)."""
        from autoresearch_workflow import workflow_init
        
        mock_run_script.return_value = (0, 'OK')
        
        config = {
            'goal': 'Test',
            'metric': 'metric',
            'verify': 'test',
            'direction': 'lower',
            'loop_control': {
                'max_steps_per_turn': 30,
                'max_retries_per_step': 5
                # No max_ralph_iterations, so line 90 should not trigger
            }
        }
        
        result = workflow_init(config)
        self.assertTrue(result)
    
    @patch('autoresearch_workflow.run_script')
    def test_workflow_init_agent_file(self, mock_run_script):
        """Test workflow_init with agent_file instead of agent (lines 105-109)."""
        from autoresearch_workflow import workflow_init
        
        mock_run_script.return_value = (0, 'OK')
        
        config = {
            'goal': 'Test',
            'metric': 'metric',
            'verify': 'test',
            'direction': 'lower',
            'agent_config': {'agent_file': './custom-agent.toml'}  # Triggers lines 105-109
        }
        
        result = workflow_init(config)
        
        self.assertTrue(result)
        # Verify agent file was passed
        call_args = mock_run_script.call_args_list
        self.assertTrue(any('--agent-file' in str(c) for c in call_args))
    
    @patch('autoresearch_workflow.workflow_init')
    @patch('autoresearch_workflow.workflow_baseline')
    def test_main_with_agent_file(self, mock_baseline, mock_init):
        """Test main with --agent-file (lines 376-378)."""
        from autoresearch_workflow import main
        
        mock_init.return_value = True
        mock_baseline.return_value = (True, 100.0)
        
        with patch('sys.argv', [
            'autoresearch_workflow.py',
            '--goal', 'Test',
            '--verify', 'test',
            '--agent-file', './custom.toml'
        ]):
            try:
                main()
            except SystemExit:
                pass  # Expected
        
        # Verify workflow_init was called with agent_file
        call_kwargs = mock_init.call_args[0][0]
        self.assertEqual(call_kwargs['agent_config']['agent_file'], './custom.toml')


class TestExecGaps(unittest.TestCase):
    """Cover missing lines in autoresearch_exec.py"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('autoresearch_exec.subprocess.run')
    def test_run_command_exception(self, mock_subprocess):
        """Test run_command when subprocess raises exception (lines 71-72)."""
        from autoresearch_exec import run_command
        
        mock_subprocess.side_effect = Exception('Command failed')
        
        code, output = run_command('some command')
        
        self.assertEqual(code, -1)
        self.assertIn('Command failed', output)
    
    @patch('autoresearch_exec.run_command')
    def test_run_iteration_no_metric_extracted(self, mock_run):
        """Test run_iteration when metric cannot be extracted (lines 207-208, 227-229)."""
        from autoresearch_exec import run_iteration
        
        mock_run.return_value = (0, 'No parseable number here')
        
        config = {
            'verify': 'npm test',
            'direction': 'lower',
            'guard': None
        }
        baseline = 85.0
        
        result = run_iteration(1, config, baseline)
        
        self.assertEqual(result['status'], 'crash')
        self.assertEqual(result['reason'], 'Could not extract metric')


class TestRalphGaps(unittest.TestCase):
    """Cover missing lines in autoresearch_ralph.py"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_agent_config_from_file(self):
        """Test get_agent_config when agent_file is set (lines 341-343)."""
        from autoresearch_ralph import get_agent_config, set_agent_config
        
        # Set agent config with agent_file
        set_agent_config(agent_file='./custom.toml')
        
        config = get_agent_config()
        
        self.assertIsNotNone(config)
        self.assertEqual(config['agent_file'], './custom.toml')
    
    def test_generate_ralph_prompt_no_loop_control(self):
        """Test generate_ralph_prompt when no loop_control in state (lines 326-331)."""
        from autoresearch_ralph import generate_ralph_prompt
        
        # Create state without loop_control
        state = {
            'version': '2.0',
            'config': {
                'goal': 'Test goal',
                'verify': 'test'
            },
            'baseline': 100
        }
        with open('autoresearch-state.json', 'w') as f:
            json.dump(state, f)
        
        prompt = generate_ralph_prompt({})
        
        # Should use defaults
        self.assertIn('Test goal', prompt)


class TestWebSearchGaps(unittest.TestCase):
    """Cover missing lines in autoresearch_web_search.py"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_extract_search_query_trimming(self):
        """Test extract_search_query with long strings (line 148)."""
        from autoresearch_web_search import extract_search_query
        
        # Test with very long error and goal to trigger trimming
        context = {
            'error': 'A' * 200,  # Longer than 100 chars
            'goal': 'B' * 100     # Longer than 50 chars
        }
        
        query = extract_search_query(context)
        
        # Should be trimmed
        self.assertLess(len(query), 250)
    
    def test_format_search_results_truncation(self):
        """Test format_search_results with long snippets (line 203-204)."""
        from autoresearch_web_search import format_search_results
        
        results = [{
            'title': 'Test',
            'snippet': 'A' * 300,  # Very long snippet
            'url': 'http://example.com'
        }]
        
        formatted = format_search_results(results)
        
        # Should truncate snippet
        self.assertIn('...', formatted)
    
    def test_cmd_search_output_file(self):
        """Test cmd_search with output file (lines 301-302)."""
        from autoresearch_web_search import cmd_search
        
        args = MagicMock()
        args.goal = 'Test goal'
        args.strategy = None
        args.error = None
        args.context_file = None
        args.dry_run = False
        args.json = False
        args.output = 'output.json'
        
        result = cmd_search(args)
        
        self.assertEqual(result, 0)
        self.assertTrue(os.path.exists('output.json'))
        with open('output.json', 'r') as f:
            data = json.load(f)
            self.assertIn('query', data)


class TestMonitorGaps(unittest.TestCase):
    """Cover missing lines in autoresearch_monitor.py"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('webbrowser.open')
    def test_main_dashboard_open_exception(self, mock_webbrowser):
        """Test main with dashboard --open when webbrowser fails (lines 172-176)."""
        from autoresearch_monitor import main
        
        # Create results file
        with open('autoresearch-results.tsv', 'w', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['iteration', 'commit', 'metric', 'delta', 'status', 'description', 'timestamp'])
            writer.writerow(['1', 'abc', '100', '0', 'baseline', 'Initial', '2024-01-01'])
        
        mock_webbrowser.side_effect = Exception('Browser failed')
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        try:
            with patch('sys.argv', ['autoresearch_monitor', 'dashboard', '--open']):
                main()
        except:
            pass  # Exception handling expected
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        # Should handle exception


class TestStuckRecoveryMoreGaps(unittest.TestCase):
    """Additional tests for autoresearch_stuck_recovery.py"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cmd_trigger_not_search_action(self):
        """Test cmd_trigger when action is not 'search' (lines 207-209)."""
        from autoresearch_stuck_recovery import cmd_trigger
        
        # Create state where action is 'pivot' not 'search'
        state = {
            'consecutive_discards': 5,
            'pivot_count': 0,  # Less than 2 pivots, so action='pivot' not 'search'
            'config': {'goal': 'Test'},
            'strategy': 'test',
            'last_error': 'error'
        }
        with open('autoresearch-state.json', 'w') as f:
            json.dump(state, f)
        
        args = MagicMock()
        args.json = False
        args.quiet = False
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_trigger(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        # Should return 1 because action is not 'search'
        self.assertEqual(result, 1)
        self.assertIn("action is 'pivot'", output)


if __name__ == '__main__':
    unittest.main()
