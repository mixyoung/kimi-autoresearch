# Ralph Loop 重构总结

## 重构目标
将项目从"手动循环控制"迁移到"依赖 Kimi Ralph Loop 机制"。

## 主要变更

### 1. 重构 workflow.py

**Before**: 手动 for 循环控制迭代
```python
def workflow_loop(config, baseline):
    for i in range(1, iteration_limit + 1):
        # 检查 session split
        # 检查 protocol fingerprint
        # 执行 iteration
        # 检查停止条件
        # 检查卡住
```

**After**: 生成 Ralph Loop 配置和 Prompt
```python
def generate_ralph_prompt(config, baseline) -> str:
    """生成 Ralph Loop 配置和初始提示"""
    # 返回给 Kimi 的完整 Prompt
    # Kimi 的 Ralph Loop 处理迭代控制
```

### 2. 优化 autoresearch_ralph.py

**新增功能**:
- `generate_ralph_prompt()` - 统一 Prompt 生成
- `prompt` 命令 - 随时生成 Ralph Loop Prompt
- 简化的状态管理

### 3. 简化 state_manager.py

**移除**:
- 手动迭代计数逻辑
- 复杂的停止条件检查

**保留**:
- 轻量级状态存储
- `update-status` 命令（供 Ralph Loop 调用）
- loop_control / agent_config 管理

### 4. 更新文档

**SKILL.md 变更**:
- 明确说明"使用 Ralph Loop 机制"
- 区分"Setup Phase"和"Ralph Loop Phase"
- 强调"Single Iteration Protocol"概念
- 更新 Helper Scripts 说明

## 架构对比

### Before (手动循环)
```
User -> workflow.py -> for loop -> iterations
                    ^
                    手动控制所有逻辑
```

### After (Ralph Loop)
```
User -> workflow.py -> Generate Prompt -> Kimi Ralph Loop -> Iterations
         (Setup only)                      (Kimi handles loop)
```

## 好处

1. **简化代码**: 移除约 200+ 行循环控制代码
2. **增强可靠性**: 依赖 Kimi 官方测试过的循环机制
3. **专注价值**: 研究协议逻辑更清晰
4. **统一架构**: 所有模式使用同一套 Ralph Loop 机制

## 使用方式变更

### Before
```bash
python scripts/autoresearch_workflow.py \
    --goal "Reduce errors" \
    --verify "..."
# 脚本内部执行循环
```

### After
```bash
python scripts/autoresearch_workflow.py \
    --goal "Reduce errors" \
    --verify "..." \
    --max-ralph-iterations 50
# 脚本生成 Prompt，复制到 Kimi 执行 Ralph Loop
```

## 文件变更

| 文件 | 变更 | 说明 |
|------|------|------|
| `scripts/autoresearch_workflow.py` | 重写 | 从循环控制改为 Prompt 生成 |
| `scripts/autoresearch_ralph.py` | 优化 | 添加统一 Prompt 生成 |
| `scripts/state_manager.py` | 简化 | 移除手动循环逻辑 |
| `SKILL.md` | 更新 | 反映 Ralph Loop 工作方式 |
| `REFACTOR_SUMMARY.md` | 新增 | 本文档 |

## 向后兼容性

- 所有现有配置仍然兼容
- JSON 配置文件格式不变
- 状态文件自动兼容（version 2.0）

## 下一步

1. 测试重构后的 workflow
2. 更新 references/loop-protocol.md
3. 考虑移除不再需要的 resilience 检查（由 Ralph Loop 处理）
