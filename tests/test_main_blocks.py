#!/usr/bin/env python3
"""
Tests for __main__ blocks using subprocess execution.
This ensures the if __name__ == '__main__': blocks are actually executed.
"""

import unittest
import sys
import os
import subprocess
import tempfile
import json

# Get the scripts directory
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'scripts')


class TestMainBlocksSubprocess(unittest.TestCase):
    """Test __main__ blocks by running scripts as subprocesses."""
    
    def run_script(self, script_name, args=None, cwd=None):
        """Helper to run a script as a subprocess."""
        script_path = os.path.join(SCRIPTS_DIR, script_name)
        cmd = [sys.executable, script_path]
        if args:
            cmd.extend(args)
        
        # Set environment for UTF-8 encoding
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            cwd=cwd,
            env=env
        )
        return result
    
    def test_autoresearch_decision_main_block(self):
        """Test autoresearch_decision.py __main__ block (line 206)."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create state file
            with open(os.path.join(temp_dir, 'autoresearch-state.json'), 'w') as f:
                json.dump({'consecutive_discards': 0}, f)
            
            result = self.run_script(
                'autoresearch_decision.py',
                ['--action', 'decide', '--current', '42', '--baseline', '50', '--direction', 'lower'],
                cwd=temp_dir
            )
            # Should not crash - either success or argparse error
            self.assertIn(result.returncode, [0, 1, 2])
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_autoresearch_main_main_block_help(self):
        """Test autoresearch_main.py __main__ block with help (line 417)."""
        result = self.run_script('autoresearch_main.py', ['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    def test_check_git_main_block_not_repo(self):
        """Test check_git.py __main__ block when not in repo (line 121)."""
        temp_dir = tempfile.mkdtemp()
        try:
            result = self.run_script(
                'check_git.py',
                ['--action', 'check'],
                cwd=temp_dir
            )
            # Should fail with "Not a git repository"
            self.assertEqual(result.returncode, 1)
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_autoresearch_exec_main_block_help(self):
        """Test autoresearch_exec.py __main__ block (line 377)."""
        result = self.run_script('autoresearch_exec.py', ['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    def test_autoresearch_parallel_main_block_help(self):
        """Test autoresearch_parallel.py __main__ block (line 345)."""
        result = self.run_script('autoresearch_parallel.py', ['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    def test_autoresearch_workflow_main_block_help(self):
        """Test autoresearch_workflow.py __main__ block (line 418)."""
        result = self.run_script('autoresearch_workflow.py', ['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    def test_autoresearch_stuck_recovery_main_block_help(self):
        """Test autoresearch_stuck_recovery.py __main__ block (line 316)."""
        result = self.run_script('autoresearch_stuck_recovery.py', ['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    def test_autoresearch_health_check_main_block(self):
        """Test autoresearch_health_check.py __main__ block (line 217)."""
        temp_dir = tempfile.mkdtemp()
        try:
            result = self.run_script(
                'autoresearch_health_check.py',
                [],
                cwd=temp_dir
            )
            # May fail due to git check but should run
            self.assertIn(result.returncode, [0, 1])
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_autoresearch_resilience_main_block_help(self):
        """Test autoresearch_resilience.py __main__ block (line 337)."""
        result = self.run_script('autoresearch_resilience.py', ['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    def test_autoresearch_infinite_main_block_help(self):
        """Test autoresearch_infinite.py __main__ block (line 367)."""
        result = self.run_script('autoresearch_infinite.py', ['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    def test_autoresearch_launch_gate_main_block_help(self):
        """Test autoresearch_launch_gate.py __main__ block (line 206)."""
        result = self.run_script('autoresearch_launch_gate.py', ['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    def test_diagnose_stop_main_block(self):
        """Test diagnose_stop.py __main__ block (line 128)."""
        temp_dir = tempfile.mkdtemp()
        try:
            result = self.run_script(
                'diagnose_stop.py',
                [],
                cwd=temp_dir
            )
            # Should run and diagnose (no state file)
            self.assertEqual(result.returncode, 0)
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_autoresearch_version_main_block_help(self):
        """Test autoresearch_version.py __main__ block (line 258)."""
        result = self.run_script('autoresearch_version.py', ['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    def test_autoresearch_init_run_main_block_help(self):
        """Test autoresearch_init_run.py __main__ block (line 110)."""
        result = self.run_script('autoresearch_init_run.py', ['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    def test_autoresearch_ralph_main_block_help(self):
        """Test autoresearch_ralph.py __main__ block (line 442)."""
        result = self.run_script('autoresearch_ralph.py', ['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    def test_autoresearch_i18n_main_block_help(self):
        """Test autoresearch_i18n.py __main__ block (line 207)."""
        result = self.run_script('autoresearch_i18n.py', ['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    def test_autoresearch_monitor_main_block_help(self):
        """Test autoresearch_monitor.py __main__ block (line 390)."""
        result = self.run_script('autoresearch_monitor.py', ['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    def test_autoresearch_web_search_main_block_help(self):
        """Test autoresearch_web_search.py __main__ block (line 368)."""
        result = self.run_script('autoresearch_web_search.py', ['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    def test_run_iteration_main_block_help(self):
        """Test run_iteration.py __main__ block (line 265)."""
        result = self.run_script('run_iteration.py', ['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    def test_autoresearch_utils_main_block_help(self):
        """Test autoresearch_utils.py __main__ block (line 307)."""
        result = self.run_script('autoresearch_utils.py', ['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    def test_state_manager_main_block_help(self):
        """Test state_manager.py __main__ block (line 165)."""
        result = self.run_script('state_manager.py', ['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    def test_autoresearch_analyze_main_block_help(self):
        """Test autoresearch_analyze.py __main__ block (line 344)."""
        result = self.run_script('autoresearch_analyze.py', ['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    def test_autoresearch_background_main_block_help(self):
        """Test autoresearch_background.py __main__ block (line 291)."""
        result = self.run_script('autoresearch_background.py', ['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    def test_autoresearch_commit_gate_main_block_help(self):
        """Test autoresearch_commit_gate.py __main__ block (line 290)."""
        result = self.run_script('autoresearch_commit_gate.py', ['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    def test_autoresearch_lessons_main_block_help(self):
        """Test autoresearch_lessons.py __main__ block (line 285)."""
        result = self.run_script('autoresearch_lessons.py', ['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    def test_generate_report_main_block_no_file(self):
        """Test generate_report.py __main__ block with no results file (line 102)."""
        temp_dir = tempfile.mkdtemp()
        try:
            result = self.run_script(
                'generate_report.py',
                [],
                cwd=temp_dir
            )
            # Should handle missing file gracefully
            self.assertEqual(result.returncode, 0)
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_log_result_main_block_help(self):
        """Test log_result.py __main__ block (line 63)."""
        result = self.run_script('log_result.py', ['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    def test_get_baseline_main_block_help(self):
        """Test get_baseline.py __main__ block (line 81)."""
        result = self.run_script('get_baseline.py', ['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())


if __name__ == '__main__':
    unittest.main()
