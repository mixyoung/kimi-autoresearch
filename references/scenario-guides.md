# 场景探索指南

基于 `$kimi-autoresearch:scenario` 的实际应用指南。

## 概述

场景模式在12个维度上生成测试场景：
- Happy paths, Errors, Edge cases, Abuse, Scale, Concurrency
- Temporal, Data variation, Permissions, Integrations, Recovery, State transitions

---

## 软件工程场景

### 1. API 端点开发

```
$kimi-autoresearch:scenario
Seed: 用户注册 API
Depth: deep
Format: test-scenarios
```

**生成的场景示例**:

| 维度 | 场景 |
|------|------|
| Happy Path | 正常用户注册，验证邮件发送 |
| Error | 重复邮箱注册，返回 409 |
| Edge Case | 邮箱长度255字符边界 |
| Abuse | 批量注册攻击，rate limit 触发 |
| Scale | 10k TPS 并发注册 |
| Concurrency | 同一邮箱同时多次提交 |
| Temporal | 验证链接24小时过期 |
| Data Variation | 国际手机号、特殊字符用户名 |
| Permissions | 未验证用户权限限制 |
| Recovery | 邮件服务宕机，队列重试 |
| State Transition | 未验证 → 已验证 → 已禁用 |

---

### 2. 数据库迁移

```
$kimi-autoresearch:scenario
Seed: 用户表添加新字段
Depth: deep
```

**关键场景**:
- **Zero-downtime 迁移** - 在线改表策略
- **Rollback 测试** - 迁移失败回滚
- **数据一致性** - 新旧字段同步验证
- **大表处理** - 千万级数据迁移性能

---

### 3. 支付流程

```
$kimi-autoresearch:scenario
Seed: 信用卡支付流程
Depth: deep
```

**安全场景**:
- **欺诈检测** - 异常交易模式
- **PCI 合规** - 敏感数据处理
- **幂等性** - 重复提交处理
- **超时处理** - 银行响应延迟

---

## DevOps 场景

### 4. CI/CD 流水线

```
$kimi-autoresearch:scenario
Seed: 部署流水线
Domain: devops
```

**场景维度**:
- **Blue/Green 部署** - 零停机发布
- **Canary 发布** - 渐进式流量切换
- **Rollback 触发** - 健康检查失败
- **Secret 轮换** - 证书自动更新

---

### 5. 监控告警

```
$kimi-autoresearch:scenario
Seed: 微服务监控
```

**场景**:
- **级联故障** - 服务雪崩检测
- **假阳性** - 告警疲劳处理
- **容量规划** - 资源使用预测
- **事后分析** - 故障复盘模板

---

## 安全场景

### 6. 认证系统

```
$kimi-autoresearch:scenario
Seed: OAuth2 实现
Domain: security
```

**攻击场景**:
- **Token 伪造** - JWT 签名验证
- **重放攻击** - nonce 机制
- **会话劫持** - 安全 cookie 设置
- **CSRF 防护** - 状态令牌验证

---

## 产品场景

### 7. 用户引导流程

```
$kimi-autoresearch:scenario
Seed: 新用户引导
Domain: product
```

**场景**:
- **跳过处理** - 用户跳过引导
- **断点续传** - 中断后重新进入
- **A/B 测试** - 不同引导版本
- **转化率** - 关键步骤流失

---

## 使用模式

### 链式调用

```
# 场景探索 → 问题修复
$kimi-autoresearch:scenario
Seed: 支付流程

# 发现问题后
$kimi-autoresearch:fix
Target: Fix security issues found

# 验证修复
$kimi-autoresearch:security
Scope: src/payment/
```

### 导出结果

```json
{
  "seed": "用户注册",
  "scenarios": [
    {
      "dimension": "Scale",
      "title": "10k TPS 并发注册",
      "description": "...",
      "priority": "P1"
    }
  ]
}
```

---

## 参考

- mode-scenario.md - 完整协议规范
- uditgoenka/autoresearch/guide/scenario/ - 详细示例
