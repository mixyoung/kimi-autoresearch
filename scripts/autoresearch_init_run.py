#!/usr/bin/env python3
"""
Initialize a new autoresearch run.
Sets up baseline, state, and results file.
"""
import argparse
import json
import os
import csv
from datetime import datetime

RESULTS_FILE = "autoresearch-results.tsv"
STATE_FILE = "autoresearch-state.json"
LESSONS_FILE = "autoresearch-lessons.md"


def init_results_file() -> None:
    """Create results TSV with headers."""
    if os.path.exists(RESULTS_FILE):
        # Archive old results
        backup_name = f"autoresearch-results.{datetime.now().strftime('%Y%m%d_%H%M%S')}.tsv"
        os.rename(RESULTS_FILE, backup_name)
        print(f"Archived old results to {backup_name}")
    
    with open(RESULTS_FILE, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['iteration', 'commit', 'metric', 'delta', 
                        'status', 'description', 'timestamp'])
    print(f"Created {RESULTS_FILE}")


def init_state(config: dict) -> None:
    """Initialize state file with run configuration."""
    state = {
        'version': '1.0',
        'start_time': datetime.now().isoformat(),
        'status': 'initialized',
        'iteration': 0,
        'baseline': None,
        'best': None,
        'consecutive_discards': 0,
        'pivot_count': 0,
        'strategy': 'initial',
        'config': config,
        'history': []
    }
    
    if os.path.exists(STATE_FILE):
        backup_name = f"autoresearch-state.{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.rename(STATE_FILE, backup_name)
    
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    print(f"Created {STATE_FILE}")


def init_lessons_file() -> None:
    """Create lessons file if not exists."""
    if not os.path.exists(LESSONS_FILE):
        with open(LESSONS_FILE, 'w') as f:
            f.write("# Autoresearch Lessons\n\n")
            f.write("Learnings from previous runs.\n\n")
        print(f"Created {LESSONS_FILE}")


def main() -> None:
    parser = argparse.ArgumentParser(description='Initialize autoresearch run')
    parser.add_argument('--goal', type=str, required=True)
    parser.add_argument('--scope', type=str, default='')
    parser.add_argument('--metric', type=str, required=True)
    parser.add_argument('--verify', type=str, required=True)
    parser.add_argument('--guard', type=str, default='')
    parser.add_argument('--direction', type=str, default='higher',
                       choices=['higher', 'lower'])
    parser.add_argument('--iterations', type=int, default=0)
    parser.add_argument('--mode', type=str, default='loop',
                       choices=['loop', 'debug', 'fix', 'security', 'ship'])
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("Initializing Autoresearch Run")
    print("=" * 50)
    
    config = {
        'goal': args.goal,
        'scope': args.scope,
        'metric': args.metric,
        'verify': args.verify,
        'guard': args.guard,
        'direction': args.direction,
        'max_iterations': args.iterations,
        'mode': args.mode
    }
    
    init_results_file()
    init_state(config)
    init_lessons_file()
    
    print("\nConfiguration:")
    for key, value in config.items():
        if value:
            print(f"  {key}: {value}")
    
    print("\n✓ Run initialized successfully")
    print(f"  Next: Establish baseline with verify command")


if __name__ == '__main__':
    main()
