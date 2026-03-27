# Debug Mode Protocol

Debug mode uses the scientific method for evidence-driven bug hunting.

## Quick Start

```
$kimi-autoresearch:debug
Symptom: API returns 500 intermittently
Scope: src/api/**/*.ts
```

## Overview

Debug mode uses the scientific method for evidence-driven bug hunting.

## Process

### Phase 1: Symptom Gathering

Collect all available information:
- Error messages and stack traces
- Logs and timestamps
- Environment details
- Reproduction steps

### Phase 2: Code Reconnaissance

Map the error surface:
1. Identify all code paths that could lead to the symptom
2. Trace data flow from input to error
3. Identify external dependencies
4. Map configuration that affects behavior

### Phase 3: Hypothesis Generation

Generate falsifiable hypotheses. Each hypothesis must:
- Be specific (not "something is wrong")
- Be testable with code evidence
- Point to specific file(s) and line(s)
- Include expected vs actual behavior

**Example good hypotheses:**
- "Null pointer at line 42 in auth.ts because user object is undefined"
- "Race condition in cache.ts: async write not awaited before read"
- "Buffer overflow: input validation missing for strings > 1024 chars"

**Example bad hypotheses:**
- "There's a bug somewhere"
- "The code is broken"

### Phase 4: Iterative Testing

Each iteration tests ONE hypothesis:

1. **State hypothesis**: "I believe X causes Y because Z"
2. **Design experiment**: Minimal code change to test hypothesis
3. **Make change**: Implement the test
4. **Verify**: Run reproduction steps
5. **Classify**:
   - `confirmed`: Hypothesis proven, bug found
   - `disproven`: Hypothesis rejected
   - `inconclusive`: Need more data

### Phase 5: Classification & Logging

Every hypothesis gets logged with:
- Status: confirmed/disproven/inconclusive
- Code evidence: file:line references
- Reproduction steps
- Fix approach (if confirmed)

## Investigation Techniques

### 1. Binary Search

When error location unknown:
1. Add logging at midpoint of suspected code path
2. Determine if error occurs before or after
3. Repeat with half the remaining code
4. Continue until exact location found

### 2. Differential Debugging

Compare working vs broken:
1. Identify last known working version (git bisect)
2. Compare code between working and broken
3. Test each difference in isolation

### 3. Minimal Reproduction

Create smallest possible test case:
1. Remove code until error disappears
2. Last removed code is likely culprit
3. Simplify test case to essentials only

### 4. Trace Execution

Add logging at key points:
- Function entry/exit
- State changes
- External calls
- Branch decisions

### 5. Pattern Search

Look for known bug patterns:
- Off-by-one errors
- Null/undefined checks missing
- Resource leaks
- Race conditions
- Injection vulnerabilities

### 6. Working Backwards

From error to cause:
1. Start at error location
2. Trace backwards through call stack
3. Identify where invalid state originated

### 7. Rubber Duck

Explain code line by line:
- Verbal/written explanation forces clarity
- Often reveals assumptions vs reality

## Decision Flow

```
Start
  │
  ▼
Gather symptoms
  │
  ▼
Generate hypothesis ──► Out of hypotheses? ──► Search web/ask human
  │                           │
  ▼                           │
Test hypothesis               │
  │                           │
  ├─► Confirmed ──► Fix bug   │
  │      │                    │
  │      ▼                    │
  │   Verify fix              │
  │      │                    │
  │      ▼                    │
  │   Log finding ◄───────────┘
  │
  ├─► Disproven ──► Log ──► Generate new hypothesis
  │
  └─► Inconclusive ──► Gather more data ──► Generate refined hypothesis
```

## Output

Debug mode produces:
1. `debug-findings.md`: All confirmed bugs with evidence
2. `autoresearch-results.tsv`: Iteration log
3. Console output: Current hypothesis and progress

## Chaining

Debug can chain to Fix mode:
```
$kimi-autoresearch:debug --fix
```

After debugging completes, automatically switch to Fix mode with findings as target.
