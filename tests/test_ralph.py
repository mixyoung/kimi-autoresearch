#!/usr/bin/env python3
"""
Tests for autoresearch_ralph.py - Ralph Loop control
"""
import json
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from autoresearch_ralph import (
    set_loop_control,
    get_loop_control,
    set_agent_config,
    get_agent_config,
    check_should_stop,
    emit_stop_signal,
    generate_ralph_prompt
)


class TestLoopControl(unittest.TestCase):
    """Test Ralph Loop control functions."""
    
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()
    
    def test_set_loop_control_defaults(self):
        """Test setting loop control with defaults."""
        config = set_loop_control()
        
        self.assertEqual(config['max_steps_per_turn'], 50)
        self.assertEqual(config['max_retries_per_step'], 3)
        self.assertEqual(config['max_ralph_iterations'], 0)
    
    def test_set_loop_control_custom(self):
        """Test setting custom loop control values."""
        config = set_loop_control(
            max_steps=30,
            max_retries=5,
            max_ralph=100
        )
        
        self.assertEqual(config['max_steps_per_turn'], 30)
        self.assertEqual(config['max_retries_per_step'], 5)
        self.assertEqual(config['max_ralph_iterations'], 100)
    
    def test_get_loop_control_default(self):
        """Test getting loop control without state file."""
        config = get_loop_control()
        
        self.assertEqual(config['max_steps_per_turn'], 50)
        self.assertEqual(config['max_retries_per_step'], 3)
        self.assertEqual(config['max_ralph_iterations'], 0)
    
    def test_loop_control_persistence(self):
        """Test that loop control is saved to state file."""
        set_loop_control(max_steps=25, max_retries=2, max_ralph=50)
        
        # Read from file directly
        with open('autoresearch-state.json', 'r') as f:
            state = json.load(f)
        
        self.assertEqual(state['loop_control']['max_steps_per_turn'], 25)
        self.assertEqual(state['loop_control']['max_retries_per_step'], 2)
        self.assertEqual(state['loop_control']['max_ralph_iterations'], 50)


class TestAgentConfig(unittest.TestCase):
    """Test agent configuration functions."""
    
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()
    
    def test_set_agent_config_builtin(self):
        """Test setting built-in agent."""
        config = set_agent_config(agent='okabe')
        
        self.assertEqual(config['agent'], 'okabe')
        self.assertIsNone(config['agent_file'])
    
    def test_set_agent_config_custom(self):
        """Test setting custom agent file."""
        config = set_agent_config(agent_file='./custom-agent.toml')
        
        self.assertIsNone(config['agent'])
        self.assertEqual(config['agent_file'], './custom-agent.toml')
    
    def test_set_agent_config_mutual_exclusion(self):
        """Test that agent and agent_file are mutually exclusive."""
        with self.assertRaises(ValueError):
            set_agent_config(agent='default', agent_file='./custom.toml')
    
    def test_get_agent_config_none(self):
        """Test getting agent config when not set."""
        config = get_agent_config()
        
        self.assertIsNone(config)


class TestStopConditions(unittest.TestCase):
    """Test stop condition checking."""
    
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
        
        # Create initial state
        state = {
            'version': '2.0',
            'iteration': 10,
            'config': {
                'goal': 'Test',
                'target': 50,
                'direction': 'lower',
                'iterations': 20
            },
            'loop_control': {
                'max_ralph_iterations': 15
            },
            'consecutive_discards': 0,
            'pivot_count': 0
        }
        
        with open('autoresearch-state.json', 'w') as f:
            json.dump(state, f)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()
    
    def test_check_should_stop_target_reached_lower(self):
        """Test stop when target reached (lower direction)."""
        should_stop, reason = check_should_stop(current_metric=45)
        
        self.assertTrue(should_stop)
        self.assertIn('Target reached', reason)
    
    def test_check_should_stop_target_not_reached(self):
        """Test continue when target not reached."""
        should_stop, reason = check_should_stop(current_metric=55)
        
        self.assertFalse(should_stop)
    
    def test_check_should_stop_max_iterations(self):
        """Test stop at max iterations."""
        # Update state to have max iterations reached (no Ralph limit)
        with open('autoresearch-state.json', 'r') as f:
            state = json.load(f)
        state['iteration'] = 20
        state['loop_control']['max_ralph_iterations'] = 0  # No Ralph limit
        with open('autoresearch-state.json', 'w') as f:
            json.dump(state, f)
        
        should_stop, reason = check_should_stop(current_metric=60)
        
        self.assertTrue(should_stop)
        self.assertIn('Max iterations reached', reason)
    
    def test_check_should_stop_ralph_limit(self):
        """Test stop at Ralph iteration limit."""
        # Update state to have Ralph limit reached
        with open('autoresearch-state.json', 'r') as f:
            state = json.load(f)
        state['iteration'] = 15
        with open('autoresearch-state.json', 'w') as f:
            json.dump(state, f)
        
        should_stop, reason = check_should_stop(current_metric=60)
        
        self.assertTrue(should_stop)
        self.assertIn('Ralph iteration limit', reason)
    
    def test_check_should_stop_truly_stuck(self):
        """Test stop when truly stuck."""
        # Update state to be stuck
        with open('autoresearch-state.json', 'r') as f:
            state = json.load(f)
        state['consecutive_discards'] = 5
        state['pivot_count'] = 2
        with open('autoresearch-state.json', 'w') as f:
            json.dump(state, f)
        
        should_stop, reason = check_should_stop(current_metric=60)
        
        self.assertTrue(should_stop)
        self.assertIn('Truly stuck', reason)


class TestRalphPrompt(unittest.TestCase):
    """Test Ralph Loop prompt generation."""
    
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
        
        # Create state
        state = {
            'version': '2.0',
            'config': {
                'goal': 'Reduce type errors',
                'scope': 'src/',
                'verify': 'tsc --noEmit 2>&1 | grep -c error',
                'guard': 'npm run build',
                'direction': 'lower'
            },
            'baseline': 50,
            'best': 45,
            'iteration': 5,
            'loop_control': {
                'max_steps_per_turn': 30,
                'max_retries_per_step': 3,
                'max_ralph_iterations': 50
            },
            'agent_config': {
                'agent': 'okabe'
            }
        }
        
        with open('autoresearch-state.json', 'w') as f:
            json.dump(state, f)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()
    
    def test_generate_ralph_prompt_contains_goal(self):
        """Test prompt contains goal."""
        prompt = generate_ralph_prompt({})
        
        self.assertIn('Reduce type errors', prompt)
    
    def test_generate_ralph_prompt_contains_verify(self):
        """Test prompt contains verify command."""
        prompt = generate_ralph_prompt({})
        
        self.assertIn('tsc --noEmit', prompt)
    
    def test_generate_ralph_prompt_contains_loop_control(self):
        """Test prompt contains loop control settings."""
        prompt = generate_ralph_prompt({})
        
        self.assertIn('30', prompt)  # max_steps_per_turn
        self.assertIn('3', prompt)   # max_retries_per_step
    
    def test_generate_ralph_prompt_contains_agent(self):
        """Test prompt contains agent info."""
        prompt = generate_ralph_prompt({})
        
        self.assertIn('okabe', prompt)
    
    def test_generate_ralph_prompt_contains_stop_signal(self):
        """Test prompt contains stop signal instruction."""
        prompt = generate_ralph_prompt({})
        
        self.assertIn('<choice>STOP</choice>', prompt)


class TestEmitStopSignal(unittest.TestCase):
    """Test stop signal emission."""
    
    def test_emit_stop_signal_with_reason(self):
        """Test emitting stop signal with reason."""
        import io
        import sys
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        emit_stop_signal("Target reached")
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertIn('[STOP SIGNAL] Target reached', output)
        self.assertIn('<choice>STOP</choice>', output)


if __name__ == '__main__':
    unittest.main()
