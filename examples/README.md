# 配置示例

这些 JSON 配置文件展示了不同场景下的 kimi-autoresearch 用法。

## 快速使用

### 方法 1: 直接在 Kimi 中使用

```
$kimi-autoresearch
Goal: Reduce type errors
Verify: tsc --noEmit 2>&1 | grep -c error
Direction: lower
```

### 方法 2: 参考 JSON 配置

查看对应的 `.json` 文件，复制参数到 Kimi:

```
$kimi-autoresearch
Goal: Increase TypeScript test coverage to 90%
Scope: src/**/*.ts
Verify: npm test -- --coverage | grep 'All files' | awk '{print $2}' | tr -d '%'
Guard: npm run build && npm run lint
Direction: higher
Iterations: 30
Target: 90
```

## 示例列表

| 文件 | 场景 | 技术栈 |
|------|------|--------|
| [typescript-coverage.json](typescript-coverage.json) | 提升测试覆盖率 | TypeScript |
| [python-type-errors.json](python-type-errors.json) | 修复类型错误 | Python |
| [reduce-bundle-size.json](reduce-bundle-size.json) | 减少包大小 | JavaScript |
| [go-test-coverage.json](go-test-coverage.json) | 提升测试覆盖率 | Go |
| [rust-compile-time.json](rust-compile-time.json) | 减少编译时间 | Rust |
| [java-memory-usage.json](java-memory-usage.json) | 减少内存使用 | Java |
| [react-lighthouse.json](react-lighthouse.json) | 提升性能评分 | React |
| [docker-image-size.json](docker-image-size.json) | 减少镜像大小 | Docker |
| [ralph-loop-config.json](ralph-loop-config.json) | Ralph Loop 完整配置 | 通用 |

## 配置参数说明

### 必需参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `goal` | 目标描述 | `"Reduce type errors"` |
| `verify` | 验证命令（输出数字） | `"tsc --noEmit 2>&1 | grep -c error"` |

### 可选参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `scope` | 修改范围 | `"."` (当前目录) |
| `direction` | 优化方向 | `"lower"` |
| `guard` | 保护命令 | `null` |
| `iterations` | 最大迭代数 | `10` |
| `target` | 目标值 | `null` |
| `metric` | 指标名称 | `"metric"` |

### Ralph Loop 参数 (v2.0+)

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `loop_control.max_steps_per_turn` | 每轮最大步数 | `50` |
| `loop_control.max_retries_per_step` | 每步最大重试 | `3` |
| `loop_control.max_ralph_iterations` | Ralph 迭代数 | `0` |
| `agent_config.agent` | Agent 配置 | `"default"` |

## 完整示例

```json
{
  "goal": "Your goal here",
  "scope": "src/**/*",
  "metric": "metric name",
  "direction": "lower",
  "verify": "your-verify-command | grep -c pattern",
  "guard": "your-guard-command",
  "iterations": 20,
  "target": 0,
  "loop_control": {
    "max_steps_per_turn": 50,
    "max_retries_per_step": 3,
    "max_ralph_iterations": 20
  },
  "agent_config": {
    "agent": "default"
  }
}
```

## v2.0 注意

在 v2.0 中，只需在 Kimi 中输入:

```
$kimi-autoresearch
Goal: (从 JSON 复制)
Verify: (从 JSON 复制)
...
```

不需要运行 `python scripts/...` 命令。
