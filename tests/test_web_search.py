#!/usr/bin/env python3
"""Tests for autoresearch_web_search.py"""
import unittest
import sys
import os
import tempfile
import json
from io import StringIO
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from autoresearch_web_search import (
    extract_search_query,
    format_search_results,
    generate_hypotheses_from_search,
    cmd_search,
    cmd_generate_hypotheses,
    cmd_check_and_search,
    main
)


class TestExtractSearchQuery(unittest.TestCase):
    """Test extract_search_query function."""
    
    def test_extract_with_error(self):
        """Test extraction with error message."""
        context = {
            'error': 'TypeError: Cannot read property',
            'goal': 'Fix type errors',
            'strategy': 'Add type annotations'
        }
        
        query = extract_search_query(context)
        
        self.assertIn('TypeError', query)
        self.assertIn('Fix type errors', query)
    
    def test_extract_with_goal_only(self):
        """Test extraction with only goal."""
        context = {
            'goal': 'Optimize performance'
        }
        
        query = extract_search_query(context)
        
        self.assertIn('Optimize performance', query)
    
    def test_extract_with_strategy(self):
        """Test extraction with strategy."""
        context = {
            'goal': 'Reduce memory',
            'strategy': 'Cache results'
        }
        
        query = extract_search_query(context)
        
        self.assertIn('Reduce memory', query)
        self.assertIn('Cache results', query)
        self.assertIn('not working', query)
    
    def test_extract_empty_context(self):
        """Test extraction with empty context."""
        context = {}
        
        query = extract_search_query(context)
        
        self.assertEqual(query, 'programming best practices')


class TestFormatSearchResults(unittest.TestCase):
    """Test format_search_results function."""
    
    def test_format_single_result(self):
        """Test formatting single result."""
        results = [
            {
                'title': 'Test Title',
                'snippet': 'This is a test snippet',
                'url': 'https://example.com'
            }
        ]
        
        formatted = format_search_results(results)
        
        self.assertIn('Test Title', formatted)
        self.assertIn('test snippet', formatted)
        self.assertIn('example.com', formatted)
    
    def test_format_multiple_results(self):
        """Test formatting multiple results."""
        results = [
            {'title': 'Title 1', 'snippet': 'Snippet 1', 'url': 'url1'},
            {'title': 'Title 2', 'snippet': 'Snippet 2', 'url': 'url2'},
        ]
        
        formatted = format_search_results(results)
        
        self.assertIn('Title 1', formatted)
        self.assertIn('Title 2', formatted)
    
    def test_format_with_max_results(self):
        """Test formatting with max_results limit."""
        results = [
            {'title': f'Title {i}', 'snippet': f'Snippet {i}', 'url': f'url{i}'}
            for i in range(10)
        ]
        
        formatted = format_search_results(results, max_results=3)
        
        # Should only contain 3 results
        self.assertIn('[1]', formatted)
        self.assertIn('[2]', formatted)
        self.assertIn('[3]', formatted)
        self.assertNotIn('[4]', formatted)
    
    def test_format_missing_fields(self):
        """Test formatting with missing fields."""
        results = [
            {}  # Missing all fields
        ]
        
        formatted = format_search_results(results)
        
        self.assertIn('No title', formatted)
        self.assertIn('No snippet', formatted)


class TestGenerateHypothesesFromSearch(unittest.TestCase):
    """Test generate_hypotheses_from_search function."""
    
    def test_generate_with_type_pattern(self):
        """Test hypothesis generation with type-related keywords."""
        results = [
            {'title': 'TypeScript Best Practices', 'snippet': 'Use interfaces and types'}
        ]
        context = {'goal': 'Fix type errors'}
        
        hypotheses = generate_hypotheses_from_search(results, context)
        
        self.assertTrue(len(hypotheses) > 0)
        strategies = [h['strategy'] for h in hypotheses]
        self.assertIn('add_type_definitions', strategies)
    
    def test_generate_with_async_pattern(self):
        """Test hypothesis generation with async-related keywords."""
        results = [
            {'title': 'Async Await Patterns', 'snippet': 'Handle promise errors'}
        ]
        context = {'goal': 'Fix async errors'}
        
        hypotheses = generate_hypotheses_from_search(results, context)
        
        strategies = [h['strategy'] for h in hypotheses]
        self.assertIn('handle_async_errors', strategies)
    
    def test_generate_with_test_pattern(self):
        """Test hypothesis generation with test-related keywords."""
        results = [
            {'title': 'Jest Testing Guide', 'snippet': 'Improve coverage with tests'}
        ]
        context = {'goal': 'Add tests'}
        
        hypotheses = generate_hypotheses_from_search(results, context)
        
        strategies = [h['strategy'] for h in hypotheses]
        self.assertIn('add_test_cases', strategies)
    
    def test_generate_no_patterns_matched(self):
        """Test hypothesis generation when no patterns match."""
        results = [
            {'title': 'Random Article', 'snippet': 'Nothing specific here'}
        ]
        context = {}
        
        hypotheses = generate_hypotheses_from_search(results, context)
        
        # Should generate generic hypothesis
        self.assertEqual(len(hypotheses), 1)
        self.assertEqual(hypotheses[0]['strategy'], 'alternative_approach')
    
    def test_generate_deduplicates_strategies(self):
        """Test that duplicate strategies are not generated."""
        results = [
            {'title': 'TypeScript Types', 'snippet': 'Use types'},
            {'title': 'More TypeScript', 'snippet': 'More types'},
        ]
        context = {}
        
        hypotheses = generate_hypotheses_from_search(results, context)
        
        strategies = [h['strategy'] for h in hypotheses]
        self.assertEqual(len(strategies), len(set(strategies)))  # No duplicates


class TestCmdSearch(unittest.TestCase):
    """Test cmd_search function."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cmd_search_dry_run(self):
        """Test search command with dry run."""
        args = MagicMock()
        args.goal = 'Test goal'
        args.strategy = 'Test strategy'
        args.error = None
        args.context_file = None
        args.dry_run = True
        args.json = False
        args.output = None
        
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_search(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Would search for', output)
    
    def test_cmd_search_json_output(self):
        """Test search command with JSON output."""
        args = MagicMock()
        args.goal = 'Test goal'
        args.strategy = None
        args.error = None
        args.context_file = None
        args.dry_run = False
        args.json = True
        args.output = None
        
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_search(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        # Should be valid JSON
        data = json.loads(output)
        self.assertIn('query', data)
    
    def test_cmd_search_with_context_file(self):
        """Test search command with context file."""
        # Create context file
        context = {'goal': 'From file', 'error': 'Test error'}
        with open('context.json', 'w') as f:
            json.dump(context, f)
        
        args = MagicMock()
        args.goal = None
        args.strategy = None
        args.error = None
        args.context_file = 'context.json'
        args.dry_run = True
        args.json = False
        args.output = None
        
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_search(args)
        
        sys.stdout = old_stdout
        
        self.assertEqual(result, 0)
    
    def test_cmd_search_with_output(self):
        """Test search command with output file."""
        args = MagicMock()
        args.goal = 'Test goal'
        args.strategy = None
        args.error = None
        args.context_file = None
        args.dry_run = False
        args.json = False
        args.output = 'output.json'
        
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_search(args)
        
        sys.stdout = old_stdout
        
        self.assertEqual(result, 0)
        self.assertTrue(os.path.exists('output.json'))


class TestCmdGenerateHypotheses(unittest.TestCase):
    """Test cmd_generate_hypotheses function."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cmd_generate_hypotheses(self):
        """Test generate hypotheses command."""
        # Create search results file
        search_data = {
            'results': [
                {'title': 'TypeScript Guide', 'snippet': 'Use interfaces'}
            ]
        }
        with open('search.json', 'w') as f:
            json.dump(search_data, f)
        
        args = MagicMock()
        args.search_results = 'search.json'
        args.context_file = None
        args.json = False
        args.output = None
        
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_generate_hypotheses(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Generated Hypotheses', output)
    
    def test_cmd_generate_hypotheses_json(self):
        """Test generate hypotheses command with JSON output."""
        search_data = {'results': []}
        with open('search.json', 'w') as f:
            json.dump(search_data, f)
        
        args = MagicMock()
        args.search_results = 'search.json'
        args.context_file = None
        args.json = True
        args.output = None
        
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_generate_hypotheses(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        # Should be valid JSON
        data = json.loads(output)
        self.assertIn('hypotheses', data)


class TestCmdCheckAndSearch(unittest.TestCase):
    """Test cmd_check_and_search function."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_check_no_state_file(self):
        """Test check when no state file exists."""
        args = MagicMock()
        args.state_file = 'nonexistent.json'
        args.force = False
        args.json = False
        args.output = None
        args.verbose = False
        
        result = cmd_check_and_search(args)
        
        self.assertEqual(result, 0)
    
    def test_check_not_stuck(self):
        """Test check when not stuck."""
        # Create state file with low discards
        state = {
            'consecutive_discards': 2,
            'pivot_count': 0,
            'config': {}
        }
        with open('autoresearch-state.json', 'w') as f:
            json.dump(state, f)
        
        args = MagicMock()
        args.state_file = 'autoresearch-state.json'
        args.force = False
        args.json = False
        args.output = None
        args.verbose = True
        
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_check_and_search(args)
        
        sys.stdout = old_stdout
        
        self.assertEqual(result, 0)
    
    def test_check_stuck(self):
        """Test check when stuck."""
        # Create state file with high discards and pivots
        state = {
            'consecutive_discards': 5,
            'pivot_count': 2,
            'config': {'goal': 'Test goal'},
            'strategy': 'Test strategy'
        }
        with open('autoresearch-state.json', 'w') as f:
            json.dump(state, f)
        
        args = MagicMock()
        args.state_file = 'autoresearch-state.json'
        args.force = False
        args.json = False
        args.output = None
        args.verbose = False
        
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_check_and_search(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Stuck detected', output)
    
    def test_check_force(self):
        """Test check with force flag."""
        # Create state file
        state = {
            'consecutive_discards': 1,
            'pivot_count': 0,
            'config': {}
        }
        with open('autoresearch-state.json', 'w') as f:
            json.dump(state, f)
        
        args = MagicMock()
        args.state_file = 'autoresearch-state.json'
        args.force = True
        args.json = False
        args.output = None
        args.verbose = False
        
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_check_and_search(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('forced search', output)
    
    def test_check_stuck_json_output(self):
        """Test check when stuck with JSON output (line 289)."""
        # Create state file with high discards and pivots
        state = {
            'consecutive_discards': 5,
            'pivot_count': 2,
            'config': {'goal': 'Test goal'},
            'strategy': 'Test strategy'
        }
        with open('autoresearch-state.json', 'w') as f:
            json.dump(state, f)
        
        args = MagicMock()
        args.state_file = 'autoresearch-state.json'
        args.force = False
        args.json = True  # JSON output
        args.output = None
        args.verbose = False
        
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_check_and_search(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        # Output has text before JSON, extract JSON part
        self.assertIn('Stuck detected', output)
        self.assertIn('triggered', output)
        self.assertIn('query', output)
        # Verify JSON structure by finding and parsing the JSON part
        json_start = output.find('{')
        self.assertNotEqual(json_start, -1)
        data = json.loads(output[json_start:])
        self.assertTrue(data['triggered'])
        self.assertIn('query', data)


class TestMain(unittest.TestCase):
    """Test main CLI function."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_main_no_command(self):
        """Test main with no command."""
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_web_search.py']
            
            main()
            
            # Should print help
        finally:
            sys.argv = old_argv
    
    def test_main_search(self):
        """Test main with search command."""
        old_argv = sys.argv
        try:
            sys.argv = [
                'autoresearch_web_search.py',
                'search',
                '--goal', 'Test goal',
                '--dry-run'
            ]
            
            main()
            
            # Should succeed
        finally:
            sys.argv = old_argv
    
    def test_main_check(self):
        """Test main with check command."""
        # Create state file
        state = {
            'consecutive_discards': 5,
            'pivot_count': 2,
            'config': {}
        }
        with open('autoresearch-state.json', 'w') as f:
            json.dump(state, f)
        
        old_argv = sys.argv
        try:
            sys.argv = [
                'autoresearch_web_search.py',
                'check',
                '--state-file', 'autoresearch-state.json'
            ]
            
            main()
            
            # Should succeed
        finally:
            sys.argv = old_argv
    
    def test_main_hypotheses(self):
        """Test main with hypotheses command."""
        # Create search results file
        search_data = {'results': []}
        with open('search.json', 'w') as f:
            json.dump(search_data, f)
        
        old_argv = sys.argv
        try:
            sys.argv = [
                'autoresearch_web_search.py',
                'hypotheses',
                '--search-results', 'search.json'
            ]
            
            main()
            
            # Should succeed
        finally:
            sys.argv = old_argv


if __name__ == '__main__':
    unittest.main()
