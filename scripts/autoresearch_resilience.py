#!/usr/bin/env python3
"""
Session Resilience Manager - 会话弹性管理器

确保长时间运行的 autoresearch 不会因为上下文漂移而失败。

Features:
1. Protocol fingerprint check - 验证核心规则记忆
2. Auto re-anchor - 自动重新加载协议文件
3. Session split detection - 检测并处理会话分割
4. State consistency check - 验证状态一致性
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

STATE_FILE = "autoresearch-state.json"
RUNTIME_FILE = "autoresearch-runtime.json"
RESILIENCE_LOG = "autoresearch-resilience.log"


class ResilienceManager:
    """会话弹性管理器"""
    
    # 关键协议规则指纹
    PROTOCOL_FINGERPRINT = {
        "core_loop": "modify → verify → keep/discard → repeat",
        "one_change_rule": "每次迭代只做一次原子修改",
        "verify_first": "修改前必须能机械验证",
        "git_commit_before_verify": "验证前必须先提交",
        "auto_rollback": "失败自动回滚",
        "atomic_change": "变更是可逆的",
        "mechanical_verify": "验证是机械的，非主观",
    }
    
    # 触发重新锚定的阈值
    REANCHOR_INTERVAL = 10  # 每10次迭代
    SESSION_SPLIT_ITERATIONS = 40  # 40次迭代分割会话
    MAX_CONTEXT_COMPACT = 2  # 最多2次上下文压缩
    
    def __init__(self):
        self.check_count = 0
        self.last_anchor_iteration = 0
        self.compaction_count = 0
        
    def load_state(self) -> dict[str, Any]:
        """加载状态"""
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_state(self, state: dict) -> None:
        """保存状态"""
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def log_event(self, event_type: str, details: dict) -> None:
        """记录弹性事件"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'details': details
        }
        
        with open(RESILIENCE_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    def protocol_fingerprint_check(self) -> dict[str, bool]:
        """
        协议指纹检查
        
        验证关键规则是否仍然记忆完整。
        返回每个规则的检查结果。
        """
        results = {}
        
        # 在实际使用中，这会被 Kimi 调用并返回结果
        # 这里我们记录检查行为
        for rule, description in self.PROTOCOL_FINGERPRINT.items():
            # 默认假设通过，实际由 Kimi 验证
            results[rule] = True
        
        self.check_count += 1
        
        return {
            'checks': results,
            'all_passed': all(results.values()),
            'check_count': self.check_count,
            'timestamp': datetime.now().isoformat()
        }
    
    def should_reanchor(self, current_iteration: int) -> tuple[bool, str]:
        """
        判断是否需要重新锚定
        
        Returns:
            (should_reanchor, reason)
        """
        # 检查1：达到重新锚定间隔
        if current_iteration - self.last_anchor_iteration >= self.REANCHOR_INTERVAL:
            return True, f"Reached reanchor interval ({self.REANCHOR_INTERVAL} iterations)"
        
        # 检查2：上下文压缩次数过多
        if self.compaction_count >= self.MAX_CONTEXT_COMPACT:
            return True, f"Context compacted {self.compaction_count} times"
        
        # 检查3：长时间未检查
        # 这里可以添加时间检查
        
        return False, ""
    
    def should_split_session(self, current_iteration: int) -> tuple[bool, str]:
        """
        判断是否需要分割会话
        
        Returns:
            (should_split, reason)
        """
        if current_iteration >= self.SESSION_SPLIT_ITERATIONS:
            return True, f"Iteration limit reached ({self.SESSION_SPLIT_ITERATIONS})"
        
        if self.compaction_count >= self.MAX_CONTEXT_COMPACT + 1:
            return True, f"Too many context compactions ({self.compaction_count})"
        
        return False, ""
    
    def perform_reanchor(self, current_iteration: int) -> dict:
        """
        执行重新锚定
        
        重新加载协议文件，刷新记忆。
        """
        self.last_anchor_iteration = current_iteration
        
        # 记录重新锚定事件
        self.log_event('reanchor', {
            'iteration': current_iteration,
            'check_count': self.check_count
        })
        
        # 生成重新锚定提示
        reanchor_prompt = self._generate_reanchor_prompt()
        
        return {
            'success': True,
            'iteration': current_iteration,
            'prompt': reanchor_prompt,
            'files_to_reload': [
                'SKILL.md',
                'references/loop-protocol.md',
                'autoresearch-state.json'
            ]
        }
    
    def _generate_reanchor_prompt(self) -> str:
        """生成重新锚定提示"""
        return """
[RE-ANCHOR] Session context has been compacted. Reloading protocol...

Please re-read these critical files to refresh your memory:

1. **SKILL.md** - Core iteration protocol
2. **references/loop-protocol.md** - Detailed loop specification  
3. **autoresearch-state.json** - Current run state

Key rules to remember:
- ONE change per iteration
- Commit BEFORE verify
- Revert if not improved
- Log every result
- Check stuck patterns

Continuing from where we left off...
"""
    
    def perform_session_split(self, current_iteration: int, state: dict) -> dict:
        """
        执行会话分割
        
        保存检查点，优雅地停止当前会话。
        """
        # 更新状态
        state['status'] = 'split'
        state['split_at'] = current_iteration
        state['split_time'] = datetime.now().isoformat()
        self.save_state(state)
        
        # 记录分割事件
        self.log_event('session_split', {
            'iteration': current_iteration,
            'state': state
        })
        
        return {
            'success': True,
            'checkpoint_saved': True,
            'split_at': current_iteration,
            'message': f"[SESSION-SPLIT] Checkpoint saved at iteration {current_iteration}",
            'resume_instruction': "Re-invoke $kimi-autoresearch to resume from checkpoint"
        }
    
    def check_state_consistency(self) -> dict:
        """
        检查状态一致性
        
        验证 state.json 和 results.tsv 是否一致。
        """
        issues = []
        
        # 检查文件存在性
        if not os.path.exists(STATE_FILE):
            issues.append("State file missing")
        
        if not os.path.exists('autoresearch-results.tsv'):
            issues.append("Results TSV missing")
        
        # 加载状态
        state = self.load_state()
        
        # 检查关键字段
        required_fields = ['iteration', 'baseline', 'config']
        for field in required_fields:
            if field not in state:
                issues.append(f"Missing field: {field}")
        
        # 检查迭代计数一致性
        tsv_iterations = self._count_tsv_iterations()
        state_iteration = state.get('iteration', 0)
        
        if tsv_iterations != state_iteration:
            issues.append(f"Iteration mismatch: TSV={tsv_iterations}, State={state_iteration}")
        
        return {
            'consistent': len(issues) == 0,
            'issues': issues,
            'tsv_iterations': tsv_iterations,
            'state_iteration': state_iteration
        }
    
    def _count_tsv_iterations(self) -> int:
        """计算 TSV 中的迭代数"""
        try:
            with open('autoresearch-results.tsv', 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 减去 header
                return max(0, len(lines) - 1)
        except FileNotFoundError:
            return 0
    
    def generate_resilience_report(self) -> str:
        """生成弹性报告"""
        state = self.load_state()
        current_iteration = state.get('iteration', 0)
        
        report = []
        report.append("=" * 60)
        report.append("Session Resilience Report")
        report.append("=" * 60)
        report.append(f"Current iteration: {current_iteration}")
        report.append(f"Last anchor: {self.last_anchor_iteration}")
        report.append(f"Context compactions: {self.compaction_count}")
        report.append(f"Protocol checks: {self.check_count}")
        
        # 检查建议
        should_reanchor, reason = self.should_reanchor(current_iteration)
        if should_reanchor:
            report.append(f"\n⚠️ RECOMMENDATION: Re-anchor needed")
            report.append(f"   Reason: {reason}")
        
        should_split, reason = self.should_split_session(current_iteration)
        if should_split:
            report.append(f"\n⚠️ RECOMMENDATION: Session split advised")
            report.append(f"   Reason: {reason}")
        
        consistency = self.check_state_consistency()
        if not consistency['consistent']:
            report.append(f"\n❌ STATE INCONSISTENCY DETECTED:")
            for issue in consistency['issues']:
                report.append(f"   - {issue}")
        
        report.append("\n" + "=" * 60)
        
        return '\n'.join(report)


def main():
    """CLI for resilience management"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Session Resilience Manager')
    subparsers = parser.add_subparsers(dest='command')
    
    # check
    subparsers.add_parser('check', help='Run protocol fingerprint check')
    
    # report
    subparsers.add_parser('report', help='Generate resilience report')
    
    # reanchor
    reanchor_parser = subparsers.add_parser('reanchor', help='Perform reanchor')
    reanchor_parser.add_argument('--iteration', type=int, default=0)
    
    # split
    split_parser = subparsers.add_parser('split', help='Perform session split')
    split_parser.add_argument('--iteration', type=int, default=0)
    
    args = parser.parse_args()
    
    manager = ResilienceManager()
    
    if args.command == 'check':
        result = manager.protocol_fingerprint_check()
        print(json.dumps(result, indent=2))
    
    elif args.command == 'report':
        print(manager.generate_resilience_report())
    
    elif args.command == 'reanchor':
        result = manager.perform_reanchor(args.iteration)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'split':
        state = manager.load_state()
        result = manager.perform_session_split(args.iteration, state)
        print(json.dumps(result, indent=2))
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
