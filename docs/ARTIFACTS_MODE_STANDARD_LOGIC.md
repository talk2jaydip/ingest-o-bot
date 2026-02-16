# ARTIFACTS_MODE Standard Logic Update

## Summary

Updated the artifact storage configuration logic to follow a **standard priority order** where `ARTIFACTS_MODE` is the primary control, and `LOCAL_ARTIFACTS_DIR` only applies when the mode is set to `local`.

## Problem

Previously, `LOCAL_ARTIFACTS_DIR` had the **highest priority** and would override `ARTIFACTS_MODE`, causing confusion:

```python
# OLD LOGIC (PROBLEMATIC)
if LOCAL_ARTIFACTS_DIR is set:
    mode = LOCAL  # Force local mode (overrides ARTIFACTS_MODE)
else:
    # Check ARTIFACTS_MODE, input mode, etc.
```

**Issue:** Users would set `ARTIFACTS_MODE=blob` but also have `LOCAL_ARTIFACTS_DIR=./artifacts` configured, and the system would **ignore their explicit mode setting** and use local storage instead.

## Solution

Changed to a **standard priority order** where `ARTIFACTS_MODE` is the primary control:

```python
# NEW LOGIC (STANDARD)
1. Determine mode (priority order):
   a. ARTIFACTS_MODE (explicit setting - HIGHEST PRIORITY)
   b. STORE_ARTIFACTS_TO_BLOB (legacy flag)
   c. Follow INPUT_MODE (auto-detect)
   d. Default to LOCAL

2. Configure storage based on mode:
   if mode == LOCAL:
       use LOCAL_ARTIFACTS_DIR (default: ./artifacts)
   else:  # mode == BLOB
       use blob storage config (ignore LOCAL_ARTIFACTS_DIR)
```

## Changes Made

### 1. Updated `src/ingestor/config.py` (Lines 806-950)

**Before:**
- `LOCAL_ARTIFACTS_DIR` checked first (highest priority)
- Would force `mode = LOCAL` if set
- `ARTIFACTS_MODE` only checked if `LOCAL_ARTIFACTS_DIR` not set

**After:**
- `ARTIFACTS_MODE` checked first (highest priority)
- Mode determined independently of `LOCAL_ARTIFACTS_DIR`
- `LOCAL_ARTIFACTS_DIR` only used when `mode == LOCAL`

### 2. Updated `envs/.env.azure-local-input.example`

**Added clear documentation:**
- Lines 38-57: Explains priority order and standard logic
- Lines 183-204: Clarifies which settings apply based on mode
- Commented out `LOCAL_ARTIFACTS_DIR` when `ARTIFACTS_MODE=blob`

**Key points documented:**
```bash
# ARTIFACTS_MODE is the PRIMARY control for artifacts storage location
# Priority order:
#   1. ARTIFACTS_MODE (explicit mode - HIGHEST PRIORITY)
#   2. Follow INPUT_MODE
#   3. Default to local

# When ARTIFACTS_MODE=blob:
#   - LOCAL_ARTIFACTS_DIR is IGNORED
#   - Blob storage configuration is used
```

### 3. Updated `docs/guides/ARTIFACT_STORAGE_SIMPLIFIED.md`

**Updated sections:**
- Summary: Changed from "simplified" to "standardized"
- New Behavior: Documented clear priority order with `ARTIFACTS_MODE` as primary control
- Common Scenarios: Added hybrid scenarios (local→blob, blob→local)
- Migration Guide: Updated to reflect new logic

## Usage Examples

### Example 1: Explicit Blob Mode (Recommended for Production)
```bash
INPUT_MODE=local
LOCAL_INPUT_GLOB=data/*.pdf
ARTIFACTS_MODE=blob  # PRIMARY CONTROL - forces blob storage
AZURE_STORAGE_ACCOUNT=mystorageaccount
AZURE_BLOB_CONTAINER_PREFIX=myproject
# LOCAL_ARTIFACTS_DIR is ignored (not applicable in blob mode)
```

**Result:** ✅ Artifacts stored in blob storage (`myproject-pages`, `myproject-chunks`, etc.), citations work in Azure Search

### Example 2: Explicit Local Mode (Development)
```bash
INPUT_MODE=local
LOCAL_INPUT_GLOB=data/*.pdf
ARTIFACTS_MODE=local  # PRIMARY CONTROL - forces local storage
LOCAL_ARTIFACTS_DIR=./my_artifacts  # Applied because mode=local
```

**Result:** ✅ Artifacts stored locally at `./my_artifacts`

### Example 3: Auto-follow Input Mode (Default Behavior)
```bash
INPUT_MODE=blob
AZURE_BLOB_CONTAINER_IN=myproject-input
# ARTIFACTS_MODE not set - automatically follows INPUT_MODE
```

**Result:** ✅ Artifacts stored in blob storage (follows blob input)

### Example 4: What Was Previously Broken (Now Fixed)
```bash
INPUT_MODE=local
ARTIFACTS_MODE=blob  # User wants blob storage
LOCAL_ARTIFACTS_DIR=./artifacts  # Set but should be ignored
AZURE_STORAGE_ACCOUNT=mystorageaccount
```

**Before (WRONG):** ❌ Would use local storage because `LOCAL_ARTIFACTS_DIR` had highest priority
**After (CORRECT):** ✅ Uses blob storage because `ARTIFACTS_MODE=blob` takes priority

## Validation

The configuration validator recognizes both parameters:
- `ARTIFACTS_MODE`: Primary mode control
- `LOCAL_ARTIFACTS_DIR`: Directory path (only used when mode=local)

## Backwards Compatibility

All deprecated flags still work with warnings:
- `AZURE_ARTIFACTS_MODE` → Use `ARTIFACTS_MODE`
- `AZURE_ARTIFACTS_DIR` → Use `LOCAL_ARTIFACTS_DIR`
- `AZURE_STORE_ARTIFACTS_TO_BLOB` → Use `ARTIFACTS_MODE=blob`

## Benefits

1. **Clear Priority:** `ARTIFACTS_MODE` is the single source of truth
2. **Predictable Behavior:** Mode setting always respected
3. **Explicit Control:** Users can override auto-detection when needed
4. **Better Documentation:** Clear explanation of which settings apply when
5. **Prevents Confusion:** `LOCAL_ARTIFACTS_DIR` no longer overrides explicit mode

## Testing Checklist

- [x] `ARTIFACTS_MODE=blob` with `LOCAL_ARTIFACTS_DIR` set → Uses blob storage
- [x] `ARTIFACTS_MODE=local` with `LOCAL_ARTIFACTS_DIR` set → Uses local storage at specified path
- [x] `ARTIFACTS_MODE=local` without `LOCAL_ARTIFACTS_DIR` → Uses default `./artifacts`
- [x] No `ARTIFACTS_MODE` set, `INPUT_MODE=blob` → Auto-follows to blob storage
- [x] No `ARTIFACTS_MODE` set, `INPUT_MODE=local` → Auto-follows to local storage
- [x] Deprecation warnings shown for old variable names

## Migration Path

**For most users:** No action needed - auto-follow behavior unchanged

**If you have both set:**
1. Decide which mode you want: `ARTIFACTS_MODE=blob` or `ARTIFACTS_MODE=local`
2. Remove or comment out `LOCAL_ARTIFACTS_DIR` if using blob mode
3. Keep `LOCAL_ARTIFACTS_DIR` only if using local mode

**Recommended:**
- Development: Let it auto-follow (remove `ARTIFACTS_MODE`)
- Production: Set `ARTIFACTS_MODE=blob` explicitly
