#!/usr/bin/env python3
"""Tests for check_git.py"""
import unittest
import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from check_git import run_git, is_git_repo, has_changes, get_current_commit


class TestGitOperations(unittest.TestCase):
    """Test git operation functions."""
    
    def setUp(self):
        """Create temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.orig_dir = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        os.chdir(self.orig_dir)
        shutil.rmtree(self.temp_dir)
    
    def test_is_git_repo_false(self):
        """Test is_git_repo returns False for non-git directory."""
        self.assertFalse(is_git_repo())
    
    def test_run_git_status(self):
        """Test running git status."""
        # Should fail (not a git repo)
        code, output = run_git(['status'])
        self.assertNotEqual(code, 0)
    
    def test_get_current_commit_unknown(self):
        """Test get_current_commit when not in git repo."""
        commit = get_current_commit()
        self.assertEqual(commit, "unknown")


class TestGitOperationsInRepo(unittest.TestCase):
    """Test git operations in actual git repo."""
    
    def setUp(self):
        """Create temporary git repository."""
        self.temp_dir = tempfile.mkdtemp()
        self.orig_dir = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Initialize git repo
        run_git(['init'])
        run_git(['config', 'user.name', 'Test'])
        run_git(['config', 'user.email', 'test@test.com'])
    
    def tearDown(self):
        """Clean up."""
        os.chdir(self.orig_dir)
        shutil.rmtree(self.temp_dir)
    
    def test_is_git_repo_true(self):
        """Test is_git_repo returns True for git directory."""
        self.assertTrue(is_git_repo())
    
    def test_has_changes_false(self):
        """Test has_changes returns False for clean repo."""
        self.assertFalse(has_changes())
    
    def test_has_changes_true(self):
        """Test has_changes returns True when there are changes."""
        # Create a file
        with open('test.txt', 'w') as f:
            f.write('test')
        
        self.assertTrue(has_changes())
    
    def test_get_current_commit(self):
        """Test get_current_commit returns commit hash."""
        # Create file and commit
        with open('test.txt', 'w') as f:
            f.write('test')
        run_git(['add', '.'])
        run_git(['commit', '-m', 'test'])
        
        commit = get_current_commit()
        self.assertNotEqual(commit, "unknown")
        self.assertEqual(len(commit), 7)  # Short hash


if __name__ == '__main__':
    unittest.main()
