# Release v2.0.0

## 🎉 kimi-autoresearch v2.0.0 Released!

**Release Date**: 2026-03-27  
**Tag**: [v2.0.0](https://github.com/mixyoung/kimi-autoresearch/releases/tag/v2.0.0)

## 🚀 What's New in v2.0.0

### Major Changes

#### 1. Pure Kimi Mode
**Before (v1.x)**:
```bash
python scripts/autoresearch_workflow.py \
    --goal "Reduce errors" \
    --verify "..."
# Then copy prompt to Kimi
```

**After (v2.0)**:
```
$kimi-autoresearch
Goal: Reduce errors
Verify: ...
```

Just type and go!

#### 2. Ralph Loop Integration
- Native Kimi Ralph Loop support
- Automatic iteration control
- `<choice>STOP</choice>` signal
- Configurable loop parameters

#### 3. Simplified Architecture
- Removed manual for-loop control (~200 lines)
- Python scripts are now internal tools
- Cleaner, more reliable codebase

## ✨ New Features

- **Ralph Loop Control**: `MaxStepsPerTurn`, `MaxRetriesPerStep`, `MaxRalphIterations`
- **Agent Support**: Built-in agents (`default`, `okabe`) and custom agent files
- **Unified Prompt Generation**: Single source of truth for Ralph Loop prompts
- **Updated Documentation**: All docs aligned with v2.0 format

## 📊 Statistics

- **Commits**: 5 major commits
- **Files Changed**: 30+ files
- **Lines Changed**: +1,500 / -800
- **Documentation**: 100% updated

## 📦 Installation

### As Kimi Skill

```bash
# Download from releases
curl -L https://github.com/mixyoung/kimi-autoresearch/releases/download/v2.0.0/kimi-autoresearch-2.0.0.skill -o kimi-autoresearch.skill

# Extract to skills directory
unzip kimi-autoresearch.skill -d ~/.agents/skills/kimi-autoresearch
```

### Quick Start

```
$kimi-autoresearch
Goal: Reduce type errors
Verify: tsc --noEmit 2>&1 | grep -c error
```

## 📚 Documentation

- [Migration Guide](VERSION_2_MIGRATION.md) - Moving from v1.x to v2.0
- [Quick Reference](references/quick-reference.md) - Common commands
- [Examples](examples/) - Configuration examples

## 🔗 Links

- **Release**: https://github.com/mixyoung/kimi-autoresearch/releases/tag/v2.0.0
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Full Documentation**: [README.md](README.md)

## 🙏 Thanks

Thanks to everyone who contributed to this release!
