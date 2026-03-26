#!/usr/bin/env python3
"""
Decision helpers for autoresearch.
Determines keep/discard based on metrics and guards.
"""
import argparse
import json
import os
import subprocess
from typing import Any

STATE_FILE = "autoresearch-state.json"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_state() -> dict[str, Any]:
    """Load current state."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_state(state: dict[str, Any]) -> None:
    """Save state."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def decide_keep_discard(current_metric: float, baseline: float, 
                        direction: str, guard_passed: bool) -> dict[str, Any]:
    """
    Decide whether to keep or discard a change.
    
    Returns dict with:
    - decision: 'keep' | 'discard' | 'rework'
    - reason: explanation
    - delta: metric change
    """
    delta = current_metric - baseline
    
    if direction == 'lower':
        improved = delta < 0
    else:
        improved = delta > 0
    
    if improved and guard_passed:
        return {
            'decision': 'keep',
            'reason': f'Metric improved ({baseline} -> {current_metric}) and guard passed',
            'delta': delta
        }
    elif improved and not guard_passed:
        return {
            'decision': 'rework',
            'reason': f'Metric improved but guard failed - needs rework',
            'delta': delta
        }
    else:
        return {
            'decision': 'discard',
            'reason': f'Metric did not improve ({baseline} -> {current_metric})',
            'delta': delta
        }


def check_stuck_pattern(state: dict[str, Any]) -> dict[str, Any]:
    """
    Check if we're stuck and need to change strategy.
    
    Returns dict with:
    - action: 'continue' | 'refine' | 'pivot' | 'search'
    - reason: explanation
    """
    discards = state.get('consecutive_discards', 0)
    pivots = state.get('pivot_count', 0)
    
    if discards >= 5:
        if pivots >= 2:
            return {
                'action': 'search',
                'reason': f'{discards} consecutive discards, {pivots} pivots - search for external solutions'
            }
        return {
            'action': 'pivot',
            'reason': f'{discards} consecutive discards - pivot to new strategy'
        }
    elif discards >= 3:
        return {
            'action': 'refine',
            'reason': f'{discards} consecutive discards - refine current strategy'
        }
    
    return {
        'action': 'continue',
        'reason': 'No stuck pattern detected'
    }


def trigger_web_search(state: dict[str, Any], auto_trigger: bool = False) -> dict[str, Any]:
    """
    Trigger web search when stuck.
    
    In Kimi environment, this would call SearchWeb tool.
    Otherwise, generates a search query for manual use.
    """
    context = {
        'goal': state.get('config', {}).get('goal', ''),
        'strategy': state.get('strategy', ''),
        'error': state.get('last_error', ''),
        'metric': state.get('config', {}).get('metric', ''),
        'discards': state.get('consecutive_discards', 0),
        'pivots': state.get('pivot_count', 0)
    }
    
    # Build search query
    query_parts = []
    if context['error']:
        query_parts.append(context['error'][:100])
    if context['goal']:
        query_parts.append(context['goal'][:50])
    if context['strategy']:
        query_parts.append(f"{context['strategy']} alternative")
    
    query = ' '.join(query_parts) if query_parts else 'programming best practices'
    
    result = {
        'triggered': True,
        'query': query,
        'context': context,
        'action': 'web_search',
        'note': 'Use Kimi SearchWeb tool with this query'
    }
    
    # In actual Kimi environment, this would be:
    # search_results = SearchWeb(query=query)
    # Then process results to generate hypotheses
    
    return result


def update_stuck_counters(state: dict[str, Any], status: str) -> dict[str, Any]:
    """Update consecutive discard counter based on result."""
    if status == 'keep':
        state['consecutive_discards'] = 0
    elif status == 'discard':
        state['consecutive_discards'] = state.get('consecutive_discards', 0) + 1
    # 'rework' doesn't change counter
    
    save_state(state)
    return state


def main() -> None:
    parser = argparse.ArgumentParser(description='Autoresearch decision helper')
    parser.add_argument('--action', type=str, required=True,
                       choices=['decide', 'check-stuck', 'update-counters', 'trigger-search'])
    
    # For decide action
    parser.add_argument('--current', type=float)
    parser.add_argument('--baseline', type=float)
    parser.add_argument('--direction', type=str, default='higher',
                       choices=['higher', 'lower'])
    parser.add_argument('--guard-passed', type=bool, default=True)
    
    # For update-counters
    parser.add_argument('--status', type=str, choices=['keep', 'discard', 'rework'])
    
    args = parser.parse_args()
    
    if args.action == 'decide':
        if args.current is None or args.baseline is None:
            print("Error: --current and --baseline required for decide")
            exit(1)
        
        result = decide_keep_discard(
            args.current, args.baseline, 
            args.direction, args.guard_passed
        )
        print(json.dumps(result, indent=2))
    
    elif args.action == 'check-stuck':
        state = load_state()
        result = check_stuck_pattern(state)
        print(json.dumps(result, indent=2))
    
    elif args.action == 'update-counters':
        if not args.status:
            print("Error: --status required")
            exit(1)
        
        state = load_state()
        state = update_stuck_counters(state, args.status)
        print(json.dumps({
            'consecutive_discards': state.get('consecutive_discards', 0),
            'pivot_count': state.get('pivot_count', 0)
        }, indent=2))
    
    elif args.action == 'trigger-search':
        state = load_state()
        result = trigger_web_search(state)
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
