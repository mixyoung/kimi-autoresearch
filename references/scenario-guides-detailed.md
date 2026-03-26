# 详细场景指南

10个完整的 autoresearch 使用场景，每个包含：
- 场景描述
- 配置示例
- 预期结果
- 最佳实践
- 常见问题

---

## 场景 1：TypeScript 类型安全改进

### 目标
消除项目中所有的 `any` 类型，提高类型安全。

### 适用项目
- TypeScript 项目
- 存在大量 `any` 类型
- 希望启用严格模式

### 配置

```json
{
  "goal": "Eliminate all 'any' types in src/",
  "scope": "src/**/*.ts",
  "metric": "count of 'any'",
  "direction": "lower",
  "verify": "grep -r 'any' src/**/*.ts | wc -l",
  "guard": "tsc --noEmit",
  "iterations": 50,
  "target": 0
}
```

### 执行

```bash
$kimi-autoresearch
Goal: Eliminate all 'any' types in src/
Scope: src/**/*.ts
Verify: grep -r "any" src/**/*.ts | wc -l
Guard: tsc --noEmit
Iterations: 50
```

### 预期结果
- **迭代 0**: 基线 47 个 `any`
- **迭代 5-15**: 快速下降到 20-30 个
- **迭代 15-40**: 缓慢优化到 5-10 个
- **迭代 40-50**: 最终清理难点

### 最佳实践

1. **从简单开始**
   - 先处理明显的类型（string, number, boolean）
   - 复杂泛型留到最后

2. **利用类型推断**
   ```typescript
   // Before
   const data: any = fetchData();
   
   // After
   const data = fetchData(); // TypeScript 会推断类型
   ```

3. **创建类型定义**
   ```typescript
   // 为 API 响应创建类型
   interface User {
     id: number;
     name: string;
     email: string;
   }
   ```

### 常见问题

**Q: tsc --noEmit 报错太多？**
A: 先用 `--noImplicitAny false` 过渡，逐步收紧。

**Q: 第三方库没有类型？**
A: 安装 @types/xxx，或创建 .d.ts 声明文件。

---

## 场景 2：Python 测试覆盖率提升

### 目标
将测试覆盖率从 60% 提升到 90%。

### 适用项目
- Python 项目
- 已有测试框架（pytest）
- coverage 工具已安装

### 配置

```json
{
  "goal": "Increase test coverage to 90%",
  "scope": "src/**/*.py",
  "metric": "coverage percentage",
  "direction": "higher",
  "verify": "pytest --cov=src --cov-report=term | grep TOTAL | awk '{print $4}'",
  "guard": "pytest",
  "iterations": 30,
  "target": 90
}
```

### 执行

```bash
$kimi-autoresearch
Goal: Increase test coverage to 90%
Verify: pytest --cov=src --cov-report=term | grep TOTAL | awk '{print $4}'
Guard: pytest
Iterations: 30
```

### 策略

1. **识别未测试代码**
   ```bash
   pytest --cov=src --cov-report=html
   # 查看 htmlcov/index.html 找到红色区域
   ```

2. **优先级**
   - 核心业务逻辑优先
   - 边界条件测试
   - 错误处理路径

3. **测试模板**
   ```python
   def test_function_name():
       # Arrange
       input_data = ...
       expected = ...
       
       # Act
       result = function(input_data)
       
       # Assert
       assert result == expected
   ```

---

## 场景 3：性能优化（API 响应时间）

### 目标
将 API 平均响应时间从 500ms 降到 100ms。

### 适用项目
- Web API（FastAPI/Flask/Express）
- 有性能基准测试
- 可本地运行负载测试

### 配置

```json
{
  "goal": "Reduce API latency to 100ms",
  "scope": "src/api/",
  "metric": "average response time (ms)",
  "direction": "lower",
  "verify": "python benchmark.py | grep 'Average' | awk '{print $2}'",
  "guard": "pytest tests/",
  "iterations": 40,
  "target": 100
}
```

### 优化策略

1. **数据库优化**
   - 添加索引
   - 优化查询（N+1 问题）
   - 使用连接池

2. **缓存**
   - Redis 缓存热点数据
   - 内存缓存（lru_cache）

3. **异步化**
   - 数据库操作 async
   - 外部 API 调用 async

4. **代码优化**
   - 减少循环嵌套
   - 避免重复计算
   - 使用生成器

---

## 场景 4：代码重构（消除重复）

### 目标
识别并消除代码重复，提高可维护性。

### 适用项目
- 任何有重复代码的项目
- 希望提高代码质量

### 配置

```json
{
  "goal": "Reduce code duplication",
  "scope": "src/",
  "metric": "duplicate lines",
  "direction": "lower",
  "verify": "jscpd src/ --reporters console | grep 'Duplicated' | awk '{print $3}'",
  "guard": "npm test",
  "iterations": 20
}
```

### 重构模式

1. **提取函数**
   ```javascript
   // Before: 重复代码
   function processA() { ...重复代码... }
   function processB() { ...重复代码... }
   
   // After: 提取公共部分
   function commonLogic() { ... }
   function processA() { commonLogic(); ... }
   function processB() { commonLogic(); ... }
   ```

2. **提取类**
3. **使用策略模式**
4. **模板方法模式**

---

## 场景 5：安全漏洞修复

### 目标
自动识别并修复安全漏洞。

### 适用项目
- 任何需要安全审计的项目
- 使用依赖包的项目

### 配置

```json
{
  "goal": "Fix security vulnerabilities",
  "scope": "src/",
  "metric": "vulnerability count",
  "direction": "lower",
  "verify": "npm audit --json | jq '.metadata.vulnerabilities.total'",
  "guard": "npm test",
  "iterations": 20,
  "target": 0
}
```

### 修复策略

1. **依赖更新**
   ```bash
   npm audit fix
   npm update
   ```

2. **输入验证**
   - SQL 注入防护
   - XSS 防护
   - CSRF 防护

3. **安全配置**
   - 禁用不安全功能
   - 启用安全头部

---

## 场景 6：文档完善

### 目标
为所有公共函数添加文档字符串。

### 适用项目
- Python 项目
- 缺少文档的项目

### 配置

```json
{
  "goal": "Add docstrings to all public functions",
  "scope": "src/**/*.py",
  "metric": "missing docstrings",
  "direction": "lower",
  "verify": "pydocstyle src/ | grep -c 'D10'",
  "guard": "pytest",
  "iterations": 30
}
```

### 文档模板

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Short description.
    
    Longer description explaining what the function does,
    when to use it, and any important details.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When input is invalid
        
    Example:
        >>> function_name("test", 42)
        True
    """
    pass
```

---

## 场景 7：代码格式化统一

### 目标
统一代码风格，符合项目规范。

### 适用项目
- 多人协作项目
- 风格不统一的项目

### 配置

```json
{
  "goal": "Enforce consistent code style",
  "scope": "src/",
  "metric": "style violations",
  "direction": "lower",
  "verify": "flake8 src/ | wc -l",
  "guard": "pytest",
  "iterations": 30
}
```

### 工具链

- **Python**: black, isort, flake8
- **JavaScript**: prettier, eslint
- **Go**: gofmt, golint

---

## 场景 8：错误处理完善

### 目标
添加全面的错误处理。

### 适用项目
- 生产环境项目
- 需要高可用性的项目

### 配置

```json
{
  "goal": "Add comprehensive error handling",
  "scope": "src/",
  "metric": "uncaught exceptions in tests",
  "direction": "lower",
  "verify": "pytest --tb=no 2>&1 | grep -c 'ERROR'",
  "guard": "pytest",
  "iterations": 25
}
```

### 错误处理模式

```python
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Specific error: {e}")
    handle_specific_error(e)
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    raise
finally:
    cleanup()
```

---

## 场景 9：API 版本迁移

### 目标
从旧版 API 迁移到新版。

### 适用项目
- 需要升级依赖的项目
- 弃用旧 API 的项目

### 配置

```json
{
  "goal": "Migrate from v1 API to v2",
  "scope": "src/",
  "metric": "v1 API usage count",
  "direction": "lower",
  "verify": "grep -r 'api/v1' src/ | wc -l",
  "guard": "pytest",
  "iterations": 40
}
```

---

## 场景 10：内存优化

### 目标
减少内存使用，解决内存泄漏。

### 适用项目
- 长时间运行的服务
- 大数据处理项目

### 配置

```json
{
  "goal": "Reduce memory usage by 50%",
  "scope": "src/",
  "metric": "peak memory (MB)",
  "direction": "lower",
  "verify": "python memory_benchmark.py | grep 'Peak' | awk '{print $3}'",
  "guard": "pytest",
  "iterations": 30,
  "target": 100
}
```

### 优化策略

1. **使用生成器**
2. **及时释放资源**
3. **避免循环引用**
4. **使用 __slots__**
5. **内存分析器定位泄漏**

---

## 通用最佳实践

### 1. 迭代策略
- **前10次**: 探索，接受高失败率
- **中间20次**: 优化，提高成功率
- **最后10次**: 精细化，追求极致

### 2. Guard 命令选择
- 必须能快速执行
- 必须覆盖核心功能
- 失败率要低

### 3. 验证指标
- 必须是可量化的
- 必须是稳定的
- 必须是相关的

### 4. 失败处理
- 不要因单次失败放弃
- 分析失败模式
- 调整策略

---

## 附录：快速配置模板

```bash
# TypeScript 类型检查
$kimi-autoresearch --config configs/typescript-types.json

# Python 测试覆盖
$kimi-autoresearch --config configs/python-coverage.json

# 性能优化
$kimi-autoresearch --config configs/performance.json

# 代码重构
$kimi-autoresearch --config configs/refactoring.json
```
