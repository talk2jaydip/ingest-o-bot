# Artifact Storage Configuration - Simplified

## Summary of Changes

The artifact storage configuration has been **simplified** to remove confusion from multiple overlapping flags.

## Old Behavior (Complex)

Previously, there were 3 different flags controlling artifact storage with confusing priority:

1. `AZURE_ARTIFACTS_DIR` (highest priority - forces local)
2. `AZURE_ARTIFACTS_MODE` (explicit mode override)
3. `AZURE_STORE_ARTIFACTS_TO_BLOB` (force blob flag)
4. Auto-detect from input mode
5. Default to local

This created confusion because multiple flags could conflict.

## New Behavior (Simple)

Now there's **ONE simple rule**:

```
1. If AZURE_ARTIFACTS_DIR is set → LOCAL storage at that path (override for debugging)
2. Otherwise → Artifacts automatically follow input mode
   • local input → local artifacts
   • blob input → blob artifacts
```

### The deprecated flags still work for backwards compatibility, but you should remove them:
- `AZURE_ARTIFACTS_MODE` - Deprecated (just use input mode)
- `AZURE_STORE_ARTIFACTS_TO_BLOB` - Deprecated (just use input mode)

## Common Scenarios

### Scenario 1: Local Development (local → local)
```bash
AZURE_INPUT_MODE=local
AZURE_LOCAL_GLOB=data/*.pdf
# Artifacts automatically go to ./artifacts (or custom path via AZURE_ARTIFACTS_DIR)
```

**Result:** Read from local disk, write artifacts to local disk

### Scenario 2: Production (blob → blob) ✅ RECOMMENDED
```bash
AZURE_INPUT_MODE=blob
AZURE_BLOB_CONTAINER_IN=myproject-input
# Artifacts automatically go to blob storage
```

**Result:** Read from blob, write artifacts to blob (required for Azure AI Search)

### Scenario 3: Debugging Production Files (blob → local)
```bash
AZURE_INPUT_MODE=blob
AZURE_BLOB_CONTAINER_IN=myproject-input
AZURE_ARTIFACTS_DIR=./debug_artifacts  # OVERRIDE: Force local storage
```

**Result:** Read from blob, but save artifacts locally for inspection

## Why This Matters for Azure AI Search

Azure AI Search is a **cloud service** that requires **blob URLs (https://)** for the `storage_url` field:

- ✅ **Blob storage:** Returns `https://account.blob.core.windows.net/...` - **WORKS**
- ❌ **Local storage:** Returns `file:///C:/path/to/file` - **FAILS**

**If you see the warning about blob storage not configured:**
- You're in local artifacts mode
- Azure AI Search won't be able to access your documents
- Users won't see citation links

**To fix:** Simply use `AZURE_INPUT_MODE=blob` (recommended for production)

## What Was Fixed

1. **Removed confusing priority logic** - One simple rule now
2. **Deprecated redundant flags** - `AZURE_ARTIFACTS_MODE`, `AZURE_STORE_ARTIFACTS_TO_BLOB`
3. **Updated warning message** - Clearer guidance on how to fix
4. **Simplified .env documentation** - Easier to understand scenarios
5. **Made input→artifacts relationship obvious** - Artifacts follow input mode by default

## Migration Guide

If you're using old configuration:

### Before (Complex)
```bash
AZURE_INPUT_MODE=local
AZURE_LOCAL_GLOB=data/*.pdf
AZURE_STORE_ARTIFACTS_TO_BLOB=false  # Confusing!
```

### After (Simple)
```bash
AZURE_INPUT_MODE=local
AZURE_LOCAL_GLOB=data/*.pdf
# That's it! Artifacts automatically go local
```

---

### Before (Complex)
```bash
AZURE_INPUT_MODE=blob
AZURE_BLOB_CONTAINER_IN=myproject-input
AZURE_ARTIFACTS_MODE=blob  # Redundant!
```

### After (Simple)
```bash
AZURE_INPUT_MODE=blob
AZURE_BLOB_CONTAINER_IN=myproject-input
# That's it! Artifacts automatically go blob
```

## Backwards Compatibility

The old flags still work but will show deprecation warnings:
- `AZURE_ARTIFACTS_MODE` → Still works, but prefer removing it
- `AZURE_STORE_ARTIFACTS_TO_BLOB` → Still works, but prefer removing it

You can safely remove these flags from your `.env` file.
