#!/usr/bin/env python3
"""
Run a single autoresearch iteration.
"""
import argparse
import subprocess
import sys
import os

check_git = os.path.join(os.path.dirname(__file__), 'check_git.py')
log_result = os.path.join(os.path.dirname(__file__), 'log_result.py')


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


def run_iteration(iteration: int, verify_cmd: str, guard_cmd: str | None,
                  baseline_metric: float, direction: str, description: str) -> bool:
    """Run a single iteration and return result."""
    
    # Commit the change
    commit_msg = f"experiment: {description}"
    exit_code, output = run_command(f'python "{check_git}" --action commit --message "{commit_msg}"')
    
    if exit_code != 0:
        print(f"Error: Failed to commit: {output}", file=sys.stderr)
        return False
    
    # Extract commit hash
    commit_hash = output.strip().replace('committed:', '')
    
    # Run verification
    print(f"Running verification: {verify_cmd}")
    verify_exit, verify_output = run_command(verify_cmd)
    
    # Extract metric
    current_metric = extract_number(verify_output)
    if current_metric is None:
        print(f"Warning: Could not extract metric from: {verify_output}")
        current_metric = baseline_metric
    
    # Determine if improved
    delta = current_metric - baseline_metric
    
    if direction == 'lower':
        improved = delta < 0
    else:
        improved = delta > 0
    
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
    
    # Log result
    log_cmd = (
        f'python "{log_result}" '
        f'--iteration {iteration} '
        f'--commit {commit_hash} '
        f'--metric "{current_metric}" '
        f'--delta "{delta_str}" '
        f'--status {status} '
        f'--description "{description}"'
    )
    run_command(log_cmd)
    
    print(f"Iteration {iteration}: {status} (metric: {current_metric}, delta: {delta_str})")
    
    return status == 'keep'


def main() -> None:
    parser = argparse.ArgumentParser(description='Run one autoresearch iteration')
    parser.add_argument('--iteration', type=int, required=True)
    parser.add_argument('--verify', type=str, required=True)
    parser.add_argument('--guard', type=str, default=None)
    parser.add_argument('--baseline', type=float, required=True)
    parser.add_argument('--direction', type=str, default='higher',
                       choices=['higher', 'lower'])
    parser.add_argument('--description', type=str, required=True)
    
    args = parser.parse_args()
    
    success = run_iteration(
        args.iteration,
        args.verify,
        args.guard,
        args.baseline,
        args.direction,
        args.description
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
