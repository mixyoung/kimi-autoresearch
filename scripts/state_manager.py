#!/usr/bin/env python3
"""
State management for autoresearch sessions.
"""
import argparse
import json
import os
from datetime import datetime
from typing import Any

STATE_FILE = "autoresearch-state.json"
LESSONS_FILE = "autoresearch-lessons.md"


def load_state() -> dict[str, Any]:
    """Load current state from file."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {
        'iteration': 0,
        'baseline': None,
        'best': None,
        'consecutive_discards': 0,
        'pivot_count': 0,
        'strategy': 'initial',
        'start_time': datetime.now().isoformat(),
        'loop_control': {
            'max_steps_per_turn': 50,
            'max_retries_per_step': 3,
            'max_ralph_iterations': 0
        },
        'agent_config': None
    }


def save_state(state: dict[str, Any]) -> None:
    """Save state to file."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def log_lesson(lesson: str, lesson_type: str = 'positive') -> None:
    """Append a lesson to the lessons file."""
    timestamp = datetime.now().isoformat()
    entry = f"\n## {timestamp} ({lesson_type})\n\n{lesson}\n"
    
    with open(LESSONS_FILE, 'a') as f:
        f.write(entry)


def update_loop_control(state: dict[str, Any], max_steps: int = None,
                        max_retries: int = None, max_ralph: int = None) -> dict[str, Any]:
    """Update loop control configuration."""
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
    
    return state


def set_agent_config(state: dict[str, Any], agent_name: str = None,
                     agent_file: str = None) -> dict[str, Any]:
    """Set agent configuration for sub-agent support."""
    if agent_name and agent_file:
        raise ValueError("Cannot specify both agent_name and agent_file")
    
    state['agent_config'] = {
        'agent': agent_name,
        'agent_file': agent_file
    }
    return state


def check_should_stop(state: dict[str, Any], current_metric: float = None) -> tuple[bool, str]:
    """
    Check if the loop should stop based on various conditions.
    
    Returns:
        (should_stop, reason)
    """
    config = state.get('config', {})
    target = config.get('target')
    direction = config.get('direction', 'lower')
    max_iterations = config.get('iterations', 0)
    current_iteration = state.get('iteration', 0)
    
    # Check target reached
    if target is not None and current_metric is not None:
        if direction == 'lower' and current_metric <= target:
            return True, f"Target reached: {current_metric} <= {target}"
        if direction == 'higher' and current_metric >= target:
            return True, f"Target reached: {current_metric} >= {target}"
    
    # Check max iterations
    if max_iterations > 0 and current_iteration >= max_iterations:
        return True, f"Max iterations reached: {current_iteration}"
    
    return False, ""


def main():
    parser = argparse.ArgumentParser(description='Manage autoresearch state')
    parser.add_argument('--action', type=str, required=True,
                       choices=['load', 'save', 'update', 'reset', 'log-lesson', 
                                'set-loop-control', 'set-agent-config', 'check-stop'])
    parser.add_argument('--key', type=str, help='State key to update')
    parser.add_argument('--value', type=str, help='Value to set')
    parser.add_argument('--lesson', type=str, help='Lesson text')
    parser.add_argument('--lesson-type', type=str, default='positive',
                       choices=['positive', 'strategic', 'negative'])
    parser.add_argument('--max-steps', type=int, help='Max steps per turn')
    parser.add_argument('--max-retries', type=int, help='Max retries per step')
    parser.add_argument('--max-ralph', type=int, help='Max Ralph iterations (0=off, -1=infinite)')
    parser.add_argument('--agent-name', type=str, help='Built-in agent name')
    parser.add_argument('--agent-file', type=str, help='Custom agent file path')
    parser.add_argument('--current-metric', type=float, help='Current metric value for check-stop')
    
    args = parser.parse_args()
    
    if args.action == 'load':
        state = load_state()
        print(json.dumps(state, indent=2))
    
    elif args.action == 'save':
        if args.key and args.value:
            state = load_state()
            # Try to parse as number
            try:
                args.value = float(args.value)
            except ValueError:
                pass
            state[args.key] = args.value
            save_state(state)
            print(f"Saved: {args.key} = {args.value}")
    
    elif args.action == 'update':
        state = load_state()
        if args.key and args.value:
            try:
                args.value = float(args.value)
            except ValueError:
                pass
            state[args.key] = args.value
        save_state(state)
        print(json.dumps(state, indent=2))
    
    elif args.action == 'reset':
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
        print("State reset")
    
    elif args.action == 'log-lesson':
        if args.lesson:
            log_lesson(args.lesson, args.lesson_type)
            print("Lesson logged")
    
    elif args.action == 'set-loop-control':
        state = load_state()
        state = update_loop_control(state, args.max_steps, args.max_retries, args.max_ralph)
        save_state(state)
        print(json.dumps(state['loop_control'], indent=2))
    
    elif args.action == 'set-agent-config':
        state = load_state()
        try:
            state = set_agent_config(state, args.agent_name, args.agent_file)
            save_state(state)
            print(json.dumps(state['agent_config'], indent=2))
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    elif args.action == 'check-stop':
        state = load_state()
        should_stop, reason = check_should_stop(state, args.current_metric)
        result = {'should_stop': should_stop, 'reason': reason}
        print(json.dumps(result, indent=2))
        if should_stop:
            print("\n<choice>STOP</choice>")


if __name__ == '__main__':
    main()
