# Fix Mode Protocol

Fix mode iteratively repairs errors until count reaches zero.

## Quick Start

```
$kimi-autoresearch:fix
Target: Fix all failing tests
Verify: pytest --tb=no -q
```

## Overview

Fix mode iteratively repairs errors until count reaches zero.

## Auto-Detection

Fix mode auto-detects what's broken:

1. **Test failures**: `pytest`, `jest`, `npm test`, etc.
2. **Type errors**: `tsc --noEmit`, `mypy`, etc.
3. **Lint errors**: `eslint`, `pylint`, `ruff`, etc.
4. **Build errors**: `npm run build`, `cargo build`, etc.

Detection order: Blockers first (build), then quality (types/lint), then tests.

## Process

### Phase 1: Error Inventory

1. Run detection command
2. Parse output for error count and locations
3. Categorize by type and file
4. Prioritize: blockers > types > lint > tests

### Phase 2: Prioritization

Fix in this order:
1. **Blockers**: Errors preventing compilation/build
2. **Types**: Type safety issues
3. **Lint**: Style and best practice violations
4. **Tests**: Failing test cases

Within each category, fix by:
- Dependency order (dependencies before dependents)
- File order (fewest errors first for quick wins)
- Risk (low-risk fixes first)

### Phase 3: Iterative Repair

For each error:

1. **Read context**: Understand file and surrounding code
2. **Identify fix**: Determine minimal correct fix
3. **Apply fix**: Make ONE change
4. **Commit**: `git commit -m "fix: <description>"`
5. **Verify**: Run detection command
   - Error count decreased → keep
   - Error count same/increased → revert
6. **Guard**: Run guard command if provided
7. **Log**: Record result

### Phase 4: Completion

Stop when:
- Error count reaches zero
- Iteration limit reached
- User interrupts
- Stuck pattern detected (3+ consecutive failures)

## Fix Patterns

### Type Errors

| Error Pattern | Fix Approach |
|--------------|--------------|
| `any` type | Replace with specific type or `unknown` |
| Missing property | Add property or use optional chaining |
| Type mismatch | Cast, narrow, or fix source type |
| Null/undefined | Add guard or use non-null assertion |

### Test Failures

| Failure Pattern | Fix Approach |
|-----------------|--------------|
| Assertion fail | Fix code or update test expectation |
| Exception thrown | Add error handling or fix bug |
| Timeout | Optimize performance or increase timeout |
| Mock issue | Fix mock setup or implementation |

### Lint Errors

| Error Pattern | Fix Approach |
|--------------|--------------|
| Unused import | Remove import |
| Var naming | Rename to follow convention |
| Complexity | Refactor to reduce complexity |
| Security warning | Address security concern |

## Decision Rules

```
Apply fix
   │
   ▼
Run verify command
   │
   ├─► Error count decreased
   │      │
   │      ▼
   │   Run guard (if provided)
   │      │
   │      ├─► Guard passed ──► KEEP
   │      │
   │      └─► Guard failed ──► REWORK (max 2 attempts)
   │
   ├─► Error count same
   │      │
   │      ▼
   │   REVERT ──► Try different approach
   │
   └─► Error count increased
          │
          ▼
       REVERT ──► Log and continue
```

## Output

Fix mode produces:
1. `autoresearch-results.tsv`: Iteration log
2. Console output: Current fix and progress
3. Summary: Errors fixed, remaining, success rate

## Chaining

Fix can read from Debug mode:
```
$kimi-autoresearch:debug --fix
# ...finds bugs...
# ...auto-chains to fix...
```

Or manually:
```
$kimi-autoresearch:fix --from-debug
```
