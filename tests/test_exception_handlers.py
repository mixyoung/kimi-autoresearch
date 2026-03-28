#!/usr/bin/env python3
"""
Tests for exception handlers and edge cases to achieve 100% coverage.
"""

import unittest
import sys
import os
import tempfile
import shutil
import json
from unittest.mock import patch, MagicMock
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


class TestAutoresearchHealthCheckExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_health_check.py."""
    
    def test_run_git_exception_line_72(self):
        """Test run_git exception handling (line 72)."""
        import autoresearch_health_check
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception('Git failed')
            code, output = autoresearch_health_check.run_git(['status'])
            self.assertEqual(code, -1)
            self.assertIn('Git failed', output)
    
    def test_check_disk_space_exception_lines_114_117(self):
        """Test check_disk_space exception handling (lines 114, 117)."""
        import autoresearch_health_check
        
        with patch('shutil.disk_usage') as mock_disk:
            mock_disk.side_effect = Exception('Disk check failed')
            result = autoresearch_health_check.check_disk_space()
            
            self.assertEqual(result['status'], 'warn')
            self.assertIn('Could not check disk space', result['message'])


class TestAutoresearchI18nExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_i18n.py."""
    
    def test_load_translations_exception_lines_53_60(self):
        """Test load_translations exception handling (lines 53-60)."""
        import autoresearch_i18n
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create locales directory structure with invalid JSON
            os.makedirs('locales/en/LC_MESSAGES', exist_ok=True)
            with open('locales/en/LC_MESSAGES/messages.json', 'w') as f:
                f.write('invalid json {{{')
            
            # Reset cache
            autoresearch_i18n._translations = {}
            
            captured_stderr = StringIO()
            old_stderr = sys.stderr
            sys.stderr = captured_stderr
            
            try:
                result = autoresearch_i18n.load_translations('en')
            finally:
                sys.stderr = old_stderr
            
            # Should handle exception and return empty dict or fallback
            self.assertIsInstance(result, dict)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)
    
    def test_init_locale_exception_lines_161_162(self):
        """Test init_locale exception handling (lines 161-162)."""
        import autoresearch_i18n
        
        with patch('builtins.open') as mock_open:
            mock_open.side_effect = Exception('Read error')
            
            # Reset locale
            old_locale = autoresearch_i18n._current_locale
            autoresearch_i18n._current_locale = autoresearch_i18n.DEFAULT_LOCALE
            
            try:
                # Should not raise exception
                autoresearch_i18n.init_locale()
            finally:
                autoresearch_i18n._current_locale = old_locale


class TestAutoresearchUtilsExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_utils.py."""
    
    def test_run_command_exception_lines_61_62(self):
        """Test run_command exception handling (lines 61-62)."""
        import autoresearch_utils
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception('Command failed')
            code, output = autoresearch_utils.run_command('test')
            self.assertEqual(code, -1)
            self.assertIn('Command failed', output)
    
    def test_run_command_timeout_lines_72_73(self):
        """Test run_command timeout handling (lines 72-73)."""
        import autoresearch_utils
        from subprocess import TimeoutExpired
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = TimeoutExpired(cmd='test', timeout=60)
            code, output = autoresearch_utils.run_command('test')
            self.assertEqual(code, -1)
            self.assertIn('timed out', output.lower())


class TestAutoresearchWebSearchExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_web_search.py."""
    
    def test_cmd_search_context_file_lines_148(self):
        """Test cmd_search with context file (line 148)."""
        import autoresearch_web_search
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create context file
            context = {'goal': 'Test', 'error': 'Error'}
            with open('context.json', 'w') as f:
                json.dump(context, f)
            
            class Args:
                context_file = 'context.json'
                goal = None
                strategy = None
                error = None
                dry_run = True
                json = False
            
            result = autoresearch_web_search.cmd_search(Args())
            self.assertEqual(result, 0)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)
    
    def test_cmd_generate_hypotheses_context_lines_226_227(self):
        """Test cmd_generate_hypotheses with context file (lines 226-227)."""
        import autoresearch_web_search
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create files
            with open('results.json', 'w') as f:
                json.dump({'results': []}, f)
            with open('context.json', 'w') as f:
                json.dump({'goal': 'Test'}, f)
            
            class Args:
                search_results = 'results.json'
                context_file = 'context.json'
                output = None
                json = True
            
            result = autoresearch_web_search.cmd_generate_hypotheses(Args())
            self.assertEqual(result, 0)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)
    
    def test_cmd_check_and_search_verbose_line_289(self):
        """Test cmd_check_and_search with verbose (line 289)."""
        import autoresearch_web_search
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create state file
            state = {'consecutive_discards': 2, 'pivot_count': 0}
            with open('autoresearch-state.json', 'w') as f:
                json.dump(state, f)
            
            class Args:
                state_file = None
                output = None
                json = False
                force = False
                verbose = True
            
            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            try:
                result = autoresearch_web_search.cmd_check_and_search(Args())
            finally:
                sys.stdout = old_stdout
            
            output = captured.getvalue()
            self.assertEqual(result, 0)
            self.assertIn('2', output)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)
    
    def test_cmd_check_and_search_output_lines_301_302(self):
        """Test cmd_check_and_search with output file (lines 301-302)."""
        import autoresearch_web_search
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create state file that triggers search
            state = {
                'consecutive_discards': 5,
                'pivot_count': 2,
                'config': {'goal': 'Test'},
                'strategy': 'debug',
                'last_error': 'error'
            }
            with open('autoresearch-state.json', 'w') as f:
                json.dump(state, f)
            
            class Args:
                state_file = None
                output = 'output.json'
                json = False
                force = False
                verbose = False
            
            result = autoresearch_web_search.cmd_check_and_search(Args())
            self.assertEqual(result, 0)
            self.assertTrue(os.path.exists('output.json'))
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)


class TestAutoresearchBackgroundExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_background.py."""
    
    def test_is_process_running_unix_exception_lines_176_179(self):
        """Test is_process_running exception on Unix (lines 176-179)."""
        import autoresearch_background
        
        with patch('sys.platform', 'linux'):
            with patch('os.kill') as mock_kill:
                mock_kill.side_effect = OSError('Process not found')
                result = autoresearch_background.is_process_running(1234)
                self.assertFalse(result)


class TestAutoresearchWorkflowExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_workflow.py."""
    
    def test_run_script_exception_lines_358_359(self):
        """Test run_script exception handling (lines 358-359)."""
        import autoresearch_workflow
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception('Script failed')
            code, output = autoresearch_workflow.run_script('test.py', [])
            self.assertEqual(code, -1)
            self.assertIn('Script failed', output)


class TestAutoresearchParallelExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_parallel.py."""
    
    def test_run_git_exception_lines_93_94(self):
        """Test run_git exception handling (lines 93-94)."""
        import autoresearch_parallel
        
        exp = autoresearch_parallel.ParallelExperiment('.')
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception('Git error')
            code, output = exp.run_git(['status'])
            self.assertEqual(code, -1)
            self.assertIn('Git error', output)


class TestAutoresearchCommitGateExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_commit_gate.py."""
    
    def test_run_git_exception_line_74(self):
        """Test run_git exception handling (line 74)."""
        import autoresearch_commit_gate
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception('Git failed')
            code, output = autoresearch_commit_gate.run_git(['status'])
            self.assertEqual(code, -1)
            self.assertIn('Git failed', output)


class TestAutoresearchAnalyzeExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_analyze.py."""
    
    def test_load_results_exception_lines_32_34(self):
        """Test load_results exception handling (lines 32-34)."""
        import autoresearch_analyze
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create invalid results file
            with open('autoresearch-results.tsv', 'w') as f:
                f.write('invalid\ttsv\n')
            
            captured_stderr = StringIO()
            old_stderr = sys.stderr
            sys.stderr = captured_stderr
            
            try:
                results = autoresearch_analyze.load_results()
            finally:
                sys.stderr = old_stderr
            
            self.assertEqual(results, [])
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)


class TestStateManagerExceptions(unittest.TestCase):
    """Test exception handlers in state_manager.py."""
    
    def test_load_state_json_error_lines_128_129(self):
        """Test load_state JSON decode error (lines 128-129)."""
        import state_manager
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create invalid JSON file
            with open('autoresearch-state.json', 'w') as f:
                f.write('invalid json')
            
            state = state_manager.load_state()
            
            # Should return default state
            self.assertIn('version', state)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)


class TestAutoresearchRalphExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_ralph.py."""
    
    def test_main_no_command_lines_407_408(self):
        """Test main with no command (lines 407-408)."""
        import autoresearch_ralph
        
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_ralph.py']
            
            with self.assertRaises(SystemExit) as cm:
                autoresearch_ralph.main()
            
            self.assertEqual(cm.exception.code, 1)
        finally:
            sys.argv = old_argv


class TestAutoresearchResilienceExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_resilience.py."""
    
    def test_main_no_command_lines_277_278(self):
        """Test main with no command (lines 277-278)."""
        import autoresearch_resilience
        
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_resilience.py']
            
            # Should print help and not raise SystemExit
            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            try:
                result = autoresearch_resilience.main()
            finally:
                sys.stdout = old_stdout
            
            output = captured.getvalue()
            self.assertIn('usage', output.lower())
        finally:
            sys.argv = old_argv


class TestAutoresearchMonitorExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_monitor.py."""
    
    def test_load_results_exception_lines_154_157(self):
        """Test load_results exception handling (lines 154-157)."""
        import autoresearch_monitor
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create invalid results file
            with open('autoresearch-results.tsv', 'w') as f:
                f.write('invalid')
            
            tracker = autoresearch_monitor.ProgressTracker()
            results = tracker.load_results()
            
            self.assertEqual(results, [])
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main()
#!/usr/bin/env python3
"""
Tests for exception handlers and edge cases to achieve 100% coverage.
"""

import unittest
import sys
import os
import tempfile
import shutil
import json
from unittest.mock import patch, MagicMock
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


class TestAutoresearchHealthCheckExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_health_check.py."""
    
    def test_run_git_exception_line_72(self):
        """Test run_git exception handling (line 72)."""
        import autoresearch_health_check
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception('Git failed')
            code, output = autoresearch_health_check.run_git(['status'])
            self.assertEqual(code, -1)
            self.assertIn('Git failed', output)
    
    def test_check_disk_space_exception_lines_114_117(self):
        """Test check_disk_space exception handling (lines 114, 117)."""
        import autoresearch_health_check
        
        with patch('shutil.disk_usage') as mock_disk:
            mock_disk.side_effect = Exception('Disk check failed')
            result = autoresearch_health_check.check_disk_space()
            
            self.assertEqual(result['status'], 'warn')
            self.assertIn('Could not check disk space', result['message'])


class TestAutoresearchI18nExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_i18n.py."""
    
    def test_load_translations_exception_lines_53_60(self):
        """Test load_translations exception handling (lines 53-60)."""
        import autoresearch_i18n
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create locales directory structure with invalid JSON
            os.makedirs('locales/en/LC_MESSAGES', exist_ok=True)
            with open('locales/en/LC_MESSAGES/messages.json', 'w') as f:
                f.write('invalid json {{{')
            
            # Reset cache
            autoresearch_i18n._translations = {}
            
            captured_stderr = StringIO()
            old_stderr = sys.stderr
            sys.stderr = captured_stderr
            
            try:
                result = autoresearch_i18n.load_translations('en')
            finally:
                sys.stderr = old_stderr
            
            # Should handle exception and return empty dict or fallback
            self.assertIsInstance(result, dict)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)
    
    def test_init_locale_exception_lines_161_162(self):
        """Test init_locale exception handling (lines 161-162)."""
        import autoresearch_i18n
        
        with patch('builtins.open') as mock_open:
            mock_open.side_effect = Exception('Read error')
            
            # Reset locale
            old_locale = autoresearch_i18n._current_locale
            autoresearch_i18n._current_locale = autoresearch_i18n.DEFAULT_LOCALE
            
            try:
                # Should not raise exception
                autoresearch_i18n.init_locale()
            finally:
                autoresearch_i18n._current_locale = old_locale


class TestAutoresearchUtilsExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_utils.py."""
    
    def test_run_command_exception_lines_61_62(self):
        """Test run_command exception handling (lines 61-62)."""
        import autoresearch_utils
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception('Command failed')
            code, output = autoresearch_utils.run_command('test')
            self.assertEqual(code, -1)
            self.assertIn('Command failed', output)
    
    def test_run_command_timeout_lines_72_73(self):
        """Test run_command timeout handling (lines 72-73)."""
        import autoresearch_utils
        from subprocess import TimeoutExpired
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = TimeoutExpired(cmd='test', timeout=60)
            code, output = autoresearch_utils.run_command('test')
            self.assertEqual(code, -1)
            self.assertIn('timed out', output.lower())


class TestAutoresearchWebSearchExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_web_search.py."""
    
    def test_cmd_search_context_file_lines_148(self):
        """Test cmd_search with context file (line 148)."""
        import autoresearch_web_search
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create context file
            context = {'goal': 'Test', 'error': 'Error'}
            with open('context.json', 'w') as f:
                json.dump(context, f)
            
            class Args:
                context_file = 'context.json'
                goal = None
                strategy = None
                error = None
                dry_run = True
                json = False
            
            result = autoresearch_web_search.cmd_search(Args())
            self.assertEqual(result, 0)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)
    
    def test_cmd_generate_hypotheses_context_lines_226_227(self):
        """Test cmd_generate_hypotheses with context file (lines 226-227)."""
        import autoresearch_web_search
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create files
            with open('results.json', 'w') as f:
                json.dump({'results': []}, f)
            with open('context.json', 'w') as f:
                json.dump({'goal': 'Test'}, f)
            
            class Args:
                search_results = 'results.json'
                context_file = 'context.json'
                output = None
                json = True
            
            result = autoresearch_web_search.cmd_generate_hypotheses(Args())
            self.assertEqual(result, 0)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)
    
    def test_cmd_check_and_search_verbose_line_289(self):
        """Test cmd_check_and_search with verbose (line 289)."""
        import autoresearch_web_search
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create state file
            state = {'consecutive_discards': 2, 'pivot_count': 0}
            with open('autoresearch-state.json', 'w') as f:
                json.dump(state, f)
            
            class Args:
                state_file = None
                output = None
                json = False
                force = False
                verbose = True
            
            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            try:
                result = autoresearch_web_search.cmd_check_and_search(Args())
            finally:
                sys.stdout = old_stdout
            
            output = captured.getvalue()
            self.assertEqual(result, 0)
            self.assertIn('2', output)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)
    
    def test_cmd_check_and_search_output_lines_301_302(self):
        """Test cmd_check_and_search with output file (lines 301-302)."""
        import autoresearch_web_search
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create state file that triggers search
            state = {
                'consecutive_discards': 5,
                'pivot_count': 2,
                'config': {'goal': 'Test'},
                'strategy': 'debug',
                'last_error': 'error'
            }
            with open('autoresearch-state.json', 'w') as f:
                json.dump(state, f)
            
            class Args:
                state_file = None
                output = 'output.json'
                json = False
                force = False
                verbose = False
            
            result = autoresearch_web_search.cmd_check_and_search(Args())
            self.assertEqual(result, 0)
            self.assertTrue(os.path.exists('output.json'))
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)


class TestAutoresearchBackgroundExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_background.py."""
    
    def test_is_process_running_unix_exception_lines_176_179(self):
        """Test is_process_running exception on Unix (lines 176-179)."""
        import autoresearch_background
        
        with patch('sys.platform', 'linux'):
            with patch('os.kill') as mock_kill:
                mock_kill.side_effect = OSError('Process not found')
                result = autoresearch_background.is_process_running(1234)
                self.assertFalse(result)


class TestAutoresearchWorkflowExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_workflow.py."""
    
    def test_run_script_exception_lines_358_359(self):
        """Test run_script exception handling (lines 358-359)."""
        import autoresearch_workflow
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception('Script failed')
            code, output = autoresearch_workflow.run_script('test.py', [])
            self.assertEqual(code, -1)
            self.assertIn('Script failed', output)


class TestAutoresearchParallelExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_parallel.py."""
    
    def test_run_git_exception_lines_93_94(self):
        """Test run_git exception handling (lines 93-94)."""
        import autoresearch_parallel
        
        exp = autoresearch_parallel.ParallelExperiment('.')
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception('Git error')
            code, output = exp.run_git(['status'])
            self.assertEqual(code, -1)
            self.assertIn('Git error', output)


class TestAutoresearchCommitGateExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_commit_gate.py."""
    
    def test_run_git_exception_line_74(self):
        """Test run_git exception handling (line 74)."""
        import autoresearch_commit_gate
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception('Git failed')
            code, output = autoresearch_commit_gate.run_git(['status'])
            self.assertEqual(code, -1)
            self.assertIn('Git failed', output)


class TestAutoresearchAnalyzeExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_analyze.py."""
    
    def test_load_results_exception_lines_32_34(self):
        """Test load_results exception handling (lines 32-34)."""
        import autoresearch_analyze
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create invalid results file
            with open('autoresearch-results.tsv', 'w') as f:
                f.write('invalid\ttsv\n')
            
            captured_stderr = StringIO()
            old_stderr = sys.stderr
            sys.stderr = captured_stderr
            
            try:
                results = autoresearch_analyze.load_results()
            finally:
                sys.stderr = old_stderr
            
            self.assertEqual(results, [])
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)


class TestStateManagerExceptions(unittest.TestCase):
    """Test exception handlers in state_manager.py."""
    
    def test_load_state_json_error_lines_128_129(self):
        """Test load_state JSON decode error (lines 128-129)."""
        import state_manager
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create invalid JSON file
            with open('autoresearch-state.json', 'w') as f:
                f.write('invalid json')
            
            state = state_manager.load_state()
            
            # Should return default state
            self.assertIn('version', state)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)


class TestAutoresearchRalphExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_ralph.py."""
    
    def test_main_no_command_lines_407_408(self):
        """Test main with no command (lines 407-408)."""
        import autoresearch_ralph
        
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_ralph.py']
            
            with self.assertRaises(SystemExit) as cm:
                autoresearch_ralph.main()
            
            self.assertEqual(cm.exception.code, 1)
        finally:
            sys.argv = old_argv


class TestAutoresearchResilienceExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_resilience.py."""
    
    def test_main_no_command_lines_277_278(self):
        """Test main with no command (lines 277-278)."""
        import autoresearch_resilience
        
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_resilience.py']
            
            # Should print help and not raise SystemExit
            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            try:
                result = autoresearch_resilience.main()
            finally:
                sys.stdout = old_stdout
            
            output = captured.getvalue()
            self.assertIn('usage', output.lower())
        finally:
            sys.argv = old_argv


class TestAutoresearchMonitorExceptions(unittest.TestCase):
    """Test exception handlers in autoresearch_monitor.py."""
    
    def test_load_results_exception_lines_154_157(self):
        """Test load_results exception handling (lines 154-157)."""
        import autoresearch_monitor
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create invalid results file
            with open('autoresearch-results.tsv', 'w') as f:
                f.write('invalid')
            
            tracker = autoresearch_monitor.ProgressTracker()
            results = tracker.load_results()
            
            self.assertEqual(results, [])
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)


class TestDiagnoseStopMissingLines(unittest.TestCase):
    """Test specific missing lines in diagnose_stop.py."""
    
    def test_diagnose_no_state_file_line_73(self):
        """Test diagnose when no state file exists (line 73)."""
        import diagnose_stop
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            try:
                diagnose_stop.diagnose()
            finally:
                sys.stdout = old_stdout
            
            output = captured.getvalue()
            # Should show message about missing state file
            self.assertIn('未找到', output)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)
    
    def test_diagnose_max_iterations_line_128(self):
        """Test diagnose with max iterations (line 128)."""
        import diagnose_stop
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create state file with iterations reached
            state = {
                'version': '1.0',
                'iteration': 10,
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
            
            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            try:
                diagnose_stop.diagnose()
            finally:
                sys.stdout = old_stdout
            
            output = captured.getvalue()
            self.assertIn('10', output)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)


class TestGenerateReportMissingLines(unittest.TestCase):
    """Test specific missing lines in generate_report.py."""
    
    def test_generate_report_empty_rows_lines_44_45(self):
        """Test generate_report with empty rows (lines 44-45)."""
        import generate_report
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create results file with only header
            with open('autoresearch-results.tsv', 'w') as f:
                f.write('iteration\tcommit\tmetric\tdelta\tstatus\tdescription\n')
            
            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            try:
                generate_report.generate_report()
            finally:
                sys.stdout = old_stdout
            
            output = captured.getvalue()
            self.assertIn('No data', output)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)
    
    def test_generate_report_no_best_row_line_102(self):
        """Test generate_report when no best row (line 102)."""
        import generate_report
        
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create results file with only baseline and discards
            with open('autoresearch-results.tsv', 'w') as f:
                f.write('iteration\tcommit\tmetric\tdelta\tstatus\tdescription\n')
                f.write('0\tabc123\t100\t0\tbaseline\tInitial\n')
                f.write('1\tdef456\t95\t-5\tdiscard\tFailed\n')
            
            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            try:
                generate_report.generate_report()
            finally:
                sys.stdout = old_stdout
            
            output = captured.getvalue()
            self.assertIn('Report generated', output)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)


class TestGetBaselineMissingLines(unittest.TestCase):
    """Test specific missing lines in get_baseline.py."""
    
    def test_extract_number_value_error_lines_42_43(self):
        """Test extract_number ValueError handling (lines 42-43)."""
        import get_baseline
        
        # Test with an edge case that might cause ValueError
        result = get_baseline.extract_number('Result: 99999999999999999999.99')
        # Should handle gracefully
        self.assertIsInstance(result, (float, type(None)))
    
    def test_main_warning_line_80(self):
        """Test main warning when cannot extract number (line 80)."""
        import get_baseline
        
        old_argv = sys.argv
        try:
            sys.argv = ['get_baseline.py', '--verify', 'echo "no number"', '--parse-number']
            
            captured_stdout = StringIO()
            captured_stderr = StringIO()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = captured_stdout
            sys.stderr = captured_stderr
            
            try:
                get_baseline.main()
            except SystemExit:
                pass
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
            
            stderr_output = captured_stderr.getvalue()
            # Should show warning
            self.assertIn('Warning', stderr_output)
        finally:
            sys.argv = old_argv
    
    def test_main_return_line_81(self):
        """Test main return value (line 81)."""
        import get_baseline
        
        old_argv = sys.argv
        try:
            sys.argv = ['get_baseline.py', '--verify', 'echo "50.5"', '--parse-number']
            
            result = get_baseline.main()
            
            # Should return the extracted number
            self.assertEqual(result, 50.5)
        finally:
            sys.argv = old_argv


if __name__ == '__main__':
    unittest.main()
