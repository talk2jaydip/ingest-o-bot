# Azure AI Search Index Configuration Guide

## Quick Start

### Basic Usage

```bash
# 1. Configure in .env (optional - uses defaults if not set)
AZURE_SEARCH_SEMANTIC_CONFIG_NAME=alfred-semantic-config
AZURE_SEARCH_SUGGESTER_NAME=product-suggester
AZURE_SEARCH_SCORING_PROFILES=productBoostingProfile,contentRAGProfile

# 2. Create or update index
python -m src.ingestor.cli --setup-index --index-only

# 3. Export schema for backup/version control
python -m src.ingestor.cli --export-schema backups/schema.json

# 4. Import schema to create index
python -m src.ingestor.cli --import-schema backups/schema.json
```

### Default Values

If environment variables are NOT set, these defaults are used:

| Configuration | Default Value |
|--------------|---------------|
| Semantic Config | `"default-semantic-config"` |
| Suggester | `"default-suggester"` |
| Scoring Profiles | `("productBoostingProfile", "contentRAGProfile")` |

### Index Features

The index includes **24 fields** with:
- **Core**: id, content, embeddings, filename, url
- **Metadata**: country, language, product_family, productTradeNames, prod_from_url
- **Document**: title, literatureType, partNumber, applicableTo, model
- **Dates**: publishedDate, pageNumber, category
- **Source**: sourcepage, sourcefile, storageUrl
- **Media**: has_figures, figure_urls, has_tables

---

## Overview

The index deployment system supports configurable names for semantic configurations, suggesters, and scoring profiles. This allows you to customize index schema names without hardcoding them.

**See also**: [JSON Schema Import/Export](JSON_SCHEMA_IMPORT_EXPORT.md) for backup and migration.

## Configuration Flow

```
.env file
    ↓
SearchConfig.from_env()
    ↓
IndexDeploymentManager
    ↓
Azure AI Search Index
```

## 1. Environment Variables (.env)

Add these **optional** variables to your `.env` file:

```bash
# ============================================================================
# AZURE AI SEARCH - Index Schema Customization (Optional)
# ============================================================================

# Semantic configuration name (default: "default-semantic-config")
AZURE_SEARCH_SEMANTIC_CONFIG_NAME=alfred-semantic-config

# Suggester name (default: "default-suggester")
AZURE_SEARCH_SUGGESTER_NAME=product-suggester

# Scoring profile names - comma-separated (default: "productBoostingProfile,contentRAGProfile")
AZURE_SEARCH_SCORING_PROFILES=productBoostingProfile,contentRAGProfile
```

**If not set**, the system uses these defaults:
- Semantic Config: `"default-semantic-config"`
- Suggester: `"default-suggester"`
- Scoring Profiles: `("productBoostingProfile", "contentRAGProfile")`

## 2. SearchConfig Class (config.py)

The `SearchConfig` class automatically loads these from environment variables:

```python
@dataclass
class SearchConfig:
    """Azure AI Search configuration."""
    endpoint: Optional[str] = None
    index_name: Optional[str] = None
    api_key: Optional[str] = None

    # Index schema customization (optional)
    semantic_config_name: Optional[str] = None
    suggester_name: Optional[str] = None
    scoring_profile_names: Optional[tuple] = None

    @classmethod
    def from_env(cls) -> "SearchConfig":
        """Load from environment variables."""
        # ... loads AZURE_SEARCH_SEMANTIC_CONFIG_NAME, etc.
```

## 3. IndexDeploymentManager (index.py)

The manager accepts these as constructor parameters:

```python
manager = IndexDeploymentManager(
    endpoint=search_config.endpoint,
    api_key=search_config.api_key,
    index_name=search_config.index_name,
    # Optional customization from config:
    semantic_config_name=search_config.semantic_config_name,
    suggester_name=search_config.suggester_name,
    scoring_profile_names=search_config.scoring_profile_names
)
```

## 4. Usage Examples

### Example 1: Use Defaults (No .env Variables Set)

```python
from src.ingestor.config import SearchConfig
from src.ingestor.index import IndexDeploymentManager

# Load config (semantic_config_name will be None)
search_config = SearchConfig.from_env()

# Create manager (will use defaults)
manager = IndexDeploymentManager(
    endpoint=search_config.endpoint,
    api_key=search_config.api_key,
    index_name=search_config.index_name,
    semantic_config_name=search_config.semantic_config_name  # None → uses "default-semantic-config"
)

# Result: Index created with default names
```

### Example 2: Use Custom Names from .env

Add to `.env`:
```bash
AZURE_SEARCH_SEMANTIC_CONFIG_NAME=alfred-semantic-config
AZURE_SEARCH_SUGGESTER_NAME=product-suggester
AZURE_SEARCH_SCORING_PROFILES=productBoostingProfile,contentRAGProfile
```

```python
from src.ingestor.config import SearchConfig
from src.ingestor.index import IndexDeploymentManager

# Load config (picks up custom names from .env)
search_config = SearchConfig.from_env()

# Create manager
manager = IndexDeploymentManager(
    endpoint=search_config.endpoint,
    api_key=search_config.api_key,
    index_name=search_config.index_name,
    semantic_config_name=search_config.semantic_config_name,  # "alfred-semantic-config"
    suggester_name=search_config.suggester_name,              # "product-suggester"
    scoring_profile_names=search_config.scoring_profile_names # ("productBoostingProfile", "contentRAGProfile")
)

# Result: Index created with custom names from .env
```

### Example 3: Override Programmatically

```python
from src.ingestor.index import IndexDeploymentManager

# Override names programmatically (ignore .env)
manager = IndexDeploymentManager(
    endpoint="https://...",
    api_key="...",
    index_name="my-index",
    semantic_config_name="my-custom-config",
    suggester_name="my-suggester",
    scoring_profile_names=("profile1", "profile2")
)

# Result: Index created with programmatic overrides
```

## 5. CLI Integration

The CLI automatically passes config values to the index manager:

```bash
# Run CLI - it reads from .env automatically
python -m src.ingestor.cli ingest --env-file .env
```

The CLI code:
```python
# Load config from .env
temp_config = PipelineConfig.from_env(env_file)

# Create manager with config values
manager = IndexDeploymentManager(
    endpoint=search_endpoint,
    api_key=search_key,
    index_name=index_name,
    semantic_config_name=temp_config.search.semantic_config_name,
    suggester_name=temp_config.search.suggester_name,
    scoring_profile_names=temp_config.search.scoring_profile_names
)
```

## 6. Validation (No Hardcoded Names)

The validation system is generic and reports actual values:

```python
# Check semantic configuration
if index.semantic_search and index.semantic_search.configurations:
    config = index.semantic_search.configurations[0]
    print(f"   Semantic search configured: {config.name}")  # Reports actual name
    print(f"   Semantic title field: {config.prioritized_fields.title_field.field_name}")
    print(f"   Semantic content fields: {len(config.prioritized_fields.content_fields)}")
```

**No hardcoded checks** like:
```python
# ❌ OLD (hardcoded):
if config.name == "alfred-semantic-config":
    print(f"   Alfred semantic config found")

# ✅ NEW (generic):
print(f"   Semantic search configured: {config.name}")
```

## 7. Complete Field Mapping

The index includes all 24 fields from your original JSON:

| Field | Type | Purpose |
|-------|------|---------|
| id | String | Primary key |
| content | String | Document text |
| embeddings | Vector(1536) | Text embeddings |
| filename | String | Source filename |
| url | String | Source URL |
| country | String | Country metadata |
| language | String | Language code |
| product_family | String | Product family |
| productTradeNames | String | Trade names |
| prod_from_url | String | Product from URL |
| title | String | Document title |
| literatureType | String | Literature type |
| partNumber | String | Part number |
| applicableTo | String | Applicable to |
| model | String | Model |
| publishedDate | DateTimeOffset | Publication date |
| pageNumber | Int32 | Page number |
| category | String | Category |
| sourcepage | String | Source page |
| sourcefile | String | Source file |
| storageUrl | String | Storage URL |
| has_figures | Boolean | Has figures flag |
| figure_urls | Collection(String) | Figure URLs |
| has_tables | Boolean | Has tables flag |

## Summary

✅ **No hardcoded names** - everything is configurable
✅ **Environment-driven** - set in .env for easy deployment
✅ **Flexible defaults** - works without configuration
✅ **CLI integration** - automatic config loading
✅ **Generic validation** - reports actual values, not expected values

The system picks up configuration in this priority:
1. **Programmatic override** (if passed to constructor)
2. **Environment variables** (from .env file)
3. **Default values** (hardcoded fallbacks)
