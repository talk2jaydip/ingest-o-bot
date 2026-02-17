# Index Configuration - Quick Reference

## 🎯 Where Names Are Defined

### Option 1: Environment Variables (.env file) ⭐ **RECOMMENDED**

```bash
# Add these to your .env file (all optional):
AZURE_SEARCH_SEMANTIC_CONFIG_NAME=alfred-semantic-config
AZURE_SEARCH_SUGGESTER_NAME=product-suggester
AZURE_SEARCH_SCORING_PROFILES=productBoostingProfile,contentRAGProfile
```

### Option 2: Programmatic Override

```python
manager = IndexDeploymentManager(
    endpoint="...",
    api_key="...",
    index_name="...",
    semantic_config_name="my-custom-name",
    suggester_name="my-suggester",
    scoring_profile_names=("profile1", "profile2")
)
```

## 🔄 How Code Picks Up the Names

```
┌─────────────────────────────────────────────────────────────┐
│  1. .env File                                               │
│     AZURE_SEARCH_SEMANTIC_CONFIG_NAME=alfred-semantic-config│
│     AZURE_SEARCH_SUGGESTER_NAME=product-suggester           │
│     AZURE_SEARCH_SCORING_PROFILES=profile1,profile2         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  2. SearchConfig.from_env()                                 │
│     - Reads environment variables                           │
│     - Returns SearchConfig object with values               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  3. IndexDeploymentManager(...)                             │
│     - Receives config values from SearchConfig              │
│     - Uses values to create index schema                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  4. Azure AI Search Index Created                           │
│     - Semantic config: "alfred-semantic-config"             │
│     - Suggester: "product-suggester"                        │
│     - Scoring profiles: ["profile1", "profile2"]            │
└─────────────────────────────────────────────────────────────┘
```

## 📝 Code Example

```python
from dotenv import load_dotenv
from src.ingestor.config import SearchConfig, AzureOpenAIConfig
from src.ingestor.index import IndexDeploymentManager

# 1. Load .env file
load_dotenv()

# 2. Load config (automatically reads env variables)
search_config = SearchConfig.from_env()
openai_config = AzureOpenAIConfig.from_env()

# 3. Create manager (passes config values)
manager = IndexDeploymentManager(
    endpoint=search_config.endpoint,
    api_key=search_config.api_key,
    index_name=search_config.index_name,
    openai_endpoint=openai_config.endpoint,
    openai_deployment=openai_config.emb_deployment,
    openai_key=openai_config.api_key,
    # These come from .env:
    semantic_config_name=search_config.semantic_config_name,
    suggester_name=search_config.suggester_name,
    scoring_profile_names=search_config.scoring_profile_names
)

# 4. Deploy index
manager.deploy_index()
```

## 🎨 Default Values

If env variables are NOT set, these defaults are used:

| Config | Default Value |
|--------|---------------|
| Semantic Config Name | `"default-semantic-config"` |
| Suggester Name | `"default-suggester"` |
| Scoring Profile Names | `("productBoostingProfile", "contentRAGProfile")` |

## ✅ Verification

To check what names will be used:

```python
from src.ingestor.config import SearchConfig

config = SearchConfig.from_env()

print(f"Semantic Config: {config.semantic_config_name or 'default-semantic-config'}")
print(f"Suggester: {config.suggester_name or 'default-suggester'}")
print(f"Scoring Profiles: {config.scoring_profile_names or ('productBoostingProfile', 'contentRAGProfile')}")
```

## 🚀 CLI Usage

The CLI automatically picks up these values:

```bash
# Just run the CLI - it reads .env automatically
python -m src.ingestor.cli ingest --env-file .env
```

## 📦 Complete Field List (24 fields)

All fields from your original JSON are included:

✅ Core: id, content, embeddings, filename, url
✅ Metadata: country, language, product_family, productTradeNames, prod_from_url
✅ Document: title, literatureType, partNumber, applicableTo, model
✅ Dates: publishedDate, pageNumber, category
✅ Source: sourcepage, sourcefile, storageUrl
✅ Media: has_figures, figure_urls, has_tables

## 🎯 Key Points

1. **No hardcoded names** in validation - reports actual values
2. **Environment-driven** - configure via .env file
3. **Flexible** - works without configuration (uses defaults)
4. **CLI-integrated** - automatic config loading
5. **SDK-based** - pure Azure AI Search Python SDK implementation
