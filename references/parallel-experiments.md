# Parallel Experiments

Test multiple hypotheses simultaneously using git worktrees.

## Overview

Instead of testing hypotheses one by one, run up to 3 experiments in parallel:

```
Orchestrator (main repo)
├── Worktree A: Hypothesis 1
├── Worktree B: Hypothesis 2
└── Worktree C: Hypothesis 3
     ↓
   Compare results
     ↓
Merge best, discard others
```

## When to Use

### Use Parallel When:

1. **Multiple promising approaches** - Can't decide which to try first
2. **Time-sensitive** - Need results faster
3. **Exploration phase** - Cast a wide net
4. **Complex problem** - Different strategies might work

### Don't Use When:

1. **Single clear path** - One obvious solution
2. **Limited resources** - CPU/disk constrained
3. **Interdependent changes** - Changes affect each other
4. **Simple problem** - Overkill for easy fixes

## Process

### Step 1: Generate Hypotheses

Create 2-3 distinct approaches:

```json
{
  "hypotheses": [
    {
      "id": "conservative",
      "description": "Minimal changes, safest approach",
      "strategy": "add_type_guards"
    },
    {
      "id": "aggressive",
      "description": "Full refactor, most improvement",
      "strategy": "rewrite_module"
    },
    {
      "id": "hybrid",
      "description": "Selective changes, balance",
      "strategy": "extract_interfaces"
    }
  ]
}
```

### Step 2: Create Worktrees

```bash
git worktree add -b autoresearch-worker-1 ../worktree-a
git worktree add -b autoresearch-worker-2 ../worktree-b
git worktree add -b autoresearch-worker-3 ../worktree-c
```

Each worktree is an isolated copy of the repo.

### Step 3: Apply Hypotheses

In each worktree, apply its specific changes:

```
Worktree A: Add minimal type guards
Worktree B: Rewrite entire module
Worktree C: Extract interfaces
```

### Step 4: Run Verification

Run the same verify command in all worktrees:

```bash
cd ../worktree-a && npm test -- --coverage
cd ../worktree-b && npm test -- --coverage
cd ../worktree-c && npm test -- --coverage
```

### Step 5: Compare Results

| Worktree | Metric | Status |
|----------|--------|--------|
| A (conservative) | 85.2% | ✓ |
| B (aggressive) | 87.1% | ✓ |
| C (hybrid) | 82.3% | ✓ |

Winner: B (aggressive) with 87.1%

### Step 6: Merge Winner

```bash
# In main repo
git merge autoresearch-worker-2
git worktree remove ../worktree-a
git worktree remove ../worktree-b
git worktree remove ../worktree-c
```

## Commands

### Run Parallel Experiments

```bash
python scripts/autoresearch_parallel.py run \
  --verify "npm test -- --coverage" \
  --hypotheses hypotheses.json \
  --workers 3
```

### Check Status

```bash
python scripts/autoresearch_parallel.py status
```

### Cleanup

```bash
python scripts/autoresearch_parallel.py cleanup
```

## Hypothesis Definition

### JSON Format

```json
{
  "hypotheses": [
    {
      "id": "unique-name",
      "description": "What this approach does",
      "strategy": "pattern-name",
      "priority": 1,
      "changes": [
        {
          "file": "src/example.ts",
          "action": "add_types"
        }
      ]
    }
  ]
}
```

### Strategies

| Strategy | Description |
|----------|-------------|
| `add_types` | Add TypeScript types |
| `extract_function` | Extract to smaller functions |
| `inline_function` | Inline small functions |
| `add_tests` | Add test coverage |
| `refactor_module` | Major restructuring |
| `optimize_loop` | Loop optimizations |
| `cache_result` | Add caching |

## Best Practices

### 1. Independent Hypotheses

Each hypothesis should be testable independently:

```
✓ Good:
  - Hypothesis A: Type guards in auth.ts
  - Hypothesis B: Type guards in api.ts

✗ Bad:
  - Hypothesis A: Change auth.ts
  - Hypothesis B: Change auth.ts differently (conflict!)
```

### 2. Comparable Metrics

All hypotheses should use the same verify command:

```bash
# Good: Same command, different implementations
npm test -- --coverage

# Bad: Different metrics can't be compared
# Worktree A: npm test
# Worktree B: npm run build
```

### 3. Resource Limits

Don't overload your system:

```bash
# On laptop: 2 workers max
python scripts/autoresearch_parallel.py run --workers 2

# On CI: 3-4 workers
python scripts/autoresearch_parallel.py run --workers 3
```

### 4. Clean Cleanup

Always clean up worktrees:

```bash
# Manual cleanup if needed
git worktree list
git worktree remove -f <path>
git branch -D autoresearch-worker-<n>
```

## Troubleshooting

### "Worktree already exists"

```bash
# Clean up existing
python scripts/autoresearch_parallel.py cleanup

# Or manually
git worktree remove -f <path>
```

### "Not a git repository"

Make sure you're in a git repo with at least one commit.

### "Permission denied" (Windows)

Run as administrator or adjust permissions.

### Disk space issues

Each worktree is a full copy:

```bash
# Check disk space
df -h

# Use fewer workers
python scripts/autoresearch_parallel.py run --workers 2
```

## Integration with Main Loop

Enable parallel mode in main autoresearch:

```
$kimi-autoresearch
Goal: Improve coverage
Parallel: true
Workers: 3
```

When stuck for 3+ iterations:
1. Generate 3 alternative hypotheses
2. Run parallel experiments
3. Continue with winner

## Advanced: Custom Worktree Paths

```bash
python scripts/autoresearch_parallel.py run \
  --verify "npm test" \
  --workers 3 \
  --repo /path/to/repo
```

## Advanced: Post-Processing

After parallel run, automatically merge winner:

```bash
python scripts/autoresearch_parallel.py run \
  --verify "npm test" \
  --auto-merge
```

Or manually review:

```bash
# Check each worktree
cd .autoresearch-worktree-worker-1 && git diff HEAD~1
cd .autoresearch-worktree-worker-2 && git diff HEAD~1

# Decide which to merge
git merge autoresearch-worker-2
```
