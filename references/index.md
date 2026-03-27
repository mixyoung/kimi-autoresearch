# Kimi Autoresearch 参考文档

## 快速开始

```
$kimi-autoresearch
Goal: Reduce type errors
Verify: tsc --noEmit 2>&1 | grep -c error
```

## 核心文档

| 文档 | 说明 |
|------|------|
| [quick-reference.md](quick-reference.md) | 常用命令速查 |
| [loop-protocol.md](loop-protocol.md) | Ralph Loop 协议详解 |

## 模式文档

| 模式 | 文档 | 用途 |
|------|------|------|
| Plan | [mode-plan.md](mode-plan.md) | 配置向导 |
| Debug | [mode-debug.md](mode-debug.md) | 科学调试 |
| Fix | [mode-fix.md](mode-fix.md) | 自动修复 |
| Security | [mode-security.md](mode-security.md) | 安全审计 |
| Ship | [mode-ship.md](mode-ship.md) | 发布工作流 |
| Scenario | [mode-scenario.md](mode-scenario.md) | 场景探索 |
| Predict | [mode-predict.md](mode-predict.md) | 多角色预测 |
| Learn | [mode-learn.md](mode-learn.md) | 文档引擎 |
| Exec | [mode-exec.md](mode-exec.md) | CI/CD 模式 |

## 高级主题

| 文档 | 说明 |
|------|------|
| [parallel-experiments.md](parallel-experiments.md) | 并行实验 |
| [web-search-protocol.md](web-search-protocol.md) | Web 搜索集成 |
| [session-resilience-protocol.md](session-resilience-protocol.md) | 会话弹性 |
| [i18n.md](i18n.md) | 国际化 |

## 对比与场景

| 文档 | 说明 |
|------|------|
| [COMPARISON.md](COMPARISON.md) | 与其他工具对比 |
| [scenario-guides.md](scenario-guides.md) | 使用场景指南 |
| [scenario-guides-detailed.md](scenario-guides-detailed.md) | 详细场景指南 |

## v2.0 重大变更

从 v1.x 迁移到 v2.0:

**使用方式**:
- v1.x: `python scripts/autoresearch_workflow.py --goal "..."`
- v2.0: `$kimi-autoresearch`

**架构**:
- v1.x: Python 脚本管理循环
- v2.0: Kimi Ralph Loop 自动处理

详见 [VERSION_2_MIGRATION.md](../VERSION_2_MIGRATION.md)
