#!/usr/bin/env python3
"""Tests for autoresearch_lessons.py"""
import unittest
import sys
import os
import tempfile
import shutil
import json
import stat
import io
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from autoresearch_lessons import (
    LessonManager, cmd_add, cmd_list, cmd_relevant, cmd_summarize, main,
    LESSONS_FILE, STATE_FILE
)


class TestLessonManager(unittest.TestCase):
    """Test LessonManager class."""
    
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
    
    def test_ensure_file_exists_creates_file(self):
        """Test that ensure_file_exists creates the file."""
        manager = LessonManager()
        self.assertTrue(os.path.exists(LESSONS_FILE))
        
        with open(LESSONS_FILE, 'r') as f:
            content = f.read()
            self.assertIn('Lessons Learned', content)
    
    def test_ensure_file_exists_no_overwrite(self):
        """Test that ensure_file_exists doesn't overwrite existing file."""
        with open(LESSONS_FILE, 'w') as f:
            f.write('Existing content')
        
        manager = LessonManager()
        
        with open(LESSONS_FILE, 'r') as f:
            content = f.read()
            self.assertEqual(content, 'Existing content')
    
    def test_add_lesson_basic(self):
        """Test adding a basic lesson."""
        manager = LessonManager()
        result = manager.add_lesson('Test lesson content', 'positive')
        
        self.assertTrue(result)
        
        with open(LESSONS_FILE, 'r') as f:
            content = f.read()
            self.assertIn('Test lesson content', content)
            self.assertIn('positive', content)
    
    def test_add_lesson_with_context(self):
        """Test adding a lesson with context."""
        manager = LessonManager()
        context = {'goal': 'Fix bugs', 'strategy': 'TDD'}
        result = manager.add_lesson('Test lesson', 'strategic', context)
        
        self.assertTrue(result)
        
        with open(LESSONS_FILE, 'r') as f:
            content = f.read()
            self.assertIn('Fix bugs', content)
            self.assertIn('TDD', content)
    
    def test_list_lessons_empty(self):
        """Test listing lessons when file doesn't exist."""
        manager = LessonManager()
        os.remove(LESSONS_FILE)
        
        lessons = manager.list_lessons()
        self.assertEqual(lessons, [])
    
    def test_list_lessons_basic(self):
        """Test listing lessons."""
        manager = LessonManager()
        manager.add_lesson('Lesson 1', 'positive')
        manager.add_lesson('Lesson 2', 'negative')
        
        lessons = manager.list_lessons()
        
        self.assertEqual(len(lessons), 2)
        # Parser includes '---' separator, so check if lesson text is contained
        lesson_texts = [l['lesson'] for l in lessons]
        self.assertTrue(any('Lesson 1' in text for text in lesson_texts))
        self.assertTrue(any('Lesson 2' in text for text in lesson_texts))
    
    def test_list_lessons_filter_by_type(self):
        """Test listing lessons filtered by type."""
        manager = LessonManager()
        manager.add_lesson('Lesson 1', 'positive')
        manager.add_lesson('Lesson 2', 'negative')
        manager.add_lesson('Lesson 3', 'positive')
        
        lessons = manager.list_lessons(lesson_type='positive')
        
        self.assertEqual(len(lessons), 2)
        for lesson in lessons:
            self.assertEqual(lesson['type'], 'positive')
    
    def test_list_lessons_with_limit(self):
        """Test listing lessons with limit."""
        manager = LessonManager()
        for i in range(15):
            manager.add_lesson(f'Lesson {i}', 'positive')
        
        lessons = manager.list_lessons(limit=5)
        
        self.assertEqual(len(lessons), 5)
    
    def test_get_relevant_lessons(self):
        """Test getting relevant lessons."""
        manager = LessonManager()
        manager.add_lesson('Lesson about testing', 'positive', {'goal': 'Fix bugs'})
        manager.add_lesson('Lesson about types', 'positive', {'goal': 'Refactor'})
        
        relevant = manager.get_relevant_lessons({'goal': 'Fix bugs'})
        
        self.assertGreater(len(relevant), 0)
    
    def test_get_relevant_lessons_scoring(self):
        """Test relevance scoring."""
        manager = LessonManager()
        manager.add_lesson('Exact match', 'positive', {'goal': 'Test', 'strategy': 'TDD'})
        manager.add_lesson('Partial match', 'positive', {'goal': 'Test'})
        manager.add_lesson('No match', 'positive', {'goal': 'Different'})
        
        relevant = manager.get_relevant_lessons({'goal': 'Test', 'strategy': 'TDD'}, limit=3)
        
        self.assertEqual(len(relevant), 3)
        # Exact match should be first due to higher score (parser includes '---')
        self.assertIn('Exact match', relevant[0]['lesson'])
    
    def test_summarize_empty(self):
        """Test summarize with no lessons."""
        manager = LessonManager()
        summary = manager.summarize()
        
        self.assertEqual(summary['total_lessons'], 0)
        self.assertEqual(summary['by_type'], {})
    
    def test_summarize_with_lessons(self):
        """Test summarize with lessons."""
        manager = LessonManager()
        manager.add_lesson('Lesson 1', 'positive')
        manager.add_lesson('Lesson 2', 'positive')
        manager.add_lesson('Lesson 3', 'negative')
        
        summary = manager.summarize()
        
        self.assertEqual(summary['total_lessons'], 3)
        self.assertEqual(summary['by_type']['positive'], 2)
        self.assertEqual(summary['by_type']['negative'], 1)


class TestCmdAdd(unittest.TestCase):
    """Test cmd_add function."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        def on_rm_error(func, path, exc_info):
            os.chmod(path, stat.S_IWRITE)
            try:
                func(path)
            except:
                pass
        shutil.rmtree(self.temp_dir, onerror=on_rm_error)
    
    def test_cmd_add_basic(self):
        """Test add command."""
        args = MagicMock()
        args.lesson = 'Test lesson'
        args.type = 'positive'
        args.goal = None
        args.strategy = None
        args.iteration = None
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_add(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Lesson added', output)
    
    def test_cmd_add_with_context(self):
        """Test add command with context."""
        args = MagicMock()
        args.lesson = 'Test lesson'
        args.type = 'strategic'
        args.goal = 'Fix bugs'
        args.strategy = 'TDD'
        args.iteration = 5
        
        result = cmd_add(args)
        
        self.assertEqual(result, 0)


class TestCmdList(unittest.TestCase):
    """Test cmd_list function."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        def on_rm_error(func, path, exc_info):
            os.chmod(path, stat.S_IWRITE)
            try:
                func(path)
            except:
                pass
        shutil.rmtree(self.temp_dir, onerror=on_rm_error)
    
    def test_cmd_list_empty(self):
        """Test list command with no lessons."""
        args = MagicMock()
        args.type = None
        args.limit = 10
        args.json = False
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_list(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('No lessons found', output)
    
    def test_cmd_list_with_lessons(self):
        """Test list command with lessons."""
        manager = LessonManager()
        manager.add_lesson('Test lesson', 'positive')
        
        args = MagicMock()
        args.type = None
        args.limit = 10
        args.json = False
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_list(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Recent Lessons', output)
    
    def test_cmd_list_json(self):
        """Test list command with JSON output."""
        manager = LessonManager()
        manager.add_lesson('Test lesson', 'positive')
        
        args = MagicMock()
        args.type = None
        args.limit = 10
        args.json = True
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_list(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        # Should be valid JSON
        data = json.loads(output)
        self.assertIsInstance(data, list)


class TestCmdRelevant(unittest.TestCase):
    """Test cmd_relevant function."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        def on_rm_error(func, path, exc_info):
            os.chmod(path, stat.S_IWRITE)
            try:
                func(path)
            except:
                pass
        shutil.rmtree(self.temp_dir, onerror=on_rm_error)
    
    def test_cmd_relevant_empty(self):
        """Test relevant command with no lessons."""
        args = MagicMock()
        args.goal = 'Test goal'
        args.strategy = None
        args.limit = 5
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_relevant(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('No relevant lessons', output)
    
    def test_cmd_relevant_with_matches(self):
        """Test relevant command with matching lessons."""
        manager = LessonManager()
        manager.add_lesson('Relevant lesson', 'positive', {'goal': 'Fix bugs'})
        
        args = MagicMock()
        args.goal = 'Fix bugs'
        args.strategy = None
        args.limit = 5
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_relevant(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Relevant Lessons', output)


class TestCmdSummarize(unittest.TestCase):
    """Test cmd_summarize function."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        def on_rm_error(func, path, exc_info):
            os.chmod(path, stat.S_IWRITE)
            try:
                func(path)
            except:
                pass
        shutil.rmtree(self.temp_dir, onerror=on_rm_error)
    
    def test_cmd_summarize_empty(self):
        """Test summarize command with no lessons."""
        args = MagicMock()
        args.json = False
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_summarize(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Total lessons: 0', output)
    
    def test_cmd_summarize_with_lessons(self):
        """Test summarize command with lessons."""
        manager = LessonManager()
        manager.add_lesson('Lesson 1', 'positive')
        
        args = MagicMock()
        args.json = False
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_summarize(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Total lessons: 1', output)
    
    def test_cmd_summarize_json(self):
        """Test summarize command with JSON output."""
        args = MagicMock()
        args.json = True
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_summarize(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        data = json.loads(output)
        self.assertIn('total_lessons', data)


class TestMain(unittest.TestCase):
    """Test main function."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        def on_rm_error(func, path, exc_info):
            os.chmod(path, stat.S_IWRITE)
            try:
                func(path)
            except:
                pass
        shutil.rmtree(self.temp_dir, onerror=on_rm_error)
    
    def test_main_no_command(self):
        """Test main with no command."""
        with patch('sys.argv', ['autoresearch_lessons']):
            result = main()
        
        self.assertEqual(result, 1)
    
    def test_main_add_command(self):
        """Test main with add command."""
        with patch('sys.argv', [
            'autoresearch_lessons', 'add', 'Test lesson'
        ]):
            result = main()
        
        self.assertEqual(result, 0)
    
    def test_main_list_command(self):
        """Test main with list command."""
        with patch('sys.argv', [
            'autoresearch_lessons', 'list'
        ]):
            result = main()
        
        self.assertEqual(result, 0)


if __name__ == '__main__':
    unittest.main()
