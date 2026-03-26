# Kimi Autoresearch - 功能导航

快速找到你需要的功能和文档。

---

## 🚀 快速开始

| 我想... | 查看文档 | 使用命令 |
|---------|---------|---------|
| 第一次使用 | [README.md](../README.md) | `$kimi-autoresearch` |
| 快速查命令 | [quick-reference.md](quick-reference.md) | - |
| 了解核心循环 | [loop-protocol.md](loop-protocol.md) | - |
| 看使用场景 | [scenario-guides-detailed.md](scenario-guides-detailed.md) | - |

---

## 🎯 按目标查找

### 代码优化

| 目标 | 模式 | 文档 | 示例 |
|------|------|------|------|
| 添加类型注解 | Loop | [TypeScript类型安全](scenario-guides-detailed.md#场景-1typescript-类型安全改进) | `$kimi-autoresearch` |
| 提升测试覆盖 | Loop | [Python测试覆盖](scenario-guides-detailed.md#场景-2python-测试覆盖率提升) | `$kimi-autoresearch` |
| 优化性能 | Loop | [性能优化](scenario-guides-detailed.md#场景-3性能优化api-响应时间) | `$kimi-autoresearch` |
| 消除重复代码 | Loop | [代码重构](scenario-guides-detailed.md#场景-4代码重构消除重复) | `$kimi-autoresearch` |
| 修复安全漏洞 | Loop | [安全漏洞修复](scenario-guides-detailed.md#场景-5安全漏洞修复) | `$kimi-autoresearch` |
| 完善文档 | Loop | [文档完善](scenario-guides-detailed.md#场景-6文档完善) | `$kimi-autoresearch` |
| 统一代码风格 | Loop | [代码格式化](scenario-guides-detailed.md#场景-7代码格式化统一) | `$kimi-autoresearch` |
| 完善错误处理 | Loop | [错误处理完善](scenario-guides-detailed.md#场景-8错误处理完善) | `$kimi-autoresearch` |
| API版本迁移 | Loop | [API版本迁移](scenario-guides-detailed.md#场景-9api-版本迁移) | `$kimi-autoresearch` |
| 内存优化 | Loop | [内存优化](scenario-guides-detailed.md#场景-10内存优化) | `$kimi-autoresearch` |

### 特殊任务

| 目标 | 模式 | 文档 |
|------|------|------|
| 调试bug | Debug | [Debug模式](mode-debug.md) |
| 自动修复错误 | Fix | [Fix模式](mode-fix.md) |
| 安全审计 | Security | [Security模式](mode-security.md) |
| 发布代码 | Ship | [Ship模式](mode-ship.md) |
| 生成测试场景 | Scenario | [Scenario模式](mode-scenario.md) |
| 多角色预测 | Predict | [Predict模式](mode-predict.md) |
| 文档维护 | Learn | [Learn模式](mode-learn.md) |
| CI/CD集成 | Exec | [Exec模式](mode-exec.md) |

---

## 🛠️ 工具脚本索引

### 核心工具

| 脚本 | 功能 | 使用场景 |
|------|------|---------|
| `autoresearch_init_run.py` | 初始化运行 | 开始新任务 |
| `autoresearch_decision.py` | 决策辅助 | keep/discard判断 |
| `autoresearch_health_check.py` | 健康检查 | 环境验证 |
| `check_git.py` | Git操作 | commit/revert |
| `get_baseline.py` | 获取基线 | 测量指标 |
| `log_result.py` | 记录结果 | 保存迭代数据 |

### 无人值守工具 ⭐

| 脚本 | 功能 | 使用场景 |
|------|------|---------|
| `autoresearch_daemon.py` | Daemon模式 | 后台运行 |
| `autoresearch_infinite.py` | 无限运行 | 突破24小时限制 |
| `autoresearch_resilience.py` | 会话弹性 | 长时间运行稳定 |
| `autoresearch_monitor.py` | 实时监控 | 进度可视化 |

### 高级工具

| 脚本 | 功能 | 使用场景 |
|------|------|---------|
| `autoresearch_parallel.py` | 并行实验 | 多假设测试 |
| `autoresearch_web_search.py` | Web搜索 | 卡住时搜索 |
| `autoresearch_version.py` | 版本管理 | 发布管理 |
| `autoresearch_lessons.py` | 经验管理 | 跨运行学习 |
| `autoresearch_utils.py` | 实用工具 | 统计/清理/导出 |

---

## 📊 监控与报告

| 功能 | 命令 | 输出 |
|------|------|------|
| HTML仪表板 | `autoresearch_monitor.py dashboard` | `autoresearch-dashboard.html` |
| 文本报告 | `autoresearch_monitor.py report` | 终端输出 |
| 实时监控 | `autoresearch_monitor.py watch` | 实时更新 |
| 弹性报告 | `autoresearch_resilience.py report` | 终端输出 |
| 最终结果 | `generate_report.py` | `autoresearch-report.md` |

---

## 🛡️ 长时间运行指南

### 运行 < 1小时
```bash
$kimi-autoresearch
Goal: Quick optimization
Iterations: 20
```

### 运行 1-24小时
```bash
python scripts/autoresearch_daemon.py start \
  --goal "Medium task" \
  --iterations 100

Agent(
    description="Daemon runner",
    prompt=read(".autoresearch-daemon-prompt.txt"),
    run_in_background=True
)
```

### 运行 > 24小时（无限）
```bash
python scripts/autoresearch_infinite.py start \
  --goal "Long running task" \
  --verify "..."

Agent(
    description="Infinite runner",
    prompt=read(".autoresearch-infinite-prompt.txt"),
    run_in_background=True
)
# 自动接力，永不停歇
```

---

## 📚 详细文档

### 模式文档
- [mode-plan.md](mode-plan.md) - 配置向导
- [mode-debug.md](mode-debug.md) - 科学调试
- [mode-fix.md](mode-fix.md) - 自动修复
- [mode-security.md](mode-security.md) - 安全审计
- [mode-ship.md](mode-ship.md) - 发布工作流
- [mode-scenario.md](mode-scenario.md) - 场景探索
- [mode-predict.md](mode-predict.md) - 多角色预测
- [mode-learn.md](mode-learn.md) - 文档维护
- [mode-exec.md](mode-exec.md) - CI/CD执行

### 协议文档
- [loop-protocol.md](loop-protocol.md) - 核心迭代协议
- [session-resilience-protocol.md](session-resilience-protocol.md) - 会话弹性
- [parallel-experiments.md](parallel-experiments.md) - 并行实验
- [web-search-protocol.md](web-search-protocol.md) - Web搜索
- [pivot-protocol.md](pivot-protocol.md) - 卡住恢复

### 参考文档
- [COMPARISON.md](COMPARISON.md) - 项目对比
- [PROJECT_COMPARISON.md](PROJECT_COMPARISON.md) - 详细对比
- [scenario-guides-detailed.md](scenario-guides-detailed.md) - 10个场景
- [quick-reference.md](quick-reference.md) - 快速参考

---

## 🆘 故障排除

| 问题 | 解决方案 | 文档 |
|------|---------|------|
| 上下文压缩 | 重新锚定协议 | [会话弹性](session-resilience-protocol.md) |
| 卡住不前进 | 切换策略 | [pivot-protocol.md](pivot-protocol.md) |
| 状态不一致 | 一致性检查 | `autoresearch_resilience.py check` |
| 长时间运行 | 自动接力 | [无限模式](#长时间运行指南) |
| 监控进度 | HTML仪表板 | `autoresearch_monitor.py dashboard` |

---

## 🔗 相关链接

- [GitHub 仓库](https://github.com/mixyoung/kimi-autoresearch)
- [Releases](https://github.com/mixyoung/kimi-autoresearch/releases)
- [Issues](https://github.com/mixyoung/kimi-autoresearch/issues)
- [Kimi CLI 文档](https://moonshotai.github.io/kimi-cli/)

---

*最后更新: 2026-03-26*
