#!/usr/bin/env python3
"""
Autoresearch Daemon - 真正的后台无限迭代

利用 Kimi Background Agent 实现自主运行的 autoresearch：
1. 启动时创建 Background Agent
2. Agent 自主执行迭代循环
3. 定期报告进度
4. 可以暂停/恢复/停止

Usage:
    python scripts/autoresearch_daemon.py start --iterations 100
    python scripts/autoresearch_daemon.py status
    python scripts/autoresearch_daemon.py pause
    python scripts/autoresearch_daemon.py resume
    python scripts/autoresearch_daemon.py stop
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

DAEMON_STATE_FILE = ".autoresearch-daemon.json"
SCRIPT_DIR = Path(__file__).parent


def load_daemon_state() -> dict:
    """Load daemon state."""
    if os.path.exists(DAEMON_STATE_FILE):
        with open(DAEMON_STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        'status': 'stopped',
        'start_time': None,
        'current_iteration': 0,
        'max_iterations': 0,
        'task_id': None,
        'config': {}
    }


def save_daemon_state(state: dict) -> None:
    """Save daemon state."""
    with open(DAEMON_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def generate_daemon_prompt(config: dict) -> str:
    """
    生成 Daemon Agent 的系统提示
    
    这个提示让 Background Agent 自主运行 autoresearch 循环
    遵循Kimi官方Ralph循环协议，支持 <choice>STOP</choice> 停止信号
    """
    loop_control = config.get('loop_control', {})
    max_steps = loop_control.get('max_steps_per_turn', 50)
    max_retries = loop_control.get('max_retries_per_step', 3)
    max_ralph = loop_control.get('max_ralph_iterations', 0)
    
    agent_config = config.get('agent_config', {})
    agent_hint = ""
    if agent_config.get('agent'):
        agent_hint = f"\nAgent profile: Use '{agent_config['agent']}' agent mode for specialized behavior."
    elif agent_config.get('agent_file'):
        agent_hint = f"\nAgent profile: Load custom agent from {agent_config['agent_file']}"
    
    return f"""You are an Autoresearch Daemon - an autonomous iterative improvement engine.

Your goal: {config.get('goal', 'Improve the codebase')}
Scope: {config.get('scope', 'current directory')}
Max iterations: {config.get('iterations', 10)}

## Loop Control Configuration

- Max steps per turn: {max_steps}
- Max retries per step: {max_retries}
- Max Ralph iterations: {max_ralph} ({'infinite' if max_ralph == -1 else 'disabled' if max_ralph == 0 else 'limited'})
{agent_hint}

## Your Task

Run an autonomous modify-verify-decide loop (Ralph loop protocol).

### Ralph Loop Protocol

This follows Kimi's official Ralph loop: the same prompt is fed repeatedly to the Agent,
allowing it to iterate around a task continuously until `<choice>STOP</choice>` is output
or the iteration limit is reached.

### Iteration Protocol

For each iteration:

1. **READ CONTEXT**
   - Read autoresearch-state.json to understand current state
   - Read autoresearch-results.tsv to see history
   - Read relevant files in scope
   - Check git log for recent changes

2. **ANALYZE & HYPOTHESIZE**
   - Identify what needs improvement
   - Form ONE concrete hypothesis
   - Choose the most promising change

3. **EXECUTE CHANGE**
   - Make ONE atomic change to the code
   - Use WriteFile or StrReplaceFile
   - Ensure change is minimal and focused
   - If a step fails, retry up to {max_retries} times before moving on

4. **COMMIT**
   ```bash
   python scripts/check_git.py --action commit --message "experiment: <description>"
   ```
   Retry up to {max_retries} times if commit fails.

5. **VERIFY**
   - Run: {config.get('verify', 'echo "No verify command"')}
   - Extract the metric from output
   - Limit verification steps to {max_steps} per iteration

6. **DECIDE**
   ```bash
   python scripts/autoresearch_decision.py --action decide --current <metric> --baseline <baseline> --direction {config.get('direction', 'lower')} --guard-passed true
   ```
   - If KEEP: Continue with new baseline
   - If DISCARD: Revert and try different approach

7. **LOG**
   ```bash
   python scripts/log_result.py --iteration <n> --commit <hash> --metric <value> --status <keep|discard> --description "<what>"
   ```

8. **CHECK STOP CONDITIONS**
   ```bash
   python scripts/state_manager.py --action check-stop --current-metric <metric>
   ```
   If the output contains `<choice>STOP</choice>`, you MUST stop the loop immediately.
   Stop conditions:
   - Target metric reached
   - Max iterations reached
   - 5+ consecutive discards with 2+ pivots (truly stuck)

9. **CHECK RELAY** (Critical for long runs)
   - Track your running time
   - At 22 hours (79200 seconds): Prepare for relay
     - Save all state
     - Generate relay prompt
     - Print "[RELAY_NEEDED]"
     - Stop gracefully
   - The next session will continue automatically

10. **REPORT**
    - Every 5 iterations, write progress to autoresearch-daemon.log
    - Include: current iteration, metric, recent changes

## Ralph Loop Stop Signal

To stop the Ralph loop gracefully, output exactly:
```
<choice>STOP</choice>
```

This signals that the task is complete or cannot proceed further.

## Important Rules

- ONE change per iteration
- Always commit before verify
- Revert failed changes immediately
- Never batch multiple changes
- Keep changes minimal and reversible
- If stuck (3+ discards), refine strategy; if 5+ discards with 2+ pivots, search web
- Log every action
- Respect loop control limits (steps, retries)
- Output `<choice>STOP</choice>` when stopping

## State Management

You maintain state in:
- autoresearch-state.json - Current run state
- autoresearch-results.tsv - History log
- autoresearch-daemon.log - Progress reports
- .autoresearch-daemon.json - Daemon control

Read these files at the start of each iteration to make informed decisions.

## Start Now

Begin with iteration 1. Execute the full protocol autonomously.
Do not ask for user confirmation - you are running in autonomous daemon mode.

Current state: Check {DAEMON_STATE_FILE} and autoresearch-state.json
"""


def cmd_start(args: argparse.Namespace) -> int:
    """Start the daemon."""
    state = load_daemon_state()
    
    if state['status'] == 'running':
        print(f"Daemon already running (iteration {state['current_iteration']}/{state['max_iterations']})")
        return 1
    
    # Load config
    config = {
        'goal': args.goal,
        'scope': args.scope,
        'verify': args.verify,
        'direction': args.direction,
        'iterations': args.iterations,
        'target': args.target,
        'loop_control': {
            'max_steps_per_turn': getattr(args, 'max_steps_per_turn', 50),
            'max_retries_per_step': getattr(args, 'max_retries_per_step', 3),
            'max_ralph_iterations': getattr(args, 'max_ralph_iterations', 0)
        },
        'agent_config': None
    }
    
    # Set agent config if provided
    if getattr(args, 'agent', None):
        config['agent_config'] = {'agent': args.agent, 'agent_file': None}
    elif getattr(args, 'agent_file', None):
        config['agent_config'] = {'agent': None, 'agent_file': args.agent_file}
    
    # Save state
    state['status'] = 'running'
    state['start_time'] = datetime.now().isoformat()
    state['current_iteration'] = 0
    state['max_iterations'] = args.iterations
    state['config'] = config
    save_daemon_state(state)
    
    # Generate the prompt for Background Agent
    prompt = generate_daemon_prompt(config)
    
    print("=" * 60)
    print("  Autoresearch Daemon")
    print("=" * 60)
    print()
    print(f"Goal: {args.goal}")
    print(f"Iterations: {args.iterations}")
    print(f"Verify: {args.verify or 'Not set'}")
    print()
    print("To start the daemon, run this Agent:")
    print()
    print("```python")
    print("Agent(")
    print(f'    description="Autoresearch daemon",')
    print(f'    prompt="""{prompt[:200]}...""",')
    print("    run_in_background=True")
    print(")")
    print("```")
    print()
    print("Or save the full prompt to a file and use it.")
    
    # Save prompt to file for easy use
    prompt_file = ".autoresearch-daemon-prompt.txt"
    with open(prompt_file, 'w') as f:
        f.write(prompt)
    print(f"\nFull prompt saved to: {prompt_file}")
    print(f"\nStatus file: {DAEMON_STATE_FILE}")
    
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Check daemon status."""
    state = load_daemon_state()
    
    print("=" * 60)
    print("  Daemon Status")
    print("=" * 60)
    print()
    print(f"Status: {state['status']}")
    print(f"Current iteration: {state['current_iteration']}/{state['max_iterations']}")
    
    if state['start_time']:
        print(f"Started: {state['start_time']}")
    
    if state.get('task_id'):
        print(f"Task ID: {state['task_id']}")
    
    config = state.get('config', {})
    if config:
        print()
        print("Configuration:")
        for key, value in config.items():
            if value:
                print(f"  {key}: {value}")
    
    # Check for recent log
    log_file = "autoresearch-daemon.log"
    if os.path.exists(log_file):
        print()
        print(f"Recent log ({log_file}):")
        with open(log_file, 'r') as f:
            lines = f.readlines()
            for line in lines[-5:]:
                print(f"  {line.strip()}")
    
    return 0


def cmd_pause(args: argparse.Namespace) -> int:
    """Pause the daemon."""
    state = load_daemon_state()
    
    if state['status'] != 'running':
        print("Daemon is not running")
        return 1
    
    state['status'] = 'paused'
    save_daemon_state(state)
    
    print("Daemon paused")
    print("Use 'resume' to continue")
    
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    """Resume the daemon."""
    state = load_daemon_state()
    
    if state['status'] != 'paused':
        print("Daemon is not paused")
        return 1
    
    state['status'] = 'running'
    save_daemon_state(state)
    
    print("Daemon resumed")
    print(f"Continuing from iteration {state['current_iteration']}")
    
    return 0


def cmd_stop(args: argparse.Namespace) -> int:
    """Stop the daemon."""
    state = load_daemon_state()
    
    state['status'] = 'stopped'
    state['task_id'] = None
    save_daemon_state(state)
    
    print("Daemon stopped")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Autoresearch Daemon - True background autonomous iteration'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # start
    start_parser = subparsers.add_parser('start', help='Start daemon')
    start_parser.add_argument('--goal', type=str, required=True)
    start_parser.add_argument('--scope', type=str, default='.')
    start_parser.add_argument('--verify', type=str, default='')
    start_parser.add_argument('--direction', type=str, default='lower',
                            choices=['lower', 'higher'])
    start_parser.add_argument('--iterations', type=int, default=10)
    start_parser.add_argument('--target', type=float)
    
    # Loop control options (Kimi Ralph loop compatible)
    start_parser.add_argument('--max-steps-per-turn', type=int, default=50,
                            help='Max steps per turn (default: 50)')
    start_parser.add_argument('--max-retries-per-step', type=int, default=3,
                            help='Max retries per step (default: 3)')
    start_parser.add_argument('--max-ralph-iterations', type=int, default=0,
                            help='Max Ralph iterations: 0=off, -1=infinite (default: 0)')
    
    # Agent configuration (Kimi sub-agent support)
    agent_group = start_parser.add_mutually_exclusive_group()
    agent_group.add_argument('--agent', type=str, choices=['default', 'okabe'],
                            help='Use built-in agent profile')
    agent_group.add_argument('--agent-file', type=str,
                            help='Use custom agent file')
    
    # status
    subparsers.add_parser('status', help='Check status')
    
    # pause
    subparsers.add_parser('pause', help='Pause daemon')
    
    # resume
    subparsers.add_parser('resume', help='Resume daemon')
    
    # stop
    subparsers.add_parser('stop', help='Stop daemon')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    commands = {
        'start': cmd_start,
        'status': cmd_status,
        'pause': cmd_pause,
        'resume': cmd_resume,
        'stop': cmd_stop
    }
    
    code = commands[args.command](args)
    sys.exit(code)


if __name__ == '__main__':
    main()
