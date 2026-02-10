# Blob Container Naming Convention

Guide to the blob container naming pattern used in `ingestor`.

---

## 📦 **Container Prefix Pattern**

The library supports a **prefix-based naming convention** for Azure Blob Storage containers, making it easy to organize and manage multiple environments or experiments.

---

## 🔧 **Configuration**

### Environment Variables

```bash
# Base prefix for all containers
AZURE_BLOB_CONTAINER_PREFIX=myproject

# Base container names (will be prefixed automatically)
AZURE_BLOB_CONTAINER_OUT_PAGES=pages
AZURE_BLOB_CONTAINER_OUT_CHUNKS=chunks
AZURE_BLOB_CONTAINER_OUT_IMAGES=images
AZURE_BLOB_CONTAINER_CITATIONS=citations
```

### Resulting Container Names

With the above configuration, the actual container names created will be:

| Base Name | Actual Container Name |
|-----------|----------------------|
| `pages` | `myproject-pages` |
| `chunks` | `myproject-chunks` |
| `images` | `myproject-images` |
| `citations` | `myproject-citations` |

---

## 📁 **Container Structure**

### 1. **Pages Container**
**Name:** `{prefix}-pages`  
**Purpose:** Store extracted page data (JSON)

```
myproject-pages/
├── document1.pdf/
│   └── pages/
│       ├── page-0001.json
│       ├── page-0002.json
│       └── page-0003.json
└── document2.pdf/
    └── pages/
        ├── page-0001.json
        └── page-0002.json
```

### 2. **Chunks Container**
**Name:** `{prefix}-chunks`  
**Purpose:** Store text chunks (JSON)

```
myproject-chunks/
├── document1.pdf/
│   └── chunks/
│       ├── page-01/
│       │   ├── chunk-000001.json
│       │   └── chunk-000002.json
│       └── page-02/
│           └── chunk-000001.json
└── document2.pdf/
    └── chunks/
        └── page-01/
            └── chunk-000001.json
```

### 3. **Images Container**
**Name:** `{prefix}-images`  
**Purpose:** Store extracted figures/images

```
myproject-images/
├── document1.pdf/
│   └── images/
│       ├── figure-01.png
│       └── figure-02.png
└── document2.pdf/
    └── images/
        └── figure-01.png
```

### 4. **Citations Container** (Optional)
**Name:** `{prefix}-citations`  
**Purpose:** Store per-page PDFs for direct citation links

```
myproject-citations/
├── document1.pdf/
│   └── pages/
│       ├── page-0001.pdf
│       ├── page-0002.pdf
│       └── page-0003.pdf
└── document2.pdf/
    └── pages/
        ├── page-0001.pdf
        └── page-0002.pdf
```

---

## ✅ **Efficient Container Creation**

### How It Works

1. **Initialization**: Containers are created **once** during pipeline initialization
2. **Check First**: The code checks if each container exists before attempting creation
3. **No Redundant Calls**: No container existence checks on every file write
4. **Race Condition Safe**: Handles concurrent creation attempts gracefully

### Implementation

```python
async def ensure_containers_exist(self):
    """Efficiently ensure all required containers exist.
    
    Checks if containers exist first, then creates only if needed.
    This should be called once during initialization.
    """
    containers_to_create = set()
    
    # Collect unique containers (with prefix applied)
    containers_to_create.add(self.pages_container)
    containers_to_create.add(self.chunks_container)
    containers_to_create.add(self.images_container)
    if self.citations_container:
        containers_to_create.add(self.citations_container)
    
    async with BlobServiceClient(...) as blob_service_client:
        for container_name in containers_to_create:
            container_client = blob_service_client.get_container_client(container_name)
            
            # Check if container exists first
            try:
                await container_client.get_container_properties()
                logger.debug(f"Container '{container_name}' already exists")
            except Exception:
                # Container doesn't exist, create it
                try:
                    await container_client.create_container()
                    logger.info(f"Created container: {container_name}")
                except ResourceExistsError:
                    # Race condition - another process created it
                    logger.debug(f"Container '{container_name}' was created by another process")
```

**Called once in:** `pipeline.py` → `_initialize_components()`

---

## 🎯 **Use Cases**

### 1. **Multiple Environments**

```bash
# Development
AZURE_BLOB_CONTAINER_PREFIX=myproject-dev

# Staging
AZURE_BLOB_CONTAINER_PREFIX=myproject-staging

# Production
AZURE_BLOB_CONTAINER_PREFIX=myproject-prod
```

### 2. **Multiple Experiments**

```bash
# Experiment 1
AZURE_BLOB_CONTAINER_PREFIX=myproject-experiment-001

# Experiment 2
AZURE_BLOB_CONTAINER_PREFIX=myproject-experiment-002
```

### 3. **No Prefix (Simple Names)**

```bash
# Leave prefix empty for simple names
AZURE_BLOB_CONTAINER_PREFIX=

# Results in:
# - pages
# - chunks
# - images
# - citations
```

---

## 🔍 **Example Configurations**

### Production Setup

```bash
# envs/env.production
AZURE_ARTIFACTS_MODE=blob
AZURE_BLOB_CONTAINER_PREFIX=myproject
AZURE_BLOB_CONTAINER_OUT_PAGES=pages
AZURE_BLOB_CONTAINER_OUT_CHUNKS=chunks
AZURE_BLOB_CONTAINER_OUT_IMAGES=images
AZURE_BLOB_CONTAINER_CITATIONS=citations
```

**Result:**
- `myproject-pages`
- `myproject-chunks`
- `myproject-images`
- `myproject-citations`

### Development Setup

```bash
# envs/env.dev
AZURE_ARTIFACTS_MODE=blob
AZURE_BLOB_CONTAINER_PREFIX=myproject-dev
AZURE_BLOB_CONTAINER_OUT_PAGES=pages
AZURE_BLOB_CONTAINER_OUT_CHUNKS=chunks
AZURE_BLOB_CONTAINER_OUT_IMAGES=images
AZURE_BLOB_CONTAINER_CITATIONS=citations
```

**Result:**
- `myproject-dev-pages`
- `myproject-dev-chunks`
- `myproject-dev-images`
- `myproject-dev-citations`

---

## 📊 **Benefits**

1. ✅ **Organization**: Easy to identify containers by environment/experiment
2. ✅ **Isolation**: Different environments don't interfere with each other
3. ✅ **Cleanup**: Easy to delete all containers for a specific experiment
4. ✅ **Efficiency**: Containers created once during initialization
5. ✅ **Flexibility**: Optional prefix - use simple names if preferred
6. ✅ **Safety**: Race condition handling for concurrent pipeline runs

---

## 🚀 **Quick Start**

1. **Set your prefix:**
   ```bash
   AZURE_BLOB_CONTAINER_PREFIX=my-project-experiment-01
   ```

2. **Define base container names:**
   ```bash
   AZURE_BLOB_CONTAINER_OUT_PAGES=pages
   AZURE_BLOB_CONTAINER_OUT_CHUNKS=chunks
   AZURE_BLOB_CONTAINER_OUT_IMAGES=images
   AZURE_BLOB_CONTAINER_CITATIONS=citations
   ```

3. **Run the pipeline:**
   ```bash
   python -m cli
   ```

4. **Containers are automatically created:**
   - `my-project-experiment-01-pages`
   - `my-project-experiment-01-chunks`
   - `my-project-experiment-01-images`
   - `my-project-experiment-01-citations`

---

## 🔧 **Troubleshooting**

### Container Creation Fails

**Error:** `Failed to create container: {name}`

**Solution:** Check that:
1. `AZURE_STORAGE_ACCOUNT` is correct
2. `AZURE_STORAGE_ACCOUNT_KEY` has write permissions
3. Container name follows Azure naming rules (lowercase, alphanumeric, hyphens)

### Container Names Too Long

**Error:** Container name exceeds Azure's 63-character limit

**Solution:** Use a shorter prefix:
```bash
# Too long
AZURE_BLOB_CONTAINER_PREFIX=myproject-very-long-name

# Better
AZURE_BLOB_CONTAINER_PREFIX=my-exp-01
```

---

## 📚 **Related Documentation**

- [Configuration Guide](../guides/CONFIGURATION.md)
- [Environment Variables Guide](12_ENVIRONMENT_VARIABLES.md)
- [Architecture Guide](04_ARCHITECTURE.md)

