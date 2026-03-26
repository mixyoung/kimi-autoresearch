# Web Search Protocol

Automatic web search integration for autoresearch when stuck.

## Overview

When autoresearch gets stuck (5+ consecutive discards, 2+ pivots), it automatically triggers web search to find external solutions and generate new hypotheses.

## When to Trigger

### Trigger Conditions

```python
if consecutive_discards >= 5 and pivot_count >= 2:
    trigger_web_search()
```

| Discards | Pivots | Action |
|----------|--------|--------|
| < 3 | Any | Continue current strategy |
| 3-4 | Any | REFINE strategy |
| 5+ | 0-1 | PIVOT to new approach |
| 5+ | 2+ | **SEARCH web for solutions** |

### Example Stuck Patterns

```
Iteration 1: discard (metric: 47)
Iteration 2: discard (metric: 47)
Iteration 3: discard (metric: 47) → REFINE
Iteration 4: discard (metric: 47)
Iteration 5: discard (metric: 47) → PIVOT
Iteration 6: discard (metric: 48) → PIVOT #2
Iteration 7: **SEARCH** "TypeScript type error solutions"
```

## Process

### Step 1: Generate Search Query

Extract context to build query:

```python
context = {
    'goal': 'Eliminate TypeScript type errors',
    'strategy': 'add_explicit_any',
    'error': 'TS2345: Argument of type X not assignable to Y',
    'metric': 'type error count',
    'discards': 5,
    'pivots': 2
}

query = extract_search_query(context)
# Result: "TS2345 Argument type not assignable TypeScript solutions"
```

Query building rules:
1. Include specific error messages (most important)
2. Add goal keywords
3. Mention tried strategy
4. Keep under 150 characters

### Step 2: Execute Search

In Kimi environment:

```python
results = SearchWeb(query=query, limit=5)
```

In other environments:
```bash
python scripts/autoresearch_web_search.py search \
  --goal "Reduce type errors" \
  --error "TS2345" \
  --strategy "strict_types"
```

### Step 3: Process Results

Analyze search results to extract:

1. **Common solutions** - What worked for others
2. **Best practices** - Recommended approaches
3. **Alternative strategies** - Different ways to solve
4. **Tools/libraries** - Helper utilities

### Step 4: Generate Hypotheses

Convert findings into testable hypotheses:

```json
{
  "source": "web_search",
  "hypotheses": [
    {
      "id": "search-1",
      "strategy": "use_type_assertions",
      "description": "Use 'as Type' assertions for known safe cases",
      "confidence": "high",
      "inspiration": "StackOverflow #456789"
    },
    {
      "id": "search-2",
      "strategy": "refactor_interfaces",
      "description": "Split large interfaces into smaller ones",
      "confidence": "medium",
      "inspiration": "TypeScript docs"
    }
  ]
}
```

### Step 5: Test New Hypotheses

Add web-generated hypotheses to the pool:

```
Original hypotheses: [A, B, C]
Web-generated: [W1, W2]
New pool: [A, B, C, W1, W2]

Next iteration: Try W1 (highest confidence)
```

## Commands

### Check and Auto-Search

```bash
python scripts/autoresearch_web_search.py check \
  --state-file autoresearch-state.json
```

Output if stuck:
```json
{
  "triggered": true,
  "reason": "5 consecutive discards, 2 pivots",
  "query": "TypeScript TS2345 type error solutions",
  "action": "web_search"
}
```

### Manual Search

```bash
python scripts/autoresearch_web_search.py search \
  --goal "Reduce bundle size" \
  --error "webpack optimization failed" \
  --strategy "tree_shaking"
```

### Generate Hypotheses from Results

```bash
python scripts/autoresearch_web_search.py hypotheses \
  --search-results search-output.json \
  --output hypotheses.json
```

## Integration with Main Loop

### In Workflow

```python
# After each discard
decision = check_stuck_pattern(state)

if decision['action'] == 'search':
    # Trigger web search
    search_result = trigger_web_search(state)
    
    # Use Kimi SearchWeb
    web_results = SearchWeb(query=search_result['query'])
    
    # Generate new hypotheses
    new_hypotheses = generate_from_search(web_results)
    
    # Add to hypothesis pool
    hypothesis_pool.extend(new_hypotheses)
    
    # Log the search
    log_lesson(f"Web search triggered: {search_result['query']}")
```

### Decision Flow with Search

```
Start iteration
    ↓
Make change
    ↓
Verify → Success? → Yes → Keep
    ↓ No
Discard
    ↓
Update counters
    ↓
Check stuck pattern
    ↓
5+ discards, 2+ pivots?
    ↓ Yes
Trigger Web Search
    ↓
SearchWeb(query)
    ↓
Generate new hypotheses
    ↓
Try new approach
```

## Query Generation Examples

### TypeScript Errors

| Context | Generated Query |
|---------|-----------------|
| TS2345 error | "TypeScript TS2345 argument not assignable solutions" |
| Strict mode | "TypeScript strict mode migration best practices" |
| Generic issues | "TypeScript generic type inference problems" |

### Performance

| Context | Generated Query |
|---------|-----------------|
| Slow API | "Node.js API performance optimization" |
| High memory | "JavaScript memory leak detection" |
| Bundle size | "Webpack tree shaking configuration" |

### Testing

| Context | Generated Query |
|---------|-----------------|
| Low coverage | "Jest increase test coverage strategies" |
| Flaky tests | "Jest flaky test solutions" |
| Slow tests | "Pytest parallel test execution" |

## Best Practices

### 1. Specific Queries

✓ Good: "TypeScript TS2345 interface extension error"
✗ Bad: "TypeScript error"

### 2. Include Error Codes

Error codes are highly searchable:
- TS2345, ES Lint rules, HTTP status codes

### 3. Context Matters

Include framework/language versions:
- "React 18 useEffect cleanup"
- "Python 3.11 asyncio performance"

### 4. Filter Results

After search, filter by:
- Date (prefer recent solutions)
- Source (prefer official docs, StackOverflow)
- Relevance (match specific error)

### 5. Validate Hypotheses

Not all web solutions apply:
- Check if solution matches your context
- Verify in a separate worktree first
- Consider side effects

## Output Format

### Search Trigger Output

```json
{
  "triggered": true,
  "timestamp": "2024-01-15T10:30:00Z",
  "reason": "5 consecutive discards, 2 pivots",
  "query": "TypeScript strict mode type inference solutions",
  "context": {
    "goal": "Eliminate type errors",
    "strategy": "enable_strict_mode",
    "error": "TS2345: Argument of type...",
    "discards": 5,
    "pivots": 2
  },
  "action": "web_search",
  "note": "SearchWeb tool should be used with this query"
}
```

### Hypothesis Generation Output

```json
{
  "source": "web_search",
  "query": "TypeScript strict mode type inference solutions",
  "hypotheses": [
    {
      "id": "web-1",
      "strategy": "use_type_assertions_sparingly",
      "description": "Use 'as Type' for third-party lib boundaries only",
      "confidence": "high",
      "source": "StackOverflow",
      "estimated_impact": "medium"
    }
  ],
  "search_metadata": {
    "results_examined": 5,
    "sources": ["StackOverflow", "TypeScript Docs", "GitHub Issues"]
  }
}
```

## Configuration

Enable/disable auto-search in config:

```json
{
  "web_search": {
    "enabled": true,
    "trigger_after_discards": 5,
    "trigger_after_pivots": 2,
    "max_results": 5,
    "min_confidence": "medium",
    "excluded_sites": ["example.com"],
    "preferred_sources": ["stackoverflow.com", "docs.python.org"]
  }
}
```

## Limitations

1. **Requires Kimi SearchWeb** - In pure CLI mode, only generates queries
2. **Network dependent** - Needs internet connection
3. **Result quality varies** - Not all web solutions are good
4. **Context matching** - May suggest irrelevant solutions

## Troubleshooting

### Search Not Triggering

Check counters:
```bash
python scripts/autoresearch_decision.py --action check-stuck
```

### Poor Results

Refine query manually:
```bash
python scripts/autoresearch_web_search.py search \
  --error "specific error message" \
  --dry-run
```

### Too Many Hypotheses

Filter by confidence:
```bash
python scripts/autoresearch_web_search.py hypotheses \
  --min-confidence high
```
