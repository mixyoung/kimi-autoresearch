#!/usr/bin/env python3
"""Tests for autoresearch_predict.py"""
import unittest
import sys
import os
import tempfile
import json
import io
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from autoresearch_predict import (
    PERSONAS, analyze_with_persona, generate_analysis, generate_consensus,
    cmd_analyze, cmd_list_personas, main
)


class TestPersonas(unittest.TestCase):
    """Test PERSONAS constant."""
    
    def test_personas_structure(self):
        """Test that PERSONAS has expected structure."""
        expected_personas = ['architect', 'security', 'performance', 'reliability', 'devil']
        for persona in expected_personas:
            self.assertIn(persona, PERSONAS)
            self.assertIn('name', PERSONAS[persona])
            self.assertIn('focus', PERSONAS[persona])
            self.assertIn('questions', PERSONAS[persona])
            self.assertIsInstance(PERSONAS[persona]['questions'], list)


class TestAnalyzeWithPersona(unittest.TestCase):
    """Test analyze_with_persona function."""
    
    def test_analyze_architect(self):
        """Test analyzing with architect persona."""
        context = {'file': 'test.py', 'description': 'Test'}
        result = analyze_with_persona('architect', context)
        
        self.assertEqual(result['persona'], 'System Architect')
        self.assertEqual(result['focus'], 'Design patterns, architecture, maintainability')
        self.assertIn('questions_considered', result)
        self.assertIn('assessment', result)
        self.assertIn('concerns', result)
        self.assertIn('recommendations', result)
    
    def test_analyze_security(self):
        """Test analyzing with security persona."""
        context = {'file': 'test.py', 'description': 'Test'}
        result = analyze_with_persona('security', context)
        
        self.assertEqual(result['persona'], 'Security Analyst')
        self.assertEqual(result['focus'], 'Vulnerabilities, attack vectors, compliance')
    
    def test_analyze_all_personas(self):
        """Test analyzing with all personas."""
        context = {'file': 'test.py', 'description': 'Test'}
        
        for persona_key in PERSONAS.keys():
            result = analyze_with_persona(persona_key, context)
            self.assertEqual(result['persona'], PERSONAS[persona_key]['name'])


class TestGenerateConsensus(unittest.TestCase):
    """Test generate_consensus function."""
    
    def test_generate_consensus_structure(self):
        """Test consensus generation returns correct structure."""
        analyses = {
            'architect': {'concerns': [], 'recommendations': []},
            'security': {'concerns': [], 'recommendations': []}
        }
        
        consensus = generate_consensus(analyses)
        
        self.assertIn('agreements', consensus)
        self.assertIn('disagreements', consensus)
        self.assertIn('final_recommendations', consensus)
        self.assertIsInstance(consensus['agreements'], list)
        self.assertIsInstance(consensus['disagreements'], list)
        self.assertIsInstance(consensus['final_recommendations'], list)


class TestGenerateAnalysis(unittest.TestCase):
    """Test generate_analysis function."""
    
    def test_generate_analysis_structure(self):
        """Test analysis generation returns correct structure."""
        context = {'file': 'test.py', 'description': 'Test description', 'goal': 'Test goal'}
        personas = ['architect', 'security']
        
        result = generate_analysis(context, personas)
        
        self.assertIn('timestamp', result)
        self.assertIn('context', result)
        self.assertIn('individual_analyses', result)
        self.assertIn('consensus', result)
        self.assertEqual(result['context'], context)
        self.assertIn('architect', result['individual_analyses'])
        self.assertIn('security', result['individual_analyses'])
    
    def test_generate_analysis_all_personas(self):
        """Test analysis with all personas."""
        context = {'file': 'test.py', 'description': 'Test'}
        personas = list(PERSONAS.keys())
        
        result = generate_analysis(context, personas)
        
        self.assertEqual(len(result['individual_analyses']), len(PERSONAS))
        for persona in personas:
            self.assertIn(persona, result['individual_analyses'])


class TestCmdAnalyze(unittest.TestCase):
    """Test cmd_analyze function."""
    
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
    
    def test_cmd_analyze_default_output(self):
        """Test analyze command with default text output."""
        args = MagicMock()
        args.file = 'test.py'
        args.description = 'Test description'
        args.goal = 'Test goal'
        args.personas = None
        args.json = False
        args.output = None
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_analyze(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Predict Mode', output)
        self.assertIn('Test description', output)
    
    def test_cmd_analyze_json_output(self):
        """Test analyze command with JSON output."""
        args = MagicMock()
        args.file = 'test.py'
        args.description = 'Test description'
        args.goal = 'Test goal'
        args.personas = None
        args.json = True
        args.output = None
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_analyze(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        # Output contains "Analyzing with X personas..." text before JSON
        # Find the JSON part (starts with {)
        json_start = output.find('{')
        self.assertNotEqual(json_start, -1)
        json_output = output[json_start:]
        # Verify JSON output is valid
        data = json.loads(json_output)
        self.assertIn('timestamp', data)
        self.assertIn('individual_analyses', data)
    
    def test_cmd_analyze_specific_personas(self):
        """Test analyze command with specific personas."""
        args = MagicMock()
        args.file = 'test.py'
        args.description = 'Test'
        args.goal = 'Test goal'
        args.personas = 'architect,security'
        args.json = True
        args.output = None
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_analyze(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        # Find the JSON part (starts with {)
        json_start = output.find('{')
        self.assertNotEqual(json_start, -1)
        json_output = output[json_start:]
        data = json.loads(json_output)
        self.assertEqual(len(data['individual_analyses']), 2)
        self.assertIn('architect', data['individual_analyses'])
        self.assertIn('security', data['individual_analyses'])
    
    def test_cmd_analyze_with_output_file(self):
        """Test analyze command with output file."""
        args = MagicMock()
        args.file = 'test.py'
        args.description = 'Test'
        args.goal = 'Test goal'
        args.personas = None
        args.json = False
        args.output = 'output.json'
        
        result = cmd_analyze(args)
        
        self.assertEqual(result, 0)
        self.assertTrue(os.path.exists('output.json'))
        
        with open('output.json', 'r') as f:
            data = json.load(f)
            self.assertIn('timestamp', data)
            self.assertIn('individual_analyses', data)


class TestCmdListPersonas(unittest.TestCase):
    """Test cmd_list_personas function."""
    
    def test_cmd_list_personas(self):
        """Test listing personas."""
        args = MagicMock()
        
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        result = cmd_list_personas(args)
        
        sys.stdout = old_stdout
        output = captured.getvalue()
        
        self.assertEqual(result, 0)
        self.assertIn('Available Personas', output)
        for persona_key in PERSONAS.keys():
            self.assertIn(persona_key, output)
            self.assertIn(PERSONAS[persona_key]['name'], output)


class TestMain(unittest.TestCase):
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
    
    def test_main_personas_command(self):
        """Test main with personas command."""
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_predict.py', 'personas']
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            result = main()
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            self.assertEqual(result, 0)
            self.assertIn('Available Personas', output)
        finally:
            sys.argv = old_argv
    
    def test_main_analyze_command(self):
        """Test main with analyze command."""
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_predict.py', 'analyze', '--file', 'test.py']
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            result = main()
            
            sys.stdout = old_stdout
            output = captured.getvalue()
            
            self.assertEqual(result, 0)
            self.assertIn('Analyzing', output)
        finally:
            sys.argv = old_argv
    
    def test_main_no_command(self):
        """Test main with no command."""
        old_argv = sys.argv
        try:
            sys.argv = ['autoresearch_predict.py']
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            
            result = main()
            
            sys.stdout = old_stdout
            
            self.assertEqual(result, 1)
        finally:
            sys.argv = old_argv


if __name__ == '__main__':
    unittest.main()
