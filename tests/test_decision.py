#!/usr/bin/env python3
"""Tests for autoresearch_decision.py"""
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from autoresearch_decision import (
    decide_keep_discard,
    check_stuck_pattern,
    update_stuck_counters
)


class TestDecision(unittest.TestCase):
    """Test decision functions."""
    
    def test_decide_keep_discard_improved_and_guard_passed(self):
        """Test keep decision when improved and guard passed."""
        result = decide_keep_discard(
            current_metric=42.0,
            baseline=50.0,
            direction='lower',
            guard_passed=True
        )
        
        self.assertEqual(result['decision'], 'keep')
        self.assertEqual(result['delta'], -8.0)
    
    def test_decide_keep_discard_improved_but_guard_failed(self):
        """Test rework decision when improved but guard failed."""
        result = decide_keep_discard(
            current_metric=42.0,
            baseline=50.0,
            direction='lower',
            guard_passed=False
        )
        
        self.assertEqual(result['decision'], 'rework')
    
    def test_decide_keep_discard_not_improved(self):
        """Test discard decision when not improved."""
        result = decide_keep_discard(
            current_metric=55.0,
            baseline=50.0,
            direction='lower',
            guard_passed=True
        )
        
        self.assertEqual(result['decision'], 'discard')
        self.assertEqual(result['delta'], 5.0)
    
    def test_decide_keep_discard_higher_direction(self):
        """Test with higher direction."""
        result = decide_keep_discard(
            current_metric=60.0,
            baseline=50.0,
            direction='higher',
            guard_passed=True
        )
        
        self.assertEqual(result['decision'], 'keep')
        self.assertEqual(result['delta'], 10.0)
    
    def test_check_stuck_pattern_not_stuck(self):
        """Test when not stuck."""
        state = {
            'consecutive_discards': 2,
            'pivot_count': 0
        }
        
        result = check_stuck_pattern(state)
        
        self.assertEqual(result['action'], 'continue')
    
    def test_check_stuck_pattern_refine(self):
        """Test refine action."""
        state = {
            'consecutive_discards': 3,
            'pivot_count': 0
        }
        
        result = check_stuck_pattern(state)
        
        self.assertEqual(result['action'], 'refine')
    
    def test_check_stuck_pattern_pivot(self):
        """Test pivot action."""
        state = {
            'consecutive_discards': 5,
            'pivot_count': 1
        }
        
        result = check_stuck_pattern(state)
        
        self.assertEqual(result['action'], 'pivot')
    
    def test_check_stuck_pattern_search(self):
        """Test search action after multiple pivots."""
        state = {
            'consecutive_discards': 5,
            'pivot_count': 2
        }
        
        result = check_stuck_pattern(state)
        
        self.assertEqual(result['action'], 'search')
    
    def test_update_stuck_counters_keep(self):
        """Test counter reset on keep."""
        state = {
            'consecutive_discards': 3
        }
        
        result = update_stuck_counters(state, 'keep')
        
        self.assertEqual(result['consecutive_discards'], 0)
    
    def test_update_stuck_counters_discard(self):
        """Test counter increment on discard."""
        state = {
            'consecutive_discards': 2
        }
        
        result = update_stuck_counters(state, 'discard')
        
        self.assertEqual(result['consecutive_discards'], 3)


if __name__ == '__main__':
    unittest.main()
