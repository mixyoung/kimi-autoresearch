#!/usr/bin/env python3
"""Tests for run_iteration.py"""
import unittest
import sys
import os
import tempfile
from io import StringIO
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from run_iteration import (
    run_command, extract_number, is_significant_improvement,
    MIN_DELTA_THRESHOLD
)


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
    
    @patch('subprocess.run')
    def test_run_command_custom_timeout(self, mock_run):
        """Test command with custom timeout."""
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        
        run_command('echo test', timeout=600)
        
        # Verify timeout was passed
        call_kwargs = mock_run.call_args[1]
        self.assertEqual(call_kwargs['timeout'], 600)


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


class TestIsSignificantImprovement(unittest.TestCase):
    """Test is_significant_improvement function."""
    
    def test_improvement_lower(self):
        """Test significant improvement for lower direction."""
        result = is_significant_improvement(
            current=40, baseline=50, direction='lower', threshold=1.0
        )
        self.assertTrue(result)
    
    def test_no_improvement_lower(self):
        """Test no improvement for lower direction."""
        result = is_significant_improvement(
            current=49, baseline=50, direction='lower', threshold=1.0
        )
        self.assertFalse(result)
    
    def test_improvement_higher(self):
        """Test significant improvement for higher direction."""
        result = is_significant_improvement(
            current=60, baseline=50, direction='higher', threshold=1.0
        )
        self.assertTrue(result)
    
    def test_no_improvement_higher(self):
        """Test no improvement for higher direction."""
        result = is_significant_improvement(
            current=50.5, baseline=50, direction='higher', threshold=1.0
        )
        self.assertFalse(result)
    
    def test_worse_lower(self):
        """Test worse metric for lower direction."""
        result = is_significant_improvement(
            current=60, baseline=50, direction='lower', threshold=1.0
        )
        self.assertFalse(result)
    
    def test_worse_higher(self):
        """Test worse metric for higher direction."""
        result = is_significant_improvement(
            current=40, baseline=50, direction='higher', threshold=1.0
        )
        self.assertFalse(result)
    
    def test_default_threshold(self):
        """Test with default threshold."""
        result = is_significant_improvement(
            current=40, baseline=50, direction='lower'
        )
        self.assertTrue(result)  # 10 > 0.5


class TestConstants(unittest.TestCase):
    """Test module constants."""
    
    def test_min_delta_threshold(self):
        """Test MIN_DELTA_THRESHOLD constant."""
        self.assertEqual(MIN_DELTA_THRESHOLD, 0.5)


if __name__ == '__main__':
    unittest.main()
