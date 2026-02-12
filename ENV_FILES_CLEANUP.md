# Environment Files Cleanup

This document explains the env file consolidation and cleanup.

---

## Problem

We had **23+ env files** with lots of duplication and confusion:
- Multiple files for the same scenarios
- Old files superseded by new ones
- Unclear which file to use
- Redundant examples

---

## Solution

Consolidated to **6 comprehensive env files** covering all scenarios:

### Files KEPT (6 total)

#### 1. **envs/.env.azure-local-input.example** (~13KB)
- **Scenario:** Azure everything (DI + OpenAI + Search) with local file input
- **Cost:** $$$ (~$10-15 per 1000 pages)
- **Use when:** Enterprise quality, no blob storage needed

#### 2. **envs/.env.azure-chromadb-hybrid.example** (~11KB)
- **Scenario:** Azure processing (DI + OpenAI) with ChromaDB storage
- **Cost:** $$ (~$2-3 per 1000 pages)
- **Use when:** Best quality with cost savings (no Azure Search!)

#### 3. **envs/.env.offline-with-vision.example** (~15KB)
- **Scenario:** Fully offline (Markitdown + HuggingFace + ChromaDB)
- **Optional:** GPT-4o vision for images
- **Cost:** FREE (or $2-5 with vision)
- **Use when:** Air-gapped, privacy, development, testing

#### 4. **envs/.env.hybrid-scenarios.example** (~18KB)
- **Scenario:** Mix & match guide with 8 different combinations
- **Cost:** Varies ($0 to $$$)
- **Use when:** Custom requirements, evaluating options

#### 5. **examples/playbooks/.env.basic-pdf.example** (~8KB)
- **Scenario:** Basic playbook example
- **Supports:** Both cloud and offline
- **Use when:** Learning, testing basic workflow

#### 6. **examples/playbooks/.env.production.example** (~13KB)
- **Scenario:** Production deployment example
- **Supports:** Full Azure stack
- **Use when:** Enterprise production deployment

---

## Files REMOVED (14 files)

### Duplicates/Superseded

| Old File | Superseded By | Reason |
|----------|--------------|---------|
| `.env.example` (root) | New files in envs/ | Generic, not useful |
| `envs/.env.chromadb.example` | `.env.offline-with-vision.example` | Offline scenario covered |
| `envs/.env.cohere.example` | `.env.hybrid-scenarios.example` | Cohere covered in hybrid |
| `envs/.env.example` | New specific files | Generic template |
| `envs/.env.example.dev` | `.env.offline-with-vision.example` | Dev covered |
| `envs/.env.example.prod` | `.env.azure-local-input.example` | Prod covered |
| `envs/.env.example.staging` | Not needed | Staging = prod config |
| `envs/.env.hybrid.example` | `.env.azure-chromadb-hybrid.example` | Hybrid covered better |
| `envs/.env.scenario-azure-cohere.example` | `.env.hybrid-scenarios.example` | Covered in scenarios |
| `envs/.env.scenario-azure-openai-default.example` | `.env.azure-local-input.example` | Default Azure covered |
| `envs/.env.scenario-cost-optimized.example` | `.env.hybrid-scenarios.example` | Covered in scenarios |
| `envs/.env.scenario-development.example` | `.env.offline-with-vision.example` | Dev covered |
| `envs/.env.scenario-multilingual.example` | `.env.hybrid-scenarios.example` | Covered in scenarios |
| `envs/.env.scenarios.example` | `.env.hybrid-scenarios.example` | Renamed/improved |

---

## How to Clean Up

### Windows (PowerShell or CMD)

```cmd
REM Run the cleanup script
cleanup-duplicate-envs.bat

REM Then commit
git add -A
git commit -m "chore: Remove duplicate env files and update gitignore"
```

### Linux/Mac

```bash
# Run the cleanup script
chmod +x cleanup-duplicate-envs.sh
./cleanup-duplicate-envs.sh

# Then commit
git add -A
git commit -m "chore: Remove duplicate env files and update gitignore"
```

---

## Updated .gitignore

Added patterns to ignore user-created env files:

```gitignore
# User working env files
.env.working
.env.mine
*.mine

# User copies based on templates
.env.azure-local-input
.env.azure-chromadb-hybrid
.env.offline-with-vision
.env.hybrid-scenarios
.env.basic-pdf
.env.production

# Playbook user files
examples/playbooks/.env
examples/playbooks/.env.*
!examples/playbooks/.env.*.example
examples/playbooks/*.mine

# All backups
.env.backup*
.env.*.backup
backups/
*.backup
backup_*
```

---

## New Recommended Workflow

### Option 1: Edit Templates Directly (Recommended)

```bash
# Edit template files directly with your credentials
notepad envs/.env.azure-local-input.example

# Use with --env-file (no copying!)
python -m ingestor.scenario_validator --env-file envs/.env.azure-local-input.example
python -m ingestor.cli --pdf test.pdf --env-file envs/.env.azure-local-input.example
```

### Option 2: Create .mine Files

```bash
# Copy template to .mine file (gitignored)
cp envs/.env.azure-local-input.example envs/.env.azure-local-input.mine

# Edit your .mine file
notepad envs/.env.azure-local-input.mine

# Use your .mine file
python -m ingestor.cli --pdf test.pdf --env-file envs/.env.azure-local-input.mine
```

### Option 3: Traditional Copy to .env (Old Way)

```bash
# Still works but not recommended
cp envs/.env.azure-local-input.example .env
notepad .env
python -m ingestor.cli --pdf test.pdf
```

---

## Scenario Selection Guide

### Which File Should I Use?

**Need enterprise quality with Azure?**
→ `envs/.env.azure-local-input.example`

**Want to save money (no Azure Search)?**
→ `envs/.env.azure-chromadb-hybrid.example`

**Need 100% offline or FREE?**
→ `envs/.env.offline-with-vision.example`

**Want to mix and match components?**
→ `envs/.env.hybrid-scenarios.example`

**Learning the basics?**
→ `examples/playbooks/.env.basic-pdf.example`

**Production deployment?**
→ `examples/playbooks/.env.production.example`

---

## Benefits of Cleanup

### Before (23+ files)
- ❌ Confusing which file to use
- ❌ Lots of duplication
- ❌ Outdated examples
- ❌ Hard to maintain
- ❌ Unclear what each file does

### After (6 files)
- ✅ Clear purpose for each file
- ✅ Comprehensive documentation
- ✅ No duplication
- ✅ Easy to choose
- ✅ Easy to maintain

---

## Migration Guide

### If You Were Using Old Files

| Old File | New File |
|----------|----------|
| `.env.chromadb.example` | `envs/.env.offline-with-vision.example` |
| `.env.cohere.example` | `envs/.env.hybrid-scenarios.example` (Scenario 3) |
| `.env.hybrid.example` | `envs/.env.azure-chromadb-hybrid.example` |
| `.env.scenario-development.example` | `envs/.env.offline-with-vision.example` |
| `.env.scenario-cost-optimized.example` | `envs/.env.hybrid-scenarios.example` (Scenario 1) |
| `.env.scenario-multilingual.example` | `envs/.env.hybrid-scenarios.example` (Scenario 3) |

**Action:** Copy your credentials to the new file, then use with `--env-file`

---

## Summary

### What Changed
- Removed 14 duplicate/old env files
- Kept 6 comprehensive files
- Updated .gitignore for better protection
- Created cleanup scripts for easy execution

### What You Need to Do
1. Run cleanup script: `cleanup-duplicate-envs.bat` (Windows) or `cleanup-duplicate-envs.sh` (Linux/Mac)
2. Stage changes: `git add -A`
3. Commit: `git commit -m "chore: Remove duplicate env files and update gitignore"`
4. Update your workflow to use `--env-file` parameter

### Result
- ✅ Cleaner repository
- ✅ Less confusion
- ✅ Better documentation
- ✅ Easier maintenance
- ✅ Better gitignore protection

---

## Questions?

See:
- [IMPROVED_WORKFLOW.md](IMPROVED_WORKFLOW.md) - New --env-file workflow
- [ENV_FILE_USAGE_GUIDE.md](ENV_FILE_USAGE_GUIDE.md) - Which commands use which files
- [ENVIRONMENT_CONFIGURATION_GUIDE.md](ENVIRONMENT_CONFIGURATION_GUIDE.md) - Complete configuration reference

All 6 remaining files have comprehensive inline documentation explaining their purpose and usage.
