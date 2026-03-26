#!/usr/bin/env python3
"""Tests for autoresearch_health_check.py"""
import unittest
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from autoresearch_health_check import (
    check_git_repository,
    check_git_config,
    check_worktree_clean,
    check_disk_space,
    check_required_tools,
    run_all_checks
)


class TestHealthCheck(unittest.TestCase):
    """Test health check functions."""
    
    def test_check_git_repository(self):
        """Test git repository check."""
        result = check_git_repository()
        
        self.assertIn('name', result)
        self.assertIn('status', result)
        self.assertIn('message', result)
        self.assertEqual(result['name'], 'git_repository')
        
        # Should pass in git repo
        self.assertIn(result['status'], ['pass', 'fail'])
    
    def test_check_git_config(self):
        """Test git config check."""
        result = check_git_config()
        
        self.assertIn('name', result)
        self.assertIn('status', result)
        self.assertIn('message', result)
        self.assertEqual(result['name'], 'git_config')
        
        # Should be pass or warn
        self.assertIn(result['status'], ['pass', 'warn'])
    
    def test_check_worktree_clean(self):
        """Test worktree clean check."""
        result = check_worktree_clean()
        
        self.assertIn('name', result)
        self.assertIn('status', result)
        self.assertIn('message', result)
        self.assertEqual(result['name'], 'worktree')
        
        # Should be pass or warn
        self.assertIn(result['status'], ['pass', 'warn'])
    
    def test_check_disk_space(self):
        """Test disk space check."""
        result = check_disk_space()
        
        self.assertIn('name', result)
        self.assertIn('status', result)
        self.assertIn('message', result)
        self.assertEqual(result['name'], 'disk_space')
        
        # Should be pass, warn, or fail
        self.assertIn(result['status'], ['pass', 'warn', 'fail'])
        
        # Message should contain GB info
        self.assertIn('GB', result['message'])
    
    def test_check_required_tools(self):
        """Test required tools check."""
        result = check_required_tools()
        
        self.assertIn('name', result)
        self.assertIn('status', result)
        self.assertIn('message', result)
        self.assertEqual(result['name'], 'required_tools')
        
        # Git and Python should be available
        self.assertEqual(result['status'], 'pass')
    
    def test_run_all_checks(self):
        """Test running all checks."""
        results = run_all_checks()
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        # Check expected checks are present
        check_names = [r['name'] for r in results]
        expected = ['git_repository', 'git_config', 'worktree', 
                   'disk_space', 'required_tools']
        
        for expected_name in expected:
            self.assertIn(expected_name, check_names)


if __name__ == '__main__':
    unittest.main()
