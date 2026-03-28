#!/usr/bin/env python3
"""Tests for autoresearch_workflow.py"""
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

from autoresearch_workflow import (
    run_script, print_header, workflow_init, workflow_baseline,
    generate_ralph_prompt, main
)


class TestRunScript(unittest.TestCase):
    """Test run_script function."""
    
    @patch('subprocess.run')
    def test_run_script_success(self, mock_run):
        """Test successful script execution."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='success',
            stderr=''
        )
        
        code, output = run_script('test.py', ['--arg', 'value'])
        
        self.assertEqual(code, 0)
        self.assertEqual(output, 'success')
    
    @patch('subprocess.run')
    def test_run_script_failure(self, mock_run):
        """Test failed script execution."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='',
            stderr='error'
        )
        
        code, output = run_script('test.py', [])
        
        self.assertEqual(code, 1)
        self.assertEqual(output, 'error')
    
    @patch('subprocess.run')
    def test_run_script_exception(self, mock_run):
        """Test script that raises exception."""
        mock_run.side_effect = Exception('Failed')
        
        code, output = run_script('test.py', [])
        
        self.assertEqual(code, -1)
        self.assertIn('Failed', output)


class TestPrintHeader(unittest.TestCase):
    """Test print_header function."""
    
    def test_print_header(self):
        """Test header printing."""
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        print_header('Test Header')
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertIn('Test Header', output)
        self.assertIn('=' * 60, output)


class TestWorkflowInit(unittest.TestCase):
    """Test workflow_init function."""
    
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
    
    @patch('autoresearch_workflow.run_script')
    def test_workflow_init_success(self, mock_run):
        """Test successful initialization."""
        mock_run.return_value = (0, 'OK')
        
        config = {
            'goal': 'Test goal',
            'metric': 'coverage',
            'verify': 'npm test',
            'direction': 'lower'
        }
        
        result = workflow_init(config)
        
        self.assertTrue(result)
    
    @patch('autoresearch_workflow.run_script')
    def test_workflow_init_health_fails(self, mock_run):
        """Test init when health check fails."""
        mock_run.return_value = (1, 'Health check failed')
        
        config = {
            'goal': 'Test goal',
            'metric': 'coverage',
            'verify': 'npm test',
            'direction': 'lower'
        }
        
        result = workflow_init(config)
        
        self.assertFalse(result)
    
    @patch('autoresearch_workflow.run_script')
    def test_workflow_init_with_loop_control(self, mock_run):
        """Test init with loop control settings."""
        mock_run.return_value = (0, 'OK')
        
        config = {
            'goal': 'Test goal',
            'metric': 'coverage',
            'verify': 'npm test',
            'direction': 'lower',
            'loop_control': {
                'max_steps_per_turn': 30,
                'max_retries_per_step': 5
            }
        }
        
        result = workflow_init(config)
        
        self.assertTrue(result)
    
    @patch('autoresearch_workflow.run_script')
    def test_workflow_init_with_agent_config(self, mock_run):
        """Test init with agent configuration."""
        mock_run.return_value = (0, 'OK')
        
        config = {
            'goal': 'Test goal',
            'metric': 'coverage',
            'verify': 'npm test',
            'direction': 'lower',
            'agent_config': {'agent': 'okabe'}
        }
        
        result = workflow_init(config)
        
        self.assertTrue(result)


class TestWorkflowBaseline(unittest.TestCase):
    """Test workflow_baseline function."""
    
    @patch('autoresearch_workflow.run_script')
    def test_workflow_baseline_success(self, mock_run):
        """Test successful baseline measurement."""
        mock_run.return_value = (0, 'Extracted metric: 85.5')
        
        config = {'verify': 'npm test'}
        
        success, baseline = workflow_baseline(config)
        
        self.assertTrue(success)
        self.assertEqual(baseline, 85.5)
    
    @patch('autoresearch_workflow.run_script')
    def test_workflow_baseline_failure(self, mock_run):
        """Test failed baseline measurement."""
        mock_run.return_value = (1, 'Command failed')
        
        config = {'verify': 'npm test'}
        
        success, baseline = workflow_baseline(config)
        
        self.assertFalse(success)
        self.assertEqual(baseline, 0.0)
    
    @patch('autoresearch_workflow.run_script')
    def test_workflow_baseline_no_metric(self, mock_run):
        """Test baseline when no metric can be extracted."""
        mock_run.return_value = (0, 'No metric here')
        
        config = {'verify': 'npm test'}
        
        success, baseline = workflow_baseline(config)
        
        self.assertTrue(success)  # Command succeeded
        self.assertEqual(baseline, 0.0)  # But no metric found


class TestGenerateRalphPrompt(unittest.TestCase):
    """Test generate_ralph_prompt function."""
    
    def test_generate_prompt_basic(self):
        """Test basic prompt generation."""
        config = {
            'goal': 'Reduce errors',
            'scope': 'src/',
            'verify': 'npm test',
            'direction': 'lower'
        }
        baseline = 100.0
        
        prompt = generate_ralph_prompt(config, baseline)
        
        self.assertIn('Reduce errors', prompt)
        self.assertIn('100.0', prompt)
        self.assertIn('Ralph Loop', prompt)
        self.assertIn('Single Iteration Protocol', prompt)
    
    def test_generate_prompt_with_loop_control(self):
        """Test prompt with loop control settings."""
        config = {
            'goal': 'Reduce errors',
            'verify': 'npm test',
            'direction': 'lower',
            'loop_control': {
                'max_steps_per_turn': 30,
                'max_retries_per_step': 5,
                'max_ralph_iterations': 50
            }
        }
        baseline = 100.0
        
        prompt = generate_ralph_prompt(config, baseline)
        
        self.assertIn('30', prompt)
        self.assertIn('5', prompt)
        self.assertIn('50', prompt)
    
    def test_generate_prompt_with_agent(self):
        """Test prompt with agent configuration."""
        config = {
            'goal': 'Reduce errors',
            'verify': 'npm test',
            'direction': 'lower',
            'agent_config': {'agent': 'okabe'}
        }
        baseline = 100.0
        
        prompt = generate_ralph_prompt(config, baseline)
        
        self.assertIn('okabe', prompt)
    
    def test_generate_prompt_with_iterations(self):
        """Test prompt with iterations info."""
        config = {
            'goal': 'Reduce errors',
            'verify': 'npm test',
            'direction': 'lower',
            'iterations': 20
        }
        baseline = 100.0
        
        prompt = generate_ralph_prompt(config, baseline)
        
        self.assertIn('Iterations:', prompt)


class TestMain(unittest.TestCase):
    """Test main function."""
    
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
    
    @patch('autoresearch_workflow.workflow_init')
    @patch('autoresearch_workflow.workflow_baseline')
    def test_main_success(self, mock_baseline, mock_init):
        """Test main success path."""
        mock_init.return_value = True
        mock_baseline.return_value = (True, 85.5)
        
        # main() doesn't raise SystemExit on success, it just completes
        with patch('sys.argv', [
            'autoresearch_workflow',
            '--goal', 'Test goal',
            '--verify', 'npm test',
            '--direction', 'lower'
        ]):
            main()  # Should complete without error
    
    @patch('autoresearch_workflow.workflow_init')
    def test_main_init_fails(self, mock_init):
        """Test main when init fails."""
        mock_init.return_value = False
        
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.argv', [
                'autoresearch_workflow',
                '--goal', 'Test goal',
                '--verify', 'npm test'
            ]):
                main()
        
        self.assertEqual(cm.exception.code, 1)
    
    @patch('autoresearch_workflow.workflow_init')
    @patch('autoresearch_workflow.workflow_baseline')
    def test_main_baseline_fails(self, mock_baseline, mock_init):
        """Test main when baseline fails."""
        mock_init.return_value = True
        mock_baseline.return_value = (False, 0)
        
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.argv', [
                'autoresearch_workflow',
                '--goal', 'Test goal',
                '--verify', 'npm test'
            ]):
                main()
        
        self.assertEqual(cm.exception.code, 1)
    
    def test_main_missing_required(self):
        """Test main with missing required arguments."""
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.argv', ['autoresearch_workflow']):
                main()
        
        self.assertEqual(cm.exception.code, 2)


if __name__ == '__main__':
    unittest.main()
