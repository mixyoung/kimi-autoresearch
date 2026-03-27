# Kimi Autoresearch

Autonomous iterative improvement for your codebase. Like [codex-autoresearch](https://github.com/leolilinxiao/codex-autoresearch) but for **Kimi Code CLI**.

## Quick Start

```
$kimi-autoresearch
Goal: Reduce type errors
Verify: tsc --noEmit 2>&1 | grep -c error
```

That's it. Kimi's Ralph Loop takes over and iterates automatically.

## How It Works

1. **You provide goal** → `$kimi-autoresearch`
2. **Kimi measures baseline** → Runs verify command
3. **Kimi enters Ralph Loop** → Prompt repeats automatically
4. **Each iteration** → Modify → Verify → Keep/Discard → Log
5. **Loop continues** → Until target reached or `<choice>STOP</choice>`

## Usage Examples

### Basic

```
$kimi-autoresearch
Goal: Reduce type errors
```

### With Configuration

```
$kimi-autoresearch
Goal: Increase test coverage to 90%
Scope: src/**/*.ts
Verify: npm test -- --coverage | grep "All files"
Guard: npm run build
Direction: higher
Iterations: 30
Target: 90
```

### Type Safety

```
$kimi-autoresearch
Goal: Eliminate all `any` types
Scope: src/**/*.ts
Verify: grep -r "any" src/**/*.ts | wc -l
Direction: lower
```

### Test Coverage

```
$kimi-autoresearch
Goal: Increase coverage to 90%
Verify: npm test -- --coverage | grep "All files"
Guard: npm test
Direction: higher
Target: 90
```

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `Goal` | ✅ | - | What to achieve |
| `Verify` | ✅ | - | Command to measure metric (must output number) |
| `Scope` | ❌ | Current dir | Files to modify |
| `Direction` | ❌ | lower | higher/lower is better |
| `Guard` | ❌ | None | Safety check command |
| `Iterations` | ❌ | 10 | Max iterations |
| `Target` | ❌ | None | Stop when metric reaches this |
| `MaxRalphIterations` | ❌ | 0 | Ralph loop limit (0=unlimited) |

## The Loop

Each iteration follows this protocol:

1. **Read Context** - Check state, history, git log
2. **Hypothesize** - Form ONE concrete improvement idea
3. **Change** - Make ONE atomic code change
4. **Commit** - `git commit -m "experiment: ..."`
5. **Verify** - Run verify command
6. **Decide** - Keep (improved) / Discard (revert) / Rework
7. **Log** - Record result to TSV
8. **Repeat** - Ralph Loop continues automatically

## Stop Conditions

Kimi outputs `<choice>STOP</choice>` when:
- Target metric reached
- Max iterations reached
- Truly stuck (5+ discards, 2+ pivots)

## Files

- `autoresearch-results.tsv` - Iteration log
- `autoresearch-state.json` - Current state
- `autoresearch-lessons.md` - Learnings across runs
- `autoresearch-report.md` - Final summary

## Background Mode

For long-running tasks:

```python
Agent(
    description="Autoresearch",
    prompt="""
$kimi-autoresearch
Goal: Refactor entire codebase
Verify: npm test 2>&1 | grep -c failing
MaxRalphIterations: 100
""",
    run_in_background=True
)
```

## Comparison with codex-autoresearch

| Feature | codex-autoresearch | kimi-autoresearch |
|---------|-------------------|-------------------|
| Trigger | `$codex-autoresearch` | `$kimi-autoresearch` ✅ |
| Loop Control | Native | Kimi Ralph Loop ✅ |
| State Management | File-based | File-based ✅ |
| Git Integration | Native | Native ✅ |
| Background Mode | Agent | Agent ✅ |

## Requirements

- Kimi Code CLI
- Git repository
- Verify command that outputs a number

## License

MIT
