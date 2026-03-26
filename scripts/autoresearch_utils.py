#!/usr/bin/env python3
"""
Utility functions and commands for autoresearch.
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta


def run_command(cmd: str, timeout: int = 60) -> tuple[int, str]:
    """Run a shell command."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout + result.stderr
    except Exception as e:
        return -1, str(e)


def cmd_stats(args):
    """Show autoresearch statistics."""
    results_file = "autoresearch-results.tsv"
    state_file = "autoresearch-state.json"
    lessons_file = "autoresearch-lessons.md"
    
    stats = {
        'runs': 0,
        'total_iterations': 0,
        'kept': 0,
        'discarded': 0,
        'lessons': 0,
        'files': {}
    }
    
    # Check files
    for f in [results_file, state_file, lessons_file]:
        stats['files'][f] = {
            'exists': os.path.exists(f),
            'size': os.path.getsize(f) if os.path.exists(f) else 0,
            'modified': datetime.fromtimestamp(os.path.getmtime(f)).isoformat() if os.path.exists(f) else None
        }
    
    # Parse results
    if os.path.exists(results_file):
        try:
            import csv
            with open(results_file, 'r') as f:
                reader = csv.DictReader(f, delimiter='\t')
                rows = list(reader)
                stats['total_iterations'] = len(rows)
                stats['kept'] = sum(1 for r in rows if r.get('status') == 'keep')
                stats['discarded'] = sum(1 for r in rows if r.get('status') == 'discard')
        except:
            pass
    
    # Parse state
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
                stats['runs'] += 1
                stats['current_goal'] = state.get('config', {}).get('goal', 'N/A')
                stats['current_iteration'] = state.get('iteration', 0)
        except:
            pass
    
    # Count lessons
    if os.path.exists(lessons_file):
        with open(lessons_file, 'r') as f:
            content = f.read()
            stats['lessons'] = content.count('## ')
    
    if args.json:
        print(json.dumps(stats, indent=2))
    else:
        print("Autoresearch Statistics")
        print("=" * 50)
        print(f"Runs: {stats['runs']}")
        print(f"Total iterations: {stats['total_iterations']}")
        print(f"  Kept: {stats['kept']}")
        print(f"  Discarded: {stats['discarded']}")
        print(f"Lessons learned: {stats['lessons']}")
        
        if 'current_goal' in stats:
            print(f"\nCurrent goal: {stats['current_goal']}")
            print(f"Current iteration: {stats['current_iteration']}")
        
        print("\nFiles:")
        for name, info in stats['files'].items():
            status = "✓" if info['exists'] else "✗"
            print(f"  {status} {name}: {info['size']} bytes")
    
    return 0


def cmd_clean(args):
    """Clean up autoresearch files."""
    files = [
        'autoresearch-results.tsv',
        'autoresearch-state.json',
        'autoresearch-runtime.json',
        'autoresearch-lessons.md',
        'autoresearch-report.md'
    ]
    
    removed = 0
    kept = 0
    
    for f in files:
        if os.path.exists(f):
            if args.force:
                os.remove(f)
                print(f"Removed: {f}")
                removed += 1
            else:
                print(f"Would remove: {f} (use --force to actually delete)")
                kept += 1
    
    # Also clean backup files
    if args.all:
        for f in os.listdir('.'):
            if f.startswith('autoresearch-') and ('.prev.' in f or f.endswith('.bak')):
                if args.force:
                    os.remove(f)
                    print(f"Removed backup: {f}")
                    removed += 1
                else:
                    print(f"Would remove backup: {f}")
    
    print(f"\n{'Removed' if args.force else 'Would remove'}: {removed} files")
    return 0


def cmd_export(args):
    """Export results to different formats."""
    results_file = "autoresearch-results.tsv"
    
    if not os.path.exists(results_file):
        print("No results file found")
        return 1
    
    import csv
    
    with open(results_file, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        rows = list(reader)
    
    if args.format == 'json':
        output = {'iterations': rows}
        with open(args.output or 'autoresearch-export.json', 'w') as f:
            json.dump(output, f, indent=2)
        print(f"Exported to {args.output or 'autoresearch-export.json'}")
    
    elif args.format == 'csv':
        with open(args.output or 'autoresearch-export.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"Exported to {args.output or 'autoresearch-export.csv'}")
    
    elif args.format == 'html':
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Autoresearch Results</title>
    <style>
        body { font-family: sans-serif; margin: 40px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .keep { color: green; }
        .discard { color: red; }
        .baseline { color: blue; }
    </style>
</head>
<body>
    <h1>Autoresearch Results</h1>
    <table>
        <tr>"""
        
        if rows:
            for key in rows[0].keys():
                html += f"<th>{key}</th>"
            html += "</tr>"
            
            for row in rows:
                html += "<tr>"
                for key, value in row.items():
                    css_class = row.get('status', '')
                    html += f'<td class="{css_class}">{value}</td>'
                html += "</tr>"
        
        html += """
    </table>
</body>
</html>"""
        
        output_file = args.output or 'autoresearch-export.html'
        with open(output_file, 'w') as f:
            f.write(html)
        print(f"Exported to {output_file}")
    
    return 0


def cmd_config(args):
    """Generate or validate configuration."""
    config_file = args.file or 'autoresearch-config.json'
    
    if args.validate:
        if not os.path.exists(config_file):
            print(f"Config file not found: {config_file}")
            return 1
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        required = ['goal', 'metric', 'verify']
        missing = [f for f in required if not config.get(f)]
        
        if missing:
            print(f"Missing required fields: {missing}")
            return 1
        
        print("✓ Configuration is valid")
        return 0
    
    # Generate sample config
    sample = {
        "goal": "Reduce type errors",
        "scope": "src/**/*.ts",
        "metric": "type error count",
        "direction": "lower",
        "verify": "tsc --noEmit 2>&1 | grep -c 'error TS'",
        "guard": "npm run build",
        "iterations": 20,
        "target": 0
    }
    
    with open(config_file, 'w') as f:
        json.dump(sample, f, indent=2)
    
    print(f"Generated sample config: {config_file}")
    print("Edit it with your specific configuration")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Autoresearch Utilities',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # stats
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    stats_parser.add_argument('--json', action='store_true')
    
    # clean
    clean_parser = subparsers.add_parser('clean', help='Clean up files')
    clean_parser.add_argument('--force', action='store_true',
                            help='Actually delete files')
    clean_parser.add_argument('--all', action='store_true',
                            help='Include backup files')
    
    # export
    export_parser = subparsers.add_parser('export', help='Export results')
    export_parser.add_argument('--format', type=str, required=True,
                             choices=['json', 'csv', 'html'])
    export_parser.add_argument('--output', type=str,
                             help='Output file path')
    
    # config
    config_parser = subparsers.add_parser('config', help='Configuration')
    config_parser.add_argument('--file', type=str,
                             help='Config file path')
    config_parser.add_argument('--validate', action='store_true',
                             help='Validate existing config')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    commands = {
        'stats': cmd_stats,
        'clean': cmd_clean,
        'export': cmd_export,
        'config': cmd_config
    }
    
    return commands[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
