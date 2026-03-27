#!/usr/bin/env python3
"""
State management for autoresearch sessions.

This is a lightweight state store for Ralph Loop sessions.
The actual loop control is handled by Kimi's Ralph Loop mechanism.
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
        'version': '2.0',  # Version 2.0 for Ralph Loop edition
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
        'agent_config': None,
        'config': {}
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


def update_iteration_status(state: dict[str, Any], status: str) -> dict[str, Any]:
    """
    Update state based on iteration result.
    
    This is called by Ralph Loop after each iteration.
    """
    state['iteration'] = state.get('iteration', 0) + 1
    
    if status == 'keep':
        state['consecutive_discards'] = 0
    elif status == 'discard':
        state['consecutive_discards'] = state.get('consecutive_discards', 0) + 1
    elif status == 'pivot':
        state['pivot_count'] = state.get('pivot_count', 0) + 1
        state['consecutive_discards'] = 0
    
    save_state(state)
    return state


def main():
    parser = argparse.ArgumentParser(
        description='Manage autoresearch state (Ralph Loop Edition)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load current state
  python scripts/state_manager.py --action load
  
  # Save a value
  python scripts/state_manager.py --action save --key best --value 42
  
  # Update iteration status (called by Ralph Loop)
  python scripts/state_manager.py --action update-status --status keep
  
  # Log a lesson
  python scripts/state_manager.py --action log-lesson --lesson "This worked well"
  
  # Reset state
  python scripts/state_manager.py --action reset
        """
    )
    parser.add_argument('--action', type=str, required=True,
                       choices=['load', 'save', 'update-status', 'reset', 'log-lesson'])
    parser.add_argument('--key', type=str, help='State key to update')
    parser.add_argument('--value', type=str, help='Value to set')
    parser.add_argument('--status', type=str, 
                       choices=['keep', 'discard', 'pivot'],
                       help='Iteration status for update-status')
    parser.add_argument('--lesson', type=str, help='Lesson text')
    parser.add_argument('--lesson-type', type=str, default='positive',
                       choices=['positive', 'strategic', 'negative'])
    
    args = parser.parse_args()
    
    if args.action == 'load':
        state = load_state()
        print(json.dumps(state, indent=2))
    
    elif args.action == 'save':
        if args.key and args.value:
            state = load_state()
            # Try to parse as number
            try:
                val = float(args.value)
                # Check if it's actually an int
                if val == int(val):
                    val = int(val)
            except ValueError:
                val = args.value
            state[args.key] = val
            save_state(state)
            print(f"Saved: {args.key} = {val}")
        else:
            print("Error: --key and --value required")
            exit(1)
    
    elif args.action == 'update-status':
        if args.status:
            state = load_state()
            state = update_iteration_status(state, args.status)
            print(json.dumps({
                'iteration': state['iteration'],
                'consecutive_discards': state['consecutive_discards'],
                'pivot_count': state['pivot_count']
            }, indent=2))
        else:
            print("Error: --status required")
            exit(1)
    
    elif args.action == 'reset':
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
        print("State reset")
    
    elif args.action == 'log-lesson':
        if args.lesson:
            log_lesson(args.lesson, args.lesson_type)
            print("Lesson logged")
        else:
            print("Error: --lesson required")
            exit(1)


if __name__ == '__main__':
    main()
