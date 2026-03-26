# Kimi Autoresearch v1.0.0

## 🎉 首次发布

Kimi Autoresearch - 专为 Kimi Code CLI 设计的自动化研究工具

### ✨ 核心功能

- **10 种工作模式**: Loop, Plan, Debug, Fix, Security, Ship, Scenario, Predict, Learn, Exec
- **20 个功能脚本**: 完整的自动化工作流（约 4,800 行代码）
- **13 个参考文档**: 详细的协议说明（约 10,000 行文档）
- **Web 搜索集成**: 卡住时自动搜索解决方案
- **并行实验**: Git worktree 同时测试多个假设
- **CI/CD 就绪**: GitHub Actions 工作流支持

### 📦 安装方式

#### 方式一：Git 克隆
```bash
git clone https://github.com/mixyoung/kimi-autoresearch.git
```

#### 方式二：下载技能包（推荐）
下载本页面下方的 `kimi-autoresearch-1.0.0.skill` 文件并解压到你的 `.agents/skills/` 目录

### 🚀 快速开始

```bash
# 运行工作流
python scripts/autoresearch_workflow.py \
  --goal "Reduce type errors" \
  --verify "tsc --noEmit 2>&1 | grep -c error"
```

或在 Kimi 中：
```
$kimi-autoresearch
Goal: Reduce TypeScript type errors
```

### 📋 系统要求

- Python 3.8+
- Git 仓库
- Kimi Code CLI（推荐）

### 🖥️ 支持平台

- ✅ Windows
- ✅ macOS
- ✅ Linux

### 📁 项目结构

```
kimi-autoresearch/
├── scripts/           # 20 个 Python 脚本
├── references/        # 13 个参考文档
├── examples/          # 3 个配置示例
└── .github/           # CI/CD 配置
```

### 📄 许可证

MIT License

---

**下载**: 使用下方的 Assets 下载 `.skill` 文件或源代码
