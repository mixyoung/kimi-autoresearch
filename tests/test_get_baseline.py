#!/usr/bin/env python3
"""Tests for get_baseline.py"""
import unittest
import sys
import os
import tempfile
from io import StringIO
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from get_baseline import run_command, extract_number, main


class TestRunCommand(unittest.TestCase):
    """Test run_command function."""
    
    @patch('subprocess.run')
    def test_run_command_success(self, mock_run):
        """Test successful command execution."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='output',
            stderr=''
        )
        
        code, output = run_command('echo test')
        
        self.assertEqual(code, 0)
        self.assertEqual(output, 'output')
    
    @patch('subprocess.run')
    def test_run_command_failure(self, mock_run):
        """Test failed command execution."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='',
            stderr='error'
        )
        
        code, output = run_command('false')
        
        self.assertEqual(code, 1)
        self.assertEqual(output, 'error')
    
    @patch('subprocess.run')
    def test_run_command_timeout(self, mock_run):
        """Test command timeout."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired('cmd', 300)
        
        code, output = run_command('sleep 400')
        
        self.assertEqual(code, -1)
        self.assertEqual(output, 'Command timed out')
    
    @patch('subprocess.run')
    def test_run_command_exception(self, mock_run):
        """Test command with exception."""
        mock_run.side_effect = Exception('Some error')
        
        code, output = run_command('invalid')
        
        self.assertEqual(code, -1)
        self.assertIn('Some error', output)


class TestExtractNumber(unittest.TestCase):
    """Test extract_number function."""
    
    def test_extract_percentage(self):
        """Test extracting percentage."""
        result = extract_number('Coverage: 85.5%')
        self.assertEqual(result, 85.5)
    
    def test_extract_integer(self):
        """Test extracting integer."""
        result = extract_number('Count: 42')
        self.assertEqual(result, 42.0)
    
    def test_extract_float(self):
        """Test extracting float."""
        result = extract_number('Value: 3.14')
        self.assertEqual(result, 3.14)
    
    def test_extract_no_number(self):
        """Test extracting from text without number."""
        result = extract_number('No numbers here')
        self.assertIsNone(result)
    
    def test_extract_empty(self):
        """Test extracting from empty string."""
        result = extract_number('')
        self.assertIsNone(result)


class TestMainFunction(unittest.TestCase):
    """Test main function."""
    
    @patch('get_baseline.run_command')
    def test_main_success(self, mock_run):
        """Test main with successful command."""
        mock_run.return_value = (0, 'test output')
        
        old_argv = sys.argv
        try:
            sys.argv = ['get_baseline.py', '--verify', 'echo test']
            result = main()
        finally:
            sys.argv = old_argv
        
        self.assertEqual(result, 'test output')
    
    @patch('get_baseline.run_command')
    def test_main_with_parse_number(self, mock_run):
        """Test main with --parse-number flag."""
        mock_run.return_value = (0, 'Coverage: 75%')
        
        old_argv = sys.argv
        try:
            sys.argv = ['get_baseline.py', '--verify', 'echo test', '--parse-number']
            result = main()
        finally:
            sys.argv = old_argv
        
        self.assertEqual(result, 75.0)
    
    @patch('get_baseline.run_command')
    def test_main_with_parse_number_no_match(self, mock_run):
        """Test main with --parse-number but no number found."""
        mock_run.return_value = (0, 'no numbers')
        
        old_argv = sys.argv
        try:
            sys.argv = ['get_baseline.py', '--verify', 'echo test', '--parse-number']
            result = main()
        finally:
            sys.argv = old_argv
        
        # When no number found, returns original output (not None)
        self.assertEqual(result, 'no numbers')
    
    @patch('get_baseline.run_command')
    def test_main_nonzero_exit(self, mock_run):
        """Test main with non-zero exit code."""
        mock_run.return_value = (1, 'error output')
        
        old_argv = sys.argv
        try:
            sys.argv = ['get_baseline.py', '--verify', 'false']
            result = main()
        finally:
            sys.argv = old_argv
        
        self.assertEqual(result, 'error output')


if __name__ == '__main__':
    unittest.main()
