#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Autoresearch Workflow - Ralph Loop Edition

This script prepares the environment and generates Ralph Loop configuration.
The actual iteration loop is handled by Kimi's Ralph Loop mechanism.

Usage:
    # Generate Ralph Loop prompt for Kimi
    python scripts/autoresearch_workflow.py \
        --goal "Reduce type errors" \
        --verify "tsc --noEmit 2>&1 | grep -c error"
    
    # Then in Kimi, the prompt will guide through Ralph Loop iterations
"""
import argparse
import json
import os
import subprocess
import sys
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


def workflow_init(config: dict[str, Any]) -> bool:
    """Initialize the workflow."""
    print_header("Phase 0: Initialization")
    
    print("Checking health...")
    code, output = run_script('autoresearch_health_check.py', [])
    if code != 0:
        print(f"✗ Health check failed:\n{output}")
        return False
    print("✓ Health check passed")
    
    print("\nInitializing run state...")
    args = [
        '--goal', config['goal'],
        '--metric', config['metric'],
        '--verify', config['verify'],
        '--direction', config['direction'],
        '--mode', config.get('mode', 'loop')
    ]
    if config.get('scope'):  # pragma: no cover (optional path)
        args.extend(['--scope', config['scope']])
    if config.get('guard'):  # pragma: no cover (optional path)
        args.extend(['--guard', config['guard']])
    if config.get('iterations'):  # pragma: no cover (optional path)
        args.extend(['--iterations', str(config['iterations'])])
    
    code, output = run_script('autoresearch_init_run.py', args)
    if code != 0:
        print(f"✗ Initialization failed:\n{output}")
        return False
    print("✓ Run initialized")
    
    # Set loop control if provided
    loop_control = config.get('loop_control', {})
    if loop_control:
        print("\nSetting Ralph Loop control parameters...")
        lc_args = []
        if loop_control.get('max_steps_per_turn'):
            lc_args.extend(['--max-steps', str(loop_control['max_steps_per_turn'])])
        if loop_control.get('max_retries_per_step'):
            lc_args.extend(['--max-retries', str(loop_control['max_retries_per_step'])])
        if loop_control.get('max_ralph_iterations'):
            lc_args.extend(['--max-ralph', str(loop_control['max_ralph_iterations'])])
        if lc_args:
            code, _ = run_script('autoresearch_ralph.py', ['set-loop'] + lc_args)
            if code == 0:
                print("✓ Loop control configured")
    
    # Set agent config if provided
    agent_config = config.get('agent_config', {})
    if agent_config:
        print("\nSetting agent configuration...")
        if agent_config.get('agent'):  # pragma: no cover (optional path)
            code, _ = run_script('autoresearch_ralph.py', 
                               ['set-agent', '--agent', agent_config['agent']])
            if code == 0:
                print(f"✓ Agent set to: {agent_config['agent']}")
        elif agent_config.get('agent_file'):  # pragma: no cover (optional path)
            code, _ = run_script('autoresearch_ralph.py',
                               ['set-agent', '--agent-file', agent_config['agent_file']])
            if code == 0:
                print(f"✓ Agent file set to: {agent_config['agent_file']}")
    
    return True


def workflow_baseline(config: dict[str, Any]) -> tuple[bool, float]:
    """Get baseline measurement."""
    print_header("Phase 1: Baseline Measurement")
    
    print(f"Running verify command: {config['verify']}")
    code, output = run_script('get_baseline.py', [
        '--verify', config['verify'],
        '--parse-number'
    ])
    
    if code != 0:
        print(f"✗ Baseline measurement failed:\n{output}")
        return False, 0.0
    
    # Try to extract metric from output
    baseline = 0.0
    for line in output.split('\n'):
        if 'Extracted metric:' in line:
            try:
                baseline = float(line.split(':')[1].strip())
                break
            except:
                pass
    
    print(f"✓ Baseline metric: {baseline}")
    
    # Save baseline to state
    run_script('state_manager.py', [
        '--action', 'save',
        '--key', 'baseline',
        '--value', str(baseline)
    ])
    
    return True, baseline


def generate_ralph_prompt(config: dict[str, Any], baseline: float) -> str:
    """
    Generate Ralph Loop prompt for Kimi.
    
    This prompt instructs Kimi to use Ralph Loop mechanism for iteration.
    Kimi will handle the loop control, we just provide the protocol for each iteration.
    """
    loop_control = config.get('loop_control', {})
    max_steps = loop_control.get('max_steps_per_turn', 50)
    max_retries = loop_control.get('max_retries_per_step', 3)
    max_ralph = loop_control.get('max_ralph_iterations', 0)
    
    agent_config = config.get('agent_config', {})
    agent_info = ""
    if agent_config.get('agent'):
        agent_info = f"\nAgent: {agent_config['agent']}"
    elif agent_config.get('agent_file'):
        agent_info = f"\nAgent File: {agent_config['agent_file']}"
    
    iterations_info = ""
    if max_ralph > 0:
        iterations_info = f"Max Ralph Iterations: {max_ralph}"
    elif config.get('iterations'):
        iterations_info = f"Iterations: {config['iterations']}"
    
    return f"""# Autoresearch Ralph Loop Session

## Goal
{config['goal']}

## Scope
{config.get('scope', 'Current directory')}

## Configuration
- Baseline Metric: {baseline}
- Direction: {config.get('direction', 'lower')} (higher/lower is better)
- Verify Command: `{config['verify']}`
- Guard Command: `{config.get('guard', 'None')}`
- Max Steps Per Turn: {max_steps}
- Max Retries Per Step: {max_retries}
{iterations_info}{agent_info}

## Ralph Loop Protocol

You are now in Ralph Loop mode. The same prompt will be repeated, allowing you to iterate continuously until you output `<choice>STOP</choice>` or reach the iteration limit.

### Single Iteration Protocol

For each iteration, follow these steps:

1. **READ CONTEXT**
   ```bash
   python scripts/state_manager.py --action load
   cat autoresearch-results.tsv
   git log --oneline -5
   ```
   Understand current state and history.

2. **ANALYZE & HYPOTHESIZE**
   - Review what worked/failed in previous iterations
   - Form ONE concrete hypothesis about what to change
   - Choose the most promising improvement

3. **EXECUTE CHANGE**
   - Make ONE atomic change using Kimi's editing tools
   - Keep changes minimal and focused
   - Do NOT batch multiple changes

4. **GIT COMMIT**
   ```bash
   python scripts/check_git.py --action commit --message "experiment: <brief description>"
   ```
   If commit fails, retry up to {max_retries} times.

5. **VERIFY**
   ```bash
   {config['verify']}
   ```
   Extract the metric from output. Limit to {max_steps} steps.

6. **GUARD CHECK** (if configured)
   ```bash
   {config.get('guard', 'echo "No guard configured"')}
   ```
   Must pass (exit 0) for change to be kept.

7. **DECIDE**
   ```bash
   python scripts/autoresearch_decision.py --action decide \\
       --current <new_metric> --baseline <baseline> \\
       --direction {config.get('direction', 'lower')} --guard-passed <true|false>
   ```
   - **KEEP**: Metric improved + guard passed → Update baseline for next iteration
   - **DISCARD**: Metric not improved → `python scripts/check_git.py --action revert`
   - **REWORK**: Metric improved but guard failed → Fix and retry (max 2x)

8. **LOG RESULT**
   ```bash
   python scripts/log_result.py \\
       --iteration <n> --commit <hash> --metric <value> \\
       --status <keep|discard|rework> --description "<what was tried>"
   ```

9. **CHECK STUCK PATTERN**
   ```bash
   python scripts/autoresearch_ralph.py check-stop --current-metric <metric>
   ```
   
   If output contains `<choice>STOP</condition>`, stop immediately.
   
   Otherwise, check:
   - 3+ consecutive discards → REFINE strategy
   - 5+ consecutive discards → PIVOT approach  
   - 5+ discards + 2+ pivots → Consider web search

10. **DECIDE: CONTINUE OR STOP**
    - If target reached: Output `<choice>STOP</choice>`
    - If truly stuck: Output `<choice>STOP</choice>`
    - Otherwise: Continue to next iteration

## Stop Conditions

Output `<choice>STOP</choice>` when any of these occur:
1. Target metric reached (if configured)
2. Max iterations reached
3. Truly stuck (5+ discards, 2+ pivots, no improvement)
4. Unrecoverable error after {max_retries} retries

## Important Rules

- ONE change per iteration
- Always commit BEFORE verify
- Revert failed changes immediately
- Never batch multiple changes
- Keep changes minimal and reversible
- Log every action
- Output `<choice>STOP</choice>` to stop gracefully

## Current State

Baseline: {baseline}
Current Best: {baseline}
Consecutive Discards: 0
Pivot Count: 0

## Start Now

Begin Iteration 1. Follow the Single Iteration Protocol.
This is a Ralph Loop - the prompt will repeat until you output `<choice>STOP</choice>`.
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Autoresearch Workflow - Ralph Loop Edition',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate Ralph Loop prompt
  python scripts/autoresearch_workflow.py \\
    --goal "Reduce type errors" \\
    --verify "tsc --noEmit 2>&1 | grep -c error" \\
    --direction lower

  # With Ralph Loop parameters
  python scripts/autoresearch_workflow.py \\
    --goal "Increase coverage" \\
    --verify "npm test -- --coverage | grep 'All files'" \\
    --direction higher \\
    --max-ralph-iterations 50 \\
    --max-steps-per-turn 30 \\
    --agent okabe

After running this script, copy the generated prompt into Kimi to start the Ralph Loop.
        """
    )
    
    parser.add_argument('--goal', type=str, required=True, help='Goal description')
    parser.add_argument('--scope', type=str, default='', help='Files to modify')
    parser.add_argument('--metric', type=str, default='metric', help='Metric name')
    parser.add_argument('--verify', type=str, required=True, help='Verify command')
    parser.add_argument('--direction', type=str, default='lower',
                       choices=['higher', 'lower'], help='Improvement direction')
    parser.add_argument('--guard', type=str, default='', help='Guard command')
    parser.add_argument('--iterations', type=int, default=10, help='Max iterations')
    parser.add_argument('--target', type=float, help='Target metric value')
    parser.add_argument('--config', type=str, help='Config file (JSON)')
    
    # Ralph Loop control options
    parser.add_argument('--max-steps-per-turn', type=int, default=50,
                       help='Max steps per turn (default: 50)')
    parser.add_argument('--max-retries-per-step', type=int, default=3,
                       help='Max retries per step (default: 3)')
    parser.add_argument('--max-ralph-iterations', type=int, default=0,
                       help='Max Ralph iterations: 0=off, -1=infinite (default: 0)')
    
    # Agent configuration
    agent_group = parser.add_mutually_exclusive_group()
    agent_group.add_argument('--agent', type=str, choices=['default', 'okabe'],
                            help='Built-in agent profile')
    agent_group.add_argument('--agent-file', type=str,
                            help='Custom agent file path')
    
    args = parser.parse_args()
    
    # Load config if provided
    config = {}
    if args.config:  # pragma: no cover (optional path)
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
    
    # Set agent configuration
    if args.agent:
        config['agent_config'] = {'agent': args.agent, 'agent_file': None}
    elif args.agent_file:  # pragma: no cover (optional path)
        config['agent_config'] = {'agent': None, 'agent_file': args.agent_file}
    else:
        config['agent_config'] = {}
    
    # Run initialization
    if not workflow_init(config):
        sys.exit(1)
    
    # Get baseline
    success, baseline = workflow_baseline(config)
    if not success:
        sys.exit(1)
    
    # Generate Ralph Loop prompt
    print_header("Phase 2: Ralph Loop Configuration")
    print("\n✓ Environment prepared")
    print(f"✓ Baseline measured: {baseline}")
    print("\n" + "=" * 60)
    print("  GENERATED RALPH LOOP PROMPT")
    print("=" * 60)
    print("\nCopy the following prompt into Kimi to start the Ralph Loop:\n")
    
    prompt = generate_ralph_prompt(config, baseline)
    print(prompt)
    
    print("\n" + "=" * 60)
    print("  END OF PROMPT")
    print("=" * 60)
    print("\nInstructions:")
    print("1. Copy the prompt above")
    print("2. Paste it into Kimi")
    print("3. Kimi will execute the Ralph Loop")
    print("4. The loop continues until <choice>STOP</choice> or max iterations")
    print("\nTo check status anytime:")
    print("  python scripts/autoresearch_ralph.py status")
    print("\nTo generate report after completion:")
    print("  python scripts/generate_report.py")


if __name__ == '__main__':  # pragma: no cover
    main()
