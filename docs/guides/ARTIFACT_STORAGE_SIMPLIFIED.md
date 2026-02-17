# Artifact Storage Configuration - Simplified

## Summary of Changes

The artifact storage configuration has been **standardized** with a clear priority order.

## Old Behavior (Complex)

Previously, `LOCAL_ARTIFACTS_DIR` had the highest priority and would force local storage mode, overriding all other settings. This created confusion when users set `ARTIFACTS_MODE=blob` but also had `LOCAL_ARTIFACTS_DIR` set.

## New Behavior (Standard)

Now there's a **clear priority order**:

```
Priority Order (highest to lowest):
1. ARTIFACTS_MODE (explicit mode setting - HIGHEST PRIORITY)
   • blob → Blob storage (LOCAL_ARTIFACTS_DIR ignored)
   • local → Local storage (uses LOCAL_ARTIFACTS_DIR)
2. STORE_ARTIFACTS_TO_BLOB (legacy override flag, still supported)
3. Auto-detect from INPUT_MODE
   • INPUT_MODE=local → local artifacts
   • INPUT_MODE=blob → blob artifacts
4. Default to local
```

### Key Points:
- **`ARTIFACTS_MODE` is the PRIMARY control** - it overrides everything else
- **`LOCAL_ARTIFACTS_DIR` only applies when `ARTIFACTS_MODE=local`**
- When `ARTIFACTS_MODE=blob`, the `LOCAL_ARTIFACTS_DIR` setting is **ignored**

### Deprecated flags (still work for backwards compatibility):
- `STORE_ARTIFACTS_TO_BLOB` - Use `ARTIFACTS_MODE=blob` instead

## Common Scenarios

### Scenario 1: Local Development (local → local)
```bash
INPUT_MODE=local
LOCAL_INPUT_GLOB=data/*.pdf
# Artifacts automatically go to ./artifacts (default behavior)
# Optional: Customize path with LOCAL_ARTIFACTS_DIR=./custom_path
```

**Result:** Read from local disk, write artifacts to local disk

### Scenario 2: Production (blob → blob) ✅ RECOMMENDED
```bash
INPUT_MODE=blob
AZURE_BLOB_CONTAINER_IN=myproject-input
AZURE_STORAGE_ACCOUNT=mystorageaccount
# Artifacts automatically go to blob storage
```

**Result:** Read from blob, write artifacts to blob (required for Azure AI Search)

### Scenario 3: Local Input with Blob Artifacts (Hybrid)
```bash
INPUT_MODE=local
LOCAL_INPUT_GLOB=data/*.pdf
ARTIFACTS_MODE=blob  # EXPLICIT override to use blob storage
AZURE_STORAGE_ACCOUNT=mystorageaccount
AZURE_BLOB_CONTAINER_PREFIX=myproject  # Prefix for containers
```

**Result:** Read from local disk, write artifacts to blob storage (good for testing with production-like citations)

### Scenario 4: Blob Input with Local Artifacts (Debugging)
```bash
INPUT_MODE=blob
AZURE_BLOB_CONTAINER_IN=myproject-input
ARTIFACTS_MODE=local  # EXPLICIT override to use local storage
LOCAL_ARTIFACTS_DIR=./debug_artifacts  # Optional: custom path
```

**Result:** Read from blob, save artifacts locally for inspection (citations won't work)

## Why This Matters for Azure AI Search

Azure AI Search is a **cloud service** that requires **blob URLs (https://)** for the `storage_url` field:

- ✅ **Blob storage:** Returns `https://account.blob.core.windows.net/...` - **WORKS**
- ❌ **Local storage:** Returns `file:///C:/path/to/file` - **FAILS**

**If you see the warning about blob storage not configured:**
- You're in local artifacts mode
- Azure AI Search won't be able to access your documents
- Users won't see citation links

**To fix:** Simply use `INPUT_MODE=blob` (recommended for production)

## What Was Fixed

1. **Removed confusing priority logic** - One simple rule now
2. **Deprecated redundant flags** - `ARTIFACTS_MODE`, `STORE_ARTIFACTS_TO_BLOB`
3. **Updated warning message** - Clearer guidance on how to fix
4. **Simplified .env documentation** - Easier to understand scenarios
5. **Made input→artifacts relationship obvious** - Artifacts follow input mode by default

## Migration Guide

### If you want artifacts to follow input mode (recommended):

**Before:**
```bash
INPUT_MODE=local
LOCAL_INPUT_GLOB=data/*.pdf
STORE_ARTIFACTS_TO_BLOB=false  # Remove this
```

**After:**
```bash
INPUT_MODE=local
LOCAL_INPUT_GLOB=data/*.pdf
# Artifacts automatically follow INPUT_MODE
```

---

**Before:**
```bash
INPUT_MODE=blob
AZURE_BLOB_CONTAINER_IN=myproject-input
ARTIFACTS_MODE=blob  # Redundant, can be removed
```

**After:**
```bash
INPUT_MODE=blob
AZURE_BLOB_CONTAINER_IN=myproject-input
# Artifacts automatically follow INPUT_MODE
```

### If you want to explicitly control artifacts storage:

Use `ARTIFACTS_MODE` as the primary control:

```bash
# Example: Local input, blob artifacts (hybrid)
INPUT_MODE=local
ARTIFACTS_MODE=blob  # Explicit mode - takes priority
AZURE_STORAGE_ACCOUNT=mystorageaccount
AZURE_BLOB_CONTAINER_PREFIX=myproject  # Prefix for auto-generated containers
```

```bash
# Example: Blob input, local artifacts (debugging)
INPUT_MODE=blob
ARTIFACTS_MODE=local  # Explicit mode - takes priority
LOCAL_ARTIFACTS_DIR=./debug
```

## Backwards Compatibility

The old flags still work but will show deprecation warnings:
- `STORE_ARTIFACTS_TO_BLOB` → Use `ARTIFACTS_MODE=blob` instead
- `AZURE_ARTIFACTS_DIR` → Use `LOCAL_ARTIFACTS_DIR` instead
- `AZURE_ARTIFACTS_MODE` → Use `ARTIFACTS_MODE` instead
- `BLOB_CONTAINER_PREFIX` → Use `AZURE_BLOB_CONTAINER_PREFIX` instead

## Key Takeaway

**Standard Variable Names:**
- **`ARTIFACTS_MODE`** - Primary control for artifacts storage location:
  - `blob` → blob storage (ignores `LOCAL_ARTIFACTS_DIR`)
  - `local` → local storage (uses `LOCAL_ARTIFACTS_DIR`)
  - Not set → automatically follows `INPUT_MODE`

- **`AZURE_BLOB_CONTAINER_PREFIX`** - Prefix for blob containers (when mode=blob):
  - Auto-generates: `{prefix}-pages`, `{prefix}-chunks`, `{prefix}-images`, `{prefix}-citations`
  - Example: `AZURE_BLOB_CONTAINER_PREFIX=myproject` creates `myproject-pages`, etc.

Note: `AZURE_STORAGE_ACCOUNT` is a separate variable for the storage account name (e.g., `mystorageaccount`)
