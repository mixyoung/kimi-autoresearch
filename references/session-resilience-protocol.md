# Session Resilience Protocol

长期运行稳定性协议 - 解决长时间运行会话的上下文漂移问题。

## 问题背景

长时间运行的会话（20+迭代）可能因为上下文压缩而导致技能规则遗忘。

## 防御机制

### 1. 自动重新锚定 (Auto Re-Anchoring)

每10次迭代（或压缩后更频繁），运行协议指纹检查：

```python
def protocol_fingerprint_check() -> dict:
    """验证关键规则是否仍然记忆完整"""
    checks = {
        "core_loop": "modify → verify → keep/discard → repeat",
        "one_change_rule": "每次迭代只做一次原子修改",
        "verify_first": "修改前必须能机械验证",
        "git_commit_before_verify": "验证前必须先提交",
        "auto_rollback": "失败自动回滚",
    }
    return checks
```

如果检查失败，从磁盘重新读取协议文件。

### 2. 会话分割 (Session Splitting)

当满足以下条件时主动停止循环并保存检查点：
- 上下文已被压缩2次或更多
- 迭代计数达到40

结果日志中包含 `[SESSION-SPLIT]` 条目。

### 3. 重新锚定标记

日志中标记 `[RE-ANCHOR]` 事件。

## 实现

```python
# 在迭代循环中添加
if iteration % 10 == 0 or context_was_compacted:
    if not protocol_fingerprint_check():
        reload_protocol_files()
        log_result(status="re-anchor", description="Protocol files reloaded")
```

## 参考

- codex-autoresearch/docs/GUIDE.md
