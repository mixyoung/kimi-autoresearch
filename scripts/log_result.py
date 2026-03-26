#!/usr/bin/env python3
"""
Log autoresearch iteration result to TSV file.
"""
import argparse
import csv
import os
from datetime import datetime

RESULTS_FILE = "autoresearch-results.tsv"


def log_result(iteration: int, commit: str, metric: str, delta: str, 
               status: str, description: str):
    """Append a result row to the TSV file."""
    
    # Create file with headers if it doesn't exist
    if not os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'w', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['iteration', 'commit', 'metric', 'delta', 
                           'status', 'description', 'timestamp'])
    
    # Append the result row
    with open(RESULTS_FILE, 'a', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow([
            iteration,
            commit,
            metric,
            delta,
            status,
            description,
            datetime.now().isoformat()
        ])
    
    print(f"Logged: iteration {iteration} - {status}")


def main():
    parser = argparse.ArgumentParser(description='Log autoresearch result')
    parser.add_argument('--iteration', type=int, required=True)
    parser.add_argument('--commit', type=str, required=True)
    parser.add_argument('--metric', type=str, required=True)
    parser.add_argument('--delta', type=str, default='0')
    parser.add_argument('--status', type=str, required=True,
                       choices=['baseline', 'keep', 'discard', 'crash'])
    parser.add_argument('--description', type=str, required=True)
    
    args = parser.parse_args()
    
    log_result(
        args.iteration,
        args.commit,
        args.metric,
        args.delta,
        args.status,
        args.description
    )


if __name__ == '__main__':
    main()
