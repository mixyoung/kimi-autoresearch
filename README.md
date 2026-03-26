# Kimi Autoresearch

[![version](https://img.shields.io/badge/version-1.0.2-blue.svg)](https://github.com/mixyoung/kimi-autoresearch/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GitHub stars](https://img.shields.io/github/stars/mixyoung/kimi-autoresearch.svg?style=social)](https://github.com/mixyoung/kimi-autoresearch/stargazers)

[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/mixyoung/kimi-autoresearch/autoresearch.yml?branch=main)](https://github.com/mixyoung/kimi-autoresearch/actions)
[![GitHub last commit](https://img.shields.io/github/last-commit/mixyoung/kimi-autoresearch.svg)](https://github.com/mixyoung/kimi-autoresearch/commits/main)
[![GitHub repo size](https://img.shields.io/github/repo-size/mixyoung/kimi-autoresearch.svg)](https://github.com/mixyoung/kimi-autoresearch)
[![GitHub downloads](https://img.shields.io/github/downloads/mixyoung/kimi-autoresearch/total.svg)](https://github.com/mixyoung/kimi-autoresearch/releases)

一个受 [Karpathy 的 autoresearch](https://karpathy.ai/) 启发的自动化研究工具，专为 **Kimi Code CLI** 设计。

通过 **modify → verify → retain or discard → repeat** 的循环，自主优化代码、修复错误、提升性能。

## ✨ 特性

- 🔁 **自主迭代循环** - 自动修改、验证、回滚
- 🎯 **10 种工作模式** - Loop/Plan/Debug/Fix/Security/Ship/Scenario/Predict/Learn/Exec
- ⚡ **并行实验** - Git worktree 同时测试多个假设
- 🔍 **Web 搜索集成** - 卡住时自动搜索解决方案
- 📊 **决策智能** - 自动判断是否保留修改
- 📝 **完整日志** - TSV 格式记录每次迭代
- 🚀 **CI/CD 就绪** - GitHub Actions 工作流支持
- 🌐 **Kimi 原生** - 专为 Kimi Code CLI 优化
- 💻 **跨平台** - 支持 Windows、macOS、Linux
- 🌍 **国际化** - 支持中英文切换

## 📦 安装

### 方法一：作为 Kimi Skill 安装

```bash
# 克隆到你的项目
cd your-project
mkdir -p .agents/skills
git clone https://github.com/mixyoung/kimi-autoresearch.git .agents/skills/kimi-autoresearch
```

### 方法二：全局安装 (Linux/macOS)

```bash
# 克隆到用户目录
git clone https://github.com/mixyoung/kimi-autoresearch.git ~/.agents/skills/kimi-autoresearch
```

### 方法三：Windows 安装（推荐）

**方式 A：自动安装脚本（推荐）**

```powershell
# 自动安装
.\install-windows.ps1
```

---

## 🤖 全自动模式（新功能）

**无需人工干预，完全自主运行！**

```bash
# 全自动添加类型注解
python scripts/autoresearch_autonomous.py \
  --goal "add type hints" \
  --scope "src/" \
  --verify "python -m mypy src/ 2>&1 | grep -c error" \
  --direction lower \
  --iterations 20

# 全自动删除未使用导入
python scripts/autoresearch_autonomous.py \
  --goal "remove unused imports" \
  --scope "scripts/" \
  --iterations 50

# 或使用 workflow 的 --autonomous 标志
python scripts/autoresearch_workflow.py \
  --autonomous \
  --goal "reduce type errors" \
  --verify "mypy src/ 2>&1 | grep -c error" \
  --direction lower
```

### 全自动工作流程

1. **自动分析** - 扫描代码识别改进点
2. **生成假设** - 基于分析生成修改建议
3. **自动修改** - 执行代码变换
4. **验证结果** - 运行测试/检查
5. **智能决策** - 保留改进，回退无效修改
6. **循环优化** - 直到达成目标或达到迭代上限

**方式 A：自动安装脚本（推荐）**
```powershell
# 以管理员身份打开 PowerShell，执行：
cd C:\path\to\kimi-autoresearch
.\install-windows.ps1

# 或指定源目录
.\install-windows.ps1 -Source "E:\your-path\kimi-autoresearch"
```

**方式 B：手动克隆**
```powershell
# 克隆到用户目录
git clone https://github.com/mixyoung/kimi-autoresearch.git "$env:USERPROFILE\.agents\skills\kimi-autoresearch"
```

**方式 C：符号链接（开发推荐）**
```powershell
# 创建符号链接（需要管理员，可实时同步开发目录）
New-Item -ItemType SymbolicLink `
  -Path "$env:USERPROFILE\.agents\skills\kimi-autoresearch" `
  -Target "C:\path\to\kimi-autoresearch"
```

### 方法四：技能包安装

下载发布的 `.skill` 文件并解压到你的 skills 目录。

## 🚀 快速开始

### 在 Kimi 中使用

```
$kimi-autoresearch
Goal: Reduce TypeScript type errors
```

### 命令行使用

```bash
# 初始化运行
python scripts/autoresearch_init_run.py \
  --goal "Reduce type errors" \
  --metric "error count" \
  --verify "tsc --noEmit 2>&1 | grep -c error"

# 运行完整工作流
python scripts/autoresearch_workflow.py \
  --goal "Increase test coverage" \
  --verify "npm test -- --coverage | grep 'All files'"

### 切换语言

```bash
# 查看当前语言
python scripts/autoresearch_main.py lang

# 切换到英文
python scripts/autoresearch_main.py lang en

# 切换到中文
python scripts/autoresearch_main.py lang zh
```

## 📖 工作模式

### 基础模式

| 模式 | 命令 | 用途 |
|------|------|------|
| **Loop** | `$kimi-autoresearch` | 迭代优化指标 |
| **Plan** | `$kimi-autoresearch:plan` | 配置向导 |
| **Debug** | `$kimi-autoresearch:debug` | 科学调试 |
| **Fix** | `$kimi-autoresearch:fix` | 自动修复错误 |
| **Security** | `$kimi-autoresearch:security` | 安全审计 |

### 高级模式

| 模式 | 命令 | 用途 |
|------|------|------|
| **Ship** | `$kimi-autoresearch:ship` | 自动化发布 |
| **Scenario** | `$kimi-autoresearch:scenario` | 场景探索 |
| **Predict** | `$kimi-autoresearch:predict` | 多角色预测 |
| **Learn** | `$kimi-autoresearch:learn` | 文档维护 |
| **Exec** | CLI | CI/CD 执行 |

## 🛠️ 核心脚本

```
scripts/
├── autoresearch_main.py          # 统一 CLI 入口
├── autoresearch_workflow.py      # 完整工作流
├── autoresearch_init_run.py      # 初始化运行
├── autoresearch_decision.py      # 决策逻辑
├── autoresearch_health_check.py  # 健康检查
├── autoresearch_launch_gate.py   # 启动门控
├── autoresearch_background.py    # 后台控制
├── autoresearch_exec.py          # CI/CD 模式
├── autoresearch_parallel.py      # 并行实验
├── autoresearch_web_search.py    # Web 搜索
└── ... (共 20 个 Python 脚本)
```

## 📚 文档

- [快速参考](references/quick-reference.md) - 常用命令速查
- [循环协议](references/loop-protocol.md) - 核心迭代机制
- [Plan 模式](references/mode-plan.md) - 配置向导
- [Debug 模式](references/mode-debug.md) - 科学调试
- [Ship 模式](references/mode-ship.md) - 发布工作流
- [并行实验](references/parallel-experiments.md) - 多工作树并行
- [Web 搜索](references/web-search-protocol.md) - 自动搜索集成

查看 [references/](references/) 目录获取完整文档。

## 🔄 CI/CD 集成

GitHub Actions 工作流示例：

```yaml
name: Autoresearch
on:
  schedule:
    - cron: '0 2 * * 0'  # 每周日凌晨 2 点
  workflow_dispatch:

jobs:
  optimize:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Run autoresearch
        run: |
          python scripts/autoresearch_exec.py \
            --mode optimize \
            --config autoresearch-config.json
```

完整配置见 [.github/workflows/autoresearch.yml](.github/workflows/autoresearch.yml)

## ⚙️ 配置示例

### TypeScript 项目 - 提升覆盖率

```json
{
  "goal": "Increase test coverage to 90%",
  "scope": "src/**/*.ts",
  "metric": "coverage percentage",
  "direction": "higher",
  "verify": "npm test -- --coverage | grep 'All files' | awk '{print $2}' | tr -d '%'",
  "guard": "npm run build && npm run lint",
  "iterations": 30,
  "target": 90
}
```

### Python 项目 - 修复类型错误

```json
{
  "goal": "Eliminate mypy type errors",
  "scope": "src/**/*.py",
  "metric": "type error count",
  "direction": "lower",
  "verify": "mypy src/ 2>&1 | grep -c 'error:'",
  "guard": "python -m pytest",
  "iterations": 25
}
```

更多示例见 [examples/](examples/) 目录。

## 📊 工作流程

```
1. 初始化 → 健康检查 → 基线测量
         ↓
2. 迭代循环 (直到完成或中断)
   - 选择假设
   - 应用修改
   - Git 提交
   - 运行验证
   - 决策 (keep/discard)
   - 记录结果
         ↓
3. 生成报告 → 提取学习
```

## 🤝 与其他项目对比

| 特性 | codex-autoresearch | autoresearch (Claude) | **kimi-autoresearch** |
|------|-------------------|----------------------|----------------------|
| 模式数量 | 7 | 9 | **10** ✅ |
| Python脚本 | 20+ | 0 (内置) | **23** ✅ |
| 并行实验 | ✅ | ❌ | **✅** |
| Web 搜索 | ⚠️ | ❌ | **✅ (自动触发)** |
| CI/CD | ✅ | ⚠️ | **✅ (2套)** |
| 噪音处理 | ✅ | ✅ | **✅** |
| 会话弹性 | ✅ | ❌ | **✅** |
| 指标分析 | ⚠️ | ⚠️ | **✅** |
| 提交门控 | ✅ | ❌ | **✅** |
| 单元测试 | ✅ | ❌ | **✅** |
| 配置示例 | ✅ | ⚠️ | **8个** ✅ |
| 语言 | 8种 | 英文 | **中文/英文** |

[详细对比 →](references/COMPARISON.md)

## 🚀 发布

### 自动发布 (GitHub Actions)

推送 tag 自动触发 Release：

```bash
# 使用版本管理工具
python scripts/autoresearch_version.py bump patch --tag
git push origin main --tags

# 或者手动创建 tag
git tag -a v1.0.1 -m "Release v1.0.1"
git push origin v1.0.1
```

GitHub Actions 会自动：
- 更新所有文件中的版本号
- 打包生成 `.skill` 文件
- 创建 GitHub Release 并上传附件
- 生成校验和

### 手动打包

**Windows:**
```powershell
# 默认版本
.\package.ps1

# 指定版本
.\package.ps1 -Version 1.1.0
```

**Linux/macOS:**
```bash
./package.sh
```

输出文件：
```
dist/
├── kimi-autoresearch-1.0.0.skill    # 主包
├── kimi-autoresearch-latest.skill   # 最新版
└── kimi-autoresearch-1.0.0.sha256   # 校验和
```

## 📝 要求

- Python 3.8+
- Git 仓库（必需）
- Kimi Code CLI（推荐）

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何参与。

## 📄 许可证

[MIT](LICENSE)

## 🙏 致谢

- 灵感来自 [Andrej Karpathy](https://karpathy.ai/) 的 autoresearch 概念
- 参考了 [codex-autoresearch](https://github.com/leo-lilinxiao/codex-autoresearch) 和 [autoresearch](https://github.com/uditgoenka/autoresearch) 的实现
- 感谢 Kimi 团队提供的优秀工具

---

**开始使用**: 运行 `python scripts/autoresearch_workflow.py --help` 查看所有选项
