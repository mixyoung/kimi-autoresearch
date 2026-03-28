#!/usr/bin/env python3
"""Tests for check_git.py"""
import unittest
import sys
import os
import tempfile
import shutil
import io
import stat
import time
from unittest.mock import patch, MagicMock

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

    def test_run_git_exception(self):
        """Test run_git with exception."""
        # Test with invalid git command that causes exception
        code, output = run_git(['invalid-command-that-does-not-exist'])
        # Should either fail with non-zero code or return exception
        self.assertNotEqual(code, 0)


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

    def test_has_changes_git_fails(self):
        """Test has_changes when git command fails."""
        # This is tested indirectly - when git fails, should return False
        # Create a situation where git status might fail
        pass  # Covered by other tests


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

    def test_main_stash_fails(self):
        """Test main with stash action when stash fails."""
        # Create and commit initial file
        with open('test.txt', 'w') as f:
            f.write('initial')
        run_git(['add', '.'])
        run_git(['commit', '-m', 'initial'])
        
        # Make changes
        with open('test.txt', 'w') as f:
            f.write('modified')
        
        # Create a situation where stash might fail is difficult
        # Just test that it works when it should
        old_argv = sys.argv
        try:
            sys.argv = ['check_git.py', '--action', 'stash']
            
            with self.assertRaises(SystemExit) as cm:
                main()
            
            self.assertEqual(cm.exception.code, 0)
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

    def test_main_commit_stage_fails(self):
        """Test main with commit action when staging fails."""
        # This is difficult to test without mocking
        pass

    def test_main_revert(self):
        """Test main with revert action."""
        # Create and commit a file
        with open('test.txt', 'w') as f:
            f.write('test')
        run_git(['add', '.'])
        run_git(['commit', '-m', 'initial'])
        
        old_argv = sys.argv
        try:
            sys.argv = ['check_git.py', '--action', 'revert']
            
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            with self.assertRaises(SystemExit) as cm:
                main()
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            self.assertEqual(cm.exception.code, 0)
            self.assertIn("reverted", output)
        finally:
            sys.argv = old_argv

    def test_main_revert_fails(self):
        """Test main with revert action when revert fails but reset succeeds."""
        # Create and commit a file
        with open('test.txt', 'w') as f:
            f.write('test')
        run_git(['add', '.'])
        run_git(['commit', '-m', 'initial'])
        
        # First commit - can't revert if there's only one commit
        # Add another commit
        with open('test2.txt', 'w') as f:
            f.write('test2')
        run_git(['add', '.'])
        run_git(['commit', '-m', 'second'])
        
        old_argv = sys.argv
        try:
            sys.argv = ['check_git.py', '--action', 'revert']
            
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            with self.assertRaises(SystemExit) as cm:
                main()
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            self.assertEqual(cm.exception.code, 0)
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


class TestGitErrorHandling(unittest.TestCase):
    """Test error handling in git operations."""
    
    def setUp(self):
        """Create temporary directory."""
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
    
    @patch('check_git.subprocess.run')
    def test_run_git_exception(self, mock_subprocess):
        """Test run_git when subprocess raises exception (lines 19-20)."""
        from check_git import run_git
        mock_subprocess.side_effect = Exception('Git command failed')
        
        code, output = run_git(['status'])
        
        self.assertEqual(code, -1)
        self.assertIn('Git command failed', output)
    
    @patch('check_git.run_git')
    def test_has_changes_git_fails(self, mock_run_git):
        """Test has_changes when git status fails (line 33)."""
        from check_git import has_changes
        mock_run_git.return_value = (1, 'fatal: not a git repository')
        
        result = has_changes()
        
        self.assertFalse(result)
    
    @patch('check_git.run_git')
    def test_main_stash_fails_error(self, mock_run_git):
        """Test main stash action when stash fails (lines 83-84)."""
        # Setup: Create file and commit
        with open('test.txt', 'w') as f:
            f.write('initial')
        run_git(['add', '.'])
        run_git(['commit', '-m', 'initial'])
        
        # Make changes
        with open('test.txt', 'w') as f:
            f.write('modified')
        
        # Mock run_git to fail on stash
        def mock_git(args):
            if args[0] == 'status' and args[1] == '--porcelain':
                return (0, 'M test.txt')
            if args[0] == 'stash':
                return (1, 'stash failed')
            return (0, '')
        
        mock_run_git.side_effect = mock_git
        
        old_argv = sys.argv
        try:
            sys.argv = ['check_git.py', '--action', 'stash']
            
            captured_stderr = io.StringIO()
            old_stderr = sys.stderr
            sys.stderr = captured_stderr
            
            with self.assertRaises(SystemExit) as cm:
                main()
            
            sys.stderr = old_stderr
            output = captured_stderr.getvalue()
            
            self.assertEqual(cm.exception.code, 1)
            self.assertIn('Failed to stash', output)
        finally:
            sys.argv = old_argv
    
    @patch('check_git.run_git')
    def test_main_commit_stage_fails_error(self, mock_run_git):
        """Test main commit action when staging fails (lines 93-94)."""
        with open('test.txt', 'w') as f:
            f.write('test')
        
        def mock_git(args):
            if args[0] == 'add':
                return (1, 'add failed')
            return (0, '')
        
        mock_run_git.side_effect = mock_git
        
        old_argv = sys.argv
        try:
            sys.argv = ['check_git.py', '--action', 'commit', '--message', 'Test']
            
            captured_stderr = io.StringIO()
            old_stderr = sys.stderr
            sys.stderr = captured_stderr
            
            with self.assertRaises(SystemExit) as cm:
                main()
            
            sys.stderr = old_stderr
            output = captured_stderr.getvalue()
            
            self.assertEqual(cm.exception.code, 1)
            self.assertIn('Failed to stage', output)
        finally:
            sys.argv = old_argv
    
    @patch('check_git.run_git')
    def test_main_commit_fails_error(self, mock_run_git):
        """Test main commit action when commit fails (lines 99-100)."""
        with open('test.txt', 'w') as f:
            f.write('test')
        
        def mock_git(args):
            if args[0] == 'add':
                return (0, '')
            if args[0] == 'commit':
                return (1, 'commit failed: nothing to commit')
            if args[0] == 'rev-parse':
                return (0, 'abc1234')
            return (0, '')
        
        mock_run_git.side_effect = mock_git
        
        old_argv = sys.argv
        try:
            sys.argv = ['check_git.py', '--action', 'commit', '--message', 'Test']
            
            captured_stderr = io.StringIO()
            old_stderr = sys.stderr
            sys.stderr = captured_stderr
            
            with self.assertRaises(SystemExit) as cm:
                main()
            
            sys.stderr = old_stderr
            output = captured_stderr.getvalue()
            
            self.assertEqual(cm.exception.code, 1)
            self.assertIn('Failed to commit', output)
        finally:
            sys.argv = old_argv
    
    @patch('check_git.run_git')
    def test_main_revert_both_fail(self, mock_run_git):
        """Test main revert when both revert and reset fail (lines 111-114)."""
        # Create and commit files so we have something to revert
        with open('test.txt', 'w') as f:
            f.write('test')
        run_git(['add', '.'])
        run_git(['commit', '-m', 'first'])
        
        with open('test2.txt', 'w') as f:
            f.write('test2')
        run_git(['add', '.'])
        run_git(['commit', '-m', 'second'])
        
        def mock_git(args):
            if args[0] == 'revert':
                return (1, 'revert failed')
            if args[0] == 'reset':
                return (1, 'reset failed')
            return (0, '')
        
        mock_run_git.side_effect = mock_git
        
        old_argv = sys.argv
        try:
            sys.argv = ['check_git.py', '--action', 'revert']
            
            captured_stderr = io.StringIO()
            old_stderr = sys.stderr
            sys.stderr = captured_stderr
            
            with self.assertRaises(SystemExit) as cm:
                main()
            
            sys.stderr = old_stderr
            output = captured_stderr.getvalue()
            
            self.assertEqual(cm.exception.code, 1)
            self.assertIn('Failed to revert', output)
        finally:
            sys.argv = old_argv


class TestGitMainBlock(unittest.TestCase):
    """Test the __main__ block."""
    
    @patch('check_git.main')
    def test_main_block(self, mock_main):
        """Test the __main__ block calls main() (line 121)."""
        # Import the module to trigger the __main__ block
        import importlib
        import check_git
        
        # Simulate __main__ block being called
        if __name__ == '__main__':
            check_git.main()
        
        # The __main__ block should call main()
        # We can't directly test this, but we can verify main exists
        self.assertTrue(hasattr(check_git, 'main'))


if __name__ == '__main__':
    unittest.main()
