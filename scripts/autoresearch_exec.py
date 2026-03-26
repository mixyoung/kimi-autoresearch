#!/usr/bin/env python3
"""
Exec mode for CI/CD - Non-interactive autoresearch execution.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from typing import Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_FILE = "autoresearch-results.tsv"
STATE_FILE = "autoresearch-state.json"


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'


def log(msg: str, level: str = 'info'):
    """Log with timestamp and level."""
    timestamp = datetime.now().isoformat()
    
    if level == 'error':
        color = Colors.RED
    elif level == 'warn':
        color = Colors.YELLOW
    elif level == 'success':
        color = Colors.GREEN
    else:
        color = ''
    
    # Always print to stderr for logs
    print(f"[{timestamp}] {color}{level.upper()}{Colors.END}: {msg}", 
          file=sys.stderr)


def run_command(cmd: str, timeout: int = 300) -> tuple[int, str]:
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
    except subprocess.TimeoutExpired:
        return -1, f"Command timed out after {timeout}s"
    except Exception as e:
        return -1, str(e)


def extract_number(output: str) -> float | None:
    """Extract number from output."""
    import re
    patterns = [r'(\d+\.?\d*)%', r'(\d+\.?\d*)']
    for pattern in patterns:
        match = re.search(pattern, output)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    return None


def init_run(config: dict[str, Any]) -> bool:
    """Initialize the run."""
    log("Initializing autoresearch run")
    
    cmd = [
        'python', os.path.join(SCRIPT_DIR, 'autoresearch_init_run.py'),
        '--goal', config['goal'],
        '--metric', config['metric'],
        '--verify', config['verify'],
        '--direction', config['direction'],
        '--mode', config.get('mode', 'loop')
    ]
    
    if config.get('scope'):
        cmd.extend(['--scope', config['scope']])
    if config.get('guard'):
        cmd.extend(['--guard', config['guard']])
    if config.get('iterations'):
        cmd.extend(['--iterations', str(config['iterations'])])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            log(f"Init failed: {result.stderr}", 'error')
            return False
        return True
    except Exception as e:
        log(f"Init error: {e}", 'error')
        return False


def get_baseline(verify_cmd: str) -> tuple[bool, float]:
    """Get baseline metric."""
    exit_code, output = run_command(verify_cmd)
    
    if exit_code != 0:
        log(f"Baseline verify failed: {output}", 'error')
        return False, 0
    
    metric = extract_number(output)
    if metric is None:
        log(f"Could not extract metric from: {output}", 'error')
        return False, 0
    
    return True, metric


def run_iteration(iteration: int, config: dict[str, Any], baseline: float) -> dict[str, Any]:
    """Run a single iteration."""
    import random
    
    # This is a simplified version - in practice, this would be more sophisticated
    log(f"Running iteration {iteration}")
    
    # Run verify
    exit_code, output = run_command(config['verify'])
    current_metric = extract_number(output)
    
    if current_metric is None:
        return {
            'status': 'crash',
            'metric': baseline,
            'reason': 'Could not extract metric'
        }
    
    # Determine if improved
    direction = config.get('direction', 'lower')
    if direction == 'lower':
        improved = current_metric < baseline
    else:
        improved = current_metric > baseline
    
    # Run guard if provided
    guard_passed = True
    if config.get('guard'):
        guard_exit, _ = run_command(config['guard'])
        guard_passed = guard_exit == 0
    
    if improved and guard_passed:
        return {
            'status': 'keep',
            'metric': current_metric,
            'delta': current_metric - baseline
        }
    else:
        return {
            'status': 'discard',
            'metric': current_metric,
            'delta': current_metric - baseline,
            'reason': 'Did not improve' if not improved else 'Guard failed'
        }


def exec_loop(config: dict[str, Any]) -> dict[str, Any]:
    """Main execution loop."""
    log("Starting autoresearch exec", 'success')
    
    # Initialize
    if not init_run(config):
        return {'success': False, 'exit_code': 3, 'error': 'Init failed'}
    
    # Health check
    log("Running health check")
    exit_code, _ = run_command(f'python {SCRIPT_DIR}/autoresearch_health_check.py')
    if exit_code != 0:
        log("Health check failed", 'error')
        return {'success': False, 'exit_code': 3, 'error': 'Health check failed'}
    
    # Get baseline
    log("Getting baseline")
    success, baseline = get_baseline(config['verify'])
    if not success:
        return {'success': False, 'exit_code': 3, 'error': 'Baseline failed'}
    
    log(f"Baseline: {baseline}", 'success')
    
    # Run iterations
    max_iterations = config.get('iterations', 10)
    results = []
    best_metric = baseline
    keep_count = 0
    discard_count = 0
    
    start_time = time.time()
    
    for i in range(1, max_iterations + 1):
        log(f"Iteration {i}/{max_iterations}")
        
        # Check timeout
        elapsed = time.time() - start_time
        if config.get('timeout') and elapsed > config['timeout']:
            log(f"Timeout reached after {elapsed:.0f}s", 'warn')
            break
        
        # Run iteration (simplified - in practice, this would make actual changes)
        result = run_iteration(i, config, baseline)
        results.append(result)
        
        if result['status'] == 'keep':
            keep_count += 1
            best_metric = result['metric']
            log(f"  Kept: metric = {result['metric']}", 'success')
        else:
            discard_count += 1
            log(f"  Discarded: metric = {result['metric']}")
        
        # Check if target reached
        if config.get('target'):
            if config['direction'] == 'lower' and best_metric <= config['target']:
                log(f"Target reached: {best_metric} <= {config['target']}", 'success')
                break
            elif config['direction'] == 'higher' and best_metric >= config['target']:
                log(f"Target reached: {best_metric} >= {config['target']}", 'success')
                break
    
    # Calculate summary
    total_iterations = len(results)
    improvement = ((best_metric - baseline) / baseline * 100) if baseline != 0 else 0
    
    summary = {
        'success': True,
        'exit_code': 0 if improvement > 0 else 1,
        'summary': {
            'baseline': baseline,
            'best': best_metric,
            'improvement_pct': round(improvement, 2),
            'iterations': total_iterations,
            'kept': keep_count,
            'discarded': discard_count,
            'duration_seconds': int(time.time() - start_time)
        },
        'config': {
            'goal': config['goal'],
            'metric': config['metric'],
            'direction': config['direction']
        }
    }
    
    return summary


def exec_check(config: dict[str, Any]) -> dict[str, Any]:
    """Check mode - verify metric meets threshold."""
    log("Running check mode")
    
    success, metric = get_baseline(config['verify'])
    if not success:
        return {'success': False, 'exit_code': 3}
    
    threshold = config.get('threshold', 0)
    direction = config.get('direction', 'higher')
    
    if direction == 'higher':
        passed = metric >= threshold
    else:
        passed = metric <= threshold
    
    result = {
        'success': passed,
        'exit_code': 0 if passed else 1,
        'metric': metric,
        'threshold': threshold,
        'passed': passed
    }
    
    if passed:
        log(f"Check passed: {metric} meets threshold {threshold}", 'success')
    else:
        log(f"Check failed: {metric} does not meet threshold {threshold}", 'error')
    
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Autoresearch Exec - CI/CD Mode',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Optimize mode
  %(prog)s --mode optimize \\
    --goal "Reduce bundle size" \\
    --verify "du -k dist/main.js | cut -f1" \\
    --direction lower \\
    --iterations 20

  # Check mode
  %(prog)s --mode check \\
    --verify "npm test -- --coverage | grep 'All files'" \\
    --threshold 80

  # With config file
  %(prog)s --config autoresearch-config.json
        """
    )
    
    parser.add_argument('--mode', type=str, required=True,
                       choices=['optimize', 'check'],
                       help='Execution mode')
    parser.add_argument('--config', type=str,
                       help='Config file (JSON)')
    parser.add_argument('--goal', type=str)
    parser.add_argument('--metric', type=str)
    parser.add_argument('--verify', type=str)
    parser.add_argument('--direction', type=str, choices=['higher', 'lower'])
    parser.add_argument('--guard', type=str)
    parser.add_argument('--scope', type=str)
    parser.add_argument('--iterations', type=int, default=10)
    parser.add_argument('--timeout', type=int,
                       help='Timeout in seconds')
    parser.add_argument('--target', type=float,
                       help='Target metric value')
    parser.add_argument('--threshold', type=float,
                       help='Threshold for check mode')
    parser.add_argument('--output-json', type=str,
                       help='Output file for JSON results')
    
    args = parser.parse_args()
    
    # Load config
    config = {}
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Override with CLI args
    for key in ['goal', 'metric', 'verify', 'direction', 'guard', 
                'scope', 'iterations', 'timeout', 'target', 'threshold']:
        if getattr(args, key) is not None:
            config[key] = getattr(args, key)
    
    # Validate required fields
    if args.mode == 'optimize':
        required = ['goal', 'metric', 'verify', 'direction']
        missing = [f for f in required if not config.get(f)]
        if missing:
            log(f"Missing required fields: {missing}", 'error')
            sys.exit(3)
    elif args.mode == 'check':
        if not config.get('verify'):
            log("Missing required: verify", 'error')
            sys.exit(3)
    
    # Run
    if args.mode == 'optimize':
        result = exec_loop(config)
    else:
        result = exec_check(config)
    
    # Output JSON
    if args.output_json:
        with open(args.output_json, 'w') as f:
            json.dump(result, f, indent=2)
    
    # Also print to stdout
    print(json.dumps(result, indent=2))
    
    sys.exit(result.get('exit_code', 1))


if __name__ == '__main__':
    main()
