# Exec Mode Protocol

Exec mode is a non-interactive, CI/CD-friendly execution mode for autoresearch.

## Purpose

- Run autoresearch in automation pipelines
- No interactive prompts
- JSON output for parsing
- Defined exit codes
- API key authentication support

## Use Cases

1. **GitHub Actions**: Optimize code on PR
2. **Scheduled runs**: Nightly optimization
3. **Pre-commit hooks**: Ensure metrics meet thresholds
4. **Release gates**: Verify performance before shipping

## Configuration

All configuration provided upfront via JSON or command-line flags:

```json
{
  "mode": "loop",
  "goal": "Reduce bundle size",
  "scope": "src/**/*.ts",
  "metric": "bundle_size_kb",
  "direction": "lower",
  "verify": "npm run build && du -k dist/main.js | cut -f1",
  "guard": "npm test",
  "iterations": 20,
  "timeout_minutes": 30,
  "loop_control": {
    "max_steps_per_turn": 50,
    "max_retries_per_step": 3,
    "max_ralph_iterations": 0
  },
  "agent_config": {
    "agent": "default",
    "agent_file": null
  }
}
```

Or command-line:

```bash
python -m autoresearch_exec \
  --mode loop \
  --goal "Reduce bundle size" \
  --verify "npm run build && du -k dist/main.js | cut -f1" \
  --direction lower \
  --iterations 20 \
  --max-steps-per-turn 50 \
  --max-retries-per-step 3 \
  --max-ralph-iterations 100
```

## Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success - metric improved | ✅ Continue pipeline |
| 1 | No improvement | ⚠️ Warning, continue or block |
| 2 | Hard blocker | ❌ Stop pipeline |
| 3 | Configuration error | ❌ Stop pipeline |
| 4 | Runtime error | ❌ Stop pipeline |

## Output Format

### Stdout (JSON)

```json
{
  "success": true,
  "exit_code": 0,
  "summary": {
    "baseline": 245.5,
    "best": 198.2,
    "improvement_pct": 19.3,
    "iterations": 20,
    "kept": 12,
    "discarded": 8
  },
  "iterations": [
    {
      "iteration": 0,
      "status": "baseline",
      "metric": 245.5,
      "commit": "a1b2c3d"
    },
    {
      "iteration": 1,
      "status": "keep",
      "metric": 238.1,
      "delta": -7.4,
      "commit": "b2c3d4e",
      "description": "Remove unused lodash imports"
    }
  ],
  "artifacts": {
    "results_tsv": "autoresearch-results.tsv",
    "state_json": "autoresearch-state.json",
    "report_md": "autoresearch-report.md"
  }
}
```

### Stderr (Logs)

Human-readable progress logs:

```
[2024-01-15T10:00:00Z] Starting autoresearch exec
[2024-01-15T10:00:01Z] Baseline: 245.5 KB
[2024-01-15T10:00:05Z] Iteration 1: keep (238.1 KB, -7.4)
[2024-01-15T10:00:12Z] Iteration 2: discard (251.2 KB, +13.1)
...
[2024-01-15T10:05:30Z] Completed 20 iterations
[2024-01-15T10:05:30Z] Best: 198.2 KB (-19.3%)
```

## GitHub Actions Example

```yaml
name: Autoresearch Optimization

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  optimize:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run autoresearch
        run: |
          python -m autoresearch_exec \
            --mode loop \
            --goal "Reduce bundle size" \
            --verify "npm run build && du -k dist/main.js | cut -f1" \
            --direction lower \
            --iterations 10 \
            --output-json results.json
        env:
          AUTORESEARCH_API_KEY: ${{ secrets.AUTORESEARCH_API_KEY }}
      
      - name: Check results
        run: |
          improvement=$(jq '.summary.improvement_pct' results.json)
          if (( $(echo "$improvement > 5" | bc -l) )); then
            echo "Significant improvement: ${improvement}%"
          fi
      
      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: autoresearch-results
          path: |
            autoresearch-results.tsv
            autoresearch-report.md
            results.json
```

## Pre-commit Hook Example

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: autoresearch-coverage
        name: Check test coverage
        entry: python -m autoresearch_exec
        args:
          - --mode=check
          - --metric=coverage
          - --min-threshold=80
        language: python
        pass_filenames: false
```

## Ralph Loop Support

Exec mode supports Ralph loop protocol for continuous iteration:

```bash
python -m autoresearch_exec \
  --mode optimize \
  --goal "Reduce type errors" \
  --verify "tsc --noEmit 2>&1 | grep -c error" \
  --direction lower \
  --max-ralph-iterations 100 \
  --max-steps-per-turn 30 \
  --agent okabe
```

**Ralph Loop Parameters:**
- `--max-steps-per-turn`: Maximum steps per iteration turn (default: 50)
- `--max-retries-per-step`: Maximum retries per step (default: 3)
- `--max-ralph-iterations`: Ralph loop iterations (0=off, -1=infinite)
- `--agent`: Built-in agent (`default`, `okabe`)
- `--agent-file`: Path to custom agent file

**Stop Signal:**
The loop stops when:
- Target metric is reached
- Max iterations reached
- `<choice>STOP</choice>` signal is detected
- 5+ consecutive discards with 2+ pivots

## Modes

### Check Mode

Verify metric meets threshold without making changes:

```bash
python -m autoresearch_exec \
  --mode check \
  --metric coverage \
  --verify "npm test -- --coverage" \
  --min-threshold 80
```

Exit codes:
- 0: Metric meets threshold
- 1: Metric below threshold

### Optimize Mode

Run optimization loop:

```bash
python -m autoresearch_exec \
  --mode optimize \
  --goal "Increase coverage to 90%" \
  --verify "npm test -- --coverage | grep 'All files' | awk '{print $2}'" \
  --direction higher \
  --iterations 20 \
  --target 90
```

Stops early if target reached.

## Safety

### Sandboxing

- No network access (unless explicitly allowed)
- File writes limited to project directory
- Git operations only on current branch
- Maximum runtime enforced

### Rollback

- Original state tagged: `autoresearch-baseline-{timestamp}`
- Failed experiments auto-reverted
- Can abort and rollback mid-run

## Configuration File

`.autoresearch.json` in project root:

```json
{
  "exec": {
    "timeout_minutes": 30,
    "max_disk_mb": 1000,
    "allowed_commands": ["npm", "node", "python"],
    "blocked_paths": [".env", "secrets/"]
  }
}
```

## Error Handling

| Error | Response | Exit Code |
|-------|----------|-----------|
| Verify command fails | Log error, skip iteration | Continue (1) |
| Guard fails | Revert change | Continue |
| Timeout | Stop gracefully, report progress | 1 |
| Out of disk | Stop, cleanup temp files | 4 |
| Git conflict | Stop, notify user | 4 |
