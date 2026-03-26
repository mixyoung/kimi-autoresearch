#!/usr/bin/env python3
"""
Background runtime controller for autoresearch.
Manages detached execution and status tracking.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from typing import Any

RUNTIME_FILE = "autoresearch-runtime.json"
STATE_FILE = "autoresearch-state.json"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_runtime() -> dict[str, Any]:
    """Load runtime state."""
    if os.path.exists(RUNTIME_FILE):
        try:
            with open(RUNTIME_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {
        'status': 'stopped',
        'pid': None,
        'start_time': None,
        'last_update': None,
        'iterations_completed': 0,
        'errors': []
    }


def save_runtime(runtime: dict[str, Any]) -> None:
    """Save runtime state."""
    runtime['last_update'] = datetime.now().isoformat()
    with open(RUNTIME_FILE, 'w') as f:
        json.dump(runtime, f, indent=2)


def load_state() -> dict[str, Any]:
    """Load autoresearch state."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}


def is_process_running(pid: int) -> bool:
    """Check if a process is running."""
    if pid is None:
        return False
    try:
        # Windows check
        if sys.platform == 'win32':
            result = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}'],
                capture_output=True,
                text=True
            )
            return str(pid) in result.stdout
        else:
            # Unix check
            os.kill(pid, 0)
            return True
    except (OSError, ProcessLookupError):
        return False


def cmd_status(args: argparse.Namespace) -> int:
    """Check background runtime status."""
    runtime = load_runtime()
    state = load_state()
    
    status = runtime.get('status', 'unknown')
    pid = runtime.get('pid')
    
    # Verify process is actually running
    if status == 'running' and pid:
        if not is_process_running(pid):
            runtime['status'] = 'stopped'
            runtime['pid'] = None
            save_runtime(runtime)
            status = 'stopped'
    
    result = {
        'status': status,
        'pid': pid,
        'start_time': runtime.get('start_time'),
        'last_update': runtime.get('last_update'),
        'iterations_completed': runtime.get('iterations_completed', 0),
        'current_iteration': state.get('iteration', 0),
        'config': state.get('config', {})
    }
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("=" * 50)
        print("Autoresearch Background Runtime Status")
        print("=" * 50)
        print(f"Status: {status}")
        if pid:
            print(f"PID: {pid}")
        if result['start_time']:
            print(f"Started: {result['start_time']}")
        if result['last_update']:
            print(f"Last update: {result['last_update']}")
        print(f"Iterations completed: {result['iterations_completed']}")
        print(f"Current iteration: {result['current_iteration']}")
        
        config = result['config']
        if config:
            print("\nConfiguration:")
            for key in ['goal', 'metric', 'direction']:
                if key in config:
                    print(f"  {key}: {config[key]}")
    
    return 0 if status != 'error' else 1


def cmd_start(args: argparse.Namespace) -> int:
    """Start background runtime."""
    runtime = load_runtime()
    
    if runtime.get('status') == 'running':
        print("Error: Background runtime already running")
        print(f"PID: {runtime.get('pid')}")
        print("Use 'status' to check or 'stop' to terminate")
        return 1
    
    # Update runtime state
    runtime['status'] = 'running'
    runtime['start_time'] = datetime.now().isoformat()
    runtime['iterations_completed'] = 0
    runtime['errors'] = []
    
    # Create the background process
    # Note: This is a simplified version - in practice, you'd use
    # a proper daemon process or service
    
    print("Starting background runtime...")
    print("Note: In Kimi Code CLI, use the Background Task feature instead:")
    print("  1. Run $kimi-autoresearch with Background: true")
    print("  2. Or use Shell with run_in_background=true")
    
    # Write a marker that we're in background mode
    runtime['marker'] = 'background'
    save_runtime(runtime)
    
    print(f"\nRuntime state saved to {RUNTIME_FILE}")
    print("Status: ready for background execution")
    
    return 0


def cmd_stop(args: argparse.Namespace) -> int:
    """Stop background runtime."""
    runtime = load_runtime()
    
    if runtime.get('status') != 'running':
        print("Background runtime is not running")
        return 0
    
    pid = runtime.get('pid')
    if pid and is_process_running(pid):
        try:
            if sys.platform == 'win32':
                subprocess.run(['taskkill', '/PID', str(pid), '/F'], 
                             capture_output=True)
            else:
                os.kill(pid, 15)  # SIGTERM
                time.sleep(2)
                if is_process_running(pid):
                    os.kill(pid, 9)  # SIGKILL
        except Exception as e:
            print(f"Warning: Error stopping process: {e}")
    
    runtime['status'] = 'stopped'
    runtime['pid'] = None
    save_runtime(runtime)
    
    print("Background runtime stopped")
    return 0


def cmd_pause(args: argparse.Namespace) -> int:
    """Pause background runtime."""
    runtime = load_runtime()
    
    if runtime.get('status') != 'running':
        print("Background runtime is not running")
        return 1
    
    runtime['status'] = 'paused'
    save_runtime(runtime)
    
    print("Background runtime paused")
    print("Use 'resume' to continue")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    """Resume background runtime."""
    runtime = load_runtime()
    
    if runtime.get('status') != 'paused':
        print("Background runtime is not paused")
        return 1
    
    runtime['status'] = 'running'
    save_runtime(runtime)
    
    print("Background runtime resumed")
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    """Show recent runtime log."""
    runtime = load_runtime()
    errors = runtime.get('errors', [])
    
    if not errors:
        print("No errors logged")
        return 0
    
    print("Recent Errors:")
    print("=" * 50)
    for error in errors[-10:]:  # Show last 10
        print(f"[{error.get('timestamp', 'unknown')}]")
        print(f"  Iteration: {error.get('iteration', 'N/A')}")
        print(f"  Error: {error.get('message', 'unknown')}")
        print()
    
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Autoresearch Background Runtime Controller'
    )
    parser.add_argument('--json', action='store_true', 
                       help='Output in JSON format')
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # status
    subparsers.add_parser('status', help='Check runtime status')
    
    # start
    start_parser = subparsers.add_parser('start', help='Start background runtime')
    start_parser.add_argument('--iterations', type=int, default=0,
                            help='Max iterations')
    
    # stop
    subparsers.add_parser('stop', help='Stop background runtime')
    
    # pause
    subparsers.add_parser('pause', help='Pause background runtime')
    
    # resume
    subparsers.add_parser('resume', help='Resume background runtime')
    
    # log
    subparsers.add_parser('log', help='Show runtime log')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    commands = {
        'status': cmd_status,
        'start': cmd_start,
        'stop': cmd_stop,
        'pause': cmd_pause,
        'resume': cmd_resume,
        'log': cmd_log
    }
    
    code = commands[args.command](args)
    sys.exit(code)


if __name__ == '__main__':
    main()
