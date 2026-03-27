# Autoresearch Quick Reference

## Quick Commands

### Start a Run

```bash
# Basic
$kimi-autoresearch
Goal: Reduce type errors

# With all options
$kimi-autoresearch
Goal: Increase test coverage to 90%
Scope: src/**/*.ts
Metric: coverage %
Verify: npm test -- --coverage | grep "All files"
Guard: npm run build
Direction: higher
Iterations: 20
```

### Mode Shortcuts

```bash
# Plan mode - interactive wizard
$kimi-autoresearch:plan
Goal: Make API faster

# Debug mode - find bugs
$kimi-autoresearch:debug
Symptom: API returns 500
Scope: src/api/**/*.ts

# Fix mode - auto-fix errors
$kimi-autoresearch:fix
Target: Fix all failing tests

# Security mode - audit
$kimi-autoresearch:security
Scope: src/api/**/*.ts
Focus: SQL injection

# Ship mode - release
$kimi-autoresearch:ship
Type: code-pr
Target: main

# Scenario mode - generate test scenarios
$kimi-autoresearch:scenario
Seed: User checkout flow
```

## Common Verify Commands

### TypeScript

```bash
# Count type errors
tsc --noEmit 2>&1 | grep -c "error TS"

# Count `any` types
grep -r "any" src/**/*.ts | wc -l
```

### JavaScript/Node.js

```bash
# Test coverage
npm test -- --coverage | grep "All files" | awk '{print $2}'

# Lint errors
npm run lint 2>&1 | grep -c "error"

# Bundle size
npm run build && du -k dist/*.js | cut -f1
```

### Python

```bash
# Test coverage
pytest --cov=src --cov-report=term | grep TOTAL | awk '{print $2}'

# Type errors
mypy src/ | grep -c "error"

# Lint errors
ruff check src/ | grep -c "E\|F"
```

### Go

```bash
# Build errors
go build ./... 2>&1 | grep -c "error"

# Test coverage
go test -cover ./... | grep -o "coverage: [0-9.]*%"

# Lint issues
golangci-lint run | grep -c "^[^#]"
```

## Guard Commands

```bash
# Type check (don't modify)
tsc --noEmit

# Run tests
npm test
pytest

# Build
npm run build
go build ./...

# Lint
npm run lint
ruff check src/
```

## File Locations

| File | Purpose |
|------|---------|
| `autoresearch-results.tsv` | Iteration results log |
| `autoresearch-state.json` | Current run state (includes loop_control, agent_config) |
| `autoresearch-runtime.json` | Background runtime state |
| `autoresearch-lessons.md` | Cross-run learnings |
| `autoresearch-report.md` | Final summary report |
| `.autoresearch-daemon-prompt.txt` | Daemon prompt file |
| `.autoresearch-infinite-prompt.txt` | Infinite mode prompt file |

## Decision Rules

| Metric Change | Guard | Decision |
|--------------|-------|----------|
| Improved | Passed | ✓ Keep |
| Improved | Failed | ↻ Rework (max 2x) |
| Same | - | ✗ Discard |
| Worse | - | ✗ Discard |

## Stuck Recovery

| Pattern | Action |
|---------|--------|
| 3+ discards | REFINE strategy |
| 5+ discards | PIVOT approach |
| 2 pivots + no improvement | Search web |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success / Improved |
| 1 | No improvement |
| 2 | Hard blocker |
| 3 | Config error |
| 4 | Runtime error |

## Ralph Loop Stop Signal

To stop a Ralph loop gracefully, output exactly:

```
<choice>STOP</choice>
```

This is the standard Ralph loop termination signal recognized by Kimi.

Stop conditions:
- Target metric reached
- Max iterations reached (`Iterations` or `MaxRalphIterations`)
- 5+ consecutive discards with 2+ pivots (truly stuck)

## Git Workflow

```bash
# Each iteration:
git add -A
git commit -m "experiment: description"
# Verify...
git revert --no-edit HEAD  # if discard
```

## Helper Scripts (Pure Tools - No AI)

These scripts perform mechanical tasks only. They do NOT analyze code or generate changes.

### 基础工具

```bash
# Initialize run - setup state and TSV
python scripts/autoresearch_init_run.py \
  --goal "Reduce errors" \
  --metric "error count" \
  --verify "tsc --noEmit 2>&1 | grep -c error"

# Health check - verify environment
python scripts/autoresearch_health_check.py

# Git operations
python scripts/check_git.py --action commit --message "experiment: description"
python scripts/check_git.py --action revert

# Get baseline - run verify command
python scripts/get_baseline.py --verify "your-command" --parse-number

# Decision helper - numerical comparison
python scripts/autoresearch_decision.py --action decide \
  --current 42 --baseline 50 --direction lower --guard-passed true

# Log result - append to TSV
python scripts/log_result.py --iteration 1 --commit abc123 \
  --metric 42 --status keep --description "Fixed types"

# Lessons management
python scripts/autoresearch_lessons.py add "This worked well" --type positive
python scripts/autoresearch_lessons.py list
```

### Ralph Loop Control ⭐NEW

```bash
# Check Ralph loop status
python scripts/autoresearch_ralph.py status

# Set loop control parameters
python scripts/autoresearch_ralph.py set-loop \
  --max-steps 30 \
  --max-retries 5 \
  --max-ralph 100

# Set agent configuration
python scripts/autoresearch_ralph.py set-agent --agent okabe
python scripts/autoresearch_ralph.py set-agent --agent-file ./custom-agent.toml

# Check stop conditions
python scripts/autoresearch_ralph.py check-stop --current-metric 42

# Emit stop signal
python scripts/autoresearch_ralph.py stop --reason "Target reached"
```

### 无人值守 Daemon

```bash
# Start daemon configuration
python scripts/autoresearch_daemon.py start \
  --goal "Add type hints" \
  --scope "src/" \
  --verify "mypy src/ | grep -c error" \
  --iterations 100 \
  --max-steps-per-turn 30 \
  --max-ralph-iterations 100 \
  --agent okabe

# Check daemon status
python scripts/autoresearch_daemon.py status

# Pause/Resume/Stop
python scripts/autoresearch_daemon.py pause
python scripts/autoresearch_daemon.py resume
python scripts/autoresearch_daemon.py stop
```

### 无限运行模式 ⭐NEW

```bash
# Start infinite run (no time limit)
python scripts/autoresearch_infinite.py start \
  --goal "Refactor entire codebase" \
  --scope "src/" \
  --verify "npm test | grep -c failing"

# Check infinite run status
python scripts/autoresearch_infinite.py status

# Trigger manual relay
python scripts/autoresearch_infinite.py relay

# Stop infinite run
python scripts/autoresearch_infinite.py stop
```

### 实时监控 ⭐NEW

```bash
# Generate HTML dashboard
python scripts/autoresearch_monitor.py dashboard --open

# Generate text report
python scripts/autoresearch_monitor.py report

# Watch for changes (live updates)
python scripts/autoresearch_monitor.py watch --interval 5
```

### 会话弹性 ⭐NEW

```bash
# Run protocol fingerprint check
python scripts/autoresearch_resilience.py check

# Generate resilience report
python scripts/autoresearch_resilience.py report

# Perform reanchor (reload protocol)
python scripts/autoresearch_resilience.py reanchor --iteration 40

# Perform session split
python scripts/autoresearch_resilience.py split --iteration 40
```

**Note**: The actual iteration loop is driven by Kimi following the protocol in SKILL.md. Python scripts are pure tools for recording, git operations, and verification.

## Kimi-Specific Tips

### Background Tasks

```python
# In Kimi, use background task for long runs
$kimi-autoresearch
Goal: Optimize all day
Iterations: 1000
Background: true
```

### Shell with Background

```python
# Or use Shell with run_in_background
Shell(
    command="python scripts/autoresearch_workflow.py --config config.json",
    run_in_background=True,
    description="Autoresearch optimization"
)
```

### Task Management

```python
# Check background tasks
TaskList()

# Get task output
TaskOutput(task_id="xxx")

# Stop task if needed
TaskStop(task_id="xxx")
```

## Troubleshooting

### "Not a git repository"

```bash
git init
git add .
git commit -m "Initial commit"
```

### "Verify command failed"

1. Test command manually: `your-verify-command`
2. Ensure it outputs a number
3. Check exit code: `echo $?`

### "No improvement"

- Try different approach
- Expand scope
- Check if metric is actually measurable
- Review lessons: `cat autoresearch-lessons.md`

### "Disk full"

```bash
# Clean up old results
rm autoresearch-results.*.tsv
rm autoresearch-state.*.json
```

## Best Practices

1. **Start small**: 5-10 iterations to test
2. **Verify manually**: Test your verify command first
3. **Use guard**: Always have a safety check
4. **Commit often**: Let autoresearch handle git
5. **Review lessons**: Check what worked before
6. **Set target**: Stop when goal reached
7. **Monitor disk**: Long runs can generate files
8. **Background for >50 iterations**: Don't block session
