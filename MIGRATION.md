# Migration Guide: v1.x to v2.0

> Comprehensive guide for upgrading from Ingestor v1.x to v2.0

## Table of Contents

1. [What Changed in v2.0](#what-changed-in-v20)
2. [Breaking Changes](#breaking-changes)
3. [Variable Renames](#variable-renames)
4. [Migration Steps](#migration-steps)
5. [Automated Migration](#automated-migration)
6. [Testing Your Migration](#testing-your-migration)
7. [Rollback Plan](#rollback-plan)

---

## What Changed in v2.0

### Major Changes

**1. Generic Variable Naming**
- Removed Azure-specific prefixes from provider-agnostic configuration variables
- Makes the system more flexible for multi-cloud and hybrid deployments
- Improves clarity about which variables are Azure-specific vs. generic

**2. Token-Only Chunking (Default)**
- `CHUNKING_DISABLE_CHAR_LIMIT=true` is now the default
- Provides more consistent chunk sizes across different document types
- Prevents truncation issues with embedding models

**3. Backward Compatibility**
- All old variable names still work with deprecation warnings
- Gives you time to migrate at your own pace
- Support for old names will be removed in v3.0

---

## Breaking Changes

### None in v2.0

All changes in v2.0 are **backward compatible**. Your existing `.env` files will continue to work with deprecation warnings in the logs.

**Timeline:**
- **v2.0 (Current)**: Old names work with warnings
- **v3.0 (Future)**: Old names will be removed

---

## Variable Renames

### Complete Rename Table

| Category | Old Name (v1.x) | New Name (v2.0) | Status |
|----------|-----------------|-----------------|--------|
| **Mode Selection** |
| Input Mode | `AZURE_INPUT_MODE` | `INPUT_MODE` | Deprecated |
| Artifacts Mode | `AZURE_ARTIFACTS_MODE` | `ARTIFACTS_MODE` | Deprecated |
| Extraction Mode | `AZURE_OFFICE_EXTRACTOR_MODE` | `EXTRACTION_MODE` | Deprecated |
| **Chunking Configuration** |
| Max Chars | `AZURE_CHUNKING_MAX_CHARS` | `CHUNKING_MAX_CHARS` | Deprecated |
| Max Tokens | `AZURE_CHUNKING_MAX_TOKENS` | `CHUNKING_MAX_TOKENS` | Deprecated |
| Overlap % | `AZURE_CHUNKING_OVERLAP_PERCENT` | `CHUNKING_OVERLAP_PERCENT` | Deprecated |
| Cross-Page | `AZURE_CHUNKING_CROSS_PAGE_OVERLAP` | `CHUNKING_CROSS_PAGE_OVERLAP` | Deprecated |
| Disable Char Limit | `AZURE_CHUNKING_DISABLE_CHAR_LIMIT` | `CHUNKING_DISABLE_CHAR_LIMIT` | Deprecated |
| Table Legend Buffer | `AZURE_CHUNKING_TABLE_LEGEND_BUFFER` | `CHUNKING_TABLE_LEGEND_BUFFER` | Deprecated |
| Absolute Max | `AZURE_CHUNKING_ABSOLUTE_MAX_TOKENS` | `CHUNKING_ABSOLUTE_MAX_TOKENS` | Deprecated |
| **Performance Configuration** |
| Workers | `AZURE_MAX_WORKERS` | `MAX_WORKERS` | Deprecated |
| Batch Size | `AZURE_EMBED_BATCH_SIZE` | `EMBEDDING_BATCH_SIZE` | Deprecated |

### Variables That Did NOT Change

**Azure Service Variables (Keep as-is):**
- `AZURE_SEARCH_SERVICE`
- `AZURE_SEARCH_KEY`
- `AZURE_SEARCH_INDEX`
- `AZURE_DOC_INT_ENDPOINT`
- `AZURE_DOC_INT_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_KEY`
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`
- `AZURE_OPENAI_EMBEDDING_MODEL`
- `AZURE_OPENAI_EMBEDDING_DIMENSIONS`
- `AZURE_OPENAI_CHAT_DEPLOYMENT`
- `AZURE_OPENAI_API_VERSION`
- `AZURE_OPENAI_MAX_CONCURRENCY`
- `AZURE_OPENAI_MAX_RETRIES`
- `AZURE_STORAGE_ACCOUNT`
- `AZURE_STORAGE_ACCOUNT_KEY`
- `AZURE_CONNECTION_STRING`
- `AZURE_BLOB_CONTAINER_*`
- `AZURE_LOCAL_GLOB`
- `AZURE_ARTIFACTS_DIR`
- All other Azure-specific service variables

---

## Migration Steps

### Step 1: Backup Your Configuration

```bash
# Backup your current .env file
cp .env .env.v1.backup

# If you have multiple environment files
cp .env.production .env.production.v1.backup
cp .env.staging .env.staging.v1.backup
cp .env.development .env.development.v1.backup
```

### Step 2: Update Variable Names

You have two options:

#### Option A: Automated Migration (Recommended)

Use the migration script (see [Automated Migration](#automated-migration) section below).

#### Option B: Manual Migration

Update your `.env` file with the new variable names:

```bash
# Mode Configuration
AZURE_INPUT_MODE=local          →  INPUT_MODE=local
AZURE_ARTIFACTS_MODE=local      →  ARTIFACTS_MODE=local
AZURE_OFFICE_EXTRACTOR_MODE=... →  EXTRACTION_MODE=...

# Chunking Configuration
AZURE_CHUNKING_MAX_CHARS=1000              →  CHUNKING_MAX_CHARS=1000
AZURE_CHUNKING_MAX_TOKENS=500              →  CHUNKING_MAX_TOKENS=500
AZURE_CHUNKING_OVERLAP_PERCENT=20          →  CHUNKING_OVERLAP_PERCENT=20
AZURE_CHUNKING_CROSS_PAGE_OVERLAP=false    →  CHUNKING_CROSS_PAGE_OVERLAP=false
AZURE_CHUNKING_DISABLE_CHAR_LIMIT=false    →  CHUNKING_DISABLE_CHAR_LIMIT=false
AZURE_CHUNKING_TABLE_LEGEND_BUFFER=100     →  CHUNKING_TABLE_LEGEND_BUFFER=100
AZURE_CHUNKING_ABSOLUTE_MAX_TOKENS=8000    →  CHUNKING_ABSOLUTE_MAX_TOKENS=8000

# Performance Configuration
AZURE_MAX_WORKERS=4           →  MAX_WORKERS=4
AZURE_EMBED_BATCH_SIZE=100    →  EMBEDDING_BATCH_SIZE=100
```

### Step 3: Test Configuration

```bash
# Validate your new configuration
python -m ingestor.cli --validate

# Or with specific environment file
python -m ingestor.cli --validate --env-file .env.production
```

### Step 4: Run Test Ingestion

```bash
# Test with a small document
python -m ingestor.cli --pdf test-document.pdf

# Check results
python -m ingestor.cli --check-index
```

---

## Automated Migration

### Migration Scripts

We provide automated migration scripts for both Linux/Mac and Windows.

#### Linux/Mac: migrate_env.sh

Create a file `migrate_env.sh`:

```bash
#!/bin/bash
# migrate_env.sh - Migrate .env file to v2.0 variable names

ENV_FILE="${1:-.env}"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: $ENV_FILE not found"
    exit 1
fi

# Backup original
cp "$ENV_FILE" "${ENV_FILE}.backup"
echo "Created backup: ${ENV_FILE}.backup"

# v2.0 Renames (mode configuration)
sed -i 's/^AZURE_INPUT_MODE=/INPUT_MODE=/g' "$ENV_FILE"
sed -i 's/^AZURE_ARTIFACTS_MODE=/ARTIFACTS_MODE=/g' "$ENV_FILE"
sed -i 's/^AZURE_OFFICE_EXTRACTOR_MODE=/EXTRACTION_MODE=/g' "$ENV_FILE"

# v2.0 Renames (chunking configuration)
sed -i 's/^AZURE_CHUNKING_MAX_CHARS=/CHUNKING_MAX_CHARS=/g' "$ENV_FILE"
sed -i 's/^AZURE_CHUNKING_MAX_TOKENS=/CHUNKING_MAX_TOKENS=/g' "$ENV_FILE"
sed -i 's/^AZURE_CHUNKING_OVERLAP_PERCENT=/CHUNKING_OVERLAP_PERCENT=/g' "$ENV_FILE"
sed -i 's/^AZURE_CHUNKING_CROSS_PAGE_OVERLAP=/CHUNKING_CROSS_PAGE_OVERLAP=/g' "$ENV_FILE"
sed -i 's/^AZURE_CHUNKING_DISABLE_CHAR_LIMIT=/CHUNKING_DISABLE_CHAR_LIMIT=/g' "$ENV_FILE"
sed -i 's/^AZURE_CHUNKING_TABLE_LEGEND_BUFFER=/CHUNKING_TABLE_LEGEND_BUFFER=/g' "$ENV_FILE"
sed -i 's/^AZURE_CHUNKING_ABSOLUTE_MAX_TOKENS=/CHUNKING_ABSOLUTE_MAX_TOKENS=/g' "$ENV_FILE"

# v2.0 Renames (performance configuration)
sed -i 's/^AZURE_MAX_WORKERS=/MAX_WORKERS=/g' "$ENV_FILE"
sed -i 's/^AZURE_EMBED_BATCH_SIZE=/EMBEDDING_BATCH_SIZE=/g' "$ENV_FILE"

echo "✅ Migration complete!"
echo "   Original saved to: ${ENV_FILE}.backup"
echo "   Updated file: $ENV_FILE"
echo ""
echo "Next steps:"
echo "  1. Review changes: diff ${ENV_FILE}.backup $ENV_FILE"
echo "  2. Test: python -m ingestor.cli --validate --env-file $ENV_FILE"
```

Make it executable:
```bash
chmod +x migrate_env.sh
```

Run it:
```bash
# Migrate default .env
./migrate_env.sh

# Migrate specific file
./migrate_env.sh .env.production
```

#### Windows: migrate_env.bat

Create a file `migrate_env.bat`:

```batch
@echo off
REM migrate_env.bat - Migrate .env file to v2.0 variable names

set "ENV_FILE=%~1"
if "%ENV_FILE%"=="" set "ENV_FILE=.env"

if not exist "%ENV_FILE%" (
    echo Error: %ENV_FILE% not found
    exit /b 1
)

REM Backup original
copy "%ENV_FILE%" "%ENV_FILE%.backup" >nul
echo Created backup: %ENV_FILE%.backup

REM Mode configuration
powershell -Command "(gc '%ENV_FILE%') -replace '^AZURE_INPUT_MODE=', 'INPUT_MODE=' | Set-Content '%ENV_FILE%'"
powershell -Command "(gc '%ENV_FILE%') -replace '^AZURE_ARTIFACTS_MODE=', 'ARTIFACTS_MODE=' | Set-Content '%ENV_FILE%'"
powershell -Command "(gc '%ENV_FILE%') -replace '^AZURE_OFFICE_EXTRACTOR_MODE=', 'EXTRACTION_MODE=' | Set-Content '%ENV_FILE%'"

REM Chunking configuration
powershell -Command "(gc '%ENV_FILE%') -replace '^AZURE_CHUNKING_MAX_CHARS=', 'CHUNKING_MAX_CHARS=' | Set-Content '%ENV_FILE%'"
powershell -Command "(gc '%ENV_FILE%') -replace '^AZURE_CHUNKING_MAX_TOKENS=', 'CHUNKING_MAX_TOKENS=' | Set-Content '%ENV_FILE%'"
powershell -Command "(gc '%ENV_FILE%') -replace '^AZURE_CHUNKING_OVERLAP_PERCENT=', 'CHUNKING_OVERLAP_PERCENT=' | Set-Content '%ENV_FILE%'"
powershell -Command "(gc '%ENV_FILE%') -replace '^AZURE_CHUNKING_CROSS_PAGE_OVERLAP=', 'CHUNKING_CROSS_PAGE_OVERLAP=' | Set-Content '%ENV_FILE%'"
powershell -Command "(gc '%ENV_FILE%') -replace '^AZURE_CHUNKING_DISABLE_CHAR_LIMIT=', 'CHUNKING_DISABLE_CHAR_LIMIT=' | Set-Content '%ENV_FILE%'"
powershell -Command "(gc '%ENV_FILE%') -replace '^AZURE_CHUNKING_TABLE_LEGEND_BUFFER=', 'CHUNKING_TABLE_LEGEND_BUFFER=' | Set-Content '%ENV_FILE%'"
powershell -Command "(gc '%ENV_FILE%') -replace '^AZURE_CHUNKING_ABSOLUTE_MAX_TOKENS=', 'CHUNKING_ABSOLUTE_MAX_TOKENS=' | Set-Content '%ENV_FILE%'"

REM Performance configuration
powershell -Command "(gc '%ENV_FILE%') -replace '^AZURE_MAX_WORKERS=', 'MAX_WORKERS=' | Set-Content '%ENV_FILE%'"
powershell -Command "(gc '%ENV_FILE%') -replace '^AZURE_EMBED_BATCH_SIZE=', 'EMBEDDING_BATCH_SIZE=' | Set-Content '%ENV_FILE%'"

echo.
echo Migration complete!
echo   Original saved to: %ENV_FILE%.backup
echo   Updated file: %ENV_FILE%
echo.
echo Next steps:
echo   1. Review changes: fc %ENV_FILE%.backup %ENV_FILE%
echo   2. Test: python -m ingestor.cli --validate --env-file %ENV_FILE%
```

Run it:
```cmd
REM Migrate default .env
migrate_env.bat

REM Migrate specific file
migrate_env.bat .env.production
```

### Python Migration Script

For more control, use this Python script:

```python
#!/usr/bin/env python3
"""
migrate_to_v2.py - Migrate environment files to v2.0 variable naming
"""
import re
import shutil
import sys
from pathlib import Path

# Variable rename mappings
RENAMES = {
    # Mode configuration
    'AZURE_INPUT_MODE': 'INPUT_MODE',
    'AZURE_ARTIFACTS_MODE': 'ARTIFACTS_MODE',
    'AZURE_OFFICE_EXTRACTOR_MODE': 'EXTRACTION_MODE',

    # Chunking configuration
    'AZURE_CHUNKING_MAX_CHARS': 'CHUNKING_MAX_CHARS',
    'AZURE_CHUNKING_MAX_TOKENS': 'CHUNKING_MAX_TOKENS',
    'AZURE_CHUNKING_OVERLAP_PERCENT': 'CHUNKING_OVERLAP_PERCENT',
    'AZURE_CHUNKING_CROSS_PAGE_OVERLAP': 'CHUNKING_CROSS_PAGE_OVERLAP',
    'AZURE_CHUNKING_DISABLE_CHAR_LIMIT': 'CHUNKING_DISABLE_CHAR_LIMIT',
    'AZURE_CHUNKING_TABLE_LEGEND_BUFFER': 'CHUNKING_TABLE_LEGEND_BUFFER',
    'AZURE_CHUNKING_ABSOLUTE_MAX_TOKENS': 'CHUNKING_ABSOLUTE_MAX_TOKENS',

    # Performance configuration
    'AZURE_MAX_WORKERS': 'MAX_WORKERS',
    'AZURE_EMBED_BATCH_SIZE': 'EMBEDDING_BATCH_SIZE',
}

def migrate_env_file(env_file: Path, dry_run: bool = False):
    """Migrate a single .env file to v2.0 naming."""
    if not env_file.exists():
        print(f"❌ Error: {env_file} not found")
        return False

    print(f"\n📄 Processing: {env_file}")

    # Read original content
    content = env_file.read_text()
    original_content = content

    # Track changes
    changes = []

    # Apply renames
    for old_name, new_name in RENAMES.items():
        pattern = f'^{old_name}='
        if re.search(pattern, content, re.MULTILINE):
            content = re.sub(pattern, f'{new_name}=', content, flags=re.MULTILINE)
            changes.append(f"  {old_name} → {new_name}")

    # Check if any changes were made
    if content == original_content:
        print("  ℹ️  No changes needed (already v2.0 format)")
        return True

    # Display changes
    print(f"  ✅ Found {len(changes)} variables to update:")
    for change in changes:
        print(change)

    if dry_run:
        print("  🔍 Dry run - no changes made")
        return True

    # Backup original
    backup_file = env_file.with_suffix(env_file.suffix + '.backup')
    shutil.copy2(env_file, backup_file)
    print(f"  💾 Backup created: {backup_file}")

    # Write updated content
    env_file.write_text(content)
    print(f"  ✅ Updated: {env_file}")

    return True

def main():
    """Main migration script."""
    import argparse

    parser = argparse.ArgumentParser(description='Migrate .env files to v2.0 naming')
    parser.add_argument('files', nargs='*', default=['.env'],
                       help='Environment files to migrate (default: .env)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be changed without modifying files')
    parser.add_argument('--all', action='store_true',
                       help='Migrate all .env* files in current directory')

    args = parser.parse_args()

    # Get files to process
    if args.all:
        files = list(Path('.').glob('.env*'))
        # Exclude backup files
        files = [f for f in files if not f.name.endswith('.backup')]
    else:
        files = [Path(f) for f in args.files]

    if not files:
        print("❌ No files to process")
        return 1

    print("=" * 60)
    print("Migration to v2.0 Variable Naming")
    print("=" * 60)

    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")

    # Process each file
    success = True
    for env_file in files:
        if not migrate_env_file(env_file, dry_run=args.dry_run):
            success = False

    print("\n" + "=" * 60)
    if success:
        print("✅ Migration completed successfully!")
        if not args.dry_run:
            print("\nNext steps:")
            print("  1. Review changes: git diff")
            print("  2. Test configuration: python -m ingestor.cli --validate")
            print("  3. Run test ingestion: python -m ingestor.cli --pdf test.pdf")
    else:
        print("❌ Migration completed with errors")
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
```

Save as `migrate_to_v2.py` and run:

```bash
# Dry run (show changes without modifying)
python migrate_to_v2.py --dry-run

# Migrate default .env
python migrate_to_v2.py

# Migrate specific files
python migrate_to_v2.py .env.production .env.staging

# Migrate all .env files in directory
python migrate_to_v2.py --all
```

---

## Testing Your Migration

### 1. Validate Configuration

```bash
# Validate configuration
python -m ingestor.cli --validate

# Should see: "✓ Configuration is valid!"
```

### 2. Check for Deprecation Warnings

If you missed any renames, you'll see warnings in the logs:

```
WARNING: AZURE_INPUT_MODE is deprecated. Use INPUT_MODE instead.
         Support for AZURE_INPUT_MODE will be removed in v2.0.
```

### 3. Test Document Ingestion

```bash
# Process a test document
python -m ingestor.cli --pdf test-document.pdf

# Check index
python -m ingestor.cli --check-index
```

### 4. Verify Chunking Behavior

The default chunking mode has changed to token-only:

```bash
# Old default (v1.x): Character AND token limits
CHUNKING_MAX_CHARS=1000
CHUNKING_MAX_TOKENS=500
CHUNKING_DISABLE_CHAR_LIMIT=false  # default

# New default (v2.0): Token-only limits
CHUNKING_MAX_TOKENS=500
CHUNKING_DISABLE_CHAR_LIMIT=true  # default
```

If you want the old behavior:
```bash
CHUNKING_MAX_CHARS=1000
CHUNKING_MAX_TOKENS=500
CHUNKING_DISABLE_CHAR_LIMIT=false
```

---

## Rollback Plan

If you need to rollback to v1.x:

### 1. Restore Backup

```bash
# Restore from backup
cp .env.v1.backup .env

# Or for specific environment
cp .env.production.v1.backup .env.production
```

### 2. Downgrade Package

```bash
# Downgrade to v1.x
pip install ingestor==1.9.0  # or your previous version
```

### 3. Verify

```bash
# Check version
python -c "import ingestor; print(ingestor.__version__)"

# Validate configuration
python -m ingestor.cli --validate
```

---

## Common Issues

### Issue: Deprecation warnings after migration

**Cause:** Some variables weren't renamed (check for typos or commented lines)

**Solution:**
```bash
# Find remaining old variable names
grep -E "AZURE_(INPUT_MODE|ARTIFACTS_MODE|OFFICE_EXTRACTOR_MODE|CHUNKING_|MAX_WORKERS|EMBED_BATCH_SIZE)" .env
```

### Issue: Token-only chunking produces different results

**Cause:** v2.0 defaults to token-only chunking

**Solution:** Add to `.env` to restore v1.x behavior:
```bash
CHUNKING_DISABLE_CHAR_LIMIT=false
```

### Issue: Configuration validation fails

**Cause:** Typo in variable name or missing required value

**Solution:**
```bash
# Validate and see detailed error
python -m ingestor.cli --validate --env-file .env
```

---

## FAQ

### Q: Do I need to migrate immediately?

**A:** No. v1.x variable names will continue to work until v3.0. You have plenty of time to migrate.

### Q: Can I use a mix of old and new variable names?

**A:** Yes, but we recommend migrating all at once to avoid confusion. The system will use the new name if both are present.

### Q: Will my existing indexed documents still work?

**A:** Yes. Variable renames don't affect already-indexed documents or index schemas.

### Q: What if I'm using environment variables in CI/CD?

**A:** Update your CI/CD pipeline to use the new variable names. The old names will work but with warnings in logs.

### Q: Do I need to update my code?

**A:** No code changes required. The `PipelineConfig.from_env()` method handles both old and new variable names automatically.

---

## Get Help

- **Documentation:** [docs/INDEX.md](docs/INDEX.md)
- **Configuration Guide:** [docs/guides/CONFIGURATION.md](docs/guides/CONFIGURATION.md)
- **Variable Reference:** [ENV_VARIABLES_FIX_SUMMARY.md](ENV_VARIABLES_FIX_SUMMARY.md)
- **Quick Reference:** [docs/guides/QUICK_REFERENCE.md](docs/guides/QUICK_REFERENCE.md)

---

**Last Updated:** February 13, 2026
