---
name: kimi-autoresearch
description: Autonomous iterative improvement engine for Kimi Code CLI. Runs a modify-verify-decide loop to optimize code, fix bugs, improve metrics, or explore solutions. Use when the user wants to (1) iteratively improve a measurable aspect of their codebase (test coverage, performance, type safety, etc.), (2) autonomously fix errors until resolved, (3) debug issues using scientific method with falsifiable hypotheses, (4) run unattended optimization sessions, or (5) experiment with multiple approaches and keep only improvements. Trigger with "$kimi-autoresearch" followed by a goal description.
---

# Kimi Autoresearch

[![version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/mixyoung/kimi-autoresearch/releases)
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

### Phase 3: Iteration Loop (Kimi-Driven)

**IMPORTANT**: Each iteration MUST be executed by Kimi, not automated scripts.

For each iteration, Kimi MUST:

1. **Read Context**
   - Read all files in the defined scope
   - Read `autoresearch-results.tsv` to understand history
   - Read git log (`git log --oneline -10`) to see what worked/failed
   - Read `autoresearch-lessons.md` for prior learnings

2. **Analyze & Hypothesize**
   - Understand the codebase structure
   - Identify specific improvement opportunities
   - Form **ONE concrete hypothesis** about what to change
   - Document why this change might improve the metric
   - Consider: What worked before? What failed? What's untried?

3. **Execute Change (Manual)**
   - Make **ONE atomic change** to the code using Kimi's editing tools
   - Ensure the change is minimal and focused
   - Do NOT batch multiple changes
   - The change should be easily revertable

4. **Commit**
   ```bash
   python scripts/check_git.py --action commit --message "experiment: <description>"
   ```

5. **Verify**
   - Run the verify command
   - Extract the metric from output
   - Record the new metric value

6. **Decide**
   ```bash
   python scripts/autoresearch_decision.py \
     --action decide \
     --current <new_metric> \
     --baseline <baseline> \
     --direction <higher|lower> \
     --guard-passed <true|false>
   ```
   
   Based on result:
   - **KEEP**: Extract lesson, update baseline for next iteration
   - **DISCARD**: Run `python scripts/check_git.py --action revert`
   - **REWORK**: Attempt fix (max 2 times)

7. **Log Result**
   ```bash
   python scripts/log_result.py \
     --iteration <num> \
     --commit <hash> \
     --metric <value> \
     --status <keep|discard|crash> \
     --description "<what was tried>"
   ```

8. **Check Stuck Pattern**
   ```bash
   python scripts/autoresearch_decision.py --action check-stuck
   ```
   
   If stuck:
   - 3+ discards: **REFINE** - adjust within current strategy
   - 5+ discards: **PIVOT** - try fundamentally different approach
   - 2+ pivots: **Web Search** - search for external solutions

9. **Repeat**
   - Continue to next iteration
   - Stop if: target reached, iteration cap, manual stop, or hard blocker

### Phase 4: Summary
- Print baseline → best summary
- Extract lessons learned
- Generate report with `scripts/generate_report.py`

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

### True Autonomous Mode (New)

Kimi Background Agent can run autoresearch fully autonomously:

```bash
# 1. Start daemon configuration
python scripts/autoresearch_daemon.py start \
  --goal "Add type hints" \
  --scope "src/" \
  --verify "mypy src/ | grep -c error" \
  --direction lower \
  --iterations 100

# This generates a prompt file and instructions

# 2. Launch the Background Agent
Agent(
    description="Autoresearch daemon",
    prompt=read(".autoresearch-daemon-prompt.txt"),
    run_in_background=True
)

# 3. Agent runs autonomously:
#    - Reads state and history
#    - Makes decisions
#    - Modifies code
#    - Commits changes
#    - Verifies results
#    - Logs progress
#    - Repeats until done
```

### Daemon Control

```bash
# Check status
python scripts/autoresearch_daemon.py status

# Pause (agent will check state and stop at next iteration)
python scripts/autoresearch_daemon.py pause

# Resume
python scripts/autoresearch_daemon.py resume

# Stop
python scripts/autoresearch_daemon.py stop
```

### Background Task Capabilities

**Verified**: Background Agent can autonomously:
- ✅ Read files
- ✅ Modify files
- ✅ Execute shell commands
- ✅ Run git operations
- ✅ Make decisions
- ✅ Iterate without user intervention

**Max runtime**: 24 hours (86400 seconds)

### Simple Background Mode

For shorter tasks (< 1 hour):

```
$kimi-autoresearch
Goal: Quick optimization
Iterations: 20
Background: true
```

Or use Shell background:

```python
Shell(
    command="python scripts/autoresearch_workflow.py --config config.json",
    run_in_background=True,
    description="Autoresearch optimization",
    timeout=3600
)
```

### 🚀 Infinite Mode - No Time Limit!

Break the 24-hour barrier with automatic relay:

```bash
# 1. Start infinite mode
python scripts/autoresearch_infinite.py start \
  --goal "Optimize entire codebase" \
  --scope "src/" \
  --verify "npm test 2>&1 | grep -c failing" \
  --direction lower

# 2. Launch first Background Agent
Agent(
    description="Autoresearch infinite runner",
    prompt=read(".autoresearch-infinite-prompt.txt"),
    run_in_background=True
)

# 3. Runs indefinitely!
#    - Each session runs for 23 hours
#    - Automatically triggers relay
#    - New session continues seamlessly
#    - No manual intervention needed
#    - Can run for days, weeks, months...
```

**How it works**:
1. Session 1 runs for 23 hours
2. At 22 hours: prepares relay, saves state
3. Session 2 starts, continues from where Session 1 left off
4. Session 3, 4, 5... continues indefinitely
5. State preserved across all sessions

**Use cases**:
- Long-term optimization projects
- Large codebase refactoring
- Continuous improvement
- "Set and forget" for weeks

```bash
# Check infinite run status
python scripts/autoresearch_infinite.py status

# Stop infinite run
python scripts/autoresearch_infinite.py stop
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

## Helper Scripts (Pure Tools - No AI)

These scripts perform mechanical tasks only. They do NOT analyze code or generate changes.

| Script | Purpose |
|--------|---------|
| `autoresearch_init_run.py` | Initialize run state and TSV log |
| `autoresearch_decision.py` | Numerical keep/discard decision helper |
| `autoresearch_health_check.py` | Pre-run environment checks |
| `autoresearch_launch_gate.py` | Resume or fresh start decision |
| `check_git.py` | Git commit/revert operations |
| `get_baseline.py` | Run verify command and extract metric |
| `log_result.py` | Append result to TSV log |
| `state_manager.py` | Read/write state.json |
| `generate_report.py` | Generate summary report |

**Note**: Scripts like `autoresearch_main.py`, `autoresearch_workflow.py` are entry points that set up the environment, but the actual iteration loop is driven by Kimi following the protocol above.

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
