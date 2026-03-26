#!/usr/bin/env python3
"""
Autoresearch Autonomous Engine - 全自动引擎

实现真正无人值守的 autoresearch：
1. 自动分析代码
2. 生成修改假设
3. 自动执行修改
4. 验证结果
5. 决策保留/回滚
6. 循环直到目标达成

Usage:
    # 全自动模式 - 完全无人值守
    python autoresearch_autonomous.py --goal "add type hints" --scope "scripts/*.py" --iterations 10
    
    # 带验证命令
    python autoresearch_autonomous.py --goal "reduce type errors" --scope "src/" --verify "mypy src/ 2>&1 | grep -c error" --direction lower --iterations 20
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# Import our modules
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from autoresearch_analyzer import CodeAnalyzer, AnalysisResult
from autoresearch_applier import CodeApplier, Transformation


class AutonomousEngine:
    """全自动研究引擎"""
    
    def __init__(self, config: dict):
        self.config = config
        self.goal = config['goal']
        self.scope = config['scope']
        self.verify_cmd = config.get('verify', '')
        self.guard_cmd = config.get('guard', '')
        self.direction = config.get('direction', 'lower')
        self.max_iterations = config.get('iterations', 10)
        self.target = config.get('target')
        
        self.baseline = None
        self.current_metric = None
        self.iteration = 0
        self.kept_count = 0
        self.discard_count = 0
        self.suggestions = []
        self.results_log = []
        
        self.applier = CodeApplier(dry_run=False)
        
    def run(self) -> dict:
        """
        运行全自动研究循环
        
        Returns:
            运行结果统计
        """
        print("=" * 70)
        print("  Autoresearch Autonomous Engine")
        print("=" * 70)
        print(f"\nGoal: {self.goal}")
        print(f"Scope: {self.scope}")
        print(f"Max iterations: {self.max_iterations}")
        print(f"Direction: {self.direction}")
        if self.target:
            print(f"Target: {self.target}")
        print()
        
        # Phase 1: 初始分析
        print("[Phase 1] Initial Analysis...")
        self.suggestions = self._analyze_code()
        
        if not self.suggestions:
            print("No improvement suggestions found. Exiting.")
            return self._build_result('no_suggestions')
        
        print(f"Found {len(self.suggestions)} suggestions")
        print()
        
        # Phase 2: 获取基线
        if self.verify_cmd:
            print("[Phase 2] Establishing Baseline...")
            success, self.baseline = self._get_baseline()
            if not success:
                print("Failed to get baseline. Exiting.")
                return self._build_result('baseline_failed')
            print(f"Baseline: {self.baseline}")
            print()
        else:
            self.baseline = 0
            print("[Phase 2] No verify command, skipping baseline")
            print()
        
        self.current_metric = self.baseline
        
        # Phase 3: 迭代循环
        print("[Phase 3] Starting Iteration Loop...")
        print()
        
        start_time = time.time()
        
        for i in range(1, self.max_iterations + 1):
            self.iteration = i
            print(f"\n{'='*70}")
            print(f"  Iteration {i}/{self.max_iterations}")
            print(f"{'='*70}")
            
            result = self._run_iteration()
            
            if result == 'target_reached':
                print(f"\n✅ Target reached! Stopping.")
                break
            elif result == 'no_more_suggestions':
                print(f"\n⚠️  No more suggestions to try. Stopping.")
                break
            elif result == 'stuck':
                print(f"\n⚠️  Stuck detected (5+ discards). Stopping.")
                break
        
        duration = time.time() - start_time
        
        # Phase 4: 总结
        print(f"\n{'='*70}")
        print("  Summary")
        print(f"{'='*70}")
        print(f"Iterations: {self.iteration}")
        print(f"Kept: {self.kept_count}")
        print(f"Discarded: {self.discard_count}")
        if self.verify_cmd:
            print(f"Baseline: {self.baseline}")
            print(f"Final: {self.current_metric}")
            improvement = self.current_metric - self.baseline
            print(f"Improvement: {improvement:+.2f}")
        print(f"Duration: {duration:.1f}s")
        
        return self._build_result('completed')
    
    def _analyze_code(self) -> list:
        """分析代码并获取建议"""
        analyzer = CodeAnalyzer(self.goal, self.scope)
        result = analyzer.analyze()
        
        # 按置信度排序
        suggestions = sorted(result.suggestions, key=lambda x: x.get('confidence', 0), reverse=True)
        return suggestions
    
    def _get_baseline(self) -> Tuple[bool, float]:
        """获取基线指标"""
        try:
            result = subprocess.run(
                self.verify_cmd,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=60
            )
            
            # 尝试从输出中提取数字
            output = result.stdout + result.stderr
            
            # 查找数字
            import re
            numbers = re.findall(r'\d+\.?\d*', output)
            if numbers:
                return True, float(numbers[0])
            
            # 如果没有数字，使用退出码
            return True, float(result.returncode)
            
        except Exception as e:
            print(f"Error getting baseline: {e}")
            return False, 0.0
    
    def _run_iteration(self) -> str:
        """
        运行单次迭代
        
        Returns:
            'keep', 'discard', 'target_reached', 'no_more_suggestions', 'stuck'
        """
        # 1. 选择下一个建议
        if not self.suggestions:
            return 'no_more_suggestions'
        
        suggestion = self.suggestions.pop(0)
        
        print(f"\nTrying: {suggestion['description']}")
        print(f"  File: {suggestion['file']}")
        print(f"  Type: {suggestion['type']}")
        
        # 2. 执行修改
        transformation = self._suggestion_to_transformation(suggestion)
        success, message = self.applier.apply(transformation)
        
        if not success:
            print(f"  ❌ Failed to apply: {message}")
            self.discard_count += 1
            return 'discard'
        
        print(f"  ✓ Applied successfully")
        
        # 3. Git 提交
        commit_hash = self._git_commit(f"experiment: {suggestion['description']}")
        if not commit_hash:
            print(f"  ⚠️  Git commit failed, reverting...")
            self._git_revert()
            self.discard_count += 1
            return 'discard'
        
        print(f"  ✓ Committed: {commit_hash[:8]}")
        
        # 4. 运行 Guard（如果配置）
        if self.guard_cmd:
            print(f"  Running guard...")
            guard_passed = self._run_guard()
            if not guard_passed:
                print(f"  ❌ Guard failed, reverting...")
                self._git_revert()
                self.discard_count += 1
                self._log_result(self.iteration, commit_hash, self.current_metric, 'discard', 'guard_failed')
                return 'discard'
            print(f"  ✓ Guard passed")
        
        # 5. 验证指标
        if self.verify_cmd:
            print(f"  Verifying...")
            success, new_metric = self._get_baseline()
            if not success:
                print(f"  ⚠️  Verification failed, reverting...")
                self._git_revert()
                self.discard_count += 1
                self._log_result(self.iteration, commit_hash, self.current_metric, 'discard', 'verify_failed')
                return 'discard'
            
            print(f"  Metric: {new_metric} (was {self.current_metric})")
            
            # 6. 决策
            improved = self._is_improved(new_metric, self.current_metric)
            
            if improved:
                print(f"  ✅ Improved! Keeping change.")
                self.current_metric = new_metric
                self.kept_count += 1
                self._log_result(self.iteration, commit_hash, new_metric, 'keep', suggestion['description'])
                
                # 检查是否达成目标
                if self._target_reached(new_metric):
                    return 'target_reached'
                
                return 'keep'
            else:
                print(f"  ❌ No improvement. Reverting...")
                self._git_revert()
                self.discard_count += 1
                self._log_result(self.iteration, commit_hash, new_metric, 'discard', 'no_improvement')
                
                # 检查是否卡住
                if self.discard_count >= 5:
                    return 'stuck'
                
                return 'discard'
        else:
            # 没有验证命令，直接保留
            print(f"  ✓ No verify command, keeping change.")
            self.kept_count += 1
            self._log_result(self.iteration, commit_hash, 0, 'keep', suggestion['description'])
            return 'keep'
    
    def _suggestion_to_transformation(self, suggestion: dict) -> Transformation:
        """将建议转换为变换对象"""
        return Transformation(
            type=suggestion['type'],
            file=suggestion['file'],
            description=suggestion['description'],
            function=suggestion.get('function'),
            params=suggestion.get('params'),
            returns=suggestion.get('returns'),
            import_name=suggestion.get('import_name'),
            docstring=suggestion.get('docstring'),
            old_name=suggestion.get('old_name'),
            new_name=suggestion.get('new_name'),
            line_number=suggestion.get('line_number')
        )
    
    def _git_commit(self, message: str) -> Optional[str]:
        """Git 提交"""
        try:
            subprocess.run(['git', 'add', '-A'], check=True, capture_output=True)
            subprocess.run(['git', 'commit', '-m', message], check=True, capture_output=True)
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None
    
    def _git_revert(self) -> bool:
        """Git 回滚"""
        try:
            subprocess.run(['git', 'reset', '--hard', 'HEAD'], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _run_guard(self) -> bool:
        """运行 guard 命令"""
        try:
            result = subprocess.run(
                self.guard_cmd,
                shell=True,
                capture_output=True,
                timeout=120
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _is_improved(self, new_val: float, old_val: float) -> bool:
        """判断是否改进"""
        if self.direction == 'lower':
            return new_val < old_val
        else:
            return new_val > old_val
    
    def _target_reached(self, metric: float) -> bool:
        """检查是否达成目标"""
        if self.target is None:
            return False
        if self.direction == 'lower':
            return metric <= self.target
        else:
            return metric >= self.target
    
    def _log_result(self, iteration: int, commit: str, metric: float, status: str, description: str):
        """记录结果"""
        self.results_log.append({
            'iteration': iteration,
            'commit': commit[:8],
            'metric': metric,
            'status': status,
            'description': description,
            'timestamp': datetime.now().isoformat()
        })
    
    def _build_result(self, status: str) -> dict:
        """构建结果"""
        return {
            'status': status,
            'config': self.config,
            'iterations': self.iteration,
            'kept': self.kept_count,
            'discarded': self.discard_count,
            'baseline': self.baseline,
            'final_metric': self.current_metric,
            'results': self.results_log
        }


def main():
    parser = argparse.ArgumentParser(
        description='Autoresearch Autonomous Engine - Fully automated improvement',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add type hints automatically
  python autoresearch_autonomous.py --goal "add type hints" --scope "scripts/*.py" --iterations 10

  # Reduce type errors with verification
  python autoresearch_autonomous.py \\
    --goal "reduce type errors" \\
    --scope "src/" \\
    --verify "mypy src/ 2>&1 | grep -c error" \\
    --direction lower \\
    --target 0 \\
    --iterations 20

  # Remove unused imports
  python autoresearch_autonomous.py \\
    --goal "remove unused imports" \\
    --scope "src/" \\
    --iterations 50
        """
    )
    
    parser.add_argument('--goal', type=str, required=True,
                       help='Optimization goal (e.g., "add type hints")')
    parser.add_argument('--scope', type=str, required=True,
                       help='Code scope pattern (e.g., "src/**/*.py")')
    parser.add_argument('--verify', type=str, default='',
                       help='Verification command to measure metric')
    parser.add_argument('--guard', type=str, default='',
                       help='Guard command (must pass for keep)')
    parser.add_argument('--direction', type=str, default='lower',
                       choices=['lower', 'higher'],
                       help='Whether lower or higher metric is better')
    parser.add_argument('--target', type=float,
                       help='Target metric value to reach')
    parser.add_argument('--iterations', type=int, default=10,
                       help='Maximum number of iterations')
    parser.add_argument('--output', type=str,
                       help='Output JSON file for results')
    
    args = parser.parse_args()
    
    config = {
        'goal': args.goal,
        'scope': args.scope,
        'verify': args.verify,
        'guard': args.guard,
        'direction': args.direction,
        'target': args.target,
        'iterations': args.iterations
    }
    
    # 检查 git 仓库
    if not Path('.git').exists():
        print("Error: Not a git repository. Autoresearch requires git.")
        sys.exit(1)
    
    # 运行引擎
    engine = AutonomousEngine(config)
    result = engine.run()
    
    # 保存结果
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nResults saved to {args.output}")
    
    # 返回退出码
    if result['status'] == 'completed' or result['status'] == 'target_reached':
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
