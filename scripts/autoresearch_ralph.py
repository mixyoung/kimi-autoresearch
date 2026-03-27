#!/usr/bin/env python3
"""
Ralph Loop utilities for autoresearch.

Supports Kimi's official Ralph loop protocol with:
- <choice>STOP</choice> signal handling
- Loop control configuration
- Sub-agent management

Reference: https://moonshotai.github.io/kimi-cli/zh/reference/kimi-command.html
"""

import argparse
import json
import os
import sys
from typing import Any

STATE_FILE = "autoresearch-state.json"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_state() -> dict[str, Any]:
    """Load current state."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_state(state: dict[str, Any]) -> None:
    """Save state."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def set_loop_control(max_steps: int = None, max_retries: int = None, 
                     max_ralph: int = None) -> dict[str, Any]:
    """
    Set Ralph loop control parameters.
    
    Args:
        max_steps: Maximum steps per turn
        max_retries: Maximum retries per step
        max_ralph: Maximum Ralph iterations (0=off, -1=infinite)
    """
    state = load_state()
    
    if 'loop_control' not in state:
        state['loop_control'] = {
            'max_steps_per_turn': 50,
            'max_retries_per_step': 3,
            'max_ralph_iterations': 0
        }
    
    if max_steps is not None:
        state['loop_control']['max_steps_per_turn'] = max_steps
    if max_retries is not None:
        state['loop_control']['max_retries_per_step'] = max_retries
    if max_ralph is not None:
        state['loop_control']['max_ralph_iterations'] = max_ralph
    
    save_state(state)
    return state['loop_control']


def get_loop_control() -> dict[str, Any]:
    """Get current loop control configuration."""
    state = load_state()
    return state.get('loop_control', {
        'max_steps_per_turn': 50,
        'max_retries_per_step': 3,
        'max_ralph_iterations': 0
    })


def set_agent_config(agent: str = None, agent_file: str = None) -> dict[str, Any]:
    """
    Set agent configuration for sub-agent support.
    
    Args:
        agent: Built-in agent name (e.g., 'default', 'okabe')
        agent_file: Path to custom agent file
        
    Note: agent and agent_file are mutually exclusive.
    """
    if agent and agent_file:
        raise ValueError("Cannot specify both agent and agent_file")
    
    state = load_state()
    state['agent_config'] = {
        'agent': agent,
        'agent_file': agent_file
    }
    save_state(state)
    return state['agent_config']


def get_agent_config() -> dict[str, Any] | None:
    """Get current agent configuration."""
    state = load_state()
    return state.get('agent_config')


def emit_stop_signal(reason: str = "") -> None:
    """
    Emit Ralph loop stop signal.
    
    Outputs the standard <choice>STOP</choice> signal that Ralph loops recognize.
    """
    if reason:
        print(f"[STOP SIGNAL] {reason}")
    print("<choice>STOP</choice>")


def check_stop_conditions(current_metric: float = None) -> tuple[bool, str]:
    """
    Check if Ralph loop should stop.
    
    Returns:
        (should_stop, reason)
    """
    state = load_state()
    config = state.get('config', {})
    
    target = config.get('target')
    direction = config.get('direction', 'lower')
    max_iterations = config.get('iterations', 0)
    current_iteration = state.get('iteration', 0)
    
    loop_control = state.get('loop_control', {})
    max_ralph = loop_control.get('max_ralph_iterations', 0)
    
    # Check Ralph loop iteration limit (if not infinite)
    if max_ralph > 0 and current_iteration >= max_ralph:
        return True, f"Ralph iteration limit reached: {current_iteration}/{max_ralph}"
    
    # Check target reached
    if target is not None and current_metric is not None:
        if direction == 'lower' and current_metric <= target:
            return True, f"Target reached: {current_metric} <= {target}"
        if direction == 'higher' and current_metric >= target:
            return True, f"Target reached: {current_metric} >= {target}"
    
    # Check max iterations
    if max_iterations > 0 and current_iteration >= max_iterations:
        return True, f"Max iterations reached: {current_iteration}"
    
    # Check stuck pattern
    discards = state.get('consecutive_discards', 0)
    pivots = state.get('pivot_count', 0)
    if discards >= 5 and pivots >= 2:
        return True, f"Truly stuck: {discards} discards, {pivots} pivots"
    
    return False, ""


def print_ralph_status() -> None:
    """Print current Ralph loop status."""
    state = load_state()
    loop_control = get_loop_control()
    agent_config = get_agent_config()
    
    print("=" * 60)
    print("  Ralph Loop Status")
    print("=" * 60)
    print()
    print("Loop Control:")
    print(f"  Max steps per turn: {loop_control['max_steps_per_turn']}")
    print(f"  Max retries per step: {loop_control['max_retries_per_step']}")
    print(f"  Max Ralph iterations: {loop_control['max_ralph_iterations']}")
    
    if agent_config:
        print()
        print("Agent Configuration:")
        if agent_config.get('agent'):
            print(f"  Built-in agent: {agent_config['agent']}")
        if agent_config.get('agent_file'):
            print(f"  Custom agent file: {agent_config['agent_file']}")
    
    print()
    print(f"Current iteration: {state.get('iteration', 0)}")
    print(f"Baseline: {state.get('baseline', 'N/A')}")
    print(f"Best: {state.get('best', 'N/A')}")
    
    # Check if we should stop
    should_stop, reason = check_stop_conditions(state.get('best'))
    if should_stop:
        print()
        print(f"[STOP CONDITION] {reason}")
        print("<choice>STOP</choice>")


def main():
    parser = argparse.ArgumentParser(
        description='Ralph Loop utilities for autoresearch',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Set loop control parameters
  %(prog)s set-loop --max-steps 30 --max-retries 5 --max-ralph 100
  
  # Set built-in agent
  %(prog)s set-agent --agent okabe
  
  # Set custom agent file
  %(prog)s set-agent --agent-file ./my-agent.toml
  
  # Check stop conditions
  %(prog)s check-stop --current-metric 42
  
  # Emit stop signal
  %(prog)s stop --reason "Target reached"
  
  # Show status
  %(prog)s status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # set-loop command
    set_loop_parser = subparsers.add_parser('set-loop', help='Set loop control parameters')
    set_loop_parser.add_argument('--max-steps', type=int, help='Max steps per turn')
    set_loop_parser.add_argument('--max-retries', type=int, help='Max retries per step')
    set_loop_parser.add_argument('--max-ralph', type=int, help='Max Ralph iterations')
    
    # set-agent command
    set_agent_parser = subparsers.add_parser('set-agent', help='Set agent configuration')
    agent_group = set_agent_parser.add_mutually_exclusive_group()
    agent_group.add_argument('--agent', type=str, choices=['default', 'okabe'],
                            help='Built-in agent name')
    agent_group.add_argument('--agent-file', type=str, help='Path to custom agent file')
    
    # check-stop command
    check_stop_parser = subparsers.add_parser('check-stop', help='Check if should stop')
    check_stop_parser.add_argument('--current-metric', type=float, help='Current metric value')
    
    # stop command
    stop_parser = subparsers.add_parser('stop', help='Emit stop signal')
    stop_parser.add_argument('--reason', type=str, help='Reason for stopping')
    
    # status command
    subparsers.add_parser('status', help='Show Ralph loop status')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'set-loop':
        config = set_loop_control(args.max_steps, args.max_retries, args.max_ralph)
        print("Loop control configuration:")
        print(json.dumps(config, indent=2))
    
    elif args.command == 'set-agent':
        try:
            config = set_agent_config(args.agent, args.agent_file)
            print("Agent configuration:")
            print(json.dumps(config, indent=2))
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    elif args.command == 'check-stop':
        should_stop, reason = check_stop_conditions(args.current_metric)
        result = {'should_stop': should_stop, 'reason': reason}
        print(json.dumps(result, indent=2))
        if should_stop:
            print("\n<choice>STOP</choice>")
    
    elif args.command == 'stop':
        emit_stop_signal(args.reason)
    
    elif args.command == 'status':
        print_ralph_status()


if __name__ == '__main__':
    main()
