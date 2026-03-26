# Contributing to Kimi Autoresearch

感谢你对 Kimi Autoresearch 的兴趣！我们欢迎各种形式的贡献。

## 🚀 如何贡献

### 报告问题

如果你发现了 bug 或有功能建议：

1. 先搜索 [Issues](https://github.com/YOUR_USERNAME/kimi-autoresearch/issues) 看是否已存在
2. 如果没有，创建一个新的 Issue
3. 提供详细的信息：
   - 问题描述
   - 复现步骤
   - 期望行为
   - 实际行为
   - 环境信息（OS, Python 版本等）

### 提交代码

1. **Fork 仓库**
   ```bash
   git clone https://github.com/YOUR_USERNAME/kimi-autoresearch.git
   cd kimi-autoresearch
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

3. **进行修改**
   - 遵循现有的代码风格
   - 添加必要的注释
   - 更新相关文档

4. **提交更改**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   # 或
   git commit -m "fix: resolve bug in workflow"
   ```

   Commit 消息规范：
   - `feat:` 新功能
   - `fix:` 修复 bug
   - `docs:` 文档更新
   - `refactor:` 代码重构
   - `test:` 测试相关
   - `chore:` 构建/工具

5. **推送并创建 PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   然后在 GitHub 上创建 Pull Request

## 📋 开发指南

### 项目结构

```
kimi-autoresearch/
├── scripts/           # Python 脚本
├── references/        # 文档
├── examples/          # 配置示例
├── .github/           # GitHub 配置
└── tests/             # 测试（待添加）
```

### 添加新脚本

1. 在 `scripts/` 目录创建 `.py` 文件
2. 使用 `argparse` 处理命令行参数
3. 添加 `#!/usr/bin/env python3` shebang
4. 包含 `if __name__ == '__main__':` 块
5. 在 `autoresearch_main.py` 中添加命令

示例模板：

```python
#!/usr/bin/env python3
"""
简短描述。
"""
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description='描述')
    parser.add_argument('--option', type=str, help='选项说明')
    args = parser.parse_args()
    
    # 你的代码
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
```

### 添加新文档

1. 在 `references/` 创建 `.md` 文件
2. 使用清晰的标题结构
3. 包含代码示例
4. 在 README.md 中添加链接

### 代码风格

- 遵循 PEP 8
- 使用类型注解（可选但推荐）
- 函数和类添加 docstring
- 保持行长度在 100 字符以内

## 🧪 测试

目前项目缺少测试。如果你有兴趣添加测试，我们非常欢迎！

建议的测试框架：
- `pytest` 用于单元测试
- 测试脚本放在 `tests/` 目录

## 📝 文档

- 更新 README.md 如果添加新功能
- 在 references/ 添加详细文档
- 更新快速参考 (quick-reference.md)

## 🎯 优先事项

我们特别需要帮助的地方：

1. **测试** - 添加单元测试
2. **文档** - 完善英文文档
3. **示例** - 更多配置示例
4. **i18n** - 多语言支持
5. **性能** - 优化脚本性能

## 💬 沟通

- **Issue**: 用于 bug 报告和功能请求
- **Pull Request**: 用于代码审查
- **Discussions**: 用于一般讨论（如果启用）

## ⚖️ 行为准则

- 友善和尊重
- 接受建设性批评
- 关注对社区最有利的事情

## 📄 许可证

通过贡献代码，你同意你的贡献将在 MIT 许可证下发布。

---

再次感谢你的贡献！🎉
