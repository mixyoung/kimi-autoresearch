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

**Confirmation required**: Show config summary and get user approval.

## Phase 3: Baseline

1. Run verify command on current state
2. Record baseline metric
3. Log iteration 0 as baseline

## Phase 4: Iteration Loop

For each iteration:

```python
def iterate(iteration_num):
    # 1. Review state
    read_results_log()
    read_git_history()
    
    # 2. Pick hypothesis
    hypothesis = select_hypothesis(
        what_worked=successful_changes,
        what_failed=discarded_changes,
        lessons=lessons_learned
    )
    
    # 3. Make ONE atomic change
    apply_change(hypothesis)
    
    # 4. Git commit
    git_add_all()
    git_commit(f"experiment: {hypothesis.description}")
    commit_hash = get_current_commit()
    
    # 5. Verify
    exit_code, output = run(verify_command)
    current_metric = extract_number(output)
    
    # 6. Guard check
    guard_passed = True
    if guard_command:
        guard_exit, _ = run(guard_command)
        guard_passed = guard_exit == 0
    
    # 7. Decide
    improved = is_improved(current_metric, baseline, direction)
    
    if improved and guard_passed:
        status = 'keep'
        baseline = current_metric  # Update baseline for next iteration
        extract_lesson(hypothesis, success=True)
    else:
        status = 'discard'
        git_revert_head()
        extract_lesson(hypothesis, success=False)
    
    # 8. Log
    log_result(iteration_num, commit_hash, current_metric, 
               delta, status, hypothesis.description)
    
    # 9. Check for stuck patterns
    update_stuck_counters(status)
    if consecutive_discards >= 3:
        refine_strategy()
    if consecutive_discards >= 5:
        pivot_strategy()
    
    return status
```

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
