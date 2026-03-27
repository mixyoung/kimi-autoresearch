---
name: kimi-autoresearch
description: Autonomous iterative improvement engine using Kimi's Ralph Loop. Triggers a modify-verify-decide loop directly in Kimi to optimize code, fix bugs, improve metrics. Use "$kimi-autoresearch" followed by a goal description to start immediately. No external scripts needed - everything runs natively in Kimi using Ralph Loop mechanism.
---

# Kimi Autoresearch

[![version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/mixyoung/kimi-autoresearch/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A self-directed iterative system for Kimi that continuously cycles through: **modify → verify → retain or discard → repeat**.

Inspired by Karpathy's autoresearch principles, adapted for Kimi Code CLI.

## Quick Start

Just type:

```
$kimi-autoresearch
Goal: Reduce type errors in src/
Verify: tsc --noEmit 2>&1 | grep -c error
```

That's it. Kimi's Ralph Loop takes over and iterates automatically.

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

# With Ralph Loop Control
$kimi-autoresearch
Goal: Reduce type errors
MaxRalphIterations: 50
MaxStepsPerTurn: 30
MaxRetriesPerStep: 5
Agent: okabe
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
| `Iterations` | Max iterations (optional, default: unlimited) | `20` or omit |

## Ralph Loop Protocol

Kimi Autoresearch uses **Kimi's native Ralph Loop**. The prompt repeats automatically, allowing continuous iteration.

### How It Works

1. **User provides goal** via `$kimi-autoresearch`
2. **Kimi performs setup** (check git, measure baseline)
3. **Kimi enters Ralph Loop** - the prompt repeats automatically
4. **Each iteration**: Kimi follows the Single Iteration Protocol
5. **Loop continues** until `<choice>STOP</choice>` or max iterations

### Configuration Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `Goal` | ✅ | - | What to achieve |
| `Verify` | ✅ | - | Command to measure metric |
| `Scope` | ❌ | Current dir | Files to modify |
| `Direction` | ❌ | lower | higher/lower is better |
| `Guard` | ❌ | None | Safety check command |
| `Iterations` | ❌ | 无限 | Max iterations (unset = unlimited) |
| `Target` | ❌ | None | Target metric value |
| `MaxStepsPerTurn` | ❌ | 50 | Max steps per iteration |
| `MaxRetriesPerStep` | ❌ | 3 | Max retries per step |
| `MaxRalphIterations` | ❌ | 0 | Ralph loop iterations |
| `Agent` | ❌ | default | Agent profile |

### Stop Signal

Kimi outputs this when stopping:

```
<choice>STOP</choice>
```

Stop conditions (handled automatically):
1. Target metric reached
2. Max iterations reached
3. Truly stuck (5+ discards, 2+ pivots)

### Internal Tools (Used by Kimi)

Kimi automatically uses these helper scripts during the Ralph Loop:

```bash
# Check git status
python scripts/check_git.py --action check

# Commit changes
python scripts/check_git.py --action commit --message "experiment: fix types"

# Revert failed changes
python scripts/check_git.py --action revert

# Log results
python scripts/log_result.py \
    --iteration 1 --commit abc123 --metric 42 \
    --status keep --description "Fixed auth types"

# Make decisions
python scripts/autoresearch_decision.py --action decide \
    --current 42 --baseline 50 --direction lower --guard-passed true
```

**You don't need to run these manually** - Kimi runs them as part of the Ralph Loop protocol.

## Sub-Agent Configuration

You can specify different agent profiles for specialized behavior:

| Option | Description |
|--------|-------------|
| `Agent` | Built-in agent: `default` or `okabe` |
| `AgentFile` | Path to custom agent configuration file |

Note: `Agent` and `AgentFile` are mutually exclusive.

You can pre-configure agent settings using CLI tools:

```bash
# Set built-in agent
python scripts/autoresearch_ralph.py set-agent --agent okabe

# Set custom agent file
python scripts/autoresearch_ralph.py set-agent --agent-file ./my-agent.toml
```

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

## Ralph Loop Protocol

When you type `$kimi-autoresearch`, Kimi automatically executes:

### Phase 0: Environment Check
```bash
# Check git repository
git rev-parse --git-dir

# Check for uncommitted changes
git status --porcelain

# Detect available tools (npm, pytest, tsc, etc.)
which npm python tsc
```

### Phase 1: Setup
1. Read configuration from user input
2. Check git status (must be clean or stashed)
3. Load prior state if exists

### Phase 2: Baseline Measurement
```bash
# Run verify command to get baseline
<verify_command>
# Extract numeric metric from output
```

Save baseline to `autoresearch-state.json` and log to `autoresearch-results.tsv`.

### Phase 3: Ralph Loop

**The prompt now repeats automatically (Ralph Loop).**

Each iteration, Kimi follows:

1. **Read Context**
   - Read `autoresearch-state.json` for current state
   - Read `autoresearch-results.tsv` for history
   - Read git log (`git log --oneline -5`) to see recent changes
   - Read `autoresearch-lessons.md` for prior learnings

2. **Analyze & Hypothesize**
   - Understand what worked/failed in previous iterations
   - Form **ONE concrete hypothesis** about what to change
   - Document why this change might improve the metric

3. **Execute Change**
   - Make **ONE atomic change** using Kimi's editing tools
   - Keep changes minimal and focused
   - Do NOT batch multiple changes

4. **Git Commit**
   ```bash
   python scripts/check_git.py --action commit --message "experiment: <description>"
   ```

5. **Verify**
   - Run the verify command
   - Extract the metric from output

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

8. **Update State**
   ```bash
   python scripts/state_manager.py --action update-status --status <keep|discard|pivot>
   ```

9. **Check Stop Conditions**
   ```bash
   python scripts/autoresearch_ralph.py check-stop --current-metric <metric>
   ```
   
   If should stop, output: `<choice>STOP</choice>`
   
   Otherwise, check stuck patterns:
   - 3+ discards: **REFINE** strategy
   - 5+ discards: **PIVOT** approach
   - 5+ discards + 2+ pivots: **Web Search**

10. **Ralph Loop Continues**
    - The prompt repeats automatically
    - You perform the next Single Iteration Protocol
    - Loop continues until `<choice>STOP</choice>`

### Phase 4: Summary (After Ralph Loop Stops)
- Print baseline → best summary
- Extract lessons learned
- Generate report with `scripts/generate_report.py`
- Review `autoresearch-results.tsv` for complete history

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

### Ralph Loop Integration

Web search is automatically triggered in Ralph loop mode when:
- 5+ consecutive discards AND 2+ pivots
- Agent outputs `<choice>SEARCH</choice>` signal

The search results are used to generate new hypotheses for the next iterations.

## Running in Background

### Interactive Mode (Default)

```
$kimi-autoresearch
Goal: Reduce type errors
MaxRalphIterations: 50
```

Kimi runs in foreground, you can observe and intervene anytime.

### Background Agent Mode

For long-running tasks, use Kimi's Background Agent:

```python
Agent(
    description="Autoresearch optimization",
    prompt="""
$kimi-autoresearch
Goal: Refactor entire codebase
Scope: src/
Verify: npm test 2>&1 | grep -c failing
Direction: lower
MaxRalphIterations: 100
""",
    run_in_background=True
)
```

The Background Agent:
- Runs Ralph Loop autonomously
- Can operate for up to 24 hours
- Reports progress periodically

### Infinite Mode (Auto-Relay)

For tasks running longer than 24 hours:

```python
# Session 1
Agent(
    description="Infinite autoresearch",
    prompt="""
$kimi-autoresearch
Goal: Optimize entire codebase
MaxRalphIterations: -1

At 22 hours, save state and output [RELAY_NEEDED]
""",
    run_in_background=True
)

# When [RELAY_NEEDED] appears, start Session 2
Agent(
    description="Infinite autoresearch - relay",
    prompt="""
Continue from previous session state...
""",
    run_in_background=True
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
- `autoresearch-state.json` - State snapshot for resume (includes `loop_control` and `agent_config`)
- `autoresearch-runtime.json` - Background runtime state
- `autoresearch-lessons.md` - Cross-run learning
- `autoresearch-report.md` - Final summary report

### State File Structure

The state file now includes loop control configuration:

```json
{
  "iteration": 10,
  "baseline": 47,
  "best": 38,
  "loop_control": {
    "max_steps_per_turn": 50,
    "max_retries_per_step": 3,
    "max_ralph_iterations": 100
  },
  "agent_config": {
    "agent": "okabe",
    "agent_file": null
  }
}
```

## Helper Scripts (Used by Kimi)

These are **mechanical tools** that Kimi calls during the Ralph Loop. You don't need to run them manually.

### Core Tools (Auto-used by Kimi)

| Script | When Used |
|--------|-----------|
| `check_git.py` | Git commit/revert during iterations |
| `log_result.py` | Log each iteration result to TSV |
| `autoresearch_decision.py` | Numerical keep/discard decision |
| `state_manager.py` | Read/write state.json |
| `generate_report.py` | Generate final report |

### Optional Tools (Manual use)

| Script | Purpose |
|--------|---------|
| `autoresearch_ralph.py status` | Check Ralph Loop configuration |
| `autoresearch_ralph.py prompt` | Generate Ralph Loop prompt manually |
| `generate_report.py` | Generate report after completion |

### Example: Check Status

```bash
# Check current status anytime
python scripts/autoresearch_ralph.py status

# Generate prompt manually (if needed)
python scripts/autoresearch_ralph.py prompt

# Generate final report
python scripts/generate_report.py
```

**Note**: In normal usage, just type `$kimi-autoresearch` and Kimi handles everything automatically.

# Pre-configure loop parameters
python scripts/autoresearch_ralph.py set-loop --max-steps 30 --max-retries 5

# Pre-configure agent
python scripts/autoresearch_ralph.py set-agent --agent okabe

# Check if should stop (used within Ralph Loop)
python scripts/autoresearch_ralph.py check-stop --current-metric 42

# Generate prompt anytime
python scripts/autoresearch_ralph.py prompt

# Emit stop signal manually (if needed)
python scripts/autoresearch_ralph.py stop --reason "Target reached"
```

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
