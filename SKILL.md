---
name: kimi-autoresearch
description: Autonomous iterative improvement engine for Kimi Code CLI. Runs a modify-verify-decide loop to optimize code, fix bugs, improve metrics, or explore solutions. Use when the user wants to (1) iteratively improve a measurable aspect of their codebase (test coverage, performance, type safety, etc.), (2) autonomously fix errors until resolved, (3) debug issues using scientific method with falsifiable hypotheses, (4) run unattended optimization sessions, or (5) experiment with multiple approaches and keep only improvements. Trigger with "$kimi-autoresearch" followed by a goal description.
---

# Kimi Autoresearch

[![version](https://img.shields.io/badge/version-1.0.2-blue.svg)](https://github.com/mixyoung/kimi-autoresearch/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A self-directed iterative system for Kimi that continuously cycles through: **modify → verify → retain or discard → repeat**.

Inspired by Karpathy's autoresearch principles, adapted for Kimi Code CLI.

## Core Loop

```
LOOP (forever or N iterations):
  1. Review current state + git history + results log
  2. Pick ONE hypothesis based on what worked, what failed, what's untried
  3. Make ONE atomic change
  4. Git commit (before verification)
  5. Run mechanical verification (tests, metrics, counts)
  6. If improved → keep. If worse → git revert. If crashed → fix or skip.
  7. Log the result
  8. Repeat until stop condition, manual stop, or iteration cap
```

## Usage

### Basic Usage

```
$kimi-autoresearch
Goal: Eliminate all `any` types in src/**/*.ts
```

### With Explicit Configuration

```
$kimi-autoresearch
Goal: Increase test coverage to 90%
Scope: src/**/*.ts
Metric: coverage percentage
Verify: npm test -- --coverage | grep "All files"
Guard: npm run build
Iterations: 20
```

## Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `Goal` | What you want to achieve | `Reduce bundle size` |
| `Scope` | Files/paths to modify | `src/**/*.ts` |
| `Metric` | Measurable target | `test coverage %` |
| `Direction` | `higher` or `lower` | `higher` |
| `Verify` | Command to measure metric | `npm test -- --coverage` |
| `Guard` | Safety check (must pass) | `npm run build` |
| `Iterations` | Max iterations (optional) | `20` |

## Modes

### Default Mode: Loop
Iterates toward a measurable target.

```
$kimi-autoresearch
Goal: Reduce type errors to zero
```

### Plan Mode
Interactive wizard to define goal, scope, metric, and verify command.

```
$kimi-autoresearch:plan
Goal: Make API faster
```

### Debug Mode
Evidence-driven bug hunting using falsifiable hypotheses.

```
$kimi-autoresearch:debug
Symptom: API returns 500 intermittently
Scope: src/api/**/*.ts
```

### Fix Mode
Iteratively repairs errors until count reaches zero.

```
$kimi-autoresearch:fix
Target: Fix all failing tests
Verify: pytest --tb=no -q
```

### Security Mode
Read-only security audit using STRIDE + OWASP.

```
$kimi-autoresearch:security
Scope: src/api/**/*.ts
Focus: SQL injection, XSS
```

### Ship Mode
Universal shipping workflow for code, content, marketing, or design assets.

```
$kimi-autoresearch:ship
Type: code-pr
Target: main
Dry-run: true
```

Ship mode runs through 8 phases:
1. **Identify** - Detect what is being shipped
2. **Inventory** - Catalog all files and changes
3. **Checklist** - Generate type-specific checklist
4. **Prepare** - Run final tests and staging
5. **Dry-run** - Simulate without side effects
6. **Ship** - Execute the actual release
7. **Verify** - Post-ship verification
8. **Log** - Record the shipment

**Supported types**: code-pr, code-release, deployment, content, marketing-email, marketing-campaign, sales, research, design

### Scenario Mode
Autonomous scenario exploration for test case generation.

```
$kimi-autoresearch:scenario
Seed: User checkout flow
Depth: deep
Format: test-scenarios
Iterations: 25
```

Generates scenarios across 12 dimensions:
Happy paths, Errors, Edge cases, Abuse, Scale, Concurrency, 
Temporal, Data variation, Permissions, Integrations, Recovery, State transitions

### Exec Mode
Non-interactive CI/CD mode for automation pipelines.

```bash
# In GitHub Actions or other CI
python scripts/autoresearch_exec.py \
  --mode loop \
  --goal "Reduce bundle size" \
  --verify "npm run build && du -k dist/main.js | cut -f1" \
  --direction lower \
  --iterations 20
```

Exit codes:
- `0` - Success, metric improved
- `1` - No improvement
- `2` - Hard blocker
- `3` - Configuration error

## Protocol

### Phase 0: Environment Probe
- Detect CPU/RAM/toolchains
- Check for prior run state using `scripts/autoresearch_launch_gate.py`
- Run health check with `scripts/autoresearch_health_check.py`

### Phase 1: Context Reading
- Read scope files
- Check git status
- Load prior lessons if exist

### Phase 2: Configuration
- Initialize run with `scripts/autoresearch_init_run.py`
- Extract or confirm: Goal, Scope, Metric, Verify, Guard
- Establish baseline measurement
- User confirms configuration

### Phase 3: Iteration Loop
- Run until iteration cap or interrupted
- Each iteration: change → commit → verify → decide
- Use `scripts/autoresearch_decision.py` for keep/discard decisions
- Use `scripts/autoresearch_launch_gate.py` to check stuck patterns
- Log results to TSV with `scripts/log_result.py`

### Phase 4: Summary
- Print baseline → best summary
- Extract lessons learned

## Results Logging

Every iteration logged to `autoresearch-results.tsv`:

```
iteration  commit   metric  delta   status    description
0          a1b2c3d  47      0       baseline  initial any count
1          b2c3d4e  41      -6      keep      add strict types to auth
2          c3d4e5f  49      +8      discard   generic wrapper issue
3          d4e5f6g  38      -3      keep      narrow API handlers
```

## Decision Rules

| Outcome | Action |
|---------|--------|
| Metric improved + Guard passed | Keep change, extract lesson |
| Metric improved + Guard failed | Rework (max 2 attempts) |
| Metric worse | Revert change |
| Crash/Syntax error | Fix immediately or skip |

## Recovery Strategies

| Stuck Pattern | Response |
|---------------|----------|
| 3+ consecutive discards | REFINE current strategy |
| 5+ consecutive discards | PIVOT to new approach |
| 5+ discards + 2+ pivots | **Web Search** for external solutions |
| Syntax error | Auto-fix, don't count as iteration |
| Runtime crash | Attempt fix (max 3 tries) |

## Git Workflow

1. **Before loop**: Ensure clean worktree or stash changes
2. **Each iteration**:
   - `git add -A`
   - `git commit -m "experiment: <description>"`
   - Run verification
   - If discard: `git revert --no-edit HEAD`
3. **Results file**: `autoresearch-results.tsv` (uncommitted)

## Web Search Integration

When stuck (5+ consecutive discards, 2+ pivots), autoresearch can trigger web search to find external solutions:

```bash
# Auto-check and search if stuck
python scripts/autoresearch_web_search.py check

# Manual search with context
python scripts/autoresearch_web_search.py search \
  --goal "Reduce TypeScript errors" \
  --error "TS2345: Argument of type X not assignable" \
  --strategy "strict_mode"

# Generate hypotheses from search results
python scripts/autoresearch_web_search.py hypotheses \
  --search-results results.json
```

In Kimi environment, this automatically uses `SearchWeb` tool when triggered.

## Running in Background

For long-running sessions, use Kimi's background task:

```
$kimi-autoresearch
Goal: Optimize performance
Iterations: 100
Background: true
```

Or use the background controller:

```bash
# Start background runtime
python scripts/autoresearch_background.py start

# Check status
python scripts/autoresearch_background.py status

# Pause/Resume
python scripts/autoresearch_background.py pause
python scripts/autoresearch_background.py resume

# Stop
python scripts/autoresearch_background.py stop
```

## Example Workflows

### Example 1: Type Safety

```
$kimi-autoresearch
Goal: Eliminate all `any` types
Scope: src/**/*.ts
Metric: count of `any`
Verify: grep -r "any" src/**/*.ts | wc -l
Direction: lower
```

**Iteration process:**
1. Baseline: count current `any` occurrences
2. Identify files with most `any` usage
3. Replace one `any` with proper type
4. Commit, run `tsc --noEmit` as guard
5. If type check passes and count decreased → keep
6. Repeat until zero

### Example 2: Test Coverage

```
$kimi-autoresearch
Goal: Increase coverage from 72% to 90%
Verify: npm test -- --coverage | grep "All files"
Guard: npm test
Iterations: 30
```

### Example 3: Bug Hunting

```
$kimi-autoresearch:debug
Symptom: Memory leak in data processing
Scope: src/processing/**/*.py
Iterations: 15
```

## Important Rules

1. **One change per iteration** - Atomic changes for clear causality
2. **Read before write** - Understand full context before modifying
3. **Mechanical verification only** - No subjective "looks good"
4. **Automatic rollback** - Failed changes revert instantly
5. **Git is memory** - Every experiment committed
6. **Simplicity wins** - Equal results + less code = KEEP
7. **When stuck, think harder** - Re-read, combine near-misses

## Files

- `autoresearch-results.tsv` - Results log (uncommitted)
- `autoresearch-state.json` - State snapshot for resume
- `autoresearch-runtime.json` - Background runtime state
- `autoresearch-lessons.md` - Cross-run learning
- `autoresearch-report.md` - Final summary report

## Helper Scripts

Located in `scripts/`:

| Script | Purpose |
|--------|---------|
| `autoresearch_main.py` | Unified CLI entry point |
| `autoresearch_workflow.py` | Complete workflow orchestrator |
| `autoresearch_init_run.py` | Initialize new run with config |
| `autoresearch_decision.py` | Keep/discard decisions + stuck detection |
| `autoresearch_health_check.py` | Pre-run health checks |
| `autoresearch_launch_gate.py` | Resume or fresh start decision |
| `autoresearch_background.py` | Background runtime controller |
| `autoresearch_exec.py` | CI/CD exec mode |
| `autoresearch_lessons.py` | Lessons management |
| `autoresearch_web_search.py` | **Web search when stuck** |
| `autoresearch_parallel.py` | Parallel experiments |
| `autoresearch_predict.py` | Multi-persona prediction |
| `autoresearch_utils.py` | Utility commands |
| `check_git.py` | Git operations wrapper |
| `get_baseline.py` | Get baseline metric |
| `log_result.py` | Log iteration to TSV |
| `run_iteration.py` | Execute single iteration |
| `state_manager.py` | State management |
| `generate_report.py` | Generate final report |

## References

See `references/` for detailed protocols:
- `loop-protocol.md` - Core iteration protocol
- `mode-plan.md` - Plan mode specification
- `mode-debug.md` - Debug mode protocol
- `mode-fix.md` - Fix mode protocol
- `mode-security.md` - Security audit protocol
- `mode-ship.md` - Ship workflow protocol
- `mode-scenario.md` - Scenario exploration
- `mode-predict.md` - Multi-persona prediction
- `mode-learn.md` - Documentation engine
- `mode-exec.md` - CI/CD exec mode
- `parallel-experiments.md` - Parallel testing
- `web-search-protocol.md` - **Web search when stuck**
- `quick-reference.md` - Quick command reference

See `examples/` for configuration examples:
- `typescript-coverage.json` - TypeScript coverage improvement
- `reduce-bundle-size.json` - Bundle size optimization
- `python-type-errors.json` - Python type error elimination

## Limitations

- Requires git repository
- Verify command must output a number or have exit code
- Long runs should use background mode
- User must approve initial configuration
- Ship mode requires manual confirmation for production deployments

## Version Management

Manage releases with the version tool:

```bash
# Show current version
python scripts/autoresearch_version.py show

# Bump version (patch/minor/major)
python scripts/autoresearch_version.py bump patch    # 1.0.0 -> 1.0.1
python scripts/autoresearch_version.py bump minor    # 1.0.0 -> 1.1.0
python scripts/autoresearch_version.py bump major    # 1.0.0 -> 2.0.0

# Set specific version
python scripts/autoresearch_version.py set 1.2.3

# Bump and create git tag
python scripts/autoresearch_version.py bump patch --tag
```

### Automatic Release

Push a tag to trigger GitHub Actions release:

```bash
# After bumping version
git push origin main --tags
```

This will:
- Update version in all files
- Package `.skill` file
- Create GitHub Release with attachments

### Manual Package

```bash
# Windows
.\package.ps1 -Version 1.1.0

# Linux/macOS
./package.sh
```
