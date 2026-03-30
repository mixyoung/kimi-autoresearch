# Kimi Autoresearch

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/mixyoung/kimi-autoresearch/releases)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Last Commit](https://img.shields.io/github/last-commit/mixyoung/kimi-autoresearch.svg)](https://github.com/mixyoung/kimi-autoresearch/commits/main)
[![GitHub Stars](https://img.shields.io/github/stars/mixyoung/kimi-autoresearch?style=social)](https://github.com/mixyoung/kimi-autoresearch/stargazers)

[![Code Size](https://img.shields.io/github/languages/code-size/mixyoung/kimi-autoresearch.svg)](https://github.com/mixyoung/kimi-autoresearch)
[![Issues](https://img.shields.io/github/issues/mixyoung/kimi-autoresearch.svg)](https://github.com/mixyoung/kimi-autoresearch/issues)
[![Downloads](https://img.shields.io/github/downloads/mixyoung/kimi-autoresearch/total.svg)](https://github.com/mixyoung/kimi-autoresearch/releases)
[![Release Date](https://img.shields.io/github/release-date/mixyoung/kimi-autoresearch.svg)](https://github.com/mixyoung/kimi-autoresearch/releases)

面向 **Kimi Code CLI** 的自主迭代优化工具。类似 [codex-autoresearch](https://github.com/leolilinxiao/codex-autoresearch)，但专为 Kimi 打造。

## ❤️ 赞助商

<details>
<summary>点击展开 - 支持本项目</summary>

### 🚀 MiniMax - Mini 价格 Max 性能

[![MiniMax Banner](https://img.shields.io/badge/MiniMax-M2.7%20模型-red?style=for-the-badge)](https://platform.minimaxi.com/subscribe/coding-plan?code=A5zNv8IduW&source=link)

**MiniMax M2.7** 是 MiniMax 首个深度参与自我迭代的模型，可自主构建复杂 Agent Harness，并基于 Agent Teams、复杂 Skills、Tool Search Tool 等能力完成高复杂度生产力任务。

👉 [立即订阅 MiniMax](https://platform.minimaxi.com/subscribe/coding-plan?code=A5zNv8IduW&source=link)
🎁 **专属优惠**：点击上方链接享 MiniMax Token Plan 专属 88 折优惠！

</details>

## 快速开始

```
$kimi-autoresearch
Goal: 减少类型错误
Verify: tsc --noEmit 2>&1 | grep -c error
```

就这么简单。Kimi 的 Ralph Loop 会自动接管并迭代。

## 工作原理

1. **你提供目标** → `$kimi-autoresearch`
2. **Kimi 测量基线** → 运行验证命令
3. **Kimi 进入 Ralph Loop** → 提示词自动重复
4. **每次迭代** → 修改 → 验证 → 保留/丢弃 → 记录
5. **循环继续** → 直到目标达成或输出 `<choice>STOP</choice>`

## 使用示例

### 基础用法（无限迭代）

```
$kimi-autoresearch
Goal: 减少类型错误
Verify: tsc --noEmit 2>&1 | grep -c error
```

**默认无限迭代**，直到目标达成或你手动停止。

### 限制迭代次数

```
$kimi-autoresearch
Goal: 快速优化
Verify: npm test 2>&1 | grep -c failing
Iterations: 20
```

运行 20 次后自动停止。

### 完整配置（带目标值）

```
$kimi-autoresearch
Goal: 提升测试覆盖率到 90%
Scope: src/**/*.ts
Verify: npm test -- --coverage | grep "All files"
Guard: npm run build
Direction: higher
Target: 90
# 达到 90% 自动停止，或无限运行直到达成
```

### 类型安全

```
$kimi-autoresearch
Goal: 消除所有 `any` 类型
Scope: src/**/*.ts
Verify: grep -r "any" src/**/*.ts | wc -l
Direction: lower
```

### 测试覆盖率

```
$kimi-autoresearch
Goal: 提升覆盖率到 90%
Verify: npm test -- --coverage | grep "All files"
Guard: npm test
Direction: higher
Target: 90
```

## 参数说明

| 参数 | 必需 | 默认值 | 说明 |
|-----------|------|---------|-------------|
| `Goal` | ✅ | - | 要达成的目标 |
| `Verify` | ✅ | - | 测量指标的命令（必须输出数字） |
| `Scope` | ❌ | 当前目录 | 要修改的文件 |
| `Direction` | ❌ | lower | higher/lower 表示更好 |
| `Guard` | ❌ | 无 | 安全检查命令 |
| `Iterations` | ❌ | 无限 | 最大迭代次数（不设则无限运行） |
| `Target` | ❌ | 无 | 达到此值时停止 |
| `MaxRalphIterations` | ❌ | 0 | Ralph 循环限制（0=无限制） |

## 无限迭代（默认）

kimi-autoresearch **默认无限迭代**，真正体现"自动化研究"的精神：

```
$kimi-autoresearch
Goal: 优化代码
Verify: npm test 2>&1 | grep -c failing
```

然后你可以：
- **去睡觉** - 让它整夜运行
- **去开会** - 让它在后台优化
- **去做其他事** - 定期查看进度

它会一直运行直到：
1. 目标达成（如有设置 Target）
2. 你手动停止（Ctrl+C）
3. 遇到无法恢复的错误

这才是真正的自主优化！

## 迭代流程

每次迭代遵循以下协议：

1. **读取上下文** - 检查状态、历史、git 日志
2. **形成假设** - 提出一个具体的改进想法
3. **执行修改** - 进行一次原子代码修改
4. **提交** - `git commit -m "experiment: ..."`
5. **验证** - 运行验证命令
6. **决策** - 保留（有改善）/ 丢弃（回退）/ 重做
7. **记录** - 记录结果到 TSV
8. **重复** - Ralph Loop 自动继续

## 停止条件

Kimi 在以下情况输出 `<choice>STOP</choice>`：
- 目标指标达成
- 达到最大迭代次数
- 真正卡住（5+ 次丢弃，2+ 次转向）

## 文件说明

- `autoresearch-results.tsv` - 迭代日志
- `autoresearch-state.json` - 当前状态
- `autoresearch-lessons.md` - 跨运行学习记录
- `autoresearch-report.md` - 最终摘要

## 后台模式

长时间运行的任务：

```python
Agent(
    description="Autoresearch",
    prompt="""
$kimi-autoresearch
Goal: 重构整个代码库
Verify: npm test 2>&1 | grep -c failing
# 不设置 Iterations = 无限运行，可运行 24 小时
""",
    run_in_background=True
)
```

## 与 codex-autoresearch 对比

| 功能 | codex-autoresearch | kimi-autoresearch |
|---------|-------------------|-------------------|
| 触发方式 | `$codex-autoresearch` | `$kimi-autoresearch` ✅ |
| 循环控制 | 原生 | Kimi Ralph Loop ✅ |
| 状态管理 | 文件 | 文件 ✅ |
| Git 集成 | 原生 | 原生 ✅ |
| 后台模式 | Agent | Agent ✅ |

## 要求

- Kimi Code CLI
- Git 仓库
- 输出数字的验证命令

## 许可证

MIT
