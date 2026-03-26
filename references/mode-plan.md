# Plan Mode Protocol

Plan mode is an interactive wizard that converts a vague goal into a validated, ready-to-execute autoresearch configuration.

## Purpose

The hardest part of autoresearch isn't the loop—it's defining:
- **Scope**: What files can be modified?
- **Metric**: What number should improve?
- **Verify**: How do we measure it?
- **Direction**: Higher or lower is better?

Plan mode automates this discovery through an interactive wizard.

## Process

### Phase 1: Goal Capture

Extract the user's goal in plain language.

**Examples**:
- "Make the API faster"
- "Improve test coverage"
- "Reduce bundle size"
- "Eliminate type errors"
- "Fix the failing tests"

### Phase 2: Scope Definition

Auto-discover what files should be in scope:

1. **Repository analysis**:
   - Detect project type (Node.js, Python, Go, etc.)
   - Find source directories (`src/`, `lib/`, `app/`, etc.)
   - Identify test directories
   - Find configuration files

2. **File pattern matching**:
   - Code: `src/**/*.{js,ts,py,go}`
   - Tests: `tests/**/*.test.{js,ts}`
   - Types: `src/**/*.ts`
   - Styles: `src/**/*.{css,scss}`

3. **Smart exclusions**:
   - `node_modules/`
   - `dist/`, `build/`
   - `.git/`
   - Generated files

**Confirmation**: Show discovered scope, allow user to refine.

### Phase 3: Metric Definition

Based on goal and scope, propose metrics:

| Goal | Proposed Metric | Verify Command |
|------|----------------|----------------|
| "Make API faster" | p95 latency | `curl -w "%{time_total}" ...` |
| "Improve coverage" | Coverage % | `npm test -- --coverage` |
| "Reduce bundle" | Bundle size (KB) | `ls -la dist/*.js` |
| "Eliminate type errors" | Type error count | `tsc --noEmit 2>&1 \| grep error` |
| "Fix failing tests" | Failed test count | `pytest --tb=no -q` |

**User selects** or **confirms** metric.

### Phase 4: Direction Definition

Determine if higher or lower is better:

| Metric | Direction |
|--------|-----------|
| Coverage, Performance score | higher |
| Latency, Bundle size, Error count | lower |
| Test pass rate | higher |

### Phase 5: Verify Command Validation

The verify command must:
1. **Output a number** - Extractable via regex
2. **Exit 0 on success** - Even if metric is "bad"
3. **Be deterministic** - Same input → same output
4. **Be fast** - Under 5 minutes ideally

**Dry-run validation**:
```bash
# Run verify command
# Check if output contains number
# Confirm it exits 0
```

If validation fails:
- Debug the command
- Suggest alternatives
- Allow user to provide custom command

### Phase 6: Guard Command (Optional)

Suggest a guard command if regression risk exists:

| Change Type | Suggested Guard |
|-------------|-----------------|
| Type changes | `tsc --noEmit` |
| Test changes | `npm test` |
| Build changes | `npm run build` |
| API changes | Integration tests |

**User can**:
- Accept suggested guard
- Provide custom guard
- Skip guard (not recommended)

### Phase 7: Configuration Summary

Present complete configuration:

```yaml
Goal: Reduce type errors
Scope: src/**/*.ts
Metric: TypeScript error count
Direction: lower
Verify: tsc --noEmit 2>&1 | grep -c "error TS"
Guard: npm run build
Iterations: 20 (optional)
```

**User confirms** or **modifies** before proceeding.

## Auto-Detection Heuristics

### Project Type Detection

| Files Present | Project Type |
|--------------|--------------|
| `package.json` | Node.js |
| `requirements.txt`, `setup.py` | Python |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `pom.xml`, `build.gradle` | Java |
| `Gemfile` | Ruby |

### Tool Detection

| Tool | Detection |
|------|-----------|
| Jest | `jest` in package.json |
| pytest | `pytest` available |
| TypeScript | `typescript` in package.json |
| ESLint | `.eslintrc` exists |
| Black/Ruff | `pyproject.toml` |

## Interactive Flow

```
User: /autoresearch:plan
       "Make the API faster"

Kimi: Analyzing your repository...
      
      Detected: Node.js + Express API
      API files: src/api/**/*.ts (14 files)
      
      What metric matters most?
      1. p95 response latency
      2. Requests per second (throughput)
      3. Cold start time
      
User: 1

Kimi: Proposed configuration:
      
      Goal: Reduce API p95 latency
      Scope: src/api/**/*.ts
      Metric: p95 latency (ms)
      Direction: lower
      Verify: npm run bench:api
      Guard: npm test
      
      Run this configuration? [Y/n/modify]

User: Y

Kimi: Configuration confirmed.
      Run with: $kimi-autoresearch
      
      Or customize:
      $kimi-autoresearch
      Goal: Reduce API p95 latency
      Iterations: 50
```

## Output

Plan mode produces:

1. **Console output**: Interactive wizard
2. **Launch-ready config**: Copy-paste command
3. **Configuration summary**: Can be saved to file

## Chaining

Plan feeds into the main autoresearch loop:

```
$kimi-autoresearch:plan
# ...generates config...

$kimi-autoresearch
# ...uses config...
```

Or combined:

```
$kimi-autoresearch:plan --auto-run
# Plans and immediately starts
```

## Edge Cases

### Ambiguous Goal

**Input**: "Improve the code"

**Response**:
```
"Improve" could mean many things:
1. Better test coverage
2. Fewer lint warnings
3. Better type safety
4. Faster performance
5. Smaller bundle size

Which would you like to focus on?
```

### No Detectable Metric

**Input**: "Refactor for cleaner code"

**Response**:
```
"Cleaner code" is subjective. Can we measure it?
Options:
1. Lint warnings count (measurable)
2. Cyclomatic complexity (measurable)
3. Lines of code (measurable, lower is not always better)
4. Manual review (not suitable for autoresearch)

I suggest we use lint warnings. Agree?
```

### Verify Command Fails

**Error**: Command exits non-zero or outputs no number

**Response**:
```
Verify command failed: npm test -- --coverage

Debug:
- Tests are failing (exit code 1)
- Coverage not found in output

Options:
1. Fix tests first, then plan
2. Use different metric
3. Provide custom verify command
```
