# Ship Mode Protocol

Ship mode is a universal shipping workflow for code, content, marketing, sales, research, or design assets.

## Overview

Ship mode runs through 8 phases to safely deliver work:

```
Identify → Inventory → Checklist → Prepare → Dry-run → Ship → Verify → Log
```

## Supported Types

| Type | Description | Auto-Detection |
|------|-------------|----------------|
| `code-pr` | Pull request to main branch | Git branch + open PR |
| `code-release` | Version release | Git tag + version file |
| `deployment` | Deploy to production | Deploy config files |
| `content` | Blog post, article | Markdown files in content/ |
| `marketing-email` | Email campaign | Email template files |
| `marketing-campaign` | Multi-channel campaign | Campaign config |
| `sales` | Sales deck, proposal | Presentation files |
| `research` | Research paper, report | Document files |
| `design` | Design assets, mockups | Design files (Figma export, etc.) |

## Process

### Phase 1: Identify

Auto-detect what is being shipped:

1. **Check git state**:
   - Current branch
   - Uncommitted changes
   - Ahead/behind remote
   - Open PRs

2. **Check file patterns**:
   - Code changes: `src/**/*`, `lib/**/*`, etc.
   - Content: `content/**/*`, `posts/**/*`, etc.
   - Config: `package.json` version changes, etc.

3. **Check CI/CD**:
   - GitHub Actions workflows
   - Deployment configs
   - Environment variables

Output: Detected type + confidence score

### Phase 2: Inventory

Catalog everything that will be shipped:

1. **Files inventory**:
   ```bash
   git diff --name-only origin/main
   git status --short
   ```

2. **Dependency check**:
   - New dependencies added?
   - Version updates?
   - Lock file changes?

3. **Breaking changes**:
   - API changes
   - Database migrations
   - Config changes

4. **Security review**:
   - Secrets in diff?
   - New external URLs?
   - Permission changes?

### Phase 3: Checklist

Generate type-specific checklist:

#### Code PR Checklist

- [ ] Tests pass
- [ ] Linting passes
- [ ] Type checking passes
- [ ] Code review approved
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] No secrets committed
- [ ] No console.logs left
- [ ] No broken links
- [ ] Backwards compatible

#### Deployment Checklist

- [ ] Staging tests pass
- [ ] Database migrations tested
- [ ] Environment variables set
- [ ] Health checks defined
- [ ] Rollback plan ready
- [ ] Monitoring alerts configured
- [ ] SSL certificates valid
- [ ] CDN cache cleared (if needed)

#### Content Checklist

- [ ] Grammar/spelling check
- [ ] Links verified
- [ ] Images optimized
- [ ] Meta tags present
- [ ] Preview tested
- [ ] SEO check
- [ ] Mobile responsive

### Phase 4: Prepare

Execute pre-ship preparations:

1. **Final sync**:
   ```bash
   git pull origin main
   git push origin <branch>
   ```

2. **Run checks**:
   - Full test suite
   - Build verification
   - Security scan

3. **Generate artifacts**:
   - Build outputs
   - Documentation
   - Release notes

4. **Staging deploy** (if applicable):
   - Deploy to staging
   - Run smoke tests
   - Verify functionality

### Phase 5: Dry-run

Simulate the ship without actual side effects:

1. **Code PR dry-run**:
   - Merge simulation: `git merge --no-commit --no-ff origin/main`
   - Post-merge tests
   - Abort: `git merge --abort`

2. **Deployment dry-run**:
   - Validate deployment config
   - Check permissions
   - Simulate deployment steps

3. **Content dry-run**:
   - Build preview
   - Link check
   - Image verification

### Phase 6: Ship

Execute the actual ship:

1. **Code PR**:
   ```bash
   gh pr merge --squash --delete-branch
   ```

2. **Release**:
   ```bash
   git tag -a v1.2.3 -m "Release v1.2.3"
   git push origin v1.2.3
   gh release create v1.2.3
   ```

3. **Deployment**:
   ```bash
   # Trigger deployment via CI/CD
   gh workflow run deploy.yml
   ```

4. **Content**:
   ```bash
   git push origin main
   # Trigger publish workflow
   ```

### Phase 7: Verify

Post-ship verification:

1. **Immediate verification** (0-5 min):
   - Deployment successful?
   - Service healthy?
   - No errors in logs?

2. **Short-term verification** (5-30 min):
   - Smoke tests pass?
   - Key metrics stable?
   - No error spikes?

3. **Long-term monitoring** (optional):
   - `--monitor 15` for 15-minute monitoring
   - Check dashboards
   - Verify alerts

### Phase 8: Log

Record the shipment:

```
autoresearch-ship-log.tsv
```

| timestamp | type | target | commit | duration | status | notes |
|-----------|------|--------|--------|----------|--------|-------|

## Commands

### Basic Usage

```
$kimi-autoresearch:ship
```

Ship mode auto-detects type and runs interactively.

### With Flags

```
$kimi-autoresearch:ship
Type: code-pr
Target: main
Dry-run: true
Auto: false
Monitor: 15
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--type` | Force specific type | auto-detect |
| `--target` | Target branch/environment | main/production |
| `--dry-run` | Validate without shipping | true |
| `--auto` | Auto-approve if checks pass | false |
| `--force` | Skip non-critical items | false |
| `--monitor N` | Monitor for N minutes | 0 |
| `--checklist-only` | Only show checklist | false |
| `--rollback` | Rollback last ship | false |

## Decision Flow

```
Start
  │
  ▼
Identify type ──► Can't identify? ──► Ask user
  │
  ▼
Inventory
  │
  ├─► Critical issues? ──► Block and report
  │
  ▼
Generate checklist
  │
  ▼
Prepare (tests, build, staging)
  │
  ├─► Preparation failed? ──► Block and report
  │
  ▼
Dry-run
  │
  ├─► Dry-run failed? ──► Block and report
  │
  ▼
User confirmation (unless --auto)
  │
  ▼
Ship
  │
  ▼
Verify
  │
  ├─► Verification failed? ──► Rollback or alert
  │
  ▼
Log and complete
```

## Safety Mechanisms

1. **Git safety**:
   - Clean worktree check
   - Remote sync verification
   - Branch protection check

2. **Test safety**:
   - All tests must pass
   - Guard checks enforced
   - Staging verification (if available)

3. **Rollback ready**:
   - Previous state recorded
   - Rollback command ready
   - Recovery plan documented

4. **Human checkpoints**:
   - Critical decisions require confirmation
   - `--auto` only for trusted paths
   - `--force` logs warnings

## Output Files

- `autoresearch-ship-log.tsv` - Ship history
- `autoresearch-ship-report.md` - Detailed report
- Console output - Real-time progress

## Integration with Other Modes

Ship can chain with other modes:

```
# Security audit before shipping
$kimi-autoresearch:security
$kimi-autoresearch:ship

# Auto-fix then ship
$kimi-autoresearch:fix
$kimi-autoresearch:ship --auto

# Full pipeline
$kimi-autoresearch:debug --fix
$kimi-autoresearch:security --fix
$kimi-autoresearch:ship --auto
```
