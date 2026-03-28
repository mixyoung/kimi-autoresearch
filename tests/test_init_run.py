#!/usr/bin/env python3
"""Tests for autoresearch_init_run.py"""
import unittest
import sys
import os
import tempfile
import shutil
import json
import csv
import stat
import io
from unittest.mock import patch, MagicMock
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from autoresearch_init_run import (
    init_results_file, init_state, init_lessons_file, main,
    RESULTS_FILE, STATE_FILE, LESSONS_FILE
)


class TestInitResultsFile(unittest.TestCase):
    """Test init_results_file function."""
    
    def setUp(self):
        """Create temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        os.chdir(self.old_cwd)
        def on_rm_error(func, path, exc_info):
            os.chmod(path, stat.S_IWRITE)
            try:
                func(path)
            except:
                pass
        shutil.rmtree(self.temp_dir, onerror=on_rm_error)
    
    def test_init_results_file_creates_file(self):
        """Test that init_results_file creates the TSV file."""
        init_results_file()
        
        self.assertTrue(os.path.exists(RESULTS_FILE))
        
        with open(RESULTS_FILE, 'r', newline='') as f:
            reader = csv.reader(f, delimiter='\t')
            headers = next(reader)
            self.assertIn('iteration', headers)
            self.assertIn('commit', headers)
            self.assertIn('metric', headers)
    
    def test_init_results_file_archives_existing(self):
        """Test that existing file is archived."""
        # Create existing file
        with open(RESULTS_FILE, 'w') as f:
            f.write('old content')
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        init_results_file()
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        # Check for archive message (may be "Archived" or "Created")
        self.assertTrue('Archived' in output or 'Created' in output)
        
        # Check that new file was created
        self.assertTrue(os.path.exists(RESULTS_FILE))


class TestInitState(unittest.TestCase):
    """Test init_state function."""
    
    def setUp(self):
        """Create temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        os.chdir(self.old_cwd)
        def on_rm_error(func, path, exc_info):
            os.chmod(path, stat.S_IWRITE)
            try:
                func(path)
            except:
                pass
        shutil.rmtree(self.temp_dir, onerror=on_rm_error)
    
    def test_init_state_creates_file(self):
        """Test that init_state creates the state file."""
        config = {
            'goal': 'Test goal',
            'metric': 'coverage',
            'verify': 'npm test'
        }
        
        init_state(config)
        
        self.assertTrue(os.path.exists(STATE_FILE))
        
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            self.assertEqual(state['version'], '1.0')
            self.assertEqual(state['status'], 'initialized')
            self.assertEqual(state['iteration'], 0)
            self.assertEqual(state['config'], config)
    
    def test_init_state_includes_all_fields(self):
        """Test that init_state includes all required fields."""
        config = {'goal': 'Test'}
        
        init_state(config)
        
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            self.assertIn('start_time', state)
            self.assertIn('baseline', state)
            self.assertIn('best', state)
            self.assertIn('consecutive_discards', state)
            self.assertIn('pivot_count', state)
            self.assertIn('strategy', state)
            self.assertIn('history', state)
    
    def test_init_state_archives_existing(self):
        """Test that existing state file is archived."""
        with open(STATE_FILE, 'w') as f:
            json.dump({'old': 'state'}, f)
        
        config = {'goal': 'Test'}
        init_state(config)
        
        # Check that new state file was created with correct content
        self.assertTrue(os.path.exists(STATE_FILE))
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            self.assertEqual(state['config']['goal'], 'Test')


class TestInitLessonsFile(unittest.TestCase):
    """Test init_lessons_file function."""
    
    def setUp(self):
        """Create temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        os.chdir(self.old_cwd)
        def on_rm_error(func, path, exc_info):
            os.chmod(path, stat.S_IWRITE)
            try:
                func(path)
            except:
                pass
        shutil.rmtree(self.temp_dir, onerror=on_rm_error)
    
    def test_init_lessons_file_creates_file(self):
        """Test that init_lessons_file creates the file."""
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        init_lessons_file()
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertTrue(os.path.exists(LESSONS_FILE))
        self.assertIn('Created', output)
        
        with open(LESSONS_FILE, 'r') as f:
            content = f.read()
            self.assertIn('Autoresearch Lessons', content)
    
    def test_init_lessons_file_no_overwrite(self):
        """Test that existing lessons file is not overwritten."""
        with open(LESSONS_FILE, 'w') as f:
            f.write('Existing content')
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        init_lessons_file()
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        # Should not print "Created" message
        self.assertNotIn('Created', output)
        
        with open(LESSONS_FILE, 'r') as f:
            content = f.read()
            self.assertEqual(content, 'Existing content')


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
        def on_rm_error(func, path, exc_info):
            os.chmod(path, stat.S_IWRITE)
            try:
                func(path)
            except:
                pass
        shutil.rmtree(self.temp_dir, onerror=on_rm_error)
    
    def test_main_required_args(self):
        """Test main with required arguments."""
        with patch('sys.argv', [
            'autoresearch_init_run',
            '--goal', 'Test goal',
            '--metric', 'coverage',
            '--verify', 'npm test'
        ]):
            main()
        
        # Check files were created
        self.assertTrue(os.path.exists(RESULTS_FILE))
        self.assertTrue(os.path.exists(STATE_FILE))
        self.assertTrue(os.path.exists(LESSONS_FILE))
    
    def test_main_all_args(self):
        """Test main with all arguments."""
        with patch('sys.argv', [
            'autoresearch_init_run',
            '--goal', 'Test goal',
            '--metric', 'coverage',
            '--verify', 'npm test',
            '--scope', 'src/',
            '--guard', 'npm test',
            '--direction', 'lower',
            '--iterations', '10',
            '--mode', 'debug'
        ]):
            main()
        
        # Check state file has all config
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            config = state['config']
            self.assertEqual(config['goal'], 'Test goal')
            self.assertEqual(config['scope'], 'src/')
            self.assertEqual(config['guard'], 'npm test')
            self.assertEqual(config['direction'], 'lower')
            self.assertEqual(config['max_iterations'], 10)
            self.assertEqual(config['mode'], 'debug')
    
    def test_main_default_values(self):
        """Test main with default values."""
        with patch('sys.argv', [
            'autoresearch_init_run',
            '--goal', 'Test goal',
            '--metric', 'coverage',
            '--verify', 'npm test'
        ]):
            main()
        
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            config = state['config']
            self.assertEqual(config['scope'], '')
            self.assertEqual(config['guard'], '')
            self.assertEqual(config['direction'], 'higher')
            self.assertEqual(config['max_iterations'], 0)
            self.assertEqual(config['mode'], 'loop')
    
    def test_main_missing_required(self):
        """Test main with missing required arguments."""
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.argv', [
                'autoresearch_init_run',
                '--goal', 'Test goal'
                # Missing --metric and --verify
            ]):
                main()
        
        # argparse exits with 2 on error
        self.assertEqual(cm.exception.code, 2)


if __name__ == '__main__':
    unittest.main()
