# Ralph Loop 集成总结

本文档总结了基于 [Kimi 官方循环控制文档](https://moonshotai.github.io/kimi-cli/zh/reference/kimi-command.html) 对 kimi-autoresearch 项目的优化。

## 新增特性

### 1. Ralph 循环协议支持

参考 Kimi CLI 的 `--max-ralph-iterations` 参数，实现了完整的 Ralph 循环协议支持：

- **停止信号**: 支持 `<choice>STOP</choice>` 标准停止信号
- **循环控制参数**:
  - `max_steps_per_turn`: 单轮最大步数 (默认: 50)
  - `max_retries_per_step`: 单步最大重试次数 (默认: 3)
  - `max_ralph_iterations`: Ralph 循环迭代次数 (0=关闭, -1=无限)

### 2. 子 Agent 配置支持

参考 Kimi CLI 的 `--agent` 和 `--agent-file` 参数，支持子 Agent 配置：

- **内置 Agent**: `default`, `okabe`
- **自定义 Agent**: 通过 `--agent-file` 指定自定义配置文件
- **互斥配置**: `agent` 和 `agent_file` 不能同时使用

### 3. 新增/修改的文件

| 文件 | 变更 | 说明 |
|------|------|------|
| `scripts/autoresearch_ralph.py` | 新增 | Ralph 循环控制工具 |
| `scripts/state_manager.py` | 修改 | 添加 loop_control 和 agent_config 支持 |
| `scripts/autoresearch_daemon.py` | 修改 | 添加 Ralph 循环参数和 Agent 配置支持 |
| `scripts/autoresearch_infinite.py` | 修改 | 添加 Ralph 循环支持 |
| `scripts/autoresearch_workflow.py` | 修改 | 添加 Ralph 循环参数支持 |
| `scripts/autoresearch_main.py` | 修改 | 添加 `ralph` 子命令 |
| `SKILL.md` | 修改 | 更新文档，添加 Ralph 循环说明 |
| `README.md` | 修改 | 添加新特性说明 |
| `examples/ralph-loop-config.json` | 新增 | Ralph 循环配置示例 |

## 使用方式

### 方式一：Kimi 交互模式（推荐）

使用 `$kimi-autoresearch` 触发，由 Kimi 直接执行迭代循环：

```
$kimi-autoresearch
Goal: Reduce type errors
Scope: src/**/*.ts
Verify: tsc --noEmit 2>&1 | grep -c error
Direction: lower
MaxStepsPerTurn: 30
MaxRetriesPerStep: 5
MaxRalphIterations: 100
Agent: okabe
```

### 方式二：命令行工具模式

使用 `python scripts/xxx.py` 运行辅助工具（初始化、查看状态等）：

```bash
# 查看当前 Ralph 循环状态
python scripts/autoresearch_ralph.py status

# 设置循环控制参数
python scripts/autoresearch_ralph.py set-loop \
  --max-steps 30 \
  --max-retries 5 \
  --max-ralph 100

# 设置 agent 配置
python scripts/autoresearch_ralph.py set-agent --agent okabe

# 检查是否应该停止
python scripts/autoresearch_ralph.py check-stop --current-metric 42

# 手动发出停止信号
python scripts/autoresearch_ralph.py stop --reason "Target reached"
```

### 方式三：后台 Daemon 模式

先通过命令行配置，然后在 Kimi 中启动 Background Agent：

```bash
# 1. 命令行：生成 Daemon 配置
python scripts/autoresearch_daemon.py start \
  --goal "Refactor codebase" \
  --scope "src/" \
  --verify "npm test 2>&1 | grep -c failing" \
  --direction lower \
  --iterations 100 \
  --max-steps-per-turn 30 \
  --max-retries-per-step 5 \
  --max-ralph-iterations 100 \
  --agent okabe

# 这会生成 .autoresearch-daemon-prompt.txt 文件
```

```python
# 2. Kimi 中：启动 Background Agent
Agent(
    description="Autoresearch daemon",
    prompt=read(".autoresearch-daemon-prompt.txt"),
    run_in_background=True
)
```

## 状态文件结构

更新后的 `autoresearch-state.json` 包含新的配置字段：

```json
{
  "iteration": 10,
  "baseline": 47,
  "best": 38,
  "loop_control": {
    "max_steps_per_turn": 50,
    "max_retries_per_step": 3,
    "max_ralph_iterations": 100
  },
  "agent_config": {
    "agent": "okabe",
    "agent_file": null
  }
}
```

## 与 Kimi CLI 的对应关系

| Kimi CLI 参数 | kimi-autoresearch 对应 |
|---------------|------------------------|
| `--max-steps-per-turn` | `--max-steps-per-turn` / `max_steps_per_turn` |
| `--max-retries-per-step` | `--max-retries-per-step` / `max_retries_per_step` |
| `--max-ralph-iterations` | `--max-ralph-iterations` / `max_ralph_iterations` |
| `--agent` | `--agent` |
| `--agent-file` | `--agent-file` |

## 停止条件

Ralph 循环会在以下情况下停止：

1. **目标达成**: 当前指标达到或超过目标值
2. **迭代限制**: 达到 `max_ralph_iterations` 或 `iterations` 限制
3. **停止信号**: 检测到 `<choice>STOP</choice>` 输出
4. **真正卡住**: 5+ 连续丢弃且 2+ 次转向

## 参考文档

- [Kimi CLI 循环控制文档](https://moonshotai.github.io/kimi-cli/zh/reference/kimi-command.html)
- [SKILL.md](SKILL.md) - 详细使用说明
- [examples/ralph-loop-config.json](examples/ralph-loop-config.json) - 配置示例
