#!/usr/bin/env python3
"""
Stuck recovery with automatic web search trigger.

Automatically searches for solutions when stuck pattern detected.
Integrates with Kimi's SearchWeb tool when available.
"""
import argparse
import json
import os
import sys
from typing import Optional

STATE_FILE = "autoresearch-state.json"
RESULTS_FILE = "autoresearch-results.tsv"


def load_state() -> dict:
    """Load current state."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {}


def load_results() -> list:
    """Load recent results."""
    if not os.path.exists(RESULTS_FILE):
        return []
    
    import csv
    try:
        with open(RESULTS_FILE, 'r') as f:
            reader = csv.DictReader(f, delimiter='\t')
            return list(reader)
    except:
        return []


def analyze_stuck_pattern(state: dict, results: list) -> dict:
    """
    Analyze if we're stuck and need external help.
    
    Returns:
        {
            'is_stuck': bool,
            'reason': str,
            'discards': int,
            'pivots': int,
            'action': str,  # 'continue', 'refine', 'pivot', 'search'
            'search_query': str  # suggested search query
        }
    """
    discards = state.get('consecutive_discards', 0)
    pivots = state.get('pivot_count', 0)
    goal = state.get('config', {}).get('goal', '')
    strategy = state.get('strategy', '')
    last_error = state.get('last_error', '')
    
    analysis = {
        'is_stuck': False,
        'reason': '',
        'discards': discards,
        'pivots': pivots,
        'action': 'continue',
        'search_query': '',
        'context': {
            'goal': goal,
            'strategy': strategy,
            'error': last_error
        }
    }
    
    if discards >= 5 and pivots >= 2:
        analysis['is_stuck'] = True
        analysis['action'] = 'search'
        analysis['reason'] = f'{discards} consecutive discards, {pivots} pivots'
    elif discards >= 5:
        analysis['is_stuck'] = True
        analysis['action'] = 'pivot'
        analysis['reason'] = f'{discards} consecutive discards'
    elif discards >= 3:
        analysis['action'] = 'refine'
        analysis['reason'] = f'{discards} consecutive discards - refine strategy'
    
    # Build search query
    if analysis['is_stuck'] and analysis['action'] == 'search':
        query_parts = []
        if last_error:
            query_parts.append(last_error[:100])
        if goal:
            query_parts.append(goal[:50])
        if strategy:
            query_parts.append(f"{strategy} alternative approach")
        
        if not query_parts:
            query_parts.append("programming best practices")
        
        analysis['search_query'] = ' '.join(query_parts)
    
    return analysis


def generate_recovery_suggestions(analysis: dict) -> list:
    """Generate recovery suggestions based on analysis."""
    suggestions = []
    
    action = analysis['action']
    goal = analysis['context']['goal']
    
    if action == 'refine':
        suggestions = [
            "Re-read all in-scope files from scratch",
            "Review successful changes from earlier iterations",
            "Combine 2-3 successful patterns",
            "Try smaller, more focused changes"
        ]
    elif action == 'pivot':
        suggestions = [
            "Try completely different approach",
            "Change the scope (expand or narrow)",
            "Switch to different metric",
            "Consider using different tools/libraries"
        ]
    elif action == 'search':
        suggestions = [
            f"Search for: {analysis['search_query']}",
            "Look for community solutions",
            "Check documentation for alternatives",
            "Consider asking in forums"
        ]
    
    return suggestions


def should_trigger_web_search(auto_trigger: bool = False) -> tuple[bool, dict]:
    """
    Check if web search should be triggered.
    
    Args:
        auto_trigger: Whether to auto-trigger (vs just check)
        
    Returns:
        (should_search, analysis)
    """
    state = load_state()
    results = load_results()
    
    analysis = analyze_stuck_pattern(state, results)
    
    should_search = (
        analysis['is_stuck'] and
        analysis['action'] == 'search' and
        auto_trigger
    )
    
    return should_search, analysis


def cmd_check(args):
    """Check stuck status without triggering search."""
    should_search, analysis = should_trigger_web_search(auto_trigger=False)
    
    if args.json:
        print(json.dumps(analysis, indent=2))
    else:
        print("=" * 60)
        print("Stuck Recovery Analysis")
        print("=" * 60)
        print(f"\nConsecutive discards: {analysis['discards']}")
        print(f"Pivot count: {analysis['pivots']}")
        print(f"Action: {analysis['action']}")
        
        if analysis['reason']:
            print(f"Reason: {analysis['reason']}")
        
        if analysis['is_stuck']:
            print("\n⚠ STUCK DETECTED")
            print(f"\nSuggested search query:")
            print(f"  {analysis['search_query']}")
            
            suggestions = generate_recovery_suggestions(analysis)
            print("\nRecovery suggestions:")
            for i, s in enumerate(suggestions, 1):
                print(f"  {i}. {s}")
        else:
            print("\n✓ Not stuck - continue current strategy")
    
    return 0 if not analysis['is_stuck'] else 2


def cmd_trigger(args):
    """Trigger web search if stuck."""
    should_search, analysis = should_trigger_web_search(auto_trigger=True)
    
    if not analysis['is_stuck']:
        if not args.quiet:
            print("Not stuck enough to trigger search")
            print(f"Current: {analysis['discards']} discards, {analysis['pivots']} pivots")
            print("Need: 5+ discards and 2+ pivots")
        return 0
    
    if not should_search:
        if not args.quiet:
            print(f"Stuck detected but action is '{analysis['action']}', not 'search'")
        return 1
    
    # Output search trigger
    result = {
        'triggered': True,
        'reason': analysis['reason'],
        'query': analysis['search_query'],
        'context': analysis['context'],
        'action': 'web_search',
        'note': 'Use Kimi SearchWeb tool with this query',
        'suggestions': generate_recovery_suggestions(analysis)
    }
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("=" * 60)
        print("🌐 Web Search Auto-Triggered")
        print("=" * 60)
        print(f"\nReason: {result['reason']}")
        print(f"\nQuery:")
        print(f"  {result['query']}")
        print(f"\nAction: Use Kimi SearchWeb")
        print(f"  SearchWeb(query='{result['query']}')")
        
        print("\nRecovery suggestions:")
        for i, s in enumerate(result['suggestions'], 1):
            print(f"  {i}. {s}")
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        if not args.quiet:
            print(f"\nSaved to: {args.output}")
    
    return 0


def cmd_simulate(args):
    """Simulate stuck condition for testing."""
    analysis = {
        'is_stuck': True,
        'action': 'search',
        'reason': 'Simulated stuck condition',
        'discards': args.discards or 5,
        'pivots': args.pivots or 2,
        'search_query': args.query or 'how to optimize python performance',
        'context': {
            'goal': 'Optimize performance',
            'strategy': 'cache optimization',
            'error': 'No improvement after 5 attempts'
        }
    }
    
    result = {
        'triggered': True,
        'reason': analysis['reason'],
        'query': analysis['search_query'],
        'context': analysis['context'],
        'action': 'web_search',
        'note': 'SIMULATION - For testing only',
        'suggestions': generate_recovery_suggestions(analysis)
    }
    
    print(json.dumps(result, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Stuck recovery with automatic web search'
    )
    parser.add_argument('--json', action='store_true', help='JSON output')
    parser.add_argument('--quiet', action='store_true', help='Minimal output')
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # check
    subparsers.add_parser('check', help='Check stuck status')
    
    # trigger
    trigger_parser = subparsers.add_parser('trigger', help='Trigger search if stuck')
    trigger_parser.add_argument('--output', type=str, help='Save result to file')
    
    # simulate (for testing)
    sim_parser = subparsers.add_parser('simulate', help='Simulate stuck (for testing)')
    sim_parser.add_argument('--discards', type=int, help='Simulated discard count')
    sim_parser.add_argument('--pivots', type=int, help='Simulated pivot count')
    sim_parser.add_argument('--query', type=str, help='Simulated search query')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    commands = {
        'check': cmd_check,
        'trigger': cmd_trigger,
        'simulate': cmd_simulate
    }
    
    return commands[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
