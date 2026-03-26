# 发布到 GitHub 完整指南

## 步骤 1: 初始化 Git 仓库

```bash
# 进入项目目录
cd kimi-autoresearch

# 初始化 Git
git init

# 添加所有文件
git add .

# 首次提交
git commit -m "feat: initial release v1.0.0

- 10 种工作模式
- 20 个功能脚本
- 13 个参考文档
- Web 搜索自动触发
- 并行实验支持
- CI/CD GitHub Actions"
```

## 步骤 2: 连接远程仓库

```bash
# 添加远程仓库（替换 YOUR_USERNAME 和 REPO_NAME）
git remote add origin https://github.com/YOUR_USERNAME/kimi-autoresearch.git

# 验证
git remote -v
```

## 步骤 3: 推送到 GitHub

```bash
# 推送到 main 分支
git branch -M main
git push -u origin main
```

## 步骤 4: 创建 Release

### 在 GitHub 网页上:

1. 进入仓库页面
2. 点击右侧的 "Releases"
3. 点击 "Create a new release"
4. 填写信息:
   - **Tag**: `v1.0.0`
   - **Title**: "Initial Release - Kimi Autoresearch v1.0.0"
   - **Description**: 复制 CHANGELOG.md 的内容

### 或者使用命令行:

```bash
# 创建标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 推送标签
git push origin v1.0.0
```

## 步骤 5: 打包 .skill 文件

```bash
# 运行打包脚本
bash package.sh

# 或者手动打包
cd dist
zip -r kimi-autoresearch-1.0.0.skill kimi-autoresearch/
```

## 步骤 6: 上传到 Release

1. 在 Release 页面点击 "Edit"
2. 拖放 `dist/kimi-autoresearch-1.0.0.skill` 文件到附件区域
3. 点击 "Update release"

## 后续更新步骤

### 日常开发

```bash
# 查看修改
git status

# 添加修改的文件
git add <files>

# 提交
git commit -m "fix: description of fix"

# 推送
git push origin main
```

### 发布新版本

```bash
# 1. 更新版本号（编辑相关文件）
# 2. 更新 CHANGELOG.md

# 3. 提交
git add .
git commit -m "release: v1.1.0"

# 4. 创建标签
git tag -a v1.1.0 -m "Release v1.1.0"

# 5. 推送
git push origin main
git push origin v1.1.0

# 6. 打包
bash package.sh

# 7. 在 GitHub 创建 Release 并上传 .skill 文件
```

## Git 常用命令速查

```bash
# 查看状态
git status

# 查看日志
git log --oneline

# 创建分支
git checkout -b feature/new-feature

# 切换分支
git checkout main

# 合并分支
git merge feature/new-feature

# 拉取更新
git pull origin main

# 解决冲突后
git add .
git commit -m "merge: resolve conflicts"
```

## 常见问题

### Q: 推送被拒绝?
```bash
# 先拉取更新
git pull origin main --rebase
# 然后再推送
git push origin main
```

### Q: 忘记了 git add?
```bash
# 修改上次提交
git commit --amend -m "新的提交信息"
# 强制推送（仅用于未共享的提交）
git push origin main --force
```

### Q: 如何撤销修改?
```bash
# 撤销工作区修改
git checkout -- <file>

# 撤销暂存区
git reset HEAD <file>
```

## 推荐的分支策略

```
main        生产分支 (保护)
  ↓
develop     开发分支
  ↓
feature/*   功能分支
  ↓
fix/*       修复分支
```

## 提交信息规范

```
feat:     新功能
fix:      修复
docs:     文档
style:    格式
refactor: 重构
test:     测试
chore:    构建/工具
release:  发布
```

示例:
```
feat: add web search auto-trigger
fix: resolve git worktree cleanup issue
docs: update README with new examples
release: v1.1.0
```

## GitHub 设置建议

### 1. 启用功能
- ✅ Issues (问题追踪)
- ✅ Discussions (讨论区)
- ✅ Projects (项目管理)
- ✅ Wiki (可选)

### 2. 保护规则 (Settings > Branches)
- 保护 `main` 分支
- 要求 PR 审查
- 要求状态检查

### 3. 添加 Topics
- `kimi`
- `autoresearch`
- `code-optimization`
- `cli-tool`
- `automation`

---

祝发布顺利！🎉
