#!/usr/bin/env python3
"""Tests for autoresearch_version.py"""
import unittest
import sys
import os
import tempfile
import json
from io import StringIO
from unittest.mock import patch, MagicMock
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from autoresearch_version import (
    get_project_root,
    get_current_version,
    bump_version,
    update_file_version,
    update_all_versions,
    update_changelog,
    create_git_tag,
    main
)


class TestGetProjectRoot(unittest.TestCase):
    """Test get_project_root function."""
    
    def test_get_project_root(self):
        """Test getting project root."""
        root = get_project_root()
        
        self.assertIsInstance(root, Path)
        # Should be the parent of scripts directory
        self.assertTrue((root / 'scripts').exists() or str(root).endswith('kimi -autoresearch'))


class TestGetCurrentVersion(unittest.TestCase):
    """Test get_current_version function."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_current_version_from_package_sh(self):
        """Test getting version from package.sh."""
        # Create package.sh
        with open('package.sh', 'w') as f:
            f.write('VERSION="1.2.3"')
        
        # Temporarily change the function's understanding of root
        with patch('autoresearch_version.get_project_root') as mock_root:
            mock_root.return_value = Path(self.temp_dir)
            version = get_current_version()
        
        self.assertEqual(version, '1.2.3')
    
    def test_get_current_version_default(self):
        """Test default version when package.sh doesn't exist."""
        with patch('autoresearch_version.get_project_root') as mock_root:
            mock_root.return_value = Path(self.temp_dir)
            version = get_current_version()
        
        self.assertEqual(version, '1.0.0')


class TestBumpVersion(unittest.TestCase):
    """Test bump_version function."""
    
    def test_bump_patch(self):
        """Test bumping patch version."""
        result = bump_version('1.2.3', 'patch')
        self.assertEqual(result, '1.2.4')
    
    def test_bump_minor(self):
        """Test bumping minor version."""
        result = bump_version('1.2.3', 'minor')
        self.assertEqual(result, '1.3.0')
    
    def test_bump_major(self):
        """Test bumping major version."""
        result = bump_version('1.2.3', 'major')
        self.assertEqual(result, '2.0.0')


class TestUpdateFileVersion(unittest.TestCase):
    """Test update_file_version function."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_update_file_version_success(self):
        """Test successful file version update."""
        file_path = Path(self.temp_dir) / 'test.txt'
        file_path.write_text('Version: 1.2.3')
        
        result = update_file_version(
            file_path,
            r'Version: 1\.2\.3',
            'Version: 1.2.4',
            '1.2.4'
        )
        
        self.assertTrue(result)
        content = file_path.read_text()
        self.assertIn('1.2.4', content)
    
    def test_update_file_version_no_match(self):
        """Test update when pattern doesn't match."""
        file_path = Path(self.temp_dir) / 'test.txt'
        file_path.write_text('No version here')
        
        result = update_file_version(
            file_path,
            r'Version: 1\.2\.3',
            'Version: 1.2.4',
            '1.2.4'
        )
        
        self.assertFalse(result)
    
    def test_update_file_version_not_exists(self):
        """Test update when file doesn't exist."""
        file_path = Path(self.temp_dir) / 'nonexistent.txt'
        
        result = update_file_version(
            file_path,
            r'pattern',
            'replacement',
            '1.2.4'
        )
        
        self.assertFalse(result)
    
    def test_update_file_version_exception(self):
        """Test update when exception occurs."""
        file_path = Path(self.temp_dir) / 'test.txt'
        file_path.write_text('test')
        
        # Make file unreadable
        import stat
        os.chmod(file_path, stat.S_IRUSR)
        
        result = update_file_version(
            file_path,
            r'test',
            'replacement',
            '1.2.4'
        )
        
        # Restore permissions for cleanup
        os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
        
        self.assertFalse(result)


class TestUpdateAllVersions(unittest.TestCase):
    """Test update_all_versions function."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_update_all_versions(self):
        """Test updating all version files."""
        # Create package.sh
        package_sh = Path(self.temp_dir) / 'package.sh'
        package_sh.write_text('VERSION="1.2.3"')
        
        # Create package.ps1
        package_ps1 = Path(self.temp_dir) / 'package.ps1'
        package_ps1.write_text('$Version = "1.2.3"')
        
        # Create SKILL.md
        skill_md = Path(self.temp_dir) / 'SKILL.md'
        skill_md.write_text('version-1.2.3')
        
        with patch('autoresearch_version.get_project_root') as mock_root:
            mock_root.return_value = Path(self.temp_dir)
            updated = update_all_versions('1.2.3', '1.2.4')
        
        self.assertIn('package.sh', updated)
        self.assertIn('package.ps1', updated)
        self.assertIn('SKILL.md', updated)


class TestUpdateChangelog(unittest.TestCase):
    """Test update_changelog function."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_update_changelog_new_file(self):
        """Test creating new CHANGELOG."""
        with patch('autoresearch_version.get_project_root') as mock_root:
            mock_root.return_value = Path(self.temp_dir)
            filename = update_changelog('1.2.4')
        
        changelog_path = Path(self.temp_dir) / 'CHANGELOG.md'
        self.assertTrue(changelog_path.exists())
        
        content = changelog_path.read_text()
        self.assertIn('1.2.4', content)
        self.assertIn('Changelog', content)
    
    def test_update_changelog_existing_file(self):
        """Test updating existing CHANGELOG."""
        changelog_path = Path(self.temp_dir) / 'CHANGELOG.md'
        changelog_path.write_text("""# Changelog

## [1.2.3] - 2024-01-01

### Added
- Old feature
""")
        
        with patch('autoresearch_version.get_project_root') as mock_root:
            mock_root.return_value = Path(self.temp_dir)
            filename = update_changelog('1.2.4')
        
        content = changelog_path.read_text()
        self.assertIn('1.2.4', content)
        self.assertIn('1.2.3', content)
    
    def test_update_changelog_with_changes(self):
        """Test updating CHANGELOG with custom changes."""
        changes = "### Added\n- New feature\n"
        
        with patch('autoresearch_version.get_project_root') as mock_root:
            mock_root.return_value = Path(self.temp_dir)
            filename = update_changelog('1.2.4', changes)
        
        changelog_path = Path(self.temp_dir) / 'CHANGELOG.md'
        content = changelog_path.read_text()
        self.assertIn('New feature', content)


class TestCreateGitTag(unittest.TestCase):
    """Test create_git_tag function."""
    
    @patch('subprocess.run')
    def test_create_git_tag_clean_repo(self, mock_run):
        """Test creating tag with clean repo."""
        # Mock git status (clean)
        mock_run.side_effect = [
            MagicMock(stdout='', stderr=''),  # git status
            MagicMock(returncode=0)           # git tag
        ]
        
        with patch('autoresearch_version.get_project_root') as mock_root:
            mock_root.return_value = Path('.')
            result = create_git_tag('1.2.4')
        
        self.assertTrue(result)
    
    @patch('subprocess.run')
    def test_create_git_tag_dirty_repo(self, mock_run):
        """Test creating tag with dirty repo."""
        # Mock git status (dirty)
        mock_run.return_value = MagicMock(stdout='M file.txt', stderr='')
        
        with patch('autoresearch_version.get_project_root') as mock_root:
            mock_root.return_value = Path('.')
            result = create_git_tag('1.2.4')
        
        self.assertFalse(result)
    
    @patch('subprocess.run')
    def test_create_git_tag_failure(self, mock_run):
        """Test tag creation failure."""
        import subprocess
        mock_run.side_effect = [
            MagicMock(stdout='', stderr=''),  # git status
            subprocess.CalledProcessError(1, 'git tag')  # git tag fails
        ]
        
        with patch('autoresearch_version.get_project_root') as mock_root:
            mock_root.return_value = Path('.')
            result = create_git_tag('1.2.4')
        
        self.assertFalse(result)


class TestMain(unittest.TestCase):
    """Test main CLI function."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create package.sh
        with open('package.sh', 'w') as f:
            f.write('VERSION="1.2.3"')
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_main_show(self):
        """Test main with show command."""
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_version.py', 'show']
            
            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            with patch('autoresearch_version.get_project_root') as mock_root:
                mock_root.return_value = Path(self.temp_dir)
                main()
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            self.assertIn('1.2.3', output)
        finally:
            sys.argv = old_argv
    
    def test_main_show_no_command(self):
        """Test main with no command (defaults to show)."""
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_version.py']
            
            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            with patch('autoresearch_version.get_project_root') as mock_root:
                mock_root.return_value = Path(self.temp_dir)
                main()
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            self.assertIn('1.2.3', output)
        finally:
            sys.argv = old_argv
    
    @patch('autoresearch_version.update_all_versions')
    @patch('autoresearch_version.update_changelog')
    def test_main_bump_patch(self, mock_changelog, mock_update):
        """Test main with bump patch command."""
        mock_update.return_value = ['package.sh', 'SKILL.md']
        
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_version.py', 'bump', 'patch']
            
            with patch('autoresearch_version.get_project_root') as mock_root:
                mock_root.return_value = Path(self.temp_dir)
                main()
            
            mock_update.assert_called_once_with('1.2.3', '1.2.4')
        finally:
            sys.argv = old_argv
    
    @patch('autoresearch_version.update_all_versions')
    @patch('autoresearch_version.update_changelog')
    def test_main_bump_minor(self, mock_changelog, mock_update):
        """Test main with bump minor command."""
        mock_update.return_value = ['package.sh']
        
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_version.py', 'bump', 'minor']
            
            with patch('autoresearch_version.get_project_root') as mock_root:
                mock_root.return_value = Path(self.temp_dir)
                main()
            
            mock_update.assert_called_once_with('1.2.3', '1.3.0')
        finally:
            sys.argv = old_argv
    
    @patch('autoresearch_version.update_all_versions')
    @patch('autoresearch_version.update_changelog')
    def test_main_bump_major(self, mock_changelog, mock_update):
        """Test main with bump major command."""
        mock_update.return_value = ['package.sh']
        
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_version.py', 'bump', 'major']
            
            with patch('autoresearch_version.get_project_root') as mock_root:
                mock_root.return_value = Path(self.temp_dir)
                main()
            
            mock_update.assert_called_once_with('1.2.3', '2.0.0')
        finally:
            sys.argv = old_argv
    
    @patch('autoresearch_version.update_all_versions')
    @patch('autoresearch_version.update_changelog')
    def test_main_bump_no_changelog(self, mock_changelog, mock_update):
        """Test main with bump --no-changelog."""
        mock_update.return_value = ['package.sh']
        
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_version.py', 'bump', 'patch', '--no-changelog']
            
            with patch('autoresearch_version.get_project_root') as mock_root:
                mock_root.return_value = Path(self.temp_dir)
                main()
            
            mock_changelog.assert_not_called()
        finally:
            sys.argv = old_argv
    
    @patch('autoresearch_version.update_all_versions')
    @patch('autoresearch_version.create_git_tag')
    def test_main_bump_with_tag(self, mock_tag, mock_update):
        """Test main with bump --tag."""
        mock_update.return_value = ['package.sh']
        mock_tag.return_value = True
        
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_version.py', 'bump', 'patch', '--tag']
            
            with patch('autoresearch_version.get_project_root') as mock_root:
                mock_root.return_value = Path(self.temp_dir)
                main()
            
            mock_tag.assert_called_once_with('1.2.4')
        finally:
            sys.argv = old_argv
    
    @patch('autoresearch_version.update_all_versions')
    def test_main_set(self, mock_update):
        """Test main with set command."""
        mock_update.return_value = ['package.sh']
        
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_version.py', 'set', '2.0.0']
            
            with patch('autoresearch_version.get_project_root') as mock_root:
                mock_root.return_value = Path(self.temp_dir)
                main()
            
            mock_update.assert_called_once_with('1.2.3', '2.0.0')
        finally:
            sys.argv = old_argv
    
    @patch('autoresearch_version.create_git_tag')
    def test_main_tag(self, mock_tag):
        """Test main with tag command."""
        mock_tag.return_value = True
        
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_version.py', 'tag', '-m', 'Release message']
            
            with patch('autoresearch_version.get_project_root') as mock_root:
                mock_root.return_value = Path(self.temp_dir)
                main()
            
            mock_tag.assert_called_once_with('1.2.3', 'Release message')
        finally:
            sys.argv = old_argv


if __name__ == '__main__':
    unittest.main()
