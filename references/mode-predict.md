# Predict Mode Protocol

Predict mode uses multi-persona analysis to get expert perspectives before taking action.

## Overview

Before debugging, fixing, or shipping, simulate a team of 5 experts who:
1. **Independently analyze** the code/problem
2. **Debate findings** among themselves
3. **Reach consensus** on recommendations

## The 5 Expert Personas

### 1. 🏗️ System Architect

**Focus**: Design patterns, architecture, long-term maintainability

**Questions they ask**:
- Does this follow established patterns?
- Are the abstractions at the right level?
- Will this scale?
- Is technical debt being introduced?

**Output format**:
```
Architecture Assessment:
- Pattern compliance: [Good/Needs work/Concerning]
- Abstraction level: [Appropriate/Too high/Too low]
- Scalability: [Will scale/Limits identified]
- Technical debt: [None/Acceptable/Concerning]

Recommendations:
1. ...
2. ...
```

### 2. 🔒 Security Analyst

**Focus**: Security vulnerabilities, attack vectors, compliance

**Questions they ask**:
- What could be exploited?
- Are inputs validated?
- Are secrets handled safely?
- What would a threat model show?

**Output format**:
```
Security Assessment:
- Input validation: [Complete/Partial/Missing]
- Secret handling: [Safe/Review needed/Unsafe]
- Attack surface: [Minimal/Moderate/Large]
- Compliance: [Meets standards/Gaps found]

Vulnerabilities:
1. [SEVERITY] Description

Recommendations:
1. ...
```

### 3. ⚡ Performance Engineer

**Focus**: Speed, resource usage, optimization opportunities

**Questions they ask**:
- What are the hot paths?
- Are there N+1 queries?
- Memory usage efficient?
- Could this be async?

**Output format**:
```
Performance Assessment:
- Algorithmic complexity: [Good/Concern/Problem]
- Resource usage: [Efficient/Acceptable/Heavy]
- Bottlenecks: [None identified/List]
- Caching opportunities: [Yes/No]

Optimization suggestions:
1. [Impact] Description
```

### 4. 🛡️ Reliability Engineer

**Focus**: Error handling, resilience, observability

**Questions they ask**:
- What happens when things fail?
- Are errors handled gracefully?
- Is there proper logging/monitoring?
- Can this recover automatically?

**Output format**:
```
Reliability Assessment:
- Error handling: [Complete/Partial/Missing]
- Observability: [Good/Needs improvement]
- Failure modes: [Documented/Identified]
- Recovery: [Automatic/Manual/None]

Reliability gaps:
1. ...

Recommendations:
1. ...
```

### 5. 👿 Devil's Advocate

**Focus**: Challenge assumptions, find blind spots, worst-case scenarios

**Questions they ask**:
- What assumptions are we making?
- What could go spectacularly wrong?
- What are we not considering?
- How could this be misused?

**Output format**:
```
Devil's Advocate Assessment:
- Assumptions challenged: [List]
- Worst-case scenarios: [List]
- Blind spots: [List]
- Misuse potential: [None/Moderate/High]

Concerns:
1. ...

What could go wrong:
1. ...
```

## Process

### Phase 1: Independent Analysis

Each persona independently analyzes the code/problem:

```
Input: Code snippet, problem description, or feature spec

Architect: [Analysis]
Security: [Analysis]
Performance: [Analysis]
Reliability: [Analysis]
Devil's Advocate: [Analysis]
```

### Phase 2: Cross-Review

Each persona reviews others' findings:

```
Architect reviews Security: "The input validation concern is valid..."
Security reviews Performance: "The caching suggestion introduces a race condition..."
...
```

### Phase 3: Consensus Building

Identify agreements and disagreements:

```
Consensus:
- Input validation needs improvement (all agree)
- Caching would help performance (4/5 agree)

Disagreements:
- Architect: Refactoring needed for maintainability
- Performance: Current design is acceptable

Resolution: Refactor core module but keep hot path optimized
```

### Phase 4: Final Recommendations

Synthesize into actionable recommendations:

```
Final Recommendations (by priority):

P0 - Critical:
1. Add input validation (Security + Architect consensus)

P1 - High:
2. Implement caching layer (Performance, with Security caveats)
3. Add error handling for edge cases (Reliability)

P2 - Medium:
4. Consider refactoring for better abstraction (Architect)
5. Add metrics/logging (Reliability)

Out of scope:
- Major redesign (not justified by current needs)
```

## Usage

### Basic Usage

```
$kimi-autoresearch:predict
Analyze: src/api/auth.ts
Context: Implementing OAuth2 flow
```

### Chain with Other Modes

```
$kimi-autoresearch:predict --chain debug
# Generates analysis, then starts debug with pre-ranked hypotheses
```

```
$kimi-autoresearch:predict --chain security
# Multi-persona red team analysis
```

```
$kimi-autoresearch:predict --chain fix
# Get recommendations, then auto-fix
```

```
$kimi-autoresearch:predict --chain scenario,debug,fix
# Full pipeline: analyze → explore → debug → fix
```

## Output Formats

### Analysis Report

```markdown
# Predict Mode Analysis

## Input
- File: src/api/auth.ts
- Context: OAuth2 implementation
- Goal: Security review before deployment

## Individual Assessments

### System Architect
[Assessment details...]

### Security Analyst
[Assessment details...]

### Performance Engineer
[Assessment details...]

### Reliability Engineer
[Assessment details...]

### Devil's Advocate
[Assessment details...]

## Cross-Review Summary

### Agreements
- ...

### Disagreements
- ...

## Consensus Recommendations

### P0 - Critical
1. ...

### P1 - High
1. ...

### P2 - Medium
1. ...

## Pre-Ranked Hypotheses (for chaining)

If debugging, test in this order:
1. Hypothesis: Input validation gap
2. Hypothesis: Token expiration handling
3. Hypothesis: Race condition in token refresh
```

## Decision Matrix

Use this matrix to synthesize recommendations:

| Finding | Architect | Security | Performance | Reliability | Devil | Consensus |
|---------|-----------|----------|-------------|-------------|-------|-----------|
| Input validation | ✓ | ✗ | - | ✓ | ✗ | **Fix** |
| Caching layer | ✓ | ⚠️ | ✓ | ✓ | ✓ | **Implement with safeguards** |
| Refactoring | ✗ | ✓ | ✓ | ✓ | ✓ | **Defer** |
| Async processing | ✓ | ✓ | ✓ | ⚠️ | ✓ | **Implement with error handling** |

Legend:
- ✓ = Approves/Recommends
- ✗ = Concerned/Against
- ⚠️ = Approves with caveats
- - = Neutral/Not applicable

## When to Use

### Use Predict Mode When:

1. **Before major changes** - Get diverse perspectives
2. **Uncertain about approach** - Multiple valid options
3. **High-stakes decisions** - Production changes, security features
4. **Learning codebase** - Understand implications
5. **Code review** - Pre-review before human review

### Skip Predict Mode When:

1. **Trivial changes** - Simple bug fixes, formatting
2. **Well-understood problem** - Clear solution exists
3. **Time-critical** - Emergency fixes
4. **Low impact** - Documentation, comments

## Chaining Patterns

### Pattern 1: Pre-Flight Check

```
predict → ship
```

Get expert sign-off before releasing.

### Pattern 2: Smart Debugging

```
predict → debug
```

Start debugging with pre-ranked hypotheses.

### Pattern 3: Comprehensive Fix

```
predict → debug --fix
```

Analyze, find bugs, auto-fix.

### Pattern 4: Security Audit

```
predict --chain security → security --fix
```

Multi-persona red team → fix findings.

### Pattern 5: Full Pipeline

```
predict → scenario → debug → security → fix → ship
```

Complete quality pipeline before release.

## Tips

1. **Provide context** - More context = better analysis
2. **Specific scope** - Analyze specific files/functions
3. **Read outputs** - Each persona brings unique insights
4. **Note disagreements** - Where experts disagree often matters most
5. **Use chaining** - Don't just predict, act on recommendations
