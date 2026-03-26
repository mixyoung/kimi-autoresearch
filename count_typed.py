#!/usr/bin/env python3
"""Count functions with type hints in scripts directory."""
import ast
import os
import glob

def count_typed_functions(filename):
    """Count typed and untyped functions in a file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
    except:
        return 0, 0
    
    total = 0
    typed = 0
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Skip __init__ methods which don't need return type
            if node.name == '__init__':
                continue
            total += 1
            if node.returns is not None:
                typed += 1
    
    return total, typed

if __name__ == '__main__':
    total_funcs = 0
    typed_funcs = 0
    
    for filepath in glob.glob('scripts/*.py'):
        t, typed = count_typed_functions(filepath)
        total_funcs += t
        typed_funcs += typed
    
    print(typed_funcs)
