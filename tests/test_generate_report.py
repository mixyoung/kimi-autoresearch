#!/usr/bin/env python3
"""Tests for generate_report.py"""
import unittest
import sys
import os
import tempfile
import csv
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from generate_report import generate_report, main, RESULTS_FILE, REPORT_FILE


class TestGenerateReport(unittest.TestCase):
    """Test generate_report function."""
    
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
    
    def _create_results_file(self, rows):
        """Helper to create results TSV file."""
        with open(RESULTS_FILE, 'w', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['iteration', 'commit', 'metric', 'delta', 
                           'status', 'description', 'timestamp'])
            for row in rows:
                writer.writerow(row)
    
    def test_no_results_file(self):
        """Test behavior when no results file exists."""
        import io
        import sys
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        generate_report()
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertIn("No results file found", output)
    
    def test_empty_results_file(self):
        """Test behavior with empty results file."""
        import io
        import sys
        
        # Create empty file with just headers
        with open(RESULTS_FILE, 'w', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['iteration', 'commit', 'metric', 'delta', 
                           'status', 'description', 'timestamp'])
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        generate_report()
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertIn("No data in results file", output)
    
    def test_generates_report(self):
        """Test that report file is generated."""
        rows = [
            ['0', 'abc123', '100', '0', 'baseline', 'Initial', '2024-01-01'],
            ['1', 'def456', '90', '-10', 'keep', 'Improved', '2024-01-02'],
        ]
        self._create_results_file(rows)
        
        generate_report()
        
        self.assertTrue(os.path.exists(REPORT_FILE))
    
    def test_report_contains_summary(self):
        """Test that report contains summary statistics."""
        rows = [
            ['0', 'abc123', '100', '0', 'baseline', 'Initial', '2024-01-01'],
            ['1', 'def456', '90', '-10', 'keep', 'Improved', '2024-01-02'],
            ['2', 'ghi789', '95', '+5', 'discard', 'Worse', '2024-01-03'],
        ]
        self._create_results_file(rows)
        
        generate_report()
        
        with open(REPORT_FILE, 'r') as f:
            content = f.read()
        
        self.assertIn("Total Iterations", content)
        self.assertIn("Successful (keep)", content)
        self.assertIn("Discarded", content)
        self.assertIn("Success Rate", content)
    
    def test_report_contains_baseline_and_best(self):
        """Test that report contains baseline and best comparison."""
        rows = [
            ['0', 'abc123def456', '100', '0', 'baseline', 'Initial', '2024-01-01'],
            ['1', 'def456ghi789', '90', '-10', 'keep', 'Improved', '2024-01-02'],
        ]
        self._create_results_file(rows)
        
        generate_report()
        
        with open(REPORT_FILE, 'r') as f:
            content = f.read()
        
        self.assertIn("Baseline", content)
        self.assertIn("Best", content)
        self.assertIn("abc123de", content)  # Short commit hash
    
    def test_report_contains_all_iterations(self):
        """Test that report contains all iterations table."""
        rows = [
            ['0', 'abc123', '100', '0', 'baseline', 'Initial', '2024-01-01'],
            ['1', 'def456', '90', '-10', 'keep', 'Improved', '2024-01-02'],
        ]
        self._create_results_file(rows)
        
        generate_report()
        
        with open(REPORT_FILE, 'r') as f:
            content = f.read()
        
        self.assertIn("All Iterations", content)
        self.assertIn("baseline", content)
        self.assertIn("keep", content)
    
    def test_report_contains_key_decisions(self):
        """Test that report contains key decisions section."""
        rows = [
            ['0', 'abc123', '100', '0', 'baseline', 'Initial', '2024-01-01'],
            ['1', 'def456', '90', '-10', 'keep', 'Fixed bug', '2024-01-02'],
            ['2', 'ghi789', '95', '+5', 'discard', 'Revert', '2024-01-03'],
        ]
        self._create_results_file(rows)
        
        generate_report()
        
        with open(REPORT_FILE, 'r') as f:
            content = f.read()
        
        self.assertIn("Key Decisions", content)
        # Check that key decisions section contains the keep decision
        key_decisions_section = content.split("## Key Decisions")[1]
        self.assertIn("Fixed bug", key_decisions_section)
        # Baseline (iteration 0) should not be in key decisions
        self.assertNotIn("Iteration 0", key_decisions_section)
    
    def test_success_rate_calculation(self):
        """Test that success rate is calculated correctly."""
        rows = [
            ['0', 'abc123', '100', '0', 'baseline', 'Initial', '2024-01-01'],
            ['1', 'def456', '90', '-10', 'keep', 'Improved', '2024-01-02'],
            ['2', 'ghi789', '95', '+5', 'keep', 'Better', '2024-01-03'],
            ['3', 'jkl012', '98', '+3', 'discard', 'Worse', '2024-01-04'],
        ]
        self._create_results_file(rows)
        
        generate_report()
        
        with open(REPORT_FILE, 'r') as f:
            content = f.read()
        
        # 2 keep / 3 total (excluding baseline) = 66.7%
        self.assertIn("66.7%", content)
    
    def test_description_truncation(self):
        """Test that long descriptions are truncated."""
        long_desc = "A" * 100
        rows = [
            ['0', 'abc123', '100', '0', 'baseline', long_desc, '2024-01-01'],
        ]
        self._create_results_file(rows)
        
        generate_report()
        
        with open(REPORT_FILE, 'r') as f:
            content = f.read()
        
        # Description should be truncated to 50 chars
        self.assertNotIn("A" * 60, content)


class TestMainFunction(unittest.TestCase):
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
    
    def test_main_calls_generate_report(self):
        """Test that main function calls generate_report."""
        # Create results file
        with open(RESULTS_FILE, 'w', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['iteration', 'commit', 'metric', 'delta', 
                           'status', 'description', 'timestamp'])
            writer.writerow(['0', 'abc123', '100', '0', 'baseline', 'Initial', '2024-01-01'])
        
        main()
        
        self.assertTrue(os.path.exists(REPORT_FILE))


if __name__ == '__main__':
    unittest.main()
