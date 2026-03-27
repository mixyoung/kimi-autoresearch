#!/usr/bin/env python3
"""
Tests for state_manager.py - v2.0 Ralph Loop Edition
"""
import json
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from state_manager import (
    load_state,
    save_state,
    update_iteration_status,
    log_lesson
)


class TestLoadState(unittest.TestCase):
    """Test state loading."""
    
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()
    
    def test_load_state_default(self):
        """Test loading state when no file exists."""
        state = load_state()
        
        self.assertEqual(state['version'], '2.0')
        self.assertEqual(state['iteration'], 0)
        self.assertIsNone(state['baseline'])
        self.assertIsNone(state['best'])
        self.assertEqual(state['consecutive_discards'], 0)
        self.assertEqual(state['pivot_count'], 0)
        self.assertEqual(state['strategy'], 'initial')
    
    def test_load_state_default_loop_control(self):
        """Test default loop control in new state."""
        state = load_state()
        
        self.assertEqual(state['loop_control']['max_steps_per_turn'], 50)
        self.assertEqual(state['loop_control']['max_retries_per_step'], 3)
        self.assertEqual(state['loop_control']['max_ralph_iterations'], 0)
    
    def test_load_state_default_agent_config(self):
        """Test default agent config in new state."""
        state = load_state()
        
        self.assertIsNone(state['agent_config'])
    
    def test_load_state_existing_file(self):
        """Test loading existing state file."""
        # Create existing state
        existing_state = {
            'version': '2.0',
            'iteration': 10,
            'baseline': 50,
            'best': 45,
            'config': {'goal': 'Test'}
        }
        
        with open('autoresearch-state.json', 'w') as f:
            json.dump(existing_state, f)
        
        state = load_state()
        
        self.assertEqual(state['iteration'], 10)
        self.assertEqual(state['baseline'], 50)
        self.assertEqual(state['best'], 45)


class TestSaveState(unittest.TestCase):
    """Test state saving."""
    
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()
    
    def test_save_state_creates_file(self):
        """Test that save_state creates the state file."""
        state = load_state()
        state['baseline'] = 100
        
        save_state(state)
        
        self.assertTrue(os.path.exists('autoresearch-state.json'))
    
    def test_save_state_persists_data(self):
        """Test that saved data can be loaded back."""
        state = load_state()
        state['baseline'] = 100
        state['best'] = 90
        state['iteration'] = 5
        
        save_state(state)
        loaded = load_state()
        
        self.assertEqual(loaded['baseline'], 100)
        self.assertEqual(loaded['best'], 90)
        self.assertEqual(loaded['iteration'], 5)


class TestUpdateIterationStatus(unittest.TestCase):
    """Test iteration status updates."""
    
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()
    
    def test_update_status_keep(self):
        """Test update with keep status."""
        state = load_state()
        state['consecutive_discards'] = 3
        
        updated = update_iteration_status(state, 'keep')
        
        self.assertEqual(updated['iteration'], 1)
        self.assertEqual(updated['consecutive_discards'], 0)
    
    def test_update_status_discard(self):
        """Test update with discard status."""
        state = load_state()
        state['consecutive_discards'] = 2
        
        updated = update_iteration_status(state, 'discard')
        
        self.assertEqual(updated['iteration'], 1)
        self.assertEqual(updated['consecutive_discards'], 3)
    
    def test_update_status_pivot(self):
        """Test update with pivot status."""
        state = load_state()
        state['pivot_count'] = 1
        state['consecutive_discards'] = 3
        
        updated = update_iteration_status(state, 'pivot')
        
        self.assertEqual(updated['iteration'], 1)
        self.assertEqual(updated['pivot_count'], 2)
        self.assertEqual(updated['consecutive_discards'], 0)
    
    def test_update_status_multiple_iterations(self):
        """Test multiple status updates."""
        state = load_state()
        
        # 3 keeps
        for _ in range(3):
            state = update_iteration_status(state, 'keep')
        
        self.assertEqual(state['iteration'], 3)
        self.assertEqual(state['consecutive_discards'], 0)
        
        # 2 discards
        for _ in range(2):
            state = update_iteration_status(state, 'discard')
        
        self.assertEqual(state['iteration'], 5)
        self.assertEqual(state['consecutive_discards'], 2)


class TestLogLesson(unittest.TestCase):
    """Test lesson logging."""
    
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()
    
    def test_log_lesson_creates_file(self):
        """Test that log_lesson creates the lessons file."""
        log_lesson("This is a test lesson")
        
        self.assertTrue(os.path.exists('autoresearch-lessons.md'))
    
    def test_log_lesson_content(self):
        """Test logged lesson content."""
        log_lesson("Test lesson content")
        
        with open('autoresearch-lessons.md', 'r') as f:
            content = f.read()
        
        self.assertIn('Test lesson content', content)
        self.assertIn('positive', content)  # default type
    
    def test_log_lesson_types(self):
        """Test different lesson types."""
        log_lesson("Positive lesson", 'positive')
        log_lesson("Strategic lesson", 'strategic')
        log_lesson("Negative lesson", 'negative')
        
        with open('autoresearch-lessons.md', 'r') as f:
            content = f.read()
        
        self.assertIn('positive', content)
        self.assertIn('strategic', content)
        self.assertIn('negative', content)
    
    def test_log_lesson_timestamp(self):
        """Test that lessons have timestamps."""
        log_lesson("Test with timestamp")
        
        with open('autoresearch-lessons.md', 'r') as f:
            content = f.read()
        
        # Should contain ISO timestamp (2024- or 2025- etc.)
        import re
        self.assertRegex(content, r'\d{4}-\d{2}-\d{2}')


class TestStateIntegrity(unittest.TestCase):
    """Test state integrity across operations."""
    
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()
    
    def test_full_workflow(self):
        """Test full state workflow."""
        # Load initial state
        state = load_state()
        
        # Simulate some iterations
        state = update_iteration_status(state, 'keep')
        state = update_iteration_status(state, 'keep')
        state = update_iteration_status(state, 'discard')
        state = update_iteration_status(state, 'pivot')
        
        # Save state
        save_state(state)
        
        # Load and verify
        loaded = load_state()
        
        self.assertEqual(loaded['iteration'], 4)
        self.assertEqual(loaded['consecutive_discards'], 0)  # reset by pivot
        self.assertEqual(loaded['pivot_count'], 1)


if __name__ == '__main__':
    unittest.main()
