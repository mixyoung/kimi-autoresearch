#!/usr/bin/env python3
"""
Generate summary report from autoresearch results.
"""
import csv
import os
from datetime import datetime

RESULTS_FILE = "autoresearch-results.tsv"
REPORT_FILE = "autoresearch-report.md"


def generate_report():
    """Generate a markdown report from results TSV."""
    
    if not os.path.exists(RESULTS_FILE):
        print("No results file found")
        return
    
    rows = []
    with open(RESULTS_FILE, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        rows = list(reader)
    
    if not rows:
        print("No data in results file")
        return
    
    # Calculate statistics
    baseline_row = rows[0] if rows else None
    keep_count = sum(1 for r in rows if r.get('status') == 'keep')
    discard_count = sum(1 for r in rows if r.get('status') == 'discard')
    
    # Find best result
    best_row = None
    best_metric = None
    for row in rows:
        if row.get('status') == 'keep':
            try:
                metric = float(row.get('metric', 0))
                if best_metric is None:
                    best_metric = metric
                    best_row = row
            except ValueError:
                continue
    
    # Generate report
    report = f"""# Autoresearch Report

Generated: {datetime.now().isoformat()}

## Summary

| Metric | Value |
|--------|-------|
| Total Iterations | {len(rows) - 1} |
| Successful (keep) | {keep_count} |
| Discarded | {discard_count} |
| Success Rate | {keep_count / max(1, keep_count + discard_count) * 100:.1f}% |

## Baseline vs Best

| | Iteration | Metric | Commit |
|--|-----------|--------|--------|
| **Baseline** | 0 | {baseline_row.get('metric', 'N/A') if baseline_row else 'N/A'} | {baseline_row.get('commit', 'N/A')[:8] if baseline_row else 'N/A'} |
| **Best** | {best_row.get('iteration', 'N/A') if best_row else 'N/A'} | {best_row.get('metric', 'N/A') if best_row else 'N/A'} | {best_row.get('commit', 'N/A')[:8] if best_row else 'N/A'} |

## All Iterations

| Iteration | Status | Metric | Delta | Description |
|-----------|--------|--------|-------|-------------|
"""
    
    for row in rows:
        report += f"| {row.get('iteration', '-')} | {row.get('status', '-')} | {row.get('metric', '-')} | {row.get('delta', '-')} | {row.get('description', '-')[:50]} |\n"
    
    report += """
## Key Decisions

"""
    
    # Extract keep decisions
    for row in rows:
        if row.get('status') == 'keep' and row.get('iteration') != '0':
            report += f"- **Iteration {row.get('iteration')}**: {row.get('description')}\n"
    
    # Write report
    with open(REPORT_FILE, 'w') as f:
        f.write(report)
    
    print(f"Report generated: {REPORT_FILE}")
    print(f"  - Total iterations: {len(rows) - 1}")
    print(f"  - Successful: {keep_count}")
    print(f"  - Discarded: {discard_count}")


def main():
    generate_report()


if __name__ == '__main__':
    main()
