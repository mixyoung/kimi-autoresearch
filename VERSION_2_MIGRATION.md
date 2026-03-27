# Version 2.0 - Pure Kimi Mode

## What's New

### 🎯 Pure Kimi Mode

**Before (v1.x)**:
```bash
python scripts/autoresearch_workflow.py \
    --goal "Reduce errors" \
    --verify "..."
# Then copy prompt to Kimi
```

**After (v2.0)**:
```
$kimi-autoresearch
Goal: Reduce errors
Verify: ...
```

Just type and go. No Python scripts needed.

## Why the Change?

**Align with codex-autoresearch experience.**

- Claude Code: `$codex-autoresearch` → works immediately
- Kimi Code CLI (v2.0): `$kimi-autoresearch` → works immediately

Both use their native agent loop:
- Claude: Built-in agent loop
- Kimi: Ralph Loop

## Migration Guide

### For Users

**Old way** (still works, but not recommended):
```bash
python scripts/autoresearch_workflow.py --goal "..."
```

**New way** (recommended):
```
$kimi-autoresearch
Goal: ...
Verify: ...
```

### For Existing Configs

Your JSON configs still work. Just use them directly:

```json
{
  "goal": "Reduce type errors",
  "verify": "tsc --noEmit 2>&1 | grep -c error",
  "direction": "lower"
}
```

Then:
```
$kimi-autoresearch
Goal: Reduce type errors
Verify: tsc --noEmit 2>&1 | grep -c error
Direction: lower
```

## Technical Changes

### Architecture

**v1.x**: Python script manages loop → Kimi executes iterations

**v2.0**: Kimi Ralph Loop manages everything → Python scripts are just tools

```
v1.x: User → Python loop controller → Kimi (per iteration)
v2.0: User → Kimi Ralph Loop (automatic iterations)
```

### File Changes

| File | v1.x | v2.0 |
|------|------|------|
| `workflow.py` | Loop controller | Prompt generator (optional) |
| `autoresearch_ralph.py` | Config tool | Config + prompt tool |
| `state_manager.py` | Complex state | Simple state |
| `SKILL.md` | Complex setup | Simple usage |

## Benefits

1. **Simpler** - No external scripts to run
2. **Faster** - Start immediately with `$kimi-autoresearch`
3. **Aligned** - Same experience as codex-autoresearch
4. **Reliable** - Uses Kimi's tested Ralph Loop

## What Was Removed

- Complex Python-based loop control
- Manual iteration counting
- Session split logic (Ralph Loop handles this)
- Protocol fingerprint checks (Ralph Loop handles this)

## What Stayed

- State management (TSV/JSON)
- Git workflow (commit/revert)
- Decision logic (keep/discard)
- Verification system
- Stuck recovery
- All modes (Debug, Fix, Ship, etc.)

## Backward Compatibility

All v1.x features still work:
- Config files
- State files
- Helper scripts (now used internally by Kimi)
- Reports

## Getting Started

1. Install as Kimi skill
2. Type `$kimi-autoresearch`
3. Provide goal and verify command
4. Let Ralph Loop do the work

That's it.
