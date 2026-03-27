#!/usr/bin/env python3
"""Tests for diagnose_stop.py"""
import unittest
import sys
import os
import tempfile
import json
from io import StringIO
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from diagnose_stop import diagnose, STATE_FILE, RESULTS_FILE


class TestDiagnose(unittest.TestCase):
    """Test diagnose function."""
    
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
    
    def test_no_state_file(self):
        """Test diagnose when no state file exists."""
        import io
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        diagnose()
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertIn("未找到状态文件", output)
        self.assertIn("autoresearch-state.json", output)
    
    def test_basic_state(self):
        """Test diagnose with basic state."""
        import io
        
        state = {
            'version': '2.0',
            'iteration': 5,
            'consecutive_discards': 0,
            'pivot_count': 0,
            'config': {
                'goal': 'Test goal',
                'target': None,
                'iterations': 0,
                'direction': 'lower'
            },
            'loop_control': {
                'max_ralph_iterations': 0,
                'max_steps_per_turn': 50,
                'max_retries_per_step': 3
            }
        }
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        diagnose()
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertIn("Kimi Autoresearch", output)
        self.assertIn("2.0", output)
        self.assertIn("Test goal", output)
        self.assertIn("应该无限运行", output)
    
    def test_with_max_ralph_limit(self):
        """Test diagnose with Ralph iteration limit."""
        import io
        
        state = {
            'version': '2.0',
            'iteration': 15,
            'consecutive_discards': 0,
            'pivot_count': 0,
            'config': {
                'goal': 'Test',
                'target': None,
                'iterations': 0,
                'direction': 'lower'
            },
            'loop_control': {
                'max_ralph_iterations': 20,
                'max_steps_per_turn': 50,
                'max_retries_per_step': 3
            }
        }
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        diagnose()
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertIn("接近 Ralph", output)
        self.assertIn("15/20", output)
    
    def test_reached_ralph_limit(self):
        """Test diagnose when Ralph limit reached."""
        import io
        
        state = {
            'version': '2.0',
            'iteration': 20,
            'consecutive_discards': 0,
            'pivot_count': 0,
            'config': {
                'goal': 'Test',
                'target': None,
                'iterations': 0,
                'direction': 'lower'
            },
            'loop_control': {
                'max_ralph_iterations': 20,
                'max_steps_per_turn': 50,
                'max_retries_per_step': 3
            }
        }
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        diagnose()
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertIn("达到 Ralph 迭代限制", output)
    
    def test_with_iterations_limit(self):
        """Test diagnose with iterations limit."""
        import io
        
        state = {
            'version': '2.0',
            'iteration': 10,
            'consecutive_discards': 0,
            'pivot_count': 0,
            'config': {
                'goal': 'Test',
                'target': None,
                'iterations': 10,
                'direction': 'lower'
            },
            'loop_control': {
                'max_ralph_iterations': 0,
                'max_steps_per_turn': 50,
                'max_retries_per_step': 3
            }
        }
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        diagnose()
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertIn("达到最大迭代限制", output)
    
    def test_with_target(self):
        """Test diagnose with target set."""
        import io
        
        state = {
            'version': '2.0',
            'iteration': 5,
            'consecutive_discards': 0,
            'pivot_count': 0,
            'config': {
                'goal': 'Test',
                'target': 50,
                'iterations': 0,
                'direction': 'lower'
            },
            'loop_control': {
                'max_ralph_iterations': 0,
                'max_steps_per_turn': 50,
                'max_retries_per_step': 3
            }
        }
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        diagnose()
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertIn("设置了目标值", output)
        self.assertIn("50", output)
    
    def test_stuck_detection(self):
        """Test diagnose with stuck detection."""
        import io
        
        state = {
            'version': '2.0',
            'iteration': 10,
            'consecutive_discards': 5,
            'pivot_count': 2,
            'config': {
                'goal': 'Test',
                'target': None,
                'iterations': 0,
                'direction': 'lower'
            },
            'loop_control': {
                'max_ralph_iterations': 0,
                'max_steps_per_turn': 50,
                'max_retries_per_step': 3
            }
        }
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        diagnose()
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertIn("卡住检测触发", output)
        self.assertIn("5 次丢弃", output)
    
    def test_near_stuck(self):
        """Test diagnose when near stuck."""
        import io
        
        state = {
            'version': '2.0',
            'iteration': 10,
            'consecutive_discards': 3,
            'pivot_count': 0,
            'config': {
                'goal': 'Test',
                'target': None,
                'iterations': 0,
                'direction': 'lower'
            },
            'loop_control': {
                'max_ralph_iterations': 0,
                'max_steps_per_turn': 50,
                'max_retries_per_step': 3
            }
        }
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        diagnose()
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertIn("接近卡住", output)
        self.assertIn("3 次连续丢弃", output)
    
    def test_with_results_file(self):
        """Test diagnose with results file."""
        import io
        
        state = {
            'version': '2.0',
            'iteration': 3,
            'consecutive_discards': 0,
            'pivot_count': 0,
            'config': {
                'goal': 'Test',
                'target': None,
                'iterations': 0,
                'direction': 'lower'
            },
            'loop_control': {
                'max_ralph_iterations': 0,
                'max_steps_per_turn': 50,
                'max_retries_per_step': 3
            }
        }
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        # Create results file
        with open(RESULTS_FILE, 'w') as f:
            f.write("iteration\tcommit\tmetric\tdelta\tstatus\tdescription\ttimestamp\n")
            f.write("0\tabc\t100\t0\tbaseline\tInitial\t2024-01-01\n")
            f.write("1\tdef\t90\t-10\tkeep\tImproved\t2024-01-02\n")
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        diagnose()
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertIn("结果日志", output)
        self.assertIn("Initial", output)


if __name__ == '__main__':
    unittest.main()
