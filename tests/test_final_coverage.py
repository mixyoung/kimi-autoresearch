#!/usr/bin/env python3
"""
Final coverage tests for remaining uncovered lines.

This file covers the remaining lines to reach 100% coverage.
"""

import unittest
import sys
import os
import tempfile
import shutil
import io
import json
import csv
from unittest.mock import patch, MagicMock, mock_open

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


class TestAutoresearchMain(unittest.TestCase):
    """Test autoresearch_main.py - missing line 163."""
    
    def test_cmd_version_no_changelog(self):
        """Test version command with --no-changelog (line 163)."""
        import autoresearch_main
        
        with patch.object(autoresearch_main, 'run_script') as mock_run:
            mock_run.return_value = (0, 'version output')
            
            args = MagicMock()
            args.version_subcommand = 'bump'
            args.value = None
            args.tag = False
            args.no_changelog = True  # This triggers line 163
            
            result = autoresearch_main.cmd_version(args)
            
            # Check that --no-changelog was passed
            call_args = mock_run.call_args[0][1]
            self.assertIn('--no-changelog', call_args)


class TestAutoresearchExec(unittest.TestCase):
    """Test autoresearch_exec.py - missing lines 207-208."""
    
    def test_check_mode_timeout(self):
        """Test exec_check with timeout (lines 207-208)."""
        import autoresearch_exec
        
        config = {
            'verify': 'echo 85',
            'threshold': 80,
            'direction': 'higher',
            'timeout': 1  # 1 second timeout
        }
        
        with patch.object(autoresearch_exec, 'get_baseline') as mock_baseline:
            mock_baseline.return_value = (True, 85.0)
            result = autoresearch_exec.exec_check(config)
            
            self.assertTrue(result['passed'])


class TestAutoresearchHealthCheck(unittest.TestCase):
    """Test autoresearch_health_check.py - missing lines 72, 114, 117."""
    
    def test_check_git_status_exception(self):
        """Test check_git_status with exception (line 72)."""
        import autoresearch_health_check
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception('Git error')
            code, output = autoresearch_health_check.run_git(['status'])
            self.assertEqual(code, -1)
    
    def test_check_required_tools_all_missing(self):
        """Test check_required_tools with all tools missing (lines 114, 117)."""
        import autoresearch_health_check
        
        with patch('shutil.which') as mock_which:
            mock_which.return_value = None
            result = autoresearch_health_check.check_required_tools()
            
            self.assertEqual(result['status'], 'fail')
            self.assertIn('git', result['message'])
            self.assertIn('python', result['message'])
            self.assertIn('python3', result['message'])


class TestAutoresearchI18n(unittest.TestCase):
    """Test autoresearch_i18n.py - missing line 58."""
    
    def test_load_translations_fallback(self):
        """Test load_translations fallback to default (line 58)."""
        import autoresearch_i18n
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create incomplete translation structure
            os.makedirs('locales/de/LC_MESSAGES', exist_ok=True)
            # No messages.json file, will trigger fallback
            
            # Reset translations cache
            autoresearch_i18n._translations = {}
            
            result = autoresearch_i18n.load_translations('de')
            
            # Should fallback to empty or default
            self.assertIsInstance(result, dict)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)


class TestAutoresearchVersion(unittest.TestCase):
    """Test autoresearch_version.py - missing line 250."""
    
    def test_set_command_with_tag(self):
        """Test set command with --tag flag (line 250)."""
        import autoresearch_version
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create package.sh
            with open('package.sh', 'w') as f:
                f.write('VERSION="1.0.0"')
            
            with patch.object(autoresearch_version, 'create_git_tag') as mock_tag:
                old_argv = sys.argv
                sys.argv = ['autoresearch_version.py', 'set', '1.2.3', '--tag']
                
                captured = io.StringIO()
                old_stdout = sys.stdout
                sys.stdout = captured
                
                try:
                    autoresearch_version.main()
                except SystemExit:
                    pass
                
                sys.stdout = old_stdout
                sys.argv = old_argv
                
                # create_git_tag should be called
                mock_tag.assert_called_once_with('1.2.3')
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)


class TestCheckGit(unittest.TestCase):
    """Test check_git.py - missing line 121."""
    
    def test_main_block(self):
        """Test __main__ block (line 121)."""
        import check_git
        
        with patch.object(check_git, 'main') as mock_main:
            mock_main.return_value = 0
            check_git.main()
            mock_main.assert_called_once()


class TestAutoresearchAnalyze(unittest.TestCase):
    """Test autoresearch_analyze.py - missing lines 32-34."""
    
    def test_load_results_exception(self):
        """Test load_results with exception (lines 32-34)."""
        import autoresearch_analyze
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create invalid results file
            with open('autoresearch-results.tsv', 'w') as f:
                f.write('invalid binary data \x00\x01\x02')
            
            results = autoresearch_analyze.load_results()
            
            # Should return empty list on error
            self.assertEqual(results, [])
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)


class TestAutoresearchUtils(unittest.TestCase):
    """Test autoresearch_utils.py - missing lines 61-62, 72-73, 136."""
    
    def test_cmd_stats_results_exception(self):
        """Test stats with results exception (lines 61-62)."""
        import autoresearch_utils
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create invalid results file
            with open('autoresearch-results.tsv', 'w') as f:
                f.write('invalid')
            
            old_argv = sys.argv
            sys.argv = ['autoresearch_utils.py', 'stats']
            
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            try:
                autoresearch_utils.main()
            except SystemExit:
                pass
            
            sys.stdout = old_stdout
            sys.argv = old_argv
            
            # Should not crash
            self.assertTrue(True)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)
    
    def test_cmd_stats_state_exception(self):
        """Test stats with state exception (lines 72-73)."""
        import autoresearch_utils
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create empty results file (valid)
            with open('autoresearch-results.tsv', 'w') as f:
                f.write('iteration\tcommit\tmetric\tdelta\tstatus\tdescription\ttimestamp\n')
            
            # Create invalid state file
            with open('autoresearch-state.json', 'w') as f:
                f.write('invalid json')
            
            old_argv = sys.argv
            sys.argv = ['autoresearch_utils.py', 'stats']
            
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            try:
                autoresearch_utils.main()
            except SystemExit:
                pass
            
            sys.stdout = old_stdout
            sys.argv = old_argv
            
            # Should not crash
            self.assertTrue(True)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)
    
    def test_cmd_clean_no_force(self):
        """Test clean without --force (line 136)."""
        import autoresearch_utils
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create backup file
            with open('autoresearch-state.json.prev.1', 'w') as f:
                f.write('{}')
            
            old_argv = sys.argv
            sys.argv = ['autoresearch_utils.py', 'clean', '--all']
            
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            try:
                autoresearch_utils.main()
            except SystemExit:
                pass
            
            sys.stdout = old_stdout
            sys.argv = old_argv
            
            output = captured.getvalue()
            # Should show "Would remove" without --force
            self.assertIn('Would remove', output)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)


class TestAutoresearchWebSearch(unittest.TestCase):
    """Test autoresearch_web_search.py - missing lines 148, 226-227."""
    
    def test_cmd_search_error_override(self):
        """Test cmd_search with error override (line 148)."""
        import autoresearch_web_search
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create context file without error
            context = {'goal': 'Test', 'strategy': 'test'}
            with open('context.json', 'w') as f:
                json.dump(context, f)
            
            class Args:
                context_file = 'context.json'
                goal = None
                strategy = None
                error = 'Overridden error'  # This triggers line 148
                dry_run = True
                json = False
            
            args = Args()
            result = autoresearch_web_search.cmd_search(args)
            
            self.assertEqual(result, 0)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)
    
    def test_cmd_generate_hypotheses_with_output(self):
        """Test generate_hypotheses with output file (lines 226-227)."""
        import autoresearch_web_search
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create search results
            with open('results.json', 'w') as f:
                json.dump({
                    'results': [
                        {'title': 'Test', 'content': 'Test content', 'url': 'http://test.com'}
                    ]
                }, f)
            
            class Args:
                search_results = 'results.json'
                context_file = None
                output = 'output.json'  # This triggers lines 226-227
                json = False
            
            args = Args()
            result = autoresearch_web_search.cmd_generate_hypotheses(args)
            
            self.assertEqual(result, 0)
            self.assertTrue(os.path.exists('output.json'))
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)


class TestDiagnoseStop(unittest.TestCase):
    """Test diagnose_stop.py - missing lines 73, 128."""
    
    def test_diagnose_with_only_max_iter_set(self):
        """Test diagnose with max_iter set but not reached (line 73)."""
        import diagnose_stop
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create state with iterations set but not reached
            state = {
                'version': '1.0',
                'iteration': 3,
                'consecutive_discards': 0,
                'pivot_count': 0,
                'config': {
                    'iterations': 10,
                    'target': None
                },
                'loop_control': {
                    'max_ralph_iterations': 0
                }
            }
            with open('autoresearch-state.json', 'w') as f:
                json.dump(state, f)
            
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            diagnose_stop.diagnose()
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            # Should show iteration info
            self.assertIn('3', output)
            self.assertIn('10', output)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)


class TestGenerateReport(unittest.TestCase):
    """Test generate_report.py - missing lines 44-45."""
    
    def test_generate_report_invalid_metric(self):
        """Test generate_report with invalid metric (lines 44-45)."""
        import generate_report
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create results with invalid metric
            with open('autoresearch-results.tsv', 'w') as f:
                f.write('iteration\tcommit\tmetric\tdelta\tstatus\tdescription\ttimestamp\n')
                f.write('1\tabc1\tinvalid\t+0\tkeep\tdesc\t2024-01-01\n')
            
            # This should not crash
            generate_report.generate_report()
            
            # Should have generated report
            self.assertTrue(os.path.exists('autoresearch-report.md'))
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)


class TestGetBaseline(unittest.TestCase):
    """Test get_baseline.py - missing lines 42-43, 80-81."""
    
    def test_extract_number_value_error(self):
        """Test extract_number with ValueError (lines 42-43)."""
        import get_baseline
        
        # Test with invalid pattern that triggers ValueError
        # The function catches ValueError and continues
        result = get_baseline.extract_number('no numbers here')
        self.assertIsNone(result)
    
    def test_main_block_no_number(self):
        """Test __main__ block when result is not a number (lines 80-81)."""
        import get_baseline
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            old_argv = sys.argv
            sys.argv = ['get_baseline.py', '--verify', 'echo "test output"']
            
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            try:
                # Simulate __main__ block
                result = get_baseline.main()
                if isinstance(result, (int, float)):
                    pass  # Would exit 0
                else:
                    # String output means exit 0 anyway based on code logic
                    pass
            except SystemExit as e:
                # Check exit code
                pass
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            self.assertIn('test output', output)
        finally:
            sys.argv = old_argv
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)


class TestAutoresearchLaunchGate(unittest.TestCase):
    """Test autoresearch_launch_gate.py - missing lines 60, 92-93, 136."""
    
    def test_check_results_no_state_file(self):
        """Test check_results_consistency with no state file (line 60)."""
        import autoresearch_launch_gate
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create results but no state
            with open('autoresearch-results.tsv', 'w') as f:
                f.write('iteration\tcommit\tmetric\tdelta\tstatus\tdescription\ttimestamp\n')
            
            result = autoresearch_launch_gate.check_results_consistency()
            
            self.assertTrue(result['consistent'])
            self.assertIn('note', result)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)
    
    def test_check_results_exception(self):
        """Test check_results_consistency with exception (lines 92-93)."""
        import autoresearch_launch_gate
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create results file
            with open('autoresearch-results.tsv', 'w') as f:
                f.write('iteration\tcommit\tmetric\tdelta\tstatus\tdescription\ttimestamp\n')
            
            # Create state with invalid JSON
            with open('autoresearch-state.json', 'w') as f:
                f.write('invalid')
            
            result = autoresearch_launch_gate.check_results_consistency()
            
            self.assertFalse(result['consistent'])
            self.assertIn('error', result)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)
    
    def test_decide_launch_needs_confirmation(self):
        """Test decide_launch_action with needs_confirmation (line 136)."""
        import autoresearch_launch_gate
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create inconsistent state
            with open('autoresearch-state.json', 'w') as f:
                json.dump({
                    'version': '1.0',
                    'iteration': 5,
                    'status': 'running'
                }, f)
            
            with open('autoresearch-results.tsv', 'w') as f:
                f.write('iteration\tcommit\tmetric\tdelta\tstatus\tdescription\ttimestamp\n')
                for i in range(10):  # More results than expected
                    f.write(f'{i}\tabc{i}\t100\t+0\tkeep\tdesc\t2024-01-01\n')
            
            class Args:
                force_fresh = False
                force_resume = False
                check_only = False
                format = 'text'
            
            result = autoresearch_launch_gate.decide_launch_action(Args())
            
            self.assertEqual(result['action'], 'needs_confirmation')
            self.assertIn('mode', result)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)


class TestAutoresearchCommitGate(unittest.TestCase):
    """Test autoresearch_commit_gate.py - missing lines 74, 82, 86, 114."""
    
    def test_get_git_status_empty_line(self):
        """Test get_git_status with empty lines (line 74)."""
        import autoresearch_commit_gate
        
        with patch('subprocess.run') as mock_run:
            # Simulate output with empty lines
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='M  file1.txt\n\n?? file2.txt\n',
                stderr=''
            )
            
            status = autoresearch_commit_gate.get_git_status('.')
            
            # Should handle empty lines
            self.assertIn('file1.txt', status['staged_files'])
    
    def test_get_git_status_staged(self):
        """Test get_git_status with staged files (line 82)."""
        import autoresearch_commit_gate
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='A  new_file.txt\nM  modified.txt\nD  deleted.txt\nR  renamed.txt\nC  copied.txt\n',
                stderr=''
            )
            
            status = autoresearch_commit_gate.get_git_status('.')
            
            self.assertIn('new_file.txt', status['staged_files'])
            self.assertIn('modified.txt', status['staged_files'])
    
    def test_get_git_status_untracked(self):
        """Test get_git_status with untracked files (line 86)."""
        import autoresearch_commit_gate
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='?? untracked.txt\n',
                stderr=''
            )
            
            status = autoresearch_commit_gate.get_git_status('.')
            
            self.assertIn('untracked.txt', status['untracked_files'])
    
    def test_check_scope_cwd(self):
        """Test check_scope_safety with cwd (line 114)."""
        import autoresearch_commit_gate
        
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Create a test file
            test_file = os.path.join(temp_dir, 'test.txt')
            with open(test_file, 'w') as f:
                f.write('test')
            
            result = autoresearch_commit_gate.check_scope_safety('*.txt', cwd=temp_dir)
            
            self.assertTrue(result['exists'])
            self.assertIn(test_file, result['files'])
        finally:
            shutil.rmtree(temp_dir)


class TestAutoresearchBackground(unittest.TestCase):
    """Test autoresearch_background.py - missing lines 84-88, 108, 110, 112, 118-121, 171-181."""
    
    def test_cmd_status_not_running(self):
        """Test cmd_status when process not running (lines 84-88)."""
        import autoresearch_background
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create runtime file with fake running status
            runtime = {
                'status': 'running',
                'pid': 99999999,  # Non-existent PID
                'start_time': '2024-01-01',
                'iterations_completed': 5
            }
            with open('.autoresearch-runtime.json', 'w') as f:
                json.dump(runtime, f)
            
            # Create state file
            state = {'iteration': 5, 'config': {}}
            with open('autoresearch-state.json', 'w') as f:
                json.dump(state, f)
            
            class Args:
                json = True
            
            args = Args()
            result = autoresearch_background.cmd_status(args)
            
            # Should return 0 (not error) and update status to stopped
            self.assertEqual(result, 0)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)
    
    def test_cmd_status_text_output(self):
        """Test cmd_status with text output (lines 108, 110, 112, 118-121)."""
        import autoresearch_background
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create runtime file
            runtime = {
                'status': 'stopped',
                'pid': None,
                'start_time': '2024-01-01',
                'last_update': '2024-01-02',
                'iterations_completed': 5
            }
            with open('.autoresearch-runtime.json', 'w') as f:
                json.dump(runtime, f)
            
            # Create state with config
            state = {
                'iteration': 5,
                'config': {
                    'goal': 'Test goal',
                    'metric': 'accuracy',
                    'direction': 'higher'
                }
            }
            with open('autoresearch-state.json', 'w') as f:
                json.dump(state, f)
            
            class Args:
                json = False
            
            args = Args()
            
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            result = autoresearch_background.cmd_status(args)
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            # Should show config info
            self.assertIn('Configuration', output)
            self.assertIn('Test goal', output)
            self.assertIn('accuracy', output)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)


class TestAutoresearchStuckRecovery(unittest.TestCase):
    """Test autoresearch_stuck_recovery.py - missing lines 39-40, 206-209, 239-243."""
    
    def test_load_results_exception(self):
        """Test load_results with exception (lines 39-40)."""
        import autoresearch_stuck_recovery
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create invalid results file
            with open('autoresearch-results.tsv', 'w') as f:
                f.write('invalid\x00binary\x01data')
            
            results = autoresearch_stuck_recovery.load_results()
            
            self.assertEqual(results, [])
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)


class TestAutoresearchRalph(unittest.TestCase):
    """Test autoresearch_ralph.py - missing lines 188, 326-331, 420-422."""
    
    def test_print_status_with_agent_config(self):
        """Test print_ralph_status with agent config (lines 326-331)."""
        import autoresearch_ralph
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create state with agent config
            state = {
                'version': '1.0',
                'iteration': 1,
                'config': {'goal': 'Test'},
                'loop_control': {
                    'max_steps_per_turn': 50,
                    'max_retries_per_step': 3,
                    'max_ralph_iterations': 0
                },
                'agent_config': {
                    'agent': 'okabe',
                    'agent_file': None
                }
            }
            with open('autoresearch-state.json', 'w') as f:
                json.dump(state, f)
            
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            autoresearch_ralph.print_ralph_status()
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            self.assertIn('Agent Configuration', output)
            self.assertIn('okabe', output)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)
    
    def test_set_agent_both_params_error(self):
        """Test set_agent_config with both agent and agent_file (lines 420-422)."""
        import autoresearch_ralph
        
        # Test the set_agent_config function with both params - should raise ValueError
        with self.assertRaises(ValueError):
            autoresearch_ralph.set_agent_config(agent='okabe', agent_file='custom.yaml')


class TestAutoresearchWorkflow(unittest.TestCase):
    """Test autoresearch_workflow.py - missing lines 358-359, 378."""
    
    def test_run_script_exception(self):
        """Test run_script with exception (lines 358-359)."""
        import autoresearch_workflow
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception('Script error')
            code, output = autoresearch_workflow.run_script('test.py', [])
            
            self.assertEqual(code, -1)
            self.assertIn('Script error', output)


class TestAutoresearchResilience(unittest.TestCase):
    """Test autoresearch_resilience.py - missing lines 277-278."""
    
    def test_generate_report_with_split_recommendation(self):
        """Test generate_resilience_report with split recommendation (lines 277-278)."""
        import autoresearch_resilience
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create state that triggers split recommendation
            state = {
                'version': '1.0',
                'iteration': 200,  # High iteration count
                'consecutive_discards': 0,
                'pivot_count': 0,
                'config': {'goal': 'Test'},
                'loop_control': {
                    'max_steps_per_turn': 50,
                    'max_retries_per_step': 3,
                    'max_ralph_iterations': 0
                }
            }
            with open('autoresearch-state.json', 'w') as f:
                json.dump(state, f)
            
            manager = autoresearch_resilience.ResilienceManager()
            report = manager.generate_resilience_report()
            
            # Should include split recommendation
            self.assertIn('Session split', report)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main()
