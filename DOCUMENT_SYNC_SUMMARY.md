# 文档同步更新摘要

本文档记录了基于 Kimi 官方循环控制文档对项目进行优化后的所有文档更新。

## 更新范围

### 1. 核心文档

| 文档 | 更新内容 |
|------|----------|
| `SKILL.md` | 添加 Ralph Loop 章节、子 Agent 配置、CLI 工具使用说明 |
| `README.md` | 添加 Ralph 循环控制、子 Agent 配置特性，更新对比表格 |
| `RALPH_LOOP_INTEGRATION.md` | 新增，详细描述 Ralph 循环集成 |
| `DOCUMENT_SYNC_SUMMARY.md` | 本文档，汇总所有更新 |

### 2. 参考文档

| 文档 | 更新内容 |
|------|----------|
| `references/quick-reference.md` | 添加 Ralph Loop 命令、停止信号说明、文件位置更新 |
| `references/loop-protocol.md` | 添加 Ralph Loop 步骤、配置项、停止信号检查 |
| `references/mode-exec.md` | 添加 Ralph Loop 配置示例和参数说明 |

### 3. 示例配置

| 文件 | 更新内容 |
|------|----------|
| `examples/ralph-loop-config.json` | 新增，完整的 Ralph 循环配置示例 |
| `examples/typescript-coverage.json` | 添加 loop_control 和 agent_config 注释 |
| `examples/python-type-errors.json` | 添加 loop_control 注释 |
| `examples/reduce-bundle-size.json` | 添加 loop_control 注释 |

### 4. 脚本文件

| 脚本 | 更新内容 |
|------|----------|
| `scripts/autoresearch_ralph.py` | 新增，Ralph 循环控制工具 |
| `scripts/state_manager.py` | 添加 loop_control 和 agent_config 支持 |
| `scripts/autoresearch_daemon.py` | 添加 Ralph 循环参数和 Agent 配置支持 |
| `scripts/autoresearch_infinite.py` | 添加 Ralph 循环支持 |
| `scripts/autoresearch_workflow.py` | 添加 Ralph 循环参数支持 |
| `scripts/autoresearch_main.py` | 添加 `ralph` 子命令 |

## 使用方式一致性

所有文档现在明确区分两种使用方式：

### 方式一：Kimi 交互模式（主要）
```
$kimi-autoresearch
Goal: Reduce type errors
MaxRalphIterations: 50
MaxStepsPerTurn: 30
Agent: okabe
```

### 方式二：CLI 工具模式（辅助）
```bash
# 查看状态
python scripts/autoresearch_ralph.py status

# 设置参数
python scripts/autoresearch_ralph.py set-loop --max-steps 30 --max-ralph 100

# 设置 Agent
python scripts/autoresearch_ralph.py set-agent --agent okabe
```

## 参数命名一致性

| 概念 | Kimi 交互模式 | CLI 参数 | JSON 字段 |
|------|--------------|----------|-----------|
| 单轮最大步数 | `MaxStepsPerTurn` | `--max-steps-per-turn` | `max_steps_per_turn` |
| 单步最大重试 | `MaxRetriesPerStep` | `--max-retries-per-step` | `max_retries_per_step` |
| Ralph 迭代次数 | `MaxRalphIterations` | `--max-ralph-iterations` | `max_ralph_iterations` |
| 内置 Agent | `Agent` | `--agent` | `agent` |
| 自定义 Agent | `AgentFile` | `--agent-file` | `agent_file` |

## 停止信号

所有文档统一使用 `<choice>STOP</choice>` 作为 Ralph 循环的标准停止信号。

## 状态文件结构

更新后的 `autoresearch-state.json` 包含：
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

## 验证清单

- [x] SKILL.md 更新了 Ralph Loop 和 Agent 配置
- [x] README.md 添加了新特性说明
- [x] quick-reference.md 添加了 Ralph 命令
- [x] loop-protocol.md 添加了 Ralph 步骤
- [x] mode-exec.md 添加了 Ralph 配置
- [x] 所有示例 JSON 添加了 loop_control 注释
- [x] 参数命名在所有文档中保持一致
- [x] 使用方式（Kimi vs CLI）明确区分
- [x] 停止信号 `<choice>STOP</choice>` 统一说明

## 参考链接

- [Kimi CLI 循环控制文档](https://moonshotai.github.io/kimi-cli/zh/reference/kimi-command.html)
- [SKILL.md](SKILL.md) - 主要使用文档
- [RALPH_LOOP_INTEGRATION.md](RALPH_LOOP_INTEGRATION.md) - 集成详情
