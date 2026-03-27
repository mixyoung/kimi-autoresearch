#!/usr/bin/env python3
"""Tests for autoresearch_utils.py"""
import unittest
import sys
import os
import tempfile
import json
import csv
import io
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from autoresearch_utils import (
    run_command, cmd_stats, cmd_clean, cmd_export, cmd_config, main
)


class TestRunCommand(unittest.TestCase):
    """Test run_command function."""
    
    @patch('subprocess.run')
    def test_run_command_success(self, mock_run):
        """Test running a command successfully."""
        mock_run.return_value = MagicMock(returncode=0, stdout='output', stderr='')
        
        code, output = run_command('echo hello')
        
        self.assertEqual(code, 0)
        self.assertEqual(output, 'output')
    
    @patch('subprocess.run')
    def test_run_command_failure(self, mock_run):
        """Test running a command that fails."""
        mock_run.return_value = MagicMock(returncode=1, stdout='', stderr='error')
        
        code, output = run_command('false')
        
        self.assertEqual(code, 1)
        self.assertEqual(output, 'error')
    
    @patch('subprocess.run')
    def test_run_command_exception(self, mock_run):
        """Test running a command that raises exception."""
        mock_run.side_effect = Exception('Command failed')
        
        code, output = run_command('invalid')
        
        self.assertEqual(code, -1)
        self.assertIn('Command failed', output)
    
    @patch('subprocess.run')
    def test_run_command_with_timeout(self, mock_run):
        """Test running a command with timeout."""
        mock_run.return_value = MagicMock(returncode=0, stdout='output', stderr='')
        
        code, output = run_command('sleep 1', timeout=5)
        
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        self.assertEqual(call_kwargs['timeout'], 5)


class TestCmdStats(unittest.TestCase):
    """Test cmd_stats function."""
    
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
    
    def test_stats_no_files(self):
        """Test stats when no files exist."""
        args = MagicMock()
        args.json = False
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_stats(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Autoresearch Statistics', output)
        self.assertIn('Runs: 0', output)
    
    def test_stats_with_results_file(self):
        """Test stats with results file."""
        # Create results file
        with open('autoresearch-results.tsv', 'w') as f:
            f.write("iteration\tcommit\tmetric\tdelta\tstatus\tdescription\ttimestamp\n")
            f.write("0\tabc\t100\t0\tbaseline\tInitial\t2024-01-01\n")
            f.write("1\tdef\t90\t-10\tkeep\tImproved\t2024-01-02\n")
        
        args = MagicMock()
        args.json = False
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_stats(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Total iterations: 2', output)
        self.assertIn('Kept: 1', output)
    
    def test_stats_json_output(self):
        """Test stats with JSON output."""
        args = MagicMock()
        args.json = True
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_stats(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        data = json.loads(output)
        self.assertIn('runs', data)
        self.assertIn('total_iterations', data)
        self.assertIn('files', data)
    
    def test_stats_with_state_file(self):
        """Test stats with state file."""
        state = {
            'iteration': 5,
            'config': {'goal': 'Test goal'}
        }
        with open('autoresearch-state.json', 'w') as f:
            json.dump(state, f)
        
        args = MagicMock()
        args.json = False
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_stats(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Test goal', output)
        self.assertIn('Current iteration: 5', output)
    
    def test_stats_with_lessons_file(self):
        """Test stats with lessons file."""
        with open('autoresearch-lessons.md', 'w') as f:
            f.write("# Lessons\n\n## Lesson 1\n\n## Lesson 2\n\n## Lesson 3\n")
        
        args = MagicMock()
        args.json = False
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_stats(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Lessons learned: 3', output)


class TestCmdClean(unittest.TestCase):
    """Test cmd_clean function."""
    
    def setUp(self):
        """Create temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create test files
        for f in ['autoresearch-results.tsv', 'autoresearch-state.json', 
                  'autoresearch-runtime.json', 'autoresearch-lessons.md']:
            with open(f, 'w') as fp:
                fp.write('test')
    
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
    
    def test_clean_dry_run(self):
        """Test clean command without force flag (dry run)."""
        args = MagicMock()
        args.force = False
        args.all = False
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_clean(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Would remove', output)
        # Files should still exist
        self.assertTrue(os.path.exists('autoresearch-results.tsv'))
    
    def test_clean_force(self):
        """Test clean command with force flag."""
        args = MagicMock()
        args.force = True
        args.all = False
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_clean(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Removed', output)
        # Files should be deleted
        self.assertFalse(os.path.exists('autoresearch-results.tsv'))
    
    def test_clean_with_backup_files(self):
        """Test clean with backup files."""
        # Create backup files
        with open('autoresearch-state.json.prev.1', 'w') as f:
            f.write('backup')
        with open('autoresearch-results.bak', 'w') as f:
            f.write('backup')
        
        args = MagicMock()
        args.force = True
        args.all = True
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_clean(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Removed backup', output)


class TestCmdExport(unittest.TestCase):
    """Test cmd_export function."""
    
    def setUp(self):
        """Create temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create results file
        with open('autoresearch-results.tsv', 'w') as f:
            f.write("iteration\tcommit\tmetric\tdelta\tstatus\n")
            f.write("0\tabc\t100\t0\tbaseline\n")
            f.write("1\tdef\t90\t-10\tkeep\n")
    
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
    
    def test_export_json(self):
        """Test export to JSON format."""
        args = MagicMock()
        args.format = 'json'
        args.output = None
        
        result = cmd_export(args)
        
        self.assertEqual(result, 0)
        self.assertTrue(os.path.exists('autoresearch-export.json'))
        
        with open('autoresearch-export.json', 'r') as f:
            data = json.load(f)
            self.assertIn('iterations', data)
            self.assertEqual(len(data['iterations']), 2)
    
    def test_export_csv(self):
        """Test export to CSV format."""
        args = MagicMock()
        args.format = 'csv'
        args.output = None
        
        result = cmd_export(args)
        
        self.assertEqual(result, 0)
        self.assertTrue(os.path.exists('autoresearch-export.csv'))
        
        with open('autoresearch-export.csv', 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 3)  # header + 2 rows
    
    def test_export_html(self):
        """Test export to HTML format."""
        args = MagicMock()
        args.format = 'html'
        args.output = None
        
        result = cmd_export(args)
        
        self.assertEqual(result, 0)
        self.assertTrue(os.path.exists('autoresearch-export.html'))
        
        with open('autoresearch-export.html', 'r') as f:
            content = f.read()
            self.assertIn('<html>', content)
            self.assertIn('Autoresearch Results', content)
            self.assertIn('<table>', content)
    
    def test_export_no_results_file(self):
        """Test export when no results file exists."""
        os.remove('autoresearch-results.tsv')
        
        args = MagicMock()
        args.format = 'json'
        args.output = None
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_export(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 1)
        self.assertIn('No results file', output)


class TestCmdConfig(unittest.TestCase):
    """Test cmd_config function."""
    
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
    
    def test_generate_sample_config(self):
        """Test generating sample config."""
        args = MagicMock()
        args.file = None
        args.validate = False
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_config(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertTrue(os.path.exists('autoresearch-config.json'))
        self.assertIn('Generated sample config', output)
        
        with open('autoresearch-config.json', 'r') as f:
            config = json.load(f)
            self.assertIn('goal', config)
            self.assertIn('metric', config)
            self.assertIn('verify', config)
    
    def test_validate_valid_config(self):
        """Test validating a valid config."""
        config = {
            'goal': 'Test goal',
            'metric': 'test metric',
            'verify': 'test command'
        }
        with open('autoresearch-config.json', 'w') as f:
            json.dump(config, f)
        
        args = MagicMock()
        args.file = None
        args.validate = True
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_config(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Configuration is valid', output)
    
    def test_validate_invalid_config(self):
        """Test validating an invalid config."""
        config = {
            'goal': 'Test goal'
            # Missing metric and verify
        }
        with open('autoresearch-config.json', 'w') as f:
            json.dump(config, f)
        
        args = MagicMock()
        args.file = None
        args.validate = True
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_config(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 1)
        self.assertIn('Missing required fields', output)
    
    def test_validate_nonexistent_config(self):
        """Test validating a nonexistent config file."""
        args = MagicMock()
        args.file = 'nonexistent.json'
        args.validate = True
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_config(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 1)
        self.assertIn('Config file not found', output)


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
    
    @patch('autoresearch_utils.sys.argv', ['autoresearch_utils.py', 'stats'])
    def test_main_stats(self):
        """Test main with stats command."""
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = main()
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Autoresearch Statistics', output)
    
    @patch('autoresearch_utils.sys.argv', ['autoresearch_utils.py', 'config'])
    def test_main_config(self):
        """Test main with config command."""
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = main()
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Generated sample config', output)
    
    @patch('autoresearch_utils.sys.argv', ['autoresearch_utils.py'])
    def test_main_no_command(self):
        """Test main with no command."""
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = main()
        
        sys.stdout = old_stdout
        
        self.assertEqual(result, 1)


if __name__ == '__main__':
    unittest.main()
