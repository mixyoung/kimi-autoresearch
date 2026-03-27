# Kimi Autoresearch 单元测试

## 测试概览

为 kimi-autoresearch v2.0 提供全面的单元测试覆盖。

## 测试文件

| 文件 | 测试内容 | 测试数量 |
|------|----------|----------|
| `test_ralph.py` | Ralph Loop 控制、Agent 配置、停止条件 | 14 |
| `test_state_manager.py` | 状态管理、迭代更新、日志记录 | 13 |
| `test_daemon.py` | 守护进程状态、决策逻辑、卡住检测 | 13 |
| `test_decision.py` | 决策逻辑（保留/丢弃/重做） | 10 |
| `test_git.py` | Git 操作 | 7 |
| `test_health_check.py` | 健康检查 | 6 |

**总计**: 60+ 个测试

## 运行测试

### 运行所有测试
```bash
python tests/run_tests.py
```

### 运行特定测试文件
```bash
python tests/run_tests.py test_ralph
python tests/run_tests.py test_state_manager
```

### 详细输出
```bash
python tests/run_tests.py -v
```

### 使用 pytest
```bash
pytest tests/ -v
```

## 测试覆盖的功能

### Ralph Loop 控制 (test_ralph.py)
- Loop 控制参数设置（max_steps, max_retries, max_ralph）
- Agent 配置（内置 agent 和自定义文件）
- 停止条件检查（目标达成、迭代限制、卡住）
- Ralph Prompt 生成
- 停止信号输出

### 状态管理 (test_state_manager.py)
- 状态加载（默认和已有文件）
- 状态保存
- 迭代状态更新（keep/discard/pivot）
- 学习日志记录
- 状态持久化

### 决策逻辑 (test_daemon.py, test_decision.py)
- 保留决策（改善 + guard 通过）
- 丢弃决策（未改善）
- 重做决策（guard 失败）
- 卡住模式检测（refine/pivot/search）
- 迭代计数器更新

### Git 操作 (test_git.py)
- Git 仓库检测
- 变更检测
- 提交哈希获取
- 命令执行

### 健康检查 (test_health_check.py)
- Git 配置检查
- 工作区清洁度
- 磁盘空间
- 必需工具

## v2.0 新增测试

### 新增测试文件
- `test_ralph.py` - Ralph Loop 功能
- `test_state_manager.py` - v2.0 简化状态管理
- `run_tests.py` - 测试运行器

### 更新的测试
- `test_daemon.py` - 移除 v1.x 特定功能测试

## 已知问题

### Windows 权限问题
在 Windows 上，`test_git.py` 中的临时目录清理可能因权限问题失败。这是测试环境问题，不影响实际代码功能。

解决方法：
1. 以管理员身份运行测试
2. 或者忽略该特定错误

## 添加新测试

### 测试模板
```python
#!/usr/bin/env python3
import unittest
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from module_name import function_name


class TestFeature(unittest.TestCase):
    def setUp(self):
        # 测试前准备
        pass
    
    def tearDown(self):
        # 测试后清理
        pass
    
    def test_something(self):
        """测试描述"""
        result = function_name()
        self.assertEqual(result, expected_value)


if __name__ == '__main__':
    unittest.main()
```

## 持续集成

测试在以下情况自动运行：
- 每次提交前（推荐）
- Pull Request 时
- 发布前

## 测试状态

- **通过**: 60+ 测试
- **失败**: 0（代码问题）
- **错误**: 1（Windows 环境权限问题，非代码问题）

**结论**: 所有核心功能测试通过 ✓
