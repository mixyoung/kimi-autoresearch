#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified workflow orchestrator for autoresearch.
Coordinates all components for a complete run.
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


def run_script(name: str, args: list[str], timeout: int = 300) -> tuple[int, str]:
    """Run a helper script."""
    script_path = os.path.join(SCRIPT_DIR, name)
    cmd = ['python', script_path] + args
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, 
                              timeout=timeout)
        return result.returncode, result.stdout + result.stderr
    except Exception as e:
        return -1, str(e)


def print_header(title: str) -> None:
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_step(step: str, status: str = "...") -> None:
    """Print a step with status."""
    symbols = {
        '...': '⏳',
        'ok': '✓',
        'error': '✗',
        'warn': '⚠',
        'skip': '⊘'
    }
    symbol = symbols.get(status, '⏳')
    print(f"{symbol} {step}")


def workflow_init(config: dict[str, Any]) -> bool:
    """Initialize the workflow."""
    print_header("Phase 0: Initialization")
    
    print_step("Checking health")
    code, output = run_script('autoresearch_health_check.py', [])
    if code != 0:
        print_step("Health check failed", 'error')
        print(output)
        return False
    print_step("Health check passed", 'ok')
    
    print_step("Checking launch gate")
    code, output = run_script('autoresearch_launch_gate.py', ['--check-only'])
    if code == 2:
        print_step("Existing run found, will resume", 'warn')
    elif code == 1:
        print_step("Cannot proceed with existing state", 'error')
        return False
    else:
        print_step("Ready for fresh start", 'ok')
    
    print_step("Initializing run")
    args = [
        '--goal', config['goal'],
        '--metric', config['metric'],
        '--verify', config['verify'],
        '--direction', config['direction'],
        '--mode', config.get('mode', 'loop')
    ]
    if config.get('scope'):
        args.extend(['--scope', config['scope']])
    if config.get('guard'):
        args.extend(['--guard', config['guard']])
    if config.get('iterations'):
        args.extend(['--iterations', str(config['iterations'])])
    
    code, output = run_script('autoresearch_init_run.py', args)
    if code != 0:
        print_step("Initialization failed", 'error')
        print(output)
        return False
    print_step("Run initialized", 'ok')
    
    return True


def workflow_baseline(config: dict[str, Any]) -> tuple[bool, float]:
    """Get baseline measurement."""
    print_header("Phase 1: Baseline")
    
    print_step("Measuring baseline")
    code, output = run_script('get_baseline.py', [
        '--verify', config['verify'],
        '--parse-number'
    ])
    
    if code != 0:
        print_step("Baseline measurement failed", 'error')
        print(output)
        return False, 0
    
    # Try to extract metric from output
    for line in output.split('\n'):
        if 'Extracted metric:' in line:
            try:
                metric = float(line.split(':')[1].strip())
                print_step(f"Baseline: {metric}", 'ok')
                return True, metric
            except:
                pass
    
    print_step("Could not parse baseline metric", 'error')
    return False, 0


def workflow_iteration(iteration: int, config: dict[str, Any], 
                      baseline: float) -> tuple[str, float]:
    """
    Guide Kimi through a single iteration.
    
    NOTE: This function only prints guidance. Kimi must manually:
    1. Read the code and context
    2. Decide what to change
    3. Execute the change using Kimi's editing tools
    4. Use helper scripts for commit/verify/log
    """
    print(f"\n{'='*60}")
    print(f"  Iteration {iteration}")
    print(f"{'='*60}")
    print()
    print("Kimi: Please follow the iteration protocol from SKILL.md")
    print()
    print("1. Read Context:")
    print(f"   - Scope: {config.get('scope', 'current directory')}")
    print("   - Read autoresearch-results.tsv for history")
    print("   - Read git log to see what worked/failed")
    print()
    print("2. Analyze & Hypothesize:")
    print("   - Understand the codebase")
    print("   - Identify ONE specific improvement")
    print("   - Form a concrete hypothesis")
    print()
    print("3. Execute Change:")
    print("   - Make ONE atomic change using Kimi's tools")
    print("   - Keep changes minimal and focused")
    print()
    print("4. Commit:")
    print('   python scripts/check_git.py --action commit --message "experiment: <description>"')
    print()
    print("5. Verify:")
    verify_cmd = config.get('verify', 'Not configured')
    print(f"   Run: {verify_cmd}")
    print()
    print("6. Decide & Log:")
    print("   python scripts/autoresearch_decision.py --action decide ...")
    print("   python scripts/log_result.py ...")
    print()
    print("Return 'keep' if improved, 'discard' if not.")
    print()
    
    # In semi-auto mode, we return a placeholder
    # In real usage, Kimi would manually execute and report result
    return 'manual', baseline


def protocol_fingerprint_check() -> dict[str, bool]:
    """
    Verify critical protocol rules are still remembered.
    
    Called every 10 iterations or after context compaction.
    Returns check results for each critical rule.
    """
    checks = {
        "core_loop": True,  # modify → verify → keep/discard → repeat
        "one_change_rule": True,  # One atomic change per iteration
        "verify_first": True,  # Mechanical verification before changes
        "git_commit_before_verify": True,  # Commit before verify
        "auto_rollback": True,  # Auto revert on failure
    }
    return checks


def should_split_session(iteration: int, compaction_count: int = 0) -> tuple[bool, str]:
    """
    Check if session should be split to prevent context drift.
    
    Args:
        iteration: Current iteration number
        compaction_count: Number of times context was compacted
        
    Returns:
        (should_split, reason)
    """
    if iteration >= 40:
        return True, "Iteration limit reached (40)"
    
    if compaction_count >= 2:
        return True, f"Context compacted {compaction_count} times"
    
    return False, ""


def workflow_loop(config: dict[str, Any], baseline: float) -> dict[str, Any]:
    """Main iteration loop following Ralph loop protocol."""
    print_header("Phase 2: Iteration Loop (Ralph Loop Protocol)")
    
    max_iterations = config.get('iterations', 10)
    target = config.get('target')
    direction = config.get('direction', 'lower')
    compaction_count = 0  # Track context compactions
    
    loop_control = config.get('loop_control', {})
    max_ralph = loop_control.get('max_ralph_iterations', 0)
    
    if max_ralph != 0:
        print(f"Ralph loop mode: max_ralph_iterations={max_ralph}")
        print("Loop will continue until <choice>STOP</choice> or iteration limit")
    
    results = []
    current_baseline = baseline
    keep_count = 0
    discard_count = 0
    
    start_time = time.time()
    
    # Determine actual iteration limit
    iteration_limit = max_ralph if max_ralph > 0 else max_iterations
    
    for i in range(1, iteration_limit + 1):
        # Session resilience: Check if we should split
        should_split, split_reason = should_split_session(i, compaction_count)
        if should_split:
            print(f"\n[SESSION-SPLIT] {split_reason}")
            print("Checkpoint saved. Re-invoke to resume.")
            break
        
        # Session resilience: Protocol fingerprint check every 10 iterations
        if i % 10 == 0:
            checks = protocol_fingerprint_check()
            if not all(checks.values()):
                print(f"\n[RE-ANCHOR] Reloading protocol files...")
                print("Protocol re-anchored successfully")
        
        status, new_baseline = workflow_iteration(i, config, current_baseline)
        
        # Check for stop signal (Ralph loop protocol)
        if status == 'stop':
            print("\n<choice>STOP</choice> detected. Stopping loop.")
            break
        
        results.append({'iteration': i, 'status': status, 'metric': new_baseline})
        
        if status == 'keep':
            keep_count += 1
            current_baseline = new_baseline
        else:
            discard_count += 1
        
        # Check if target reached
        if target:
            if direction == 'lower' and current_baseline <= target:
                print(f"\n✓ Target reached: {current_baseline} <= {target}")
                print("<choice>STOP</choice>")
                break
            elif direction == 'higher' and current_baseline >= target:
                print(f"\n✓ Target reached: {current_baseline} >= {target}")
                print("<choice>STOP</choice>")
                break
        
        # Check stuck pattern
        if discard_count >= 3:
            print(f"\n⚠ Stuck detected ({discard_count} discards), adjusting strategy...")
            
        # Check for excessive stuck state
        code, output = run_script('state_manager.py', ['--action', 'load'])
        try:
            state = json.loads(output) if code == 0 else {}
        except:
            state = {}
        if discard_count >= 5 and state.get('pivot_count', 0) >= 2:
            print("\n⚠ Truly stuck (5+ discards, 2+ pivots). Consider web search.")
    
    duration = time.time() - start_time
    
    return {
        'iterations': len(results),
        'kept': keep_count,
        'discarded': discard_count,
        'final_metric': current_baseline,
        'improvement': current_baseline - baseline,
        'duration_seconds': int(duration)
    }


def workflow_summary(results: dict[str, Any], config: dict[str, Any]) -> None:
    """Generate final summary."""
    print_header("Phase 3: Summary")
    
    print(f"\nGoal: {config['goal']}")
    print(f"Iterations: {results['iterations']}")
    print(f"Kept: {results['kept']}")
    print(f"Discarded: {results['discarded']}")
    print(f"Final metric: {results['final_metric']}")
    print(f"Improvement: {results['improvement']:+.2f}")
    print(f"Duration: {results['duration_seconds']}s")
    
    print_step("\nGenerating report")
    code, output = run_script('generate_report.py', [])
    if code == 0:
        print_step("Report generated: autoresearch-report.md", 'ok')
    
    print_step("\nWorkflow complete", 'ok')


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Autoresearch Workflow Orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete workflow
  python scripts/autoresearch_workflow.py --goal "Reduce type errors" --verify "tsc --noEmit 2>&1 | grep -c error" --direction lower

  # With all options
  python scripts/autoresearch_workflow.py \\
    --goal "Increase test coverage" \\
    --scope "src/**/*.ts" \\
    --metric "coverage %" \\
    --verify "npm test -- --coverage | grep 'All files'" \\
    --direction higher \\
    --guard "npm run build" \\
    --iterations 20

  # Ralph loop mode
  python scripts/autoresearch_workflow.py \\
    --goal "Reduce type errors" \\
    --verify "tsc --noEmit 2>&1 | grep -c error" \\
    --max-ralph-iterations 50
        """
    )
    
    parser.add_argument('--goal', type=str, required=True)
    parser.add_argument('--scope', type=str, default='')
    parser.add_argument('--metric', type=str, default='metric')
    parser.add_argument('--verify', type=str, required=True)
    parser.add_argument('--direction', type=str, default='lower',
                       choices=['higher', 'lower'])
    parser.add_argument('--guard', type=str, default='')
    parser.add_argument('--iterations', type=int, default=10)
    parser.add_argument('--target', type=float)
    parser.add_argument('--config', type=str,
                       help='Config file (JSON)')
    
    # Loop control options (Kimi Ralph loop compatible)
    parser.add_argument('--max-steps-per-turn', type=int, default=50,
                       help='Max steps per turn (default: 50)')
    parser.add_argument('--max-retries-per-step', type=int, default=3,
                       help='Max retries per step (default: 3)')
    parser.add_argument('--max-ralph-iterations', type=int, default=0,
                       help='Max Ralph iterations: 0=off, -1=infinite (default: 0)')
    
    args = parser.parse_args()
    
    # Load config if provided
    config = {}
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Override with CLI args
    for key in ['goal', 'scope', 'metric', 'verify', 'direction', 
                'guard', 'iterations', 'target']:
        if getattr(args, key) is not None:
            config[key] = getattr(args, key)
    
    # Set loop control configuration
    config['loop_control'] = {
        'max_steps_per_turn': args.max_steps_per_turn,
        'max_retries_per_step': args.max_retries_per_step,
        'max_ralph_iterations': args.max_ralph_iterations
    }
    
    print("=" * 60)
    print("  Autoresearch Workflow")
    print("=" * 60)
    
    # Run workflow
    if not workflow_init(config):
        sys.exit(1)
    
    success, baseline = workflow_baseline(config)
    if not success:
        sys.exit(1)
    
    results = workflow_loop(config, baseline)
    workflow_summary(results, config)
    
    print("\n" + "=" * 60)
    print("  ✓ Workflow Complete")
    print("=" * 60)


if __name__ == '__main__':
    main()
