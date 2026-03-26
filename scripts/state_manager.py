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
        'start_time': datetime.now().isoformat()
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


def main():
    parser = argparse.ArgumentParser(description='Manage autoresearch state')
    parser.add_argument('--action', type=str, required=True,
                       choices=['load', 'save', 'update', 'reset', 'log-lesson'])
    parser.add_argument('--key', type=str, help='State key to update')
    parser.add_argument('--value', type=str, help='Value to set')
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


if __name__ == '__main__':
    main()
