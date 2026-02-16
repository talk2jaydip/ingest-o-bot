# Blob Storage Configuration - Variables

## Summary

The system uses two distinct variables for blob storage configuration:
1. **`AZURE_STORAGE_ACCOUNT`** - The storage account name (e.g., `steusmycpipe2248`)
2. **`AZURE_BLOB_CONTAINER_PREFIX`** - Prefix for auto-generating container names (e.g., `myproject`)

## Variable Roles

| Variable | Purpose | Example Value |
|----------|---------|---------------|
| `AZURE_STORAGE_ACCOUNT` | Azure Storage Account name | `steusmycpipe2248` |
| `AZURE_STORAGE_ACCOUNT_KEY` | Storage account access key | `u73g8v...` |
| `AZURE_BLOB_CONTAINER_PREFIX` | Prefix for container names | `alfred-experiment-index` |

## How Container Naming Works

When you set `AZURE_BLOB_CONTAINER_PREFIX=myproject`, the system automatically creates:
- `myproject-pages` (page artifacts)
- `myproject-chunks` (chunk artifacts)
- `myproject-images` (extracted images)
- `myproject-citations` (full documents)
- `myproject-input` (for blob input mode - **must create manually**)

## Configuration Approaches

### Approach 1: Prefix (Recommended)
```bash
AZURE_STORAGE_ACCOUNT=mystorageaccount
AZURE_STORAGE_ACCOUNT_KEY=your-key
AZURE_BLOB_CONTAINER_PREFIX=myproject
# Auto-creates: myproject-pages, myproject-chunks, myproject-images, myproject-citations
```

### Approach 2: Explicit (Advanced)
```bash
AZURE_STORAGE_ACCOUNT=mystorageaccount
AZURE_STORAGE_ACCOUNT_KEY=your-key
AZURE_BLOB_CONTAINER_OUT_PAGES=custom-pages
AZURE_BLOB_CONTAINER_OUT_CHUNKS=custom-chunks
AZURE_BLOB_CONTAINER_OUT_IMAGES=custom-images
AZURE_BLOB_CONTAINER_CITATIONS=custom-citations
```

## Variable Priority

For container prefix:
```python
# Priority: AZURE_BLOB_CONTAINER_PREFIX > BLOB_CONTAINER_PREFIX (deprecated)
blob_container_prefix = os.getenv("AZURE_BLOB_CONTAINER_PREFIX") \
                     or os.getenv("BLOB_CONTAINER_PREFIX", "")
```

## Deprecation Warnings

- `BLOB_CONTAINER_PREFIX` → Use `AZURE_BLOB_CONTAINER_PREFIX` (shows warning)

## Key Points

1. **`AZURE_STORAGE_ACCOUNT`** and **`AZURE_BLOB_CONTAINER_PREFIX`** are DIFFERENT:
   - Storage account = the Azure resource name
   - Container prefix = naming pattern for containers within that account

2. **Automatic Container Creation:**
   - All artifact containers (`-pages`, `-chunks`, `-images`, `-citations`) are auto-created
   - Input container (`-input`) must be created manually if using `INPUT_MODE=blob`

3. **Naming Convention:**
   - Format: `{prefix}-{type}`
   - Example: `alfred-experiment-index-pages`

## Internal Implementation

Internally, `blob_container_prefix` field in `ArtifactsConfig` stores the prefix value, which is then combined with suffixes (`-pages`, `-chunks`, etc.) to generate full container names.
