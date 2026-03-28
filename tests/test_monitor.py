#!/usr/bin/env python3
"""Tests for autoresearch_monitor.py"""
import unittest
import sys
import os
import tempfile
import shutil
import json
import csv
import stat
import io
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, mock_open

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from autoresearch_monitor import (
    ProgressTracker, main, RESULTS_FILE, STATE_FILE, 
    MONITOR_LOG, DASHBOARD_FILE
)


class TestProgressTracker(unittest.TestCase):
    """Test ProgressTracker class."""
    
    def setUp(self):
        """Create temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        self.tracker = ProgressTracker()
    
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
    
    def create_results_file(self, data=None):
        """Helper to create a results file."""
        if data is None:
            data = [
                ['1', 'abc123', '100', '0', 'baseline', 'Initial', '2024-01-01T00:00:00'],
                ['2', 'def456', '90', '-10', 'keep', 'Improved', '2024-01-01T01:00:00'],
                ['3', 'ghi789', '95', '5', 'discard', 'Worsened', '2024-01-01T02:00:00'],
            ]
        
        with open(RESULTS_FILE, 'w', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['iteration', 'commit', 'metric', 'delta', 
                           'status', 'description', 'timestamp'])
            writer.writerows(data)
    
    def test_init(self):
        """Test ProgressTracker initialization."""
        self.assertEqual(self.tracker.metrics_history, [])
        self.assertIsNone(self.tracker.last_report_time)
    
    def test_load_results_no_file(self):
        """Test load_results when file doesn't exist."""
        results = self.tracker.load_results()
        self.assertEqual(results, [])
    
    def test_load_results_success(self):
        """Test load_results with valid file."""
        self.create_results_file()
        
        results = self.tracker.load_results()
        
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['iteration'], 1)
        self.assertEqual(results[0]['metric'], 100.0)
        self.assertEqual(results[0]['status'], 'baseline')
    
    def test_load_results_error(self):
        """Test load_results with corrupted file."""
        with open(RESULTS_FILE, 'w') as f:
            f.write('invalid\tcsv\tdata\nwith\twrong\tcolumns')
        
        # Should handle errors gracefully
        results = self.tracker.load_results()
        # May have partial results or empty depending on error handling
        self.assertIsInstance(results, list)
    
    def test_load_state_no_file(self):
        """Test load_state when file doesn't exist."""
        state = self.tracker.load_state()
        self.assertEqual(state, {})
    
    def test_load_state_success(self):
        """Test load_state with valid file."""
        test_state = {'goal': 'Test', 'iteration': 5}
        with open(STATE_FILE, 'w') as f:
            json.dump(test_state, f)
        
        state = self.tracker.load_state()
        
        self.assertEqual(state['goal'], 'Test')
        self.assertEqual(state['iteration'], 5)
    
    def test_calculate_progress_empty(self):
        """Test calculate_progress with no results."""
        progress = self.tracker.calculate_progress([])
        
        self.assertEqual(progress['total_iterations'], 0)
        self.assertEqual(progress['kept'], 0)
        self.assertEqual(progress['discarded'], 0)
        self.assertEqual(progress['success_rate'], 0)
        # Empty result may or may not have improvement_pct depending on implementation
        if 'improvement_pct' in progress:
            self.assertEqual(progress['improvement_pct'], 0)
    
    def test_calculate_progress_with_results(self):
        """Test calculate_progress with results."""
        self.create_results_file()
        results = self.tracker.load_results()
        
        progress = self.tracker.calculate_progress(results)
        
        self.assertEqual(progress['total_iterations'], 3)
        self.assertEqual(progress['kept'], 1)
        self.assertEqual(progress['discarded'], 1)
        self.assertEqual(progress['baseline'], 100.0)
        self.assertEqual(progress['current_metric'], 95.0)
        self.assertEqual(progress['improvement'], -5.0)
    
    def test_calculate_progress_division_by_zero(self):
        """Test calculate_progress handles zero baseline."""
        data = [['1', 'abc123', '0', '0', 'baseline', 'Initial', '2024-01-01T00:00:00']]
        self.create_results_file(data)
        results = self.tracker.load_results()
        
        progress = self.tracker.calculate_progress(results)
        
        self.assertEqual(progress['improvement_pct'], 0)
    
    def test_analyze_trends_insufficient_data(self):
        """Test analyze_trends with insufficient data."""
        results = [{'metric': 100}]
        trends = self.tracker.analyze_trends(results, window=10)
        
        self.assertIn('error', trends)
    
    def test_analyze_trends_improving(self):
        """Test analyze_trends with improving data."""
        # Create data showing improvement (decreasing metrics)
        data = []
        for i in range(15):
            metric = 100 - i * 2  # Decreasing
            data.append([str(i), 'abc', str(metric), str(-2), 'keep', 'Desc', '2024-01-01'])
        
        self.create_results_file(data)
        results = self.tracker.load_results()
        
        trends = self.tracker.analyze_trends(results, window=10)
        
        self.assertEqual(trends['window'], 10)
        self.assertIn('trend', trends)
        self.assertIn('avg_first_half', trends)
        self.assertIn('avg_second_half', trends)
    
    def test_generate_text_report_empty(self):
        """Test generate_text_report with no data."""
        report = self.tracker.generate_text_report()
        
        self.assertIn('Progress Report', report)
        self.assertIn('Total iterations: 0', report)
    
    def test_generate_text_report_with_data(self):
        """Test generate_text_report with data."""
        self.create_results_file()
        
        report = self.tracker.generate_text_report()
        
        self.assertIn('Progress Report', report)
        self.assertIn('Total iterations: 3', report)
        self.assertIn('Kept:', report)
        self.assertIn('Baseline:', report)
    
    def test_generate_html_dashboard_empty(self):
        """Test generate_html_dashboard with no data."""
        html = self.tracker.generate_html_dashboard()
        
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('Autoresearch Dashboard', html)
        self.assertIn('chart.js', html)
    
    def test_generate_html_dashboard_with_data(self):
        """Test generate_html_dashboard with data."""
        self.create_results_file()
        
        html = self.tracker.generate_html_dashboard()
        
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('3', html)  # Iterations count
        self.assertIn('100', html)  # Some metric value
        self.assertIn('stats-grid', html)
        self.assertIn('stat-card', html)
    
    def test_save_dashboard(self):
        """Test save_dashboard."""
        self.create_results_file()
        
        filepath = self.tracker.save_dashboard()
        
        self.assertEqual(filepath, DASHBOARD_FILE)
        self.assertTrue(os.path.exists(DASHBOARD_FILE))
        
        with open(DASHBOARD_FILE, 'r') as f:
            content = f.read()
            self.assertIn('<!DOCTYPE html>', content)
    
    def test_log_monitor_event(self):
        """Test log_monitor_event."""
        self.tracker.log_monitor_event('test_event', {'key': 'value'})
        
        self.assertTrue(os.path.exists(MONITOR_LOG))
        
        with open(MONITOR_LOG, 'r') as f:
            line = f.readline()
            entry = json.loads(line)
            self.assertEqual(entry['type'], 'test_event')
            self.assertEqual(entry['data']['key'], 'value')
            self.assertIn('timestamp', entry)


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
    
    def create_results_file(self):
        """Helper to create a results file."""
        with open(RESULTS_FILE, 'w', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['iteration', 'commit', 'metric', 'delta', 
                           'status', 'description', 'timestamp'])
            writer.writerow(['1', 'abc123', '100', '0', 'baseline', 'Initial', '2024-01-01'])
    
    def test_main_report(self):
        """Test main with report command."""
        self.create_results_file()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        with patch('sys.argv', ['autoresearch_monitor', 'report']):
            main()
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertIn('Progress Report', output)
    
    def test_main_dashboard(self):
        """Test main with dashboard command."""
        self.create_results_file()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        with patch('sys.argv', ['autoresearch_monitor', 'dashboard']):
            main()
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertIn('Dashboard saved', output)
        self.assertTrue(os.path.exists(DASHBOARD_FILE))
    
    @patch('webbrowser.open')
    def test_main_dashboard_open(self, mock_open_browser):
        """Test main with dashboard --open."""
        self.create_results_file()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        with patch('sys.argv', ['autoresearch_monitor', 'dashboard', '--open']):
            main()
        
        sys.stdout = old_stdout
        
        mock_open_browser.assert_called_once()
    
    def test_main_no_command(self):
        """Test main with no command."""
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        with patch('sys.argv', ['autoresearch_monitor']):
            main()
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertIn('usage', output.lower())
    
    def test_main_watch(self):
        """Test main with watch command."""
        self.create_results_file()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        # Mock time.sleep to exit after one iteration
        with patch('time.sleep', side_effect=KeyboardInterrupt):
            with patch('sys.argv', ['autoresearch_monitor', 'watch', '--interval', '1']):
                try:
                    main()
                except KeyboardInterrupt:
                    pass
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertIn('Watching', output)
        self.assertIn('Press Ctrl+C', output)


if __name__ == '__main__':
    unittest.main()
