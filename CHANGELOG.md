# Changelog

所有重要的更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且该项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.1.0] - 2026-03-26

### Added
- 

### Changed
- 

### Fixed
-
## [1.0.2] - 2026-03-26

### Added
- 

### Changed
- 

### Fixed
-
## [1.0.1] - 2026-03-26

### Added
- 

### Changed
- 

### Fixed
-
## [Unreleased]

### Added
- 初始版本发布
- 10 种工作模式实现
- 20 个功能脚本
- 14 个参考文档
- Web 搜索自动触发
- 并行实验支持
- CI/CD GitHub Actions 工作流
- **国际化 (i18n) 支持** - 支持中英文切换

## [1.0.0] - 2024-03-26

### 核心功能
- ✅ 自主迭代循环 (modify → verify → retain/discard → repeat)
- ✅ 10 种工作模式:
  - Loop - 迭代优化
  - Plan - 配置向导
  - Debug - 科学调试
  - Fix - 自动修复
  - Security - 安全审计
  - Ship - 发布工作流
  - Scenario - 场景探索
  - Predict - 多角色预测
  - Learn - 文档引擎
  - Exec - CI/CD 模式

### 脚本 (20个)
- `autoresearch_main.py` - 统一 CLI 入口
- `autoresearch_workflow.py` - 工作流编排
- `autoresearch_init_run.py` - 运行初始化
- `autoresearch_decision.py` - 决策逻辑
- `autoresearch_health_check.py` - 健康检查
- `autoresearch_launch_gate.py` - 启动门控
- `autoresearch_background.py` - 后台控制
- `autoresearch_exec.py` - CI/CD 执行
- `autoresearch_parallel.py` - 并行实验
- `autoresearch_web_search.py` - Web 搜索
- `autoresearch_lessons.py` - 学习管理
- `autoresearch_predict.py` - 预测分析
- `autoresearch_utils.py` - 工具函数
- `autoresearch_i18n.py` - **国际化支持**
- 以及 6 个基础脚本

### 文档 (14个)
- `loop-protocol.md` - 核心协议
- `mode-plan.md` - Plan 模式
- `mode-debug.md` - Debug 模式
- `mode-fix.md` - Fix 模式
- `mode-security.md` - Security 模式
- `mode-ship.md` - Ship 模式
- `mode-scenario.md` - Scenario 模式
- `mode-predict.md` - Predict 模式
- `mode-learn.md` - Learn 模式
- `mode-exec.md` - Exec 模式
- `parallel-experiments.md` - 并行实验
- `web-search-protocol.md` - Web 搜索
- `i18n.md` - **国际化文档**
- `quick-reference.md` - 快速参考

### 其他
- 3 个配置示例 (TypeScript, Python, Bundle)
- GitHub Actions CI/CD 工作流
- MIT 许可证

---

## 版本历史对比

| 版本 | 日期 | 脚本数 | 模式数 | 文档数 | 特性 |
|------|------|--------|--------|--------|------|
| 1.0.0 | 2024-03-26 | **20** | 10 | **14** | 初始完整版本 + i18n |

---

## 待办事项 (Roadmap)

### 计划中的功能
- [ ] 单元测试覆盖
- [ ] 更多配置示例
- [ ] 性能优化
- [x] **多语言支持 (i18n)** - ✅ 已完成 (v1.0.0)
- [ ] 更多语言（日语、法语等）
- [ ] MCP 协议支持
- [ ] Web UI 界面
- [ ] 插件系统

### 已知问题
- 暂无

---

**注意**: 这是初始版本，API 可能会在未来版本中发生变化。
