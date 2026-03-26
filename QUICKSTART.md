# 快速开始指南 - 手把手教你使用 Kimi Autoresearch

## 第一步：确认安装位置

你的项目在这里：
```
E:\33_dev_env\kimi-autoresearch
```

## 第二步：进入项目目录

```powershell
cd E:\33_dev_env\kimi-autoresearch
```

## 第三步：检查是否可用

```powershell
# 查看帮助
python scripts\autoresearch_main.py --help

# 运行健康检查
python scripts\autoresearch_main.py health
```

如果显示绿色 ✓，说明一切正常！

## 第四步：创建测试项目

我们先创建一个简单的测试项目来演示：

```powershell
# 创建测试目录
mkdir E:\test-project
cd E:\test-project

# 初始化 git
git init

# 创建一个简单的 Python 文件（有类型错误）
@"
def add(a, b):
    return a + b

def greet(name):
    # 故意留一个类型问题
    return "Hello " + name

result = add(1, 2)
print(result)
"@ | Out-File -Encoding UTF8 test.py

# 提交
git add .
git commit -m "initial"
```

## 第五步：使用 Autoresearch 优化代码

### 方法 A：使用工作流脚本（推荐）

```powershell
cd E:\test-project

python E:\33_dev_env\kimi-autoresearch\scripts\autoresearch_workflow.py `
  --goal "Add type hints to Python functions" `
  --scope "*.py" `
  --metric "type errors" `
  --verify "python -m pyright . 2>&1 | findstr /c:'error'" `
  --direction lower `
  --iterations 5
```

### 方法 B：分步执行

```powershell
cd E:\test-project

# 1. 初始化
python E:\33_dev_env\kimi-autoresearch\scripts\autoresearch_init_run.py `
  --goal "Add type hints" `
  --metric "type errors" `
  --verify "python -m pyright . 2>&1 | findstr /c:'error'" `
  --direction lower

# 2. 运行迭代（手动模式）
# 这里你需要手动编辑 test.py 添加类型提示
# 然后验证
```

## 第六步：查看结果

运行完成后，会生成以下文件：

```powershell
# 查看结果日志
type autoresearch-results.tsv

# 查看报告
type autoresearch-report.md

# 查看状态
type autoresearch-state.json
```

## 第七步：在 Kimi 中使用

因为已经创建了符号链接，直接在 Kimi 中输入：

```
$kimi-autoresearch
Goal: Add type hints to Python functions
```

## 完整示例命令总结

```powershell
# 1. 进入目录
cd E:\33_dev_env\kimi-autoresearch

# 2. 健康检查
python scripts\autoresearch_main.py health

# 3. 查看支持的语言
python scripts\autoresearch_main.py lang

# 4. 切换到中文
python scripts\autoresearch_main.py lang zh

# 5. 运行工作流（示例）
python scripts\autoresearch_workflow.py `
  --goal "Improve code quality" `
  --verify "echo 42" `
  --direction lower

# 6. 查看统计
python scripts\autoresearch_utils.py stats

# 7. 生成报告
python scripts\autoresearch_main.py report
```

## 常见问题

### Q: 提示找不到脚本？
A: 确保你在 `E:\33_dev_env\kimi-autoresearch` 目录下运行

### Q: 权限错误？
A: 以管理员身份运行 PowerShell

### Q: 中文显示乱码？
A: 设置编码：`chcp 65001`

## 下一步

1. 尝试运行上面的命令
2. 观察生成的结果文件
3. 在 Kimi 中体验 `$kimi-autoresearch`

有任何问题随时问我！
