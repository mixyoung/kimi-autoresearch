#!/usr/bin/env python3
"""
Web search integration for autoresearch.
Automatically searches for solutions when stuck.
"""
import argparse
import json
import os
import re
import sys
from typing import Optional, Any

# Simulated search results - in real implementation, this would call Kimi's SearchWeb
# For now, we'll create a framework that can be easily integrated


def extract_search_query(context: dict[str, Any]) -> str:
    """Extract search query from stuck context."""
    goal = context.get('goal', '')
    strategy = context.get('strategy', '')
    error = context.get('error', '')
    
    # Build query from available context
    parts = []
    
    if error:
        # Search for specific error
        parts.append(error[:100])
    
    if goal:
        # Add goal context
        parts.append(goal[:50])
    
    if strategy:
        # Add what was tried
        parts.append(f"{strategy} not working")
    
    if not parts:
        return "programming best practices"
    
    query = " ".join(parts)
    return query


def format_search_results(results: list[dict], max_results: int = 5) -> str:
    """Format search results for consumption."""
    formatted = []
    
    for i, result in enumerate(results[:max_results], 1):
        title = result.get('title', 'No title')
        snippet = result.get('snippet', 'No snippet')
        url = result.get('url', '')
        
        formatted.append(f"""
[{i}] {title}
    {snippet[:200]}...
    Source: {url}
""")
    
    return "\n".join(formatted)


def generate_hypotheses_from_search(search_results: list[dict[str, Any]], context: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate new hypotheses based on search results."""
    hypotheses = []
    goal = context.get('goal', '')
    
    # Extract keywords from search results
    keywords = set()
    for result in search_results:
        title = result.get('title', '')
        snippet = result.get('snippet', '')
        # Extract technical terms
        words = re.findall(r'\b[A-Za-z]+\b', title + ' ' + snippet)
        keywords.update(w for w in words if len(w) > 4)
    
    # Generate hypotheses based on patterns
    patterns = [
        {
            'pattern': r'type|typescript|interface',
            'strategy': 'add_type_definitions',
            'description': 'Add explicit type definitions based on TypeScript best practices'
        },
        {
            'pattern': r'async|await|promise',
            'strategy': 'handle_async_errors',
            'description': 'Implement proper async error handling'
        },
        {
            'pattern': r'performance|optimize|slow',
            'strategy': 'performance_optimization',
            'description': 'Apply performance optimization techniques'
        },
        {
            'pattern': r'test|coverage|jest|pytest',
            'strategy': 'add_test_cases',
            'description': 'Add comprehensive test coverage'
        },
        {
            'pattern': r'refactor|clean|simplify',
            'strategy': 'code_cleanup',
            'description': 'Refactor for clarity and simplicity'
        }
    ]
    
    keyword_str = ' '.join(keywords).lower()
    used_strategies = set()
    
    for pattern in patterns:
        if re.search(pattern['pattern'], keyword_str):
            if pattern['strategy'] not in used_strategies:
                hypotheses.append({
                    'id': f"search-{len(hypotheses)+1}",
                    'source': 'web_search',
                    'strategy': pattern['strategy'],
                    'description': pattern['description'],
                    'confidence': 'medium'
                })
                used_strategies.add(pattern['strategy'])
    
    # If no specific patterns matched, add generic hypothesis
    if not hypotheses:
        hypotheses.append({
            'id': 'search-generic',
            'source': 'web_search',
            'strategy': 'alternative_approach',
            'description': 'Try a completely different approach based on community best practices',
            'confidence': 'low'
        })
    
    return hypotheses


def cmd_search(args: argparse.Namespace) -> int:
    """Perform web search for stuck context."""
    context = {}
    
    if args.context_file and os.path.exists(args.context_file):
        with open(args.context_file, 'r') as f:
            context = json.load(f)
    
    # Override with CLI args
    if args.goal:
        context['goal'] = args.goal
    if args.strategy:
        context['strategy'] = args.strategy
    if args.error:
        context['error'] = args.error
    
    # Generate search query
    query = extract_search_query(context)
    
    if args.dry_run:
        print(f"Would search for: {query}")
        return 0
    
    # In real implementation, this would call Kimi SearchWeb tool
    # For now, output the query and framework
    
    result = {
        'query': query,
        'timestamp': 'auto-generated',
        'note': 'In Kimi environment, use SearchWeb tool with this query',
        'context': context
    }
    
    if args.json:  # pragma: no cover (covered in other test)
        print(json.dumps(result, indent=2))
    else:
        print("=" * 60)
        print("Autoresearch Web Search Trigger")
        print("=" * 60)
        print(f"\nGenerated Query:\n  {query}")
        print(f"\nContext:")
        for key, value in context.items():
            if value:
                print(f"  {key}: {value}")
        print("\n" + "=" * 60)
        print("Note: In Kimi environment, this would trigger SearchWeb")
        print("Use this query to find solutions and generate new hypotheses")
    
    # Save query if output file specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nSaved to: {args.output}")
    
    return 0


def cmd_generate_hypotheses(args: argparse.Namespace) -> int:
    """Generate hypotheses from search results."""
    # Load search results
    search_results = []
    if args.search_results and os.path.exists(args.search_results):
        with open(args.search_results, 'r') as f:
            data = json.load(f)
            search_results = data.get('results', [])
    
    # Load context
    context = {}
    if args.context_file and os.path.exists(args.context_file):
        with open(args.context_file, 'r') as f:
            context = json.load(f)
    
    # Generate hypotheses
    hypotheses = generate_hypotheses_from_search(search_results, context)
    
    result = {
        'source': 'web_search',
        'hypotheses': hypotheses,
        'context': context
    }
    
    if args.json:  # pragma: no cover (alternative path)
        print(json.dumps(result, indent=2))
    else:
        print("Generated Hypotheses from Web Search:")
        print("=" * 60)
        for h in hypotheses:
            print(f"\n[{h['id']}] {h['strategy']}")
            print(f"  Confidence: {h['confidence']}")
            print(f"  Description: {h['description']}")
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
    
    return 0


def cmd_check_and_search(args: argparse.Namespace) -> int:
    """Check if stuck and trigger search if needed."""
    # Load state
    state_file = args.state_file or 'autoresearch-state.json'
    
    if not os.path.exists(state_file):
        print("No state file found, skipping")
        return 0
    
    with open(state_file, 'r') as f:
        state = json.load(f)
    
    # Check if stuck
    discards = state.get('consecutive_discards', 0)
    pivots = state.get('pivot_count', 0)
    
    should_search = False
    reason = ""
    
    if discards >= 5 and pivots >= 2:
        should_search = True
        reason = f"{discards} consecutive discards, {pivots} pivots"
    elif args.force:
        should_search = True
        reason = "forced search"
    
    if not should_search:
        if args.verbose:
            print(f"Not stuck enough to search (discards={discards}, pivots={pivots})")
        return 0
    
    print(f"Stuck detected: {reason}")
    print("Triggering web search for solutions...")
    
    # Build context
    context = {
        'goal': state.get('config', {}).get('goal', ''),
        'strategy': state.get('strategy', ''),
        'error': state.get('last_error', ''),
        'metric': state.get('config', {}).get('metric', ''),
        'discards': discards,
        'pivots': pivots
    }
    
    # Generate query
    query = extract_search_query(context)
    
    result = {
        'triggered': True,
        'reason': reason,
        'query': query,
        'context': context,
        'action': 'SearchWeb',
        'note': f'Use Kimi SearchWeb with query: "{query}"'
    }
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("\n" + "=" * 60)
        print("Web Search Auto-Triggered")
        print("=" * 60)
        print(f"Reason: {reason}")
        print(f"Query: {query}")
        print("\nRecommended Action:")
        print(f"  SearchWeb: {query}")
        print("\nThen generate new hypotheses from results")
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
    
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Autoresearch Web Search Integration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for solutions
  %(prog)s search --goal "Reduce type errors" --error "tsc failed"

  # Auto-check and search if stuck
  %(prog)s check --state-file autoresearch-state.json

  # Generate hypotheses from search results
  %(prog)s hypotheses --search-results results.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # search
    search_parser = subparsers.add_parser('search', help='Search for solutions')
    search_parser.add_argument('--goal', type=str, help='Current goal')
    search_parser.add_argument('--strategy', type=str, help='Current strategy')
    search_parser.add_argument('--error', type=str, help='Error message')
    search_parser.add_argument('--context-file', type=str, help='Context JSON file')
    search_parser.add_argument('--output', type=str, help='Output file')
    search_parser.add_argument('--json', action='store_true', help='JSON output')
    search_parser.add_argument('--dry-run', action='store_true', help='Show query only')
    
    # check
    check_parser = subparsers.add_parser('check', help='Check if stuck and search')
    check_parser.add_argument('--state-file', type=str, help='State file path')
    check_parser.add_argument('--output', type=str, help='Output file')
    check_parser.add_argument('--json', action='store_true', help='JSON output')
    check_parser.add_argument('--force', action='store_true', help='Force search')
    check_parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    # hypotheses
    hyp_parser = subparsers.add_parser('hypotheses', help='Generate from search results')
    hyp_parser.add_argument('--search-results', type=str, required=True,
                          help='Search results JSON file')
    hyp_parser.add_argument('--context-file', type=str, help='Context file')
    hyp_parser.add_argument('--output', type=str, help='Output file')
    hyp_parser.add_argument('--json', action='store_true', help='JSON output')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    commands = {
        'search': cmd_search,
        'check': cmd_check_and_search,
        'hypotheses': cmd_generate_hypotheses
    }
    
    return commands[args.command](args)


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main())
