#!/usr/bin/env python3
"""
Run a single autoresearch iteration with noise handling.

Supports multi-run verification to reduce metric noise.
"""
import argparse
import subprocess
import sys
import os
import statistics
from typing import Optional

check_git = os.path.join(os.path.dirname(__file__), 'check_git.py')
log_result = os.path.join(os.path.dirname(__file__), 'log_result.py')

# Minimum delta to consider as improvement (noise floor)
MIN_DELTA_THRESHOLD = 0.5  # 0.5% or absolute 0.5


def run_command(cmd: str, timeout: int = 300) -> tuple[int, str]:
    """Run a shell command and return (exit_code, output)."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return -1, "Command timed out"
    except Exception as e:
        return -1, str(e)


def extract_number(output: str) -> float | None:
    """Try to extract a number from command output."""
    import re
    
    patterns = [
        r'(\d+\.?\d*)%',
        r'(\d+\.?\d*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, output)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    
    return None


def run_verification_with_noise_handling(verify_cmd: str, runs: int = 3, 
                                         timeout: int = 300,
                                         baseline_metric: float = 0.0) -> tuple[float, list[float]]:
    """
    Run verification multiple times and return median value.
    
    Reduces noise from fluctuating metrics (benchmarks, coverage, etc.)
    
    Args:
        verify_cmd: Command to run for verification
        runs: Number of times to run (default 3)
        timeout: Timeout per run
        baseline_metric: Baseline to return on failure
        
    Returns:
        Tuple of (median_value, all_values)
    """
    if runs <= 1:
        # Single run mode
        exit_code, output = run_command(verify_cmd, timeout)
        if exit_code != 0:
            return baseline_metric, []
        value = extract_number(output)
        if value is None:
            return baseline_metric, []
        return value, [value]
    
    print(f"Running verification {runs} times for noise reduction...")
    values = []
    
    for i in range(runs):
        exit_code, output = run_command(verify_cmd, timeout)
        if exit_code != 0:
            print(f"  Run {i+1}: failed (exit {exit_code})")
            continue
        
        value = extract_number(output)
        if value is None:
            print(f"  Run {i+1}: could not extract metric")
            continue
            
        values.append(value)
        print(f"  Run {i+1}: {value}")
    
    if not values:
        print("Warning: All verification runs failed")
        return 0.0, []
    
    # Use median for robustness against outliers
    median_value = statistics.median(values)
    
    if len(values) > 1:
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        print(f"Median: {median_value}, StdDev: {std_dev:.2f}, Values: {values}")
    
    return median_value, values


def is_significant_improvement(current: float, baseline: float, 
                               direction: str, threshold: float = MIN_DELTA_THRESHOLD) -> bool:
    """
    Check if improvement is significant above noise floor.
    
    Args:
        current: Current metric value
        baseline: Baseline metric value
        direction: 'higher' or 'lower'
        threshold: Minimum delta to consider significant
        
    Returns:
        True if improvement exceeds threshold
    """
    delta = current - baseline
    
    if direction == 'lower':
        # For 'lower', we want negative delta (decrease)
        improved = delta < -threshold
    else:
        # For 'higher', we want positive delta (increase)
        improved = delta > threshold
    
    if improved:
        print(f"  Significant improvement: {baseline} -> {current} (delta: {delta:+.2f})")
    else:
        print(f"  Not significant: {baseline} -> {current} (delta: {delta:+.2f}, threshold: ±{threshold})")
    
    return improved


def run_iteration(iteration: int, verify_cmd: str, guard_cmd: str | None,
                  baseline_metric: float, direction: str, description: str,
                  verify_runs: int = 1, min_delta: float = MIN_DELTA_THRESHOLD) -> bool:
    """Run a single iteration and return result.
    
    Args:
        iteration: Iteration number
        verify_cmd: Verification command
        guard_cmd: Optional guard command
        baseline_metric: Baseline metric value
        direction: 'higher' or 'lower'
        description: Change description
        verify_runs: Number of verification runs (default 1, use 3+ for noisy metrics)
        min_delta: Minimum delta to consider as improvement
    """
    
    # Commit the change
    commit_msg = f"experiment: {description}"
    exit_code, output = run_command(f'python "{check_git}" --action commit --message "{commit_msg}"')
    
    if exit_code != 0:
        print(f"Error: Failed to commit: {output}", file=sys.stderr)
        return False
    
    # Extract commit hash
    commit_hash = output.strip().replace('committed:', '')
    
    # Run verification with noise handling
    print(f"Running verification: {verify_cmd}")
    current_metric, all_values = run_verification_with_noise_handling(
        verify_cmd, runs=verify_runs, baseline_metric=baseline_metric
    )
    
    if not all_values:  # pragma: no cover (edge case)
        print("Warning: Could not extract metric, using baseline")
        current_metric = baseline_metric
    
    # Determine if improved using significance check
    improved = is_significant_improvement(
        current_metric, baseline_metric, direction, min_delta
    )
    
    delta = current_metric - baseline_metric
    
    # Run guard if provided
    guard_passed = True
    if guard_cmd:
        print(f"Running guard: {guard_cmd}")
        guard_exit, guard_output = run_command(guard_cmd)
        if guard_exit != 0:
            guard_passed = False
            print(f"Guard failed: {guard_output}")
    
    # Decide outcome
    if improved and guard_passed:
        status = 'keep'
        delta_str = f"+{delta:.2f}" if delta > 0 else f"{delta:.2f}"
    else:
        status = 'discard'
        delta_str = f"+{delta:.2f}" if delta > 0 else f"{delta:.2f}"
        
        # Revert the change
        print("Reverting change...")
        run_command(f'python "{check_git}" --action revert')
    
    # Build verification details
    verify_details = f"runs={verify_runs}"
    if len(all_values) > 1:
        verify_details += f", median={current_metric}, values={all_values}"
    
    # Log result
    log_cmd = (
        f'python "{log_result}" '
        f'--iteration {iteration} '
        f'--commit {commit_hash} '
        f'--metric "{current_metric}" '
        f'--delta "{delta_str}" '
        f'--status {status} '
        f'--description "{description} [{verify_details}]"'
    )
    run_command(log_cmd)
    
    print(f"Iteration {iteration}: {status} (metric: {current_metric}, delta: {delta_str})")
    
    return status == 'keep'


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Run one autoresearch iteration with noise handling'
    )
    parser.add_argument('--iteration', type=int, required=True)
    parser.add_argument('--verify', type=str, required=True)
    parser.add_argument('--guard', type=str, default=None)
    parser.add_argument('--baseline', type=float, required=True)
    parser.add_argument('--direction', type=str, default='higher',
                       choices=['higher', 'lower'])
    parser.add_argument('--description', type=str, required=True)
    parser.add_argument('--verify-runs', type=int, default=1,
                       help='Number of verification runs (default 1, use 3 for noisy metrics)')
    parser.add_argument('--min-delta', type=float, default=MIN_DELTA_THRESHOLD,
                       help=f'Minimum delta to consider significant (default {MIN_DELTA_THRESHOLD})')
    
    args = parser.parse_args()
    
    success = run_iteration(
        args.iteration,
        args.verify,
        args.guard,
        args.baseline,
        args.direction,
        args.description,
        verify_runs=args.verify_runs,
        min_delta=args.min_delta
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
