#!/usr/bin/env python3
"""
Internationalization (i18n) support for Kimi Autoresearch.
Supports multiple languages with JSON-based translations.
"""
import argparse
import json
import os
import sys
from typing import Optional

# Default locale
DEFAULT_LOCALE = 'zh'
SUPPORTED_LOCALES = ['en', 'zh']

# Get script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCALES_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'locales')

# Global translation cache
_translations = {}
_current_locale = DEFAULT_LOCALE


def get_locale_from_env() -> str:
    """Get locale from environment variables."""
    # Check various env vars
    for var in ['AUTORESEARCH_LANG', 'LANG', 'LANGUAGE', 'LC_ALL']:
        lang = os.environ.get(var, '').lower()
        if 'zh' in lang or 'cn' in lang:
            return 'zh'
        elif 'en' in lang:
            return 'en'
    return DEFAULT_LOCALE


def load_translations(locale: str) -> dict:
    """Load translations for a locale."""
    global _translations
    
    if locale in _translations:
        return _translations[locale]
    
    # Try to load from file
    translation_file = os.path.join(LOCALES_DIR, locale, 'LC_MESSAGES', 'messages.json')
    
    if os.path.exists(translation_file):
        try:
            with open(translation_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                _translations[locale] = data.get('messages', {})
                return _translations[locale]
        except Exception as e:
            print(f"Warning: Failed to load translations for {locale}: {e}", file=sys.stderr)
    
    # Fallback to default
    if locale != DEFAULT_LOCALE:
        return load_translations(DEFAULT_LOCALE)
    
    return {}


def set_locale(locale: str) -> bool:
    """Set current locale."""
    global _current_locale
    
    if locale not in SUPPORTED_LOCALES:
        print(f"Warning: Unsupported locale '{locale}', using default '{DEFAULT_LOCALE}'", file=sys.stderr)
        locale = DEFAULT_LOCALE
    
    _current_locale = locale
    load_translations(locale)
    return True


def get_current_locale() -> str:
    """Get current locale."""
    return _current_locale


def _(key: str, **kwargs) -> str:
    """Translate a key."""
    translations = load_translations(_current_locale)
    
    # Get translation or fallback to key
    text = translations.get(key, key)
    
    # Format with kwargs if provided
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    
    return text


def get_supported_locales() -> list:
    """Get list of supported locales."""
    return SUPPORTED_LOCALES


def get_locale_name(locale: str) -> str:
    """Get human-readable locale name."""
    names = {
        'en': 'English',
        'zh': '简体中文'
    }
    return names.get(locale, locale)


def cmd_switch(args):
    """Switch language command."""
    if args.locale:
        if set_locale(args.locale):
            print(f"Language switched to: {get_locale_name(args.locale)}")
            # Save preference
            config_dir = os.path.expanduser('~/.autoresearch')
            os.makedirs(config_dir, exist_ok=True)
            with open(os.path.join(config_dir, 'locale'), 'w') as f:
                f.write(args.locale)
            return 0
    else:
        print(f"Current language: {get_locale_name(_current_locale)}")
        print("\nAvailable languages:")
        for loc in SUPPORTED_LOCALES:
            marker = " *" if loc == _current_locale else ""
            print(f"  {loc}: {get_locale_name(loc)}{marker}")
        return 0


def cmd_test(args):
    """Test translations."""
    test_keys = ['welcome', 'starting', 'goal', 'success', 'error']
    
    print("Testing translations:\n")
    
    for locale in SUPPORTED_LOCALES:
        set_locale(locale)
        print(f"[{get_locale_name(locale)}]")
        for key in test_keys:
            print(f"  {key}: {_(key)}")
        print()
    
    # Reset to default
    set_locale(DEFAULT_LOCALE)
    return 0


def init_locale():
    """Initialize locale from config or env."""
    # Try to load saved preference
    config_file = os.path.expanduser('~/.autoresearch/locale')
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                locale = f.read().strip()
                if locale in SUPPORTED_LOCALES:
                    set_locale(locale)
                    return
        except:
            pass
    
    # Fall back to env
    set_locale(get_locale_from_env())


def main():
    parser = argparse.ArgumentParser(
        description='Kimi Autoresearch i18n',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # switch command
    switch_parser = subparsers.add_parser('switch', help='Switch language')
    switch_parser.add_argument('locale', nargs='?', help='Locale code (en/zh)')
    
    # test command
    subparsers.add_parser('test', help='Test translations')
    
    # list command
    subparsers.add_parser('list', help='List supported languages')
    
    args = parser.parse_args()
    
    # Initialize locale
    init_locale()
    
    if args.command == 'switch':
        return cmd_switch(args)
    elif args.command == 'test':
        return cmd_test(args)
    elif args.command == 'list':
        print("Supported languages:")
        for loc in SUPPORTED_LOCALES:
            marker = " *" if loc == _current_locale else ""
            print(f"  {loc}: {get_locale_name(loc)}{marker}")
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
