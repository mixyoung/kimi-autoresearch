#!/usr/bin/env python3
"""
Autoresearch Infinite - 无限运行模式

解决 Kimi Background Task 24小时限制：
通过"接力"机制，在接近限制时自动启动新的 Background Agent
实现真正的无限运行。

Usage:
    python scripts/autoresearch_infinite.py start --goal "..."
    python scripts/autoresearch_infinite.py status
    python scripts/autoresearch_infinite.py stop
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

INFINITE_STATE_FILE = ".autoresearch-infinite.json"
RELAY_INTERVAL = 82800  # 23小时 = 82800秒（提前1小时交接）
MAX_SINGLE_RUN = 86400  # 24小时硬性限制


class InfiniteRunner:
    """无限运行管理器"""
    
    def __init__(self):
        self.state = self._load_state()
    
    def _load_state(self) -> dict:
        """加载无限运行状态"""
        if os.path.exists(INFINITE_STATE_FILE):
            with open(INFINITE_STATE_FILE, 'r') as f:
                return json.load(f)
        return {
            'status': 'stopped',
            'total_iterations': 0,
            'total_runtime_seconds': 0,
            'relay_count': 0,
            'current_session_start': None,
            'current_session_iterations': 0,
            'config': {},
            'history': []
        }
    
    def _save_state(self) -> None:
        """保存无限运行状态"""
        with open(INFINITE_STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def _generate_relay_prompt(self, config: dict) -> str:
        """
        生成接力提示
        
        这个提示让新的 Background Agent 接力继续运行
        """
        return f"""[RELAY SESSION #{self.state['relay_count'] + 1}]

You are continuing an infinite autoresearch run.

## Previous Session Summary

- Total iterations so far: {self.state['total_iterations']}
- Total runtime: {self._format_duration(self.state['total_runtime_seconds'])}
- Previous sessions: {self.state['relay_count']}

## Goal

{config.get('goal', 'Improve the codebase')}

## Current State

1. Read {INFINITE_STATE_FILE} for full history
2. Read autoresearch-state.json for current run state
3. Read autoresearch-results.tsv for iteration history

## Your Task

Continue the autoresearch loop for up to 23 hours:

1. **Check Time**
   - Track your running time
   - At 22 hours, prepare for relay

2. **Continue Iterations**
   - Follow standard iteration protocol
   - One change → commit → verify → decide → log
   - Update {INFINITE_STATE_FILE} after each iteration

3. **Prepare for Relay**
   - At 22 hours: 
     - Save current state
     - Generate summary
     - Update {INFINITE_STATE_FILE}
     - Print "[RELAY_NEEDED]"

4. **Handle Relay**
   - If you see "[RELAY_NEEDED]" from previous session:
     - Continue seamlessly
     - Increment relay_count
     - Update total_iterations

## Critical Rules

- NEVER stop unless goal reached or explicit stop command
- At 22 hours, MUST prepare relay
- Keep state files updated
- Log every iteration

## Start Now

Continue from iteration {self.state['total_iterations'] + 1}
"""
    
    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        
        return " ".join(parts) if parts else "0m"
    
    def start(self, config: dict) -> str:
        """
        启动无限运行
        
        Returns: 启动提示，需要在 Kimi 中执行
        """
        # 初始化状态
        self.state['status'] = 'running'
        self.state['config'] = config
        self.state['current_session_start'] = datetime.now().isoformat()
        self.state['relay_count'] = 0
        self.state['history'].append({
            'start_time': datetime.now().isoformat(),
            'relay_num': 0,
            'type': 'initial'
        })
        self._save_state()
        
        # 生成启动提示
        prompt = self._generate_relay_prompt(config)
        
        # 保存提示到文件
        prompt_file = ".autoresearch-infinite-prompt.txt"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        print("=" * 70)
        print("  Autoresearch Infinite Mode")
        print("=" * 70)
        print()
        print(f"Goal: {config.get('goal')}")
        print(f"Max single session: 23 hours")
        print(f"Relay strategy: Automatic handoff")
        print()
        print("To start, run this Agent in Kimi:")
        print()
        print("```python")
        print("Agent(")
        print(f'    description="Autoresearch infinite runner",')
        print(f'    prompt=read("{prompt_file}"),')
        print("    run_in_background=True")
        print(")")
        print("```")
        print()
        print(f"State file: {INFINITE_STATE_FILE}")
        print(f"Prompt file: {prompt_file}")
        print()
        print("The agent will automatically relay every 23 hours.")
        print("No manual intervention needed.")
        
        return prompt_file
    
    def generate_relay_command(self) -> str:
        """
        生成接力命令
        
        当检测到需要接力时，生成新的 Agent 调用
        """
        self.state['relay_count'] += 1
        self.state['history'].append({
            'time': datetime.now().isoformat(),
            'relay_num': self.state['relay_count'],
            'total_iterations': self.state['total_iterations'],
            'type': 'relay'
        })
        self._save_state()
        
        prompt_file = ".autoresearch-infinite-prompt.txt"
        
        return f"""
[RELAY TRIGGERED]

Current session reached time limit.
Starting relay #{self.state['relay_count']}...

Execute this to continue:

```python
Agent(
    description="Autoresearch infinite runner (relay {self.state['relay_count']})",
    prompt=read("{prompt_file}"),
    run_in_background=True
)
```

Or use the relay helper:

```bash
python scripts/autoresearch_infinite.py relay
```
"""
    
    def update_progress(self, iterations: int, runtime_seconds: int) -> None:
        """更新进度"""
        self.state['total_iterations'] = iterations
        self.state['total_runtime_seconds'] = runtime_seconds
        self.state['current_session_iterations'] += 1
        self._save_state()
    
    def status(self) -> dict:
        """获取状态"""
        return {
            'status': self.state['status'],
            'total_iterations': self.state['total_iterations'],
            'total_runtime': self._format_duration(self.state['total_runtime_seconds']),
            'relay_count': self.state['relay_count'],
            'current_session_iterations': self.state['current_session_iterations'],
            'config': self.state['config'],
            'history': self.state['history'][-5:]  # 最近5条
        }
    
    def stop(self) -> None:
        """停止无限运行"""
        self.state['status'] = 'stopped'
        self.state['history'].append({
            'time': datetime.now().isoformat(),
            'type': 'stopped',
            'total_iterations': self.state['total_iterations'],
            'total_runtime': self.state['total_runtime_seconds']
        })
        self._save_state()
        
        print("Infinite run stopped.")
        print(f"Total iterations: {self.state['total_iterations']}")
        print(f"Total runtime: {self._format_duration(self.state['total_runtime_seconds'])}")
        print(f"Relay sessions: {self.state['relay_count']}")


def main():
    """CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Autoresearch Infinite Runner')
    subparsers = parser.add_subparsers(dest='command')
    
    # start
    start_parser = subparsers.add_parser('start', help='Start infinite run')
    start_parser.add_argument('--goal', type=str, required=True)
    start_parser.add_argument('--scope', type=str, default='.')
    start_parser.add_argument('--verify', type=str, default='')
    start_parser.add_argument('--direction', type=str, default='lower')
    start_parser.add_argument('--target', type=float)
    
    # status
    subparsers.add_parser('status', help='Show status')
    
    # relay
    subparsers.add_parser('relay', help='Trigger relay')
    
    # stop
    subparsers.add_parser('stop', help='Stop infinite run')
    
    args = parser.parse_args()
    
    runner = InfiniteRunner()
    
    if args.command == 'start':
        config = {
            'goal': args.goal,
            'scope': args.scope,
            'verify': args.verify,
            'direction': args.direction,
            'target': args.target
        }
        runner.start(config)
    
    elif args.command == 'status':
        import pprint
        pprint.pprint(runner.status())
    
    elif args.command == 'relay':
        print(runner.generate_relay_command())
    
    elif args.command == 'stop':
        runner.stop()
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
