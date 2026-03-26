# Kimi Autoresearch vs 参考项目对比

本文档详细比较 kimi-autoresearch 与两个参考项目的差异。

## 参考项目

1. **codex-autoresearch** (leo-lilinxiao) - OpenAI Codex 适配版
2. **autoresearch** (uditgoenka) - Claude Code 适配版

---

## 核心循环对比

| 特性 | Karpathy | codex-autoresearch | uditgoenka | **kimi-autoresearch** |
|------|----------|-------------------|------------|----------------------|
| **核心循环** | modify → verify → keep/discard → repeat | ✅ 完整 | ✅ 完整 | ✅ **完整** |
| **作用域读取** | 单文件 | 所有文件+git历史 | 所有文件+日志 | **所有文件+日志** |
| **历史感知** | Git log | Git log + TSV | Git log + TSV | **Git log + TSV** |
| **回滚机制** | git reset | git revert | git revert | **git revert** |
| **卡住检测** | ❌ | ✅ REFINE/PIVOT | ✅ 5次后升级 | **✅ 5次后升级** |
| **崩溃恢复** | ❌ 手动 | ✅ 自动 | ✅ 自动修复 | **✅ 自动修复** |

---

## 功能对比

### 模式数量

| 模式 | Karpathy | codex | uditgoenka | **kimi** |
|------|----------|-------|-----------|---------|
| Loop | ✅ | ✅ | ✅ | ✅ |
| Plan | ❌ | ✅ | ✅ | ✅ |
| Debug | ❌ | ✅ | ✅ | ✅ |
| Fix | ❌ | ✅ | ✅ | ✅ |
| Security | ❌ | ✅ | ✅ | ✅ |
| Ship | ❌ | ✅ | ✅ | ✅ |
| Exec | ❌ | ✅ | ✅ | ✅ |
| Scenario | ❌ | ❌ | ✅ | ✅ |
| Predict | ❌ | ❌ | ✅ | ✅ |
| Learn | ❌ | ❌ | ✅ | ✅ |
| **总计** | **1** | **7** | **9** | **10** ✅ |

### 验证与安全

| 特性 | codex | uditgoenka | **kimi** |
|------|-------|-----------|---------|
| Guard 命令 | ✅ | ✅ | ✅ |
| Guard 恢复 | ✅ | ✅ | ✅ |
| 噪音处理 | ✅ 多运行 | ✅ 中位数 | ⚠️ **基础** |
| 前置检查 | ✅ | ⚠️ | ✅ |

### Git 集成

| 特性 | codex | uditgoenka | **kimi** |
|------|-------|-----------|---------|
| 提交前缀 | `experiment:` | `experiment:` | `experiment:` |
| 失败实验 | git revert | git revert | git revert |
| 历史读取 | git log + diff | git log | git log + diff |
| 并行实验 | ✅ worktree | ❌ | ✅ worktree |

---

## kimi-autoresearch 优势

### 1. 模式数量最多
- **10种模式** vs 7-9种
- 独有组合：Scenario + Predict + Learn

### 2. 统一 CLI 入口
```bash
# kimi - 统一入口
python scripts/autoresearch_main.py <command>

# codex - 分散脚本
python scripts/autoresearch_<name>.py
```

### 3. 实用工具齐全
- `stats` - 统计信息
- `export` - 导出结果
- `clean` - 清理文件
- `config` - 配置管理

### 4. 完整工具链
- GitHub Actions 即用配置
- 打包脚本 (package.sh)
- Windows 安装脚本

### 5. 国际化支持
- 中英文双语
- 可扩展翻译系统

---

## 参考项目优势

### codex-autoresearch 有但 kimi 没有：

1. **i18n (8种语言)** - 日语、法语、德语等
2. **会话弹性** - 自动重新锚定、会话分割
3. **更复杂后台** - 完整 daemon 进程
4. **跨仓库实验** - 多仓库同时实验

### uditgoenka 有但 kimi 没有：

1. **MCP 支持** - Model Context Protocol
2. **场景指南** - 10个详细场景示例
3. **噪音处理** - 多运行中位数
4. **对比文档** - 详细的功能对比

---

## 建议改进

### 高优先级
1. **会话弹性协议** - 实现自动重新锚定
2. **噪音处理** - 多运行验证
3. **场景指南** - 添加具体示例

### 中优先级
4. **MCP 集成** - 外部工具集成
5. **更多语言** - 扩展 i18n

### 低优先级
6. **Daemon 后台** - 完全脱离运行

---

## 总结

| 维度 | kimi 评分 | 说明 |
|------|----------|------|
| 功能完整度 | ⭐⭐⭐⭐⭐ (95%) | 10种模式，功能齐全 |
| 鲁棒性 | ⭐⭐⭐⭐ (80%) | 缺少会话弹性 |
| 文档质量 | ⭐⭐⭐⭐ (85%) | 缺少场景指南 |
| 易用性 | ⭐⭐⭐⭐⭐ (90%) | 统一 CLI，中文支持 |
| CI/CD | ⭐⭐⭐⭐⭐ (100%) | GitHub Actions 完整 |

**总体**: kimi-autoresearch 在功能完整度上领先，在鲁棒性和文档丰富度上有提升空间。
