# Autoresearch Loop Protocol

## Phase 0: Environment Probe

Before starting, probe the environment:

1. **Check git repository**: `git rev-parse --git-dir`
2. **Check for uncommitted changes**: `git status --porcelain`
3. **Load prior state**: Read `autoresearch-state.json` if exists
4. **Detect tooling**: Check for npm, pytest, tsc, etc.

## Phase 1: Context Reading

1. **Read scope files**: Load all files matching the scope pattern
2. **Analyze codebase**: Understand structure and dependencies
3. **Load lessons**: Read `autoresearch-lessons.md` if exists

## Phase 2: Configuration (Wizard)

Extract or confirm:

1. **Goal**: What to achieve (e.g., "eliminate type errors")
2. **Scope**: Which files can be modified (e.g., `src/**/*.ts`)
3. **Metric**: What to measure (e.g., "type error count")
4. **Direction**: `higher` or `lower` is better
5. **Verify**: Command to measure metric
6. **Guard**: Optional safety check (must pass for keep)
7. **Iterations**: Max iterations (optional, unbounded if not specified)
8. **Loop Control** (Ralph Loop): Optional loop control parameters
   - `MaxStepsPerTurn`: Max steps per iteration turn (default: 50)
   - `MaxRetriesPerStep`: Max retries per step (default: 3)
   - `MaxRalphIterations`: Ralph loop iterations (0=off, -1=infinite)
9. **Agent Config**: Optional agent configuration
   - `Agent`: Built-in agent (`default`, `okabe`)
   - `AgentFile`: Path to custom agent file

**Confirmation required**: Show config summary and get user approval.

## Phase 3: Baseline

1. Run verify command on current state
2. Record baseline metric
3. Log iteration 0 as baseline

## Phase 4: Iteration Loop (Kimi-Driven)

**IMPORTANT**: Each iteration MUST be executed by Kimi (or human), NOT automated.

For each iteration:

### Step 1: Review State
- Read `autoresearch-results.tsv` for full history
- Read `git log --oneline -10` to see recent experiments
- Read `autoresearch-lessons.md` for prior learnings
- Review what worked, what failed, what's untried

### Step 2: Pick Hypothesis
- **Analyze**: Understand the codebase structure and current state
- **Hypothesize**: Form ONE concrete hypothesis about what to change
- **Document**: Why this change might improve the metric
- **Strategies**: Use greedy, dependency-order, risk-order, or evolutionary approaches

### Step 3: Make ONE Atomic Change
- Use Kimi's editing tools to modify code
- Make minimal, focused changes
- Ensure change is reversible (independent commit)
- Do NOT batch multiple changes

### Step 4: Git Commit
```bash
python scripts/check_git.py --action commit --message "experiment: <description>"
```

### Step 5: Verify
```bash
# Run the verify command
<verify_command>
# Extract metric from output
```

### Step 6: Guard Check (if configured)
```bash
<guard_command>  # Must pass (exit 0) for change to be kept
```

### Step 7: Decide
```bash
python scripts/autoresearch_decision.py \
  --action decide \
  --current <new_metric> \
  --baseline <baseline> \
  --direction <higher|lower> \
  --guard-passed <true|false>
```

**Actions**:
- **KEEP**: Change improved metric and guard passed
  - Update baseline for next iteration
  - Extract lesson: what worked
- **DISCARD**: Change did not improve or guard failed
  - Revert: `python scripts/check_git.py --action revert`
  - Extract lesson: what failed
- **REWORK**: Metric improved but guard failed (max 2 attempts)

### Step 8: Check Stop Signal (Ralph Loop Protocol)

Check if the loop should stop:

```bash
python scripts/autoresearch_ralph.py check-stop --current-metric <metric>
```

Or:

```bash
python scripts/state_manager.py --action check-stop --current-metric <metric>
```

**Stop conditions**:
- Target metric reached
- Max iterations reached (`Iterations` or `MaxRalphIterations`)
- 5+ consecutive discards with 2+ pivots (truly stuck)

If any stop condition is met, output:
```
<choice>STOP</choice>
```

This is the standard Ralph loop termination signal recognized by Kimi.

### Step 9: Log Result
```bash
python scripts/log_result.py \
  --iteration <num> \
  --commit <hash> \
  --metric <value> \
  --delta <+/-change> \
  --status <keep|discard|crash> \
  --description "<what was tried>"
```

### Step 10: Check Stuck Pattern
```bash
python scripts/autoresearch_decision.py --action check-stuck
```

| Pattern | Action |
|---------|--------|
| 3+ consecutive discards | **REFINE** - adjust within current strategy |
| 5+ consecutive discards | **PIVOT** - try fundamentally different approach |
| 2+ pivots without improvement | **WEB SEARCH** - search for external solutions |

### Step 11: Check Relay (for long runs)

For runs longer than 23 hours, implement automatic relay:

```bash
# Check if relay is needed (at 22 hours)
# Read .autoresearch-infinite.json
# If runtime > 79200 seconds (22 hours):
```

**Relay Protocol:**
1. Save all state
2. Generate summary
3. Update `.autoresearch-infinite.json`
4. Print "[RELAY_NEEDED]"
5. Stop gracefully

**Next Session:**
```bash
# New Background Agent reads relay signal
# Loads state from previous session
# Continues seamlessly
```

Use `autoresearch_infinite.py` for automatic relay management.

### Step 12: Repeat
Continue until: target reached, iteration cap, manual stop, hard blocker, relay triggered, or `<choice>STOP</choice>` signal.

## Phase 5: Summary

1. Generate report: `autoresearch-report.md`
2. Print baseline → best summary
3. List key successful changes

## Stuck Recovery

| Pattern | Trigger | Action |
|---------|---------|--------|
| REFINE | 3 consecutive discards | Adjust within current strategy |
| PIVOT | 5 consecutive discards | Try fundamentally different approach |
| WEB_SEARCH | 2 PIVOTs without improvement | Search for external solutions |

## Hypothesis Selection Strategies

1. **Greedy**: Pick highest-impact change first
2. **Dependency-order**: Fix dependencies before dependents
3. **Risk-order**: Low-risk changes first
4. **Random**: Try random untested approach
5. **Evolutionary**: Combine parts of near-successful attempts

## Change Atomicity Rules

- **One concern per change**: Don't mix refactoring with feature changes
- **Minimal diff**: Change only what's necessary
- **Reversible**: Each change should be independently revertable
- **Testable**: Change should be verifiable in isolation

## Session Resilience (Long Runs)

For runs longer than 40 iterations or 24 hours:

### Auto Re-anchor

Every 10 iterations, verify protocol memory:

```bash
python scripts/autoresearch_resilience.py check
```

If check fails:
1. Re-read SKILL.md
2. Re-read loop-protocol.md
3. Log re-anchor event

### Session Split

At 40 iterations or 2+ context compactions:

```bash
python scripts/autoresearch_resilience.py split --iteration 40
```

**Result:**
- Save checkpoint
- Pause gracefully
- User re-invokes to continue

### State Consistency

Verify TSV and JSON consistency:

```bash
python scripts/autoresearch_resilience.py check
```

See [session-resilience-protocol.md](session-resilience-protocol.md) for details.

## Ralph Loop Mode

Ralph loop is Kimi's official protocol for continuous iteration:

```
$kimi-autoresearch
Goal: Reduce type errors
MaxRalphIterations: 100
MaxStepsPerTurn: 50
MaxRetriesPerStep: 3
Agent: okabe
```

**Configuration via CLI:**
```bash
python scripts/autoresearch_ralph.py set-loop \
  --max-steps 50 \
  --max-retries 3 \
  --max-ralph 100

python scripts/autoresearch_ralph.py set-agent --agent okabe
```

**Stop Signal:**
Output `<choice>STOP</choice>` to stop the Ralph loop gracefully.

## Infinite Mode

Break the 24-hour barrier with automatic relay:

```bash
python scripts/autoresearch_infinite.py start --goal "..."
```

**Mechanism:**
- Session 1: 23 hours → relay
- Session 2: 23 hours → relay
- Session 3+: continues indefinitely
- Automatically sets `max_ralph_iterations` to `-1` (infinite)

See [autoresearch_infinite.py](../scripts/autoresearch_infinite.py) for implementation.

## Monitoring

Real-time progress tracking:

```bash
# HTML dashboard
python scripts/autoresearch_monitor.py dashboard --open

# Text report
python scripts/autoresearch_monitor.py report

# Live watch
python scripts/autoresearch_monitor.py watch --interval 5
```

See [autoresearch_monitor.py](../scripts/autoresearch_monitor.py) for details.
