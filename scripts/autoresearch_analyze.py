#!/usr/bin/env python3
"""
Analyze autoresearch results and trends.

Provides insights into:
- Success rate trends
- Metric improvement patterns
- Strategy effectiveness
- Stuck pattern analysis
"""
import argparse
import csv
import json
import os
import statistics
from datetime import datetime
from typing import Optional

RESULTS_FILE = "autoresearch-results.tsv"
STATE_FILE = "autoresearch-state.json"


def load_results() -> list[dict]:
    """Load results from TSV file."""
    if not os.path.exists(RESULTS_FILE):
        return []
    
    try:
        with open(RESULTS_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f, delimiter='\t')
            return list(reader)
    except Exception as e:
        print(f"Error loading results: {e}", file=sys.stderr)
        return []


def analyze_trends(results: list[dict]) -> dict:
    """Analyze overall trends from results."""
    if not results:
        return {'error': 'No results found'}
    
    # Basic counts
    total = len(results)
    baseline_count = sum(1 for r in results if r.get('status') == 'baseline')
    keep_count = sum(1 for r in results if r.get('status') == 'keep')
    discard_count = sum(1 for r in results if r.get('status') == 'discard')
    crash_count = sum(1 for r in results if r.get('status') == 'crash')
    iterations = total - baseline_count
    
    # Success rate
    success_rate = (keep_count / iterations * 100) if iterations > 0 else 0
    
    # Metric analysis
    metrics = []
    for r in results:
        try:
            m = float(r.get('metric', 0))
            metrics.append(m)
        except (ValueError, TypeError):
            pass
    
    metric_analysis = {}
    if metrics:
        metric_analysis = {
            'initial': metrics[0] if metrics else 0,
            'final': metrics[-1] if metrics else 0,
            'min': min(metrics),
            'max': max(metrics),
            'mean': statistics.mean(metrics),
            'median': statistics.median(metrics),
            'stdev': statistics.stdev(metrics) if len(metrics) > 1 else 0,
            'improvement': metrics[-1] - metrics[0] if len(metrics) > 1 else 0,
            'improvement_pct': ((metrics[-1] - metrics[0]) / metrics[0] * 100) 
                              if len(metrics) > 1 and metrics[0] != 0 else 0
        }
    
    # Streak analysis
    current_streak = 0
    longest_keep_streak = 0
    longest_discard_streak = 0
    temp_streak = 0
    last_status = None
    
    for r in results:
        status = r.get('status')
        if status == 'baseline':
            continue
        
        if status == last_status:
            temp_streak += 1
        else:
            temp_streak = 1
        
        if status == 'keep':
            longest_keep_streak = max(longest_keep_streak, temp_streak)
        elif status == 'discard':
            longest_discard_streak = max(longest_discard_streak, temp_streak)
        
        last_status = status
    
    current_streak = temp_streak if last_status != 'baseline' else 0
    
    return {
        'total_iterations': total,
        'baseline_count': baseline_count,
        'keep_count': keep_count,
        'discard_count': discard_count,
        'crash_count': crash_count,
        'success_rate': round(success_rate, 2),
        'metrics': metric_analysis,
        'streaks': {
            'current': current_streak,
            'current_status': last_status,
            'longest_keep': longest_keep_streak,
            'longest_discard': longest_discard_streak
        }
    }


def analyze_by_window(results: list[dict], window_size: int = 10) -> list[dict]:
    """Analyze results in sliding windows."""
    if not results or window_size <= 0:
        return []
    
    windows = []
    non_baseline = [r for r in results if r.get('status') != 'baseline']
    
    for i in range(0, len(non_baseline), window_size):
        window = non_baseline[i:i+window_size]
        
        keep_count = sum(1 for r in window if r.get('status') == 'keep')
        discard_count = sum(1 for r in window if r.get('status') == 'discard')
        total = len(window)
        
        windows.append({
            'window_start': i + 1,
            'window_end': min(i + window_size, len(non_baseline)),
            'keep_count': keep_count,
            'discard_count': discard_count,
            'success_rate': round(keep_count / total * 100, 2) if total > 0 else 0
        })
    
    return windows


def analyze_strategies(results: list[dict]) -> dict:
    """Analyze which strategies/descriptions were most successful."""
    strategies = {}
    
    for r in results:
        status = r.get('status')
        desc = r.get('description', '')
        
        # Extract strategy pattern (first few words)
        strategy = ' '.join(desc.split()[:3]) if desc else 'unknown'
        
        if strategy not in strategies:
            strategies[strategy] = {'keep': 0, 'discard': 0, 'total': 0}
        
        strategies[strategy]['total'] += 1
        if status == 'keep':
            strategies[strategy]['keep'] += 1
        elif status == 'discard':
            strategies[strategy]['discard'] += 1
    
    # Calculate success rates
    for strategy, counts in strategies.items():
        counts['success_rate'] = round(
            counts['keep'] / counts['total'] * 100, 2
        ) if counts['total'] > 0 else 0
    
    # Sort by success rate
    sorted_strategies = dict(sorted(
        strategies.items(),
        key=lambda x: x[1]['success_rate'],
        reverse=True
    ))
    
    return sorted_strategies


def cmd_trends(args):
    """Show overall trends."""
    results = load_results()
    
    if not results:
        print("No results found")
        return 1
    
    analysis = analyze_trends(results)
    
    if args.json:
        print(json.dumps(analysis, indent=2))
        return 0
    
    print("=" * 60)
    print("Autoresearch Trend Analysis")
    print("=" * 60)
    
    print(f"\n📊 Overall Statistics:")
    print(f"  Total iterations: {analysis['total_iterations']}")
    print(f"  Baseline: {analysis['baseline_count']}")
    print(f"  Kept: {analysis['keep_count']}")
    print(f"  Discarded: {analysis['discard_count']}")
    print(f"  Crashed: {analysis['crash_count']}")
    print(f"  Success rate: {analysis['success_rate']}%")
    
    if analysis.get('metrics'):
        m = analysis['metrics']
        print(f"\n📈 Metric Analysis:")
        print(f"  Initial: {m['initial']:.2f}")
        print(f"  Final: {m['final']:.2f}")
        print(f"  Min: {m['min']:.2f}")
        print(f"  Max: {m['max']:.2f}")
        print(f"  Mean: {m['mean']:.2f}")
        print(f"  Median: {m['median']:.2f}")
        print(f"  StdDev: {m['stdev']:.2f}")
        print(f"  Improvement: {m['improvement']:+.2f} ({m['improvement_pct']:+.1f}%)")
    
    if analysis.get('streaks'):
        s = analysis['streaks']
        print(f"\n🔥 Streak Analysis:")
        print(f"  Current streak: {s['current']} {s['current_status'] or 'N/A'}")
        print(f"  Longest keep streak: {s['longest_keep']}")
        print(f"  Longest discard streak: {s['longest_discard']}")
    
    return 0


def cmd_windows(args):
    """Show windowed analysis."""
    results = load_results()
    
    if not results:
        print("No results found")
        return 1
    
    windows = analyze_by_window(results, args.size)
    
    if args.json:
        print(json.dumps(windows, indent=2))
        return 0
    
    print("=" * 60)
    print(f"Windowed Analysis (size={args.size})")
    print("=" * 60)
    
    print(f"\n{'Window':<12} {'Iterations':<12} {'Kept':<8} {'Discarded':<10} {'Rate':<8}")
    print("-" * 60)
    
    for w in windows:
        print(f"{w['window_start']}-{w['window_end']:<10} "
              f"{w['keep_count']+w['discard_count']:<12} "
              f"{w['keep_count']:<8} "
              f"{w['discard_count']:<10} "
              f"{w['success_rate']}%")
    
    # Trend indicator
    if len(windows) >= 2:
        first_rate = windows[0]['success_rate']
        last_rate = windows[-1]['success_rate']
        
        print(f"\n📊 Trend:")
        if last_rate > first_rate:
            print(f"  ↗ Improving: {first_rate}% → {last_rate}%")
        elif last_rate < first_rate:
            print(f"  ↘ Declining: {first_rate}% → {last_rate}%")
        else:
            print(f"  → Stable: {first_rate}%")
    
    return 0


def cmd_strategies(args):
    """Analyze strategy effectiveness."""
    results = load_results()
    
    if not results:
        print("No results found")
        return 1
    
    strategies = analyze_strategies(results)
    
    if args.json:
        print(json.dumps(strategies, indent=2))
        return 0
    
    print("=" * 60)
    print("Strategy Effectiveness Analysis")
    print("=" * 60)
    
    print(f"\n{'Strategy':<30} {'Total':<8} {'Kept':<8} {'Discarded':<10} {'Rate':<8}")
    print("-" * 80)
    
    for strategy, counts in list(strategies.items())[:args.top]:
        strategy_short = strategy[:29] if len(strategy) > 30 else strategy
        print(f"{strategy_short:<30} "
              f"{counts['total']:<8} "
              f"{counts['keep']:<8} "
              f"{counts['discard']:<10} "
              f"{counts['success_rate']}%")
    
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Analyze autoresearch results and trends'
    )
    parser.add_argument('--json', action='store_true', help='JSON output')
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # trends
    subparsers.add_parser('trends', help='Show overall trends')
    
    # windows
    window_parser = subparsers.add_parser('windows', help='Windowed analysis')
    window_parser.add_argument('--size', type=int, default=10,
                              help='Window size (default 10)')
    
    # strategies
    strat_parser = subparsers.add_parser('strategies', help='Strategy analysis')
    strat_parser.add_argument('--top', type=int, default=10,
                             help='Show top N strategies')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    commands = {
        'trends': cmd_trends,
        'windows': cmd_windows,
        'strategies': cmd_strategies
    }
    
    return commands[args.command](args)


if __name__ == '__main__':
    import sys
    sys.exit(main())
