#!/usr/bin/env python3
"""Tests for check_git.py"""
import unittest
import sys
import os
import tempfile
import shutil
import io

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from check_git import run_git, is_git_repo, has_changes, get_current_commit, stash_changes, main


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
        # Handle Windows permission issues with .git directory
        import stat
        import time
        
        def on_rm_error(func, path, exc_info):
            # Try to change permissions and retry
            os.chmod(path, stat.S_IWRITE)
            try:
                func(path)
            except:
                pass
        
        # Retry a few times for Windows file locks
        for _ in range(3):
            try:
                shutil.rmtree(self.temp_dir, onerror=on_rm_error)
                break
            except PermissionError:
                time.sleep(0.1)
    
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
    
    def test_stash_changes(self):
        """Test stash_changes function."""
        # Create and commit initial file
        with open('test.txt', 'w') as f:
            f.write('initial')
        run_git(['add', '.'])
        run_git(['commit', '-m', 'initial'])
        
        # Make changes
        with open('test.txt', 'w') as f:
            f.write('modified')
        
        self.assertTrue(has_changes())
        
        # Stash changes
        result = stash_changes()
        self.assertTrue(result)
        
        # Should be clean after stash
        self.assertFalse(has_changes())


class TestMainFunction(unittest.TestCase):
    """Test main CLI function."""
    
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
        import stat
        import time
        
        def on_rm_error(func, path, exc_info):
            os.chmod(path, stat.S_IWRITE)
            try:
                func(path)
            except:
                pass
        
        for _ in range(3):
            try:
                shutil.rmtree(self.temp_dir, onerror=on_rm_error)
                break
            except PermissionError:
                time.sleep(0.1)
    
    def test_main_check_clean(self):
        """Test main with check action on clean repo."""
        old_argv = sys.argv
        try:
            sys.argv = ['check_git.py', '--action', 'check']
            
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            with self.assertRaises(SystemExit) as cm:
                main()
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            self.assertEqual(cm.exception.code, 0)
            self.assertIn("clean", output)
        finally:
            sys.argv = old_argv
    
    def test_main_check_with_changes(self):
        """Test main with check action when there are changes."""
        # Create a file
        with open('test.txt', 'w') as f:
            f.write('test')
        
        old_argv = sys.argv
        try:
            sys.argv = ['check_git.py', '--action', 'check']
            
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            with self.assertRaises(SystemExit) as cm:
                main()
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            self.assertEqual(cm.exception.code, 0)
            self.assertIn("has_changes", output)
        finally:
            sys.argv = old_argv
    
    def test_main_commit_hash(self):
        """Test main with commit-hash action."""
        # Create and commit a file
        with open('test.txt', 'w') as f:
            f.write('test')
        run_git(['add', '.'])
        run_git(['commit', '-m', 'test'])
        
        old_argv = sys.argv
        try:
            sys.argv = ['check_git.py', '--action', 'commit-hash']
            
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            with self.assertRaises(SystemExit) as cm:
                main()
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            self.assertEqual(cm.exception.code, 0)
            # Output should be a commit hash (7 chars)
            self.assertEqual(len(output.strip()), 7)
        finally:
            sys.argv = old_argv
    
    def test_main_stash_with_changes(self):
        """Test main with stash action when there are changes."""
        # Create and commit initial file
        with open('test.txt', 'w') as f:
            f.write('initial')
        run_git(['add', '.'])
        run_git(['commit', '-m', 'initial'])
        
        # Make changes
        with open('test.txt', 'w') as f:
            f.write('modified')
        
        old_argv = sys.argv
        try:
            sys.argv = ['check_git.py', '--action', 'stash']
            
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            with self.assertRaises(SystemExit) as cm:
                main()
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            self.assertEqual(cm.exception.code, 0)
            self.assertIn("stashed", output)
        finally:
            sys.argv = old_argv
    
    def test_main_stash_nothing_to_stash(self):
        """Test main with stash action when clean."""
        old_argv = sys.argv
        try:
            sys.argv = ['check_git.py', '--action', 'stash']
            
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            with self.assertRaises(SystemExit) as cm:
                main()
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            self.assertEqual(cm.exception.code, 0)
            self.assertIn("nothing_to_stash", output)
        finally:
            sys.argv = old_argv
    
    def test_main_commit(self):
        """Test main with commit action."""
        # Create a file
        with open('test.txt', 'w') as f:
            f.write('test')
        
        old_argv = sys.argv
        try:
            sys.argv = ['check_git.py', '--action', 'commit', '--message', 'Test commit']
            
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            with self.assertRaises(SystemExit) as cm:
                main()
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            self.assertEqual(cm.exception.code, 0)
            self.assertIn("committed:", output)
            
            # Verify commit was made
            self.assertFalse(has_changes())
        finally:
            sys.argv = old_argv


class TestMainNotGitRepo(unittest.TestCase):
    """Test main when not in git repo."""
    
    def setUp(self):
        """Create temporary directory (not git repo)."""
        self.temp_dir = tempfile.mkdtemp()
        self.orig_dir = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        os.chdir(self.orig_dir)
        shutil.rmtree(self.temp_dir, onerror=lambda f, p, e: None)
    
    def test_main_not_git_repo(self):
        """Test main exits with error when not in git repo."""
        old_argv = sys.argv
        try:
            sys.argv = ['check_git.py', '--action', 'check']
            
            captured_stderr = io.StringIO()
            old_stderr = sys.stderr
            sys.stderr = captured_stderr
            
            with self.assertRaises(SystemExit) as cm:
                main()
            
            sys.stderr = old_stderr
            output = captured_stderr.getvalue()
            
            self.assertEqual(cm.exception.code, 1)
            self.assertIn("Not a git repository", output)
        finally:
            sys.argv = old_argv


if __name__ == '__main__':
    unittest.main()
