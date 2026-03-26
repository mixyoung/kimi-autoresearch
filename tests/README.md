# Autoresearch Test Suite

## Running Tests

### Run all tests
```bash
python -m pytest tests/ -v
```

### Run specific test file
```bash
python -m pytest tests/test_health_check.py -v
```

### Run with coverage
```bash
python -m pytest tests/ --cov=scripts --cov-report=html
```

### Using unittest directly
```bash
python -m unittest discover tests/ -v
```

## Test Files

| File | Description |
|------|-------------|
| test_health_check.py | Health check function tests |
| test_decision.py | Decision logic tests |
| test_git.py | Git operation tests |

## Writing New Tests

```python
#!/usr/bin/env python3
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from script_to_test import function_to_test


class TestFeature(unittest.TestCase):
    def test_something(self):
        result = function_to_test()
        self.assertEqual(result, expected_value)


if __name__ == '__main__':
    unittest.main()
```
