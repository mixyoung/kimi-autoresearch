#!/usr/bin/env python3
"""Tests for autoresearch_analyze.py"""
import unittest
import sys
import os
import tempfile
import json
import csv
import io
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from autoresearch_analyze import (
    load_results, analyze_trends, analyze_by_window, analyze_strategies,
    cmd_trends, cmd_windows, cmd_strategies, main, RESULTS_FILE
)


class TestLoadResults(unittest.TestCase):
    """Test load_results function."""
    
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
    
    def test_load_results_no_file(self):
        """Test loading results when no file exists."""
        results = load_results()
        self.assertEqual(results, [])
    
    def test_load_results_with_file(self):
        """Test loading results from file."""
        with open(RESULTS_FILE, 'w', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['iteration', 'commit', 'metric', 'delta', 'status'])
            writer.writerow(['0', 'abc', '100', '0', 'baseline'])
            writer.writerow(['1', 'def', '90', '-10', 'keep'])
        
        results = load_results()
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['iteration'], '0')
        self.assertEqual(results[1]['status'], 'keep')


class TestAnalyzeTrends(unittest.TestCase):
    """Test analyze_trends function."""
    
    def test_analyze_empty_results(self):
        """Test analyzing empty results."""
        result = analyze_trends([])
        
        self.assertIn('error', result)
        self.assertEqual(result['error'], 'No results found')
    
    def test_analyze_basic_results(self):
        """Test analyzing basic results."""
        results = [
            {'iteration': '0', 'commit': 'abc', 'metric': '100', 'delta': '0', 'status': 'baseline'},
            {'iteration': '1', 'commit': 'def', 'metric': '90', 'delta': '-10', 'status': 'keep'},
            {'iteration': '2', 'commit': 'ghi', 'metric': '85', 'delta': '-5', 'status': 'keep'},
        ]
        
        result = analyze_trends(results)
        
        self.assertEqual(result['total_iterations'], 3)
        self.assertEqual(result['baseline_count'], 1)
        self.assertEqual(result['keep_count'], 2)
        self.assertEqual(result['discard_count'], 0)
        self.assertEqual(result['success_rate'], 100.0)
    
    def test_analyze_with_discards(self):
        """Test analyzing results with discards."""
        results = [
            {'iteration': '0', 'commit': 'abc', 'metric': '100', 'delta': '0', 'status': 'baseline'},
            {'iteration': '1', 'commit': 'def', 'metric': '110', 'delta': '+10', 'status': 'discard'},
            {'iteration': '2', 'commit': 'ghi', 'metric': '90', 'delta': '-10', 'status': 'keep'},
        ]
        
        result = analyze_trends(results)
        
        self.assertEqual(result['total_iterations'], 3)
        self.assertEqual(result['keep_count'], 1)
        self.assertEqual(result['discard_count'], 1)
        self.assertEqual(result['success_rate'], 50.0)
    
    def test_analyze_metrics(self):
        """Test metric analysis."""
        results = [
            {'iteration': '0', 'commit': 'abc', 'metric': '100', 'delta': '0', 'status': 'baseline'},
            {'iteration': '1', 'commit': 'def', 'metric': '90', 'delta': '-10', 'status': 'keep'},
            {'iteration': '2', 'commit': 'ghi', 'metric': '80', 'delta': '-10', 'status': 'keep'},
        ]
        
        result = analyze_trends(results)
        
        self.assertIn('metrics', result)
        m = result['metrics']
        self.assertEqual(m['initial'], 100.0)
        self.assertEqual(m['final'], 80.0)
        self.assertEqual(m['min'], 80.0)
        self.assertEqual(m['max'], 100.0)
        self.assertEqual(m['improvement'], -20.0)
    
    def test_analyze_streaks(self):
        """Test streak analysis."""
        results = [
            {'iteration': '0', 'commit': 'a', 'metric': '100', 'delta': '0', 'status': 'baseline'},
            {'iteration': '1', 'commit': 'b', 'metric': '90', 'delta': '-10', 'status': 'keep'},
            {'iteration': '2', 'commit': 'c', 'metric': '80', 'delta': '-10', 'status': 'keep'},
            {'iteration': '3', 'commit': 'd', 'metric': '85', 'delta': '+5', 'status': 'discard'},
        ]
        
        result = analyze_trends(results)
        
        self.assertIn('streaks', result)
        s = result['streaks']
        self.assertEqual(s['longest_keep'], 2)


class TestAnalyzeByWindow(unittest.TestCase):
    """Test analyze_by_window function."""
    
    def test_empty_results(self):
        """Test with empty results."""
        windows = analyze_by_window([], 10)
        self.assertEqual(windows, [])
    
    def test_window_analysis(self):
        """Test window analysis."""
        results = [
            {'iteration': '0', 'status': 'baseline'},
            {'iteration': '1', 'status': 'keep'},
            {'iteration': '2', 'status': 'keep'},
            {'iteration': '3', 'status': 'discard'},
            {'iteration': '4', 'status': 'keep'},
        ]
        
        windows = analyze_by_window(results, window_size=2)
        
        self.assertEqual(len(windows), 2)  # 2 windows of 2 iterations each
        self.assertEqual(windows[0]['keep_count'], 2)
        self.assertEqual(windows[0]['discard_count'], 0)
    
    def test_trend_indicator(self):
        """Test trend in windows."""
        results = [
            {'iteration': '0', 'status': 'baseline'},
            {'iteration': '1', 'status': 'discard'},
            {'iteration': '2', 'status': 'discard'},
            {'iteration': '3', 'status': 'keep'},
            {'iteration': '4', 'status': 'keep'},
        ]
        
        windows = analyze_by_window(results, window_size=2)
        
        self.assertEqual(len(windows), 2)
        self.assertEqual(windows[0]['success_rate'], 0.0)
        self.assertEqual(windows[1]['success_rate'], 100.0)


class TestAnalyzeStrategies(unittest.TestCase):
    """Test analyze_strategies function."""
    
    def test_analyze_strategies(self):
        """Test strategy effectiveness analysis."""
        results = [
            {'status': 'keep', 'description': 'Fixed type errors in utils'},
            {'status': 'keep', 'description': 'Fixed type errors in api'},
            {'status': 'discard', 'description': 'Fixed type errors in main'},
            {'status': 'keep', 'description': 'Added null checks'},
        ]
        
        strategies = analyze_strategies(results)
        
        self.assertIsInstance(strategies, dict)
        # Should have at least 2 strategies (based on first 3 words)
        self.assertGreaterEqual(len(strategies), 2)


class TestCmdTrends(unittest.TestCase):
    """Test cmd_trends function."""
    
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
    
    def test_trends_no_results(self):
        """Test trends with no results."""
        args = MagicMock()
        args.json = False
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_trends(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 1)
        self.assertIn('No results', output)
    
    def test_trends_with_results(self):
        """Test trends with results."""
        with open(RESULTS_FILE, 'w', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['iteration', 'commit', 'metric', 'delta', 'status'])
            writer.writerow(['0', 'abc', '100', '0', 'baseline'])
            writer.writerow(['1', 'def', '90', '-10', 'keep'])
        
        args = MagicMock()
        args.json = False
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_trends(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Autoresearch Trend Analysis', output)
        self.assertIn('Total iterations', output)


class TestCmdWindows(unittest.TestCase):
    """Test cmd_windows function."""
    
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
    
    def test_windows_no_results(self):
        """Test windows with no results."""
        args = MagicMock()
        args.json = False
        args.size = 10
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_windows(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 1)
        self.assertIn('No results', output)


class TestCmdStrategies(unittest.TestCase):
    """Test cmd_strategies function."""
    
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
    
    def test_strategies_no_results(self):
        """Test strategies with no results."""
        args = MagicMock()
        args.json = False
        args.top = 10
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_strategies(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 1)
        self.assertIn('No results', output)


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
    
    def test_main_trends(self):
        """Test main with trends command."""
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_analyze.py', 'trends']
            result = main()
            self.assertEqual(result, 1)  # No results file
        finally:
            sys.argv = old_argv
    
    def test_main_no_command(self):
        """Test main with no command."""
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_analyze.py']
            result = main()
            self.assertEqual(result, 1)
        finally:
            sys.argv = old_argv


if __name__ == '__main__':
    unittest.main()
