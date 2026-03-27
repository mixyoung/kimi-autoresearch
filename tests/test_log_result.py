#!/usr/bin/env python3
"""Tests for log_result.py"""
import unittest
import sys
import os
import tempfile
import csv
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from log_result import log_result, main, RESULTS_FILE


class TestLogResult(unittest.TestCase):
    """Test log_result function."""
    
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
    
    def test_log_result_creates_file(self):
        """Test that log_result creates the TSV file."""
        log_result(1, 'abc123', '50', '+5', 'keep', 'Test description')
        
        self.assertTrue(os.path.exists(RESULTS_FILE))
    
    def test_log_result_writes_headers(self):
        """Test that log_result writes headers for new file."""
        log_result(1, 'abc123', '50', '+5', 'keep', 'Test description')
        
        with open(RESULTS_FILE, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            rows = list(reader)
        
        self.assertEqual(rows[0], ['iteration', 'commit', 'metric', 'delta', 
                                   'status', 'description', 'timestamp'])
    
    def test_log_result_appends_row(self):
        """Test that log_result appends data row."""
        log_result(1, 'abc123', '50', '+5', 'keep', 'Test description')
        
        with open(RESULTS_FILE, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            rows = list(reader)
        
        self.assertEqual(rows[1][0], '1')
        self.assertEqual(rows[1][1], 'abc123')
        self.assertEqual(rows[1][2], '50')
        self.assertEqual(rows[1][4], 'keep')
        self.assertEqual(rows[1][5], 'Test description')
    
    def test_log_result_appends_multiple(self):
        """Test that log_result appends multiple rows."""
        log_result(1, 'abc123', '50', '0', 'baseline', 'Initial')
        log_result(2, 'def456', '45', '-5', 'keep', 'Improved')
        
        with open(RESULTS_FILE, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            rows = list(reader)
        
        self.assertEqual(len(rows), 3)  # header + 2 data rows
        self.assertEqual(rows[1][0], '1')
        self.assertEqual(rows[2][0], '2')
    
    def test_log_result_all_statuses(self):
        """Test log_result with all valid statuses."""
        statuses = ['baseline', 'keep', 'discard', 'crash']
        
        for i, status in enumerate(statuses):
            log_result(i, f'commit{i}', str(50-i), str(-i), status, f'Desc {i}')
        
        with open(RESULTS_FILE, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            rows = list(reader)
        
        self.assertEqual(len(rows), 5)  # header + 4 data rows


class TestMainFunction(unittest.TestCase):
    """Test main function with CLI args."""
    
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
    
    def test_main_with_required_args(self):
        """Test main with all required arguments."""
        old_argv = sys.argv
        try:
            sys.argv = [
                'log_result.py',
                '--iteration', '5',
                '--commit', 'abc123def',
                '--metric', '42',
                '--status', 'keep',
                '--description', 'Fixed type errors'
            ]
            main()
        finally:
            sys.argv = old_argv
        
        with open(RESULTS_FILE, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            rows = list(reader)
        
        self.assertEqual(rows[1][0], '5')
        self.assertEqual(rows[1][4], 'keep')
    
    def test_main_with_default_delta(self):
        """Test main uses default delta value."""
        old_argv = sys.argv
        try:
            sys.argv = [
                'log_result.py',
                '--iteration', '1',
                '--commit', 'abc',
                '--metric', '100',
                '--status', 'baseline',
                '--description', 'Start'
            ]
            main()
        finally:
            sys.argv = old_argv
        
        with open(RESULTS_FILE, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            rows = list(reader)
        
        self.assertEqual(rows[1][3], '0')  # default delta


if __name__ == '__main__':
    unittest.main()
