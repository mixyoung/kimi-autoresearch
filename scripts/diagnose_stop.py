#!/usr/bin/env python3
"""
诊断自动停止问题

检查可能导致 <choice>STOP</choice> 的原因
"""
import json
import os
import sys

STATE_FILE = "autoresearch-state.json"
RESULTS_FILE = "autoresearch-results.tsv"


def diagnose():
    """诊断停止问题"""
    print("=" * 60)
    print("  Kimi Autoresearch 停止问题诊断")
    print("=" * 60)
    print()
    
    # 检查状态文件
    if not os.path.exists(STATE_FILE):
        print("❌ 未找到状态文件 autoresearch-state.json")
        print("   建议：先运行一次 $kimi-autoresearch 初始化")
        return
    
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
    
    print("📋 当前状态：")
    print(f"   版本: {state.get('version', 'unknown')}")
    print(f"   当前迭代: {state.get('iteration', 0)}")
    print(f"   连续丢弃: {state.get('consecutive_discards', 0)}")
    print(f"   转向次数: {state.get('pivot_count', 0)}")
    print()
    
    # 检查配置
    config = state.get('config', {})
    print("⚙️  配置：")
    print(f"   目标: {config.get('goal', '未设置')}")
    print(f"   目标值 (target): {config.get('target', '未设置')}")
    print(f"   最大迭代 (iterations): {config.get('iterations', '无限 (0或未设置)')}")
    print(f"   方向: {config.get('direction', 'lower')}")
    print()
    
    # 检查 loop_control
    loop_control = state.get('loop_control', {})
    print("🔄 Ralph Loop 控制：")
    max_ralph = loop_control.get('max_ralph_iterations', 0)
    print(f"   Max Ralph Iterations: {max_ralph} ({'无限' if max_ralph == 0 else '限制 ' + str(max_ralph)})")
    print(f"   Max Steps Per Turn: {loop_control.get('max_steps_per_turn', 50)}")
    print(f"   Max Retries Per Step: {loop_control.get('max_retries_per_step', 3)}")
    print()
    
    # 分析可能的停止原因
    print("🔍 可能的停止原因分析：")
    
    reasons = []
    
    # 1. 检查 Ralph limit
    current_iter = state.get('iteration', 0)
    if max_ralph > 0 and current_iter >= max_ralph:
        reasons.append(f"✅ 达到 Ralph 迭代限制: {current_iter}/{max_ralph}")
    elif max_ralph > 0:
        reasons.append(f"⚠️  接近 Ralph 迭代限制: {current_iter}/{max_ralph}")
    
    # 2. 检查 max_iterations
    max_iter = config.get('iterations', 0)
    if max_iter > 0 and current_iter >= max_iter:
        reasons.append(f"✅ 达到最大迭代限制: {current_iter}/{max_iter}")
    elif max_iter > 0:
        reasons.append(f"⚠️  设置了迭代限制: {max_iter} 次")
    
    # 3. 检查 target
    if config.get('target') is not None:
        reasons.append(f"⚠️  设置了目标值: {config['target']} (达到会停止)")
    
    # 4. 检查 stuck
    discards = state.get('consecutive_discards', 0)
    pivots = state.get('pivot_count', 0)
    if discards >= 5 and pivots >= 2:
        reasons.append(f"✅ 卡住检测触发: {discards} 次丢弃, {pivots} 次转向")
    elif discards >= 3:
        reasons.append(f"⚠️  接近卡住: {discards} 次连续丢弃")
    
    if not reasons:
        print("   ✓ 配置正常，应该无限运行")
        print("   如果仍然自动停止，可能是 Kimi 的 Ralph Loop 限制")
    else:
        for r in reasons:
            print(f"   {r}")
    
    print()
    
    # 检查结果文件
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r') as f:
            lines = f.readlines()
        print(f"📊 结果日志: {len(lines)} 行 (包含表头)")
        if len(lines) > 1:
            print("   最近记录：")
            for line in lines[-3:]:
                print(f"     {line.strip()}")
    else:
        print("📊 无结果日志")
    
    print()
    print("=" * 60)
    print("💡 建议：")
    print()
    print("如果要无限运行，请确保：")
    print("  1. 不设置 Iterations 参数")
    print("  2. 不设置 Target 参数（除非想达到目标停止）")
    print("  3. MaxRalphIterations: 0 或留空")
    print()
    print("在 Kimi 中使用时输入：")
    print("```")
    print("$kimi-autoresearch")
    print("Goal: 你的目标")
    print("Verify: 你的验证命令")
    print("# 不要设置 Iterations 或 Target，除非想限制")
    print("```")
    print("=" * 60)


if __name__ == '__main__':  # pragma: no cover
    diagnose()
