#!/usr/bin/env python3
"""Tests for autoresearch_i18n.py"""
import unittest
import sys
import os
import tempfile
import json
import io
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from autoresearch_i18n import (
    get_locale_from_env, load_translations, set_locale, get_current_locale,
    _, get_supported_locales, get_locale_name, cmd_switch, cmd_test,
    init_locale, main, DEFAULT_LOCALE, SUPPORTED_LOCALES, _translations, _current_locale
)


class TestGetLocaleFromEnv(unittest.TestCase):
    """Test get_locale_from_env function."""
    
    @patch.dict(os.environ, {'AUTORESEARCH_LANG': 'en'})
    def test_from_autoresearch_lang(self):
        """Test getting locale from AUTORESEARCH_LANG."""
        result = get_locale_from_env()
        self.assertEqual(result, 'en')
    
    @patch.dict(os.environ, {'LANG': 'zh_CN.UTF-8'})
    def test_from_lang_zh(self):
        """Test getting zh locale from LANG."""
        result = get_locale_from_env()
        self.assertEqual(result, 'zh')
    
    @patch.dict(os.environ, {'LANGUAGE': 'en_US'})
    def test_from_language_en(self):
        """Test getting en locale from LANGUAGE."""
        result = get_locale_from_env()
        self.assertEqual(result, 'en')
    
    @patch.dict(os.environ, {'LC_ALL': 'zh_CN'}, clear=True)
    def test_from_lc_all(self):
        """Test getting locale from LC_ALL."""
        result = get_locale_from_env()
        self.assertEqual(result, 'zh')
    
    @patch.dict(os.environ, {}, clear=True)
    def test_default_locale(self):
        """Test default locale when no env vars set."""
        result = get_locale_from_env()
        self.assertEqual(result, DEFAULT_LOCALE)


class TestSetLocale(unittest.TestCase):
    """Test set_locale function."""
    
    def setUp(self):
        """Reset translations before each test."""
        import autoresearch_i18n
        autoresearch_i18n._translations = {}
        autoresearch_i18n._current_locale = DEFAULT_LOCALE
    
    def test_set_valid_locale(self):
        """Test setting a valid locale."""
        result = set_locale('en')
        self.assertTrue(result)
        self.assertEqual(get_current_locale(), 'en')
    
    def test_set_invalid_locale(self):
        """Test setting an invalid locale falls back to default."""
        result = set_locale('invalid')
        self.assertTrue(result)
        self.assertEqual(get_current_locale(), DEFAULT_LOCALE)
    
    def test_set_zh_locale(self):
        """Test setting zh locale."""
        result = set_locale('zh')
        self.assertTrue(result)
        self.assertEqual(get_current_locale(), 'zh')


class TestGetSupportedLocales(unittest.TestCase):
    """Test get_supported_locales function."""
    
    def test_returns_supported_locales(self):
        """Test that it returns the supported locales."""
        result = get_supported_locales()
        self.assertEqual(result, SUPPORTED_LOCALES)
        self.assertIn('en', result)
        self.assertIn('zh', result)


class TestGetLocaleName(unittest.TestCase):
    """Test get_locale_name function."""
    
    def test_english_name(self):
        """Test English locale name."""
        result = get_locale_name('en')
        self.assertEqual(result, 'English')
    
    def test_chinese_name(self):
        """Test Chinese locale name."""
        result = get_locale_name('zh')
        self.assertEqual(result, '简体中文')
    
    def test_unknown_locale(self):
        """Test unknown locale returns the code."""
        result = get_locale_name('unknown')
        self.assertEqual(result, 'unknown')


class TestTranslate(unittest.TestCase):
    """Test translate function (_)."""
    
    def setUp(self):
        """Set up locale."""
        import autoresearch_i18n
        autoresearch_i18n._translations = {}
        set_locale('en')
    
    def test_translate_key_fallback(self):
        """Test translation falls back to key if not found."""
        result = _('nonexistent_key')
        self.assertEqual(result, 'nonexistent_key')
    
    def test_translate_with_kwargs(self):
        """Test translation with kwargs formatting."""
        # Mock translations
        import autoresearch_i18n
        autoresearch_i18n._translations['en'] = {'greeting': 'Hello {name}'}
        
        result = _('greeting', name='World')
        self.assertEqual(result, 'Hello World')
    
    def test_translate_invalid_format(self):
        """Test translation with invalid format string."""
        import autoresearch_i18n
        autoresearch_i18n._translations['en'] = {'test': 'Hello {invalid}'}
        
        # Should return original string if formatting fails
        result = _('test', name='World')
        self.assertEqual(result, 'Hello {invalid}')


class TestCmdSwitch(unittest.TestCase):
    """Test cmd_switch function."""
    
    def setUp(self):
        """Create temporary directory for config."""
        self.temp_dir = tempfile.mkdtemp()
        self.old_home = os.environ.get('HOME')
        self.old_userprofile = os.environ.get('USERPROFILE')
        os.environ['HOME'] = self.temp_dir
        os.environ['USERPROFILE'] = self.temp_dir
        
        import autoresearch_i18n
        autoresearch_i18n._translations = {}
        autoresearch_i18n._current_locale = DEFAULT_LOCALE
    
    def tearDown(self):
        """Clean up."""
        if self.old_home:
            os.environ['HOME'] = self.old_home
        elif 'HOME' in os.environ:
            del os.environ['HOME']
            
        if self.old_userprofile:
            os.environ['USERPROFILE'] = self.old_userprofile
        elif 'USERPROFILE' in os.environ:
            del os.environ['USERPROFILE']
        
        import shutil
        import stat
        
        def on_rm_error(func, path, exc_info):
            os.chmod(path, stat.S_IWRITE)
            try:
                func(path)
            except:
                pass
        
        shutil.rmtree(self.temp_dir, onerror=on_rm_error)
    
    def test_switch_to_locale(self):
        """Test switching to a specific locale."""
        args = MagicMock()
        args.locale = 'en'
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_switch(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('English', output)
    
    def test_switch_show_current(self):
        """Test showing current locale."""
        args = MagicMock()
        args.locale = None
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_switch(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Current language', output)


class TestCmdTest(unittest.TestCase):
    """Test cmd_test function."""
    
    def setUp(self):
        """Reset locale."""
        import autoresearch_i18n
        autoresearch_i18n._translations = {}
        autoresearch_i18n._current_locale = DEFAULT_LOCALE
    
    def test_cmd_test_output(self):
        """Test translation test command output."""
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_test(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Testing translations', output)
        self.assertIn('English', output)


class TestInitLocale(unittest.TestCase):
    """Test init_locale function."""
    
    def setUp(self):
        """Create temporary directory for config."""
        self.temp_dir = tempfile.mkdtemp()
        self.old_home = os.environ.get('HOME')
        self.old_userprofile = os.environ.get('USERPROFILE')
        os.environ['HOME'] = self.temp_dir
        os.environ['USERPROFILE'] = self.temp_dir
        
        import autoresearch_i18n
        autoresearch_i18n._translations = {}
        autoresearch_i18n._current_locale = DEFAULT_LOCALE
    
    def tearDown(self):
        """Clean up."""
        if self.old_home:
            os.environ['HOME'] = self.old_home
        elif 'HOME' in os.environ:
            del os.environ['HOME']
            
        if self.old_userprofile:
            os.environ['USERPROFILE'] = self.old_userprofile
        elif 'USERPROFILE' in os.environ:
            del os.environ['USERPROFILE']
        
        import shutil
        import stat
        
        def on_rm_error(func, path, exc_info):
            os.chmod(path, stat.S_IWRITE)
            try:
                func(path)
            except:
                pass
        
        shutil.rmtree(self.temp_dir, onerror=on_rm_error)
    
    def test_init_from_config_file(self):
        """Test init from config file."""
        config_dir = os.path.join(self.temp_dir, '.autoresearch')
        os.makedirs(config_dir, exist_ok=True)
        with open(os.path.join(config_dir, 'locale'), 'w') as f:
            f.write('en')
        
        init_locale()
        self.assertEqual(get_current_locale(), 'en')
    
    @patch.dict(os.environ, {'AUTORESEARCH_LANG': 'en'}, clear=False)
    def test_init_from_env(self):
        """Test init from environment."""
        # Make sure config file doesn't exist
        config_dir = os.path.join(self.temp_dir, '.autoresearch')
        if os.path.exists(config_dir):
            import shutil
            shutil.rmtree(config_dir)
        
        init_locale()
        # Should get locale from env
        self.assertEqual(get_current_locale(), 'en')


class TestMain(unittest.TestCase):
    """Test main function."""
    
    def setUp(self):
        """Create temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.old_home = os.environ.get('HOME')
        self.old_userprofile = os.environ.get('USERPROFILE')
        os.environ['HOME'] = self.temp_dir
        os.environ['USERPROFILE'] = self.temp_dir
        
        import autoresearch_i18n
        autoresearch_i18n._translations = {}
        autoresearch_i18n._current_locale = DEFAULT_LOCALE
    
    def tearDown(self):
        """Clean up."""
        if self.old_home:
            os.environ['HOME'] = self.old_home
        elif 'HOME' in os.environ:
            del os.environ['HOME']
            
        if self.old_userprofile:
            os.environ['USERPROFILE'] = self.old_userprofile
        elif 'USERPROFILE' in os.environ:
            del os.environ['USERPROFILE']
        
        import shutil
        import stat
        
        def on_rm_error(func, path, exc_info):
            os.chmod(path, stat.S_IWRITE)
            try:
                func(path)
            except:
                pass
        
        shutil.rmtree(self.temp_dir, onerror=on_rm_error)
    
    @patch('autoresearch_i18n.sys.argv', ['autoresearch_i18n.py', 'list'])
    def test_main_list(self):
        """Test main with list command."""
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = main()
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Supported languages', output)
    
    @patch('autoresearch_i18n.sys.argv', ['autoresearch_i18n.py', 'test'])
    def test_main_test(self):
        """Test main with test command."""
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = main()
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Testing translations', output)
    
    @patch('autoresearch_i18n.sys.argv', ['autoresearch_i18n.py', 'switch', 'en'])
    def test_main_switch(self):
        """Test main with switch command."""
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = main()
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Language switched', output)
    
    @patch('autoresearch_i18n.sys.argv', ['autoresearch_i18n.py'])
    def test_main_no_command(self):
        """Test main with no command."""
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = main()
        
        sys.stdout = old_stdout
        
        self.assertEqual(result, 1)


if __name__ == '__main__':
    unittest.main()
