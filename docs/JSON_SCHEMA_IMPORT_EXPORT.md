# Azure AI Search Index - JSON Schema Import/Export

## Overview

The index management system now supports importing and exporting index schemas as JSON files. This enables:

- **Version Control**: Track index schema changes in git
- **Backup & Restore**: Save index configurations before making changes
- **Environment Migration**: Move index schemas between dev/test/prod
- **Schema Reuse**: Use existing index JSON definitions from Azure Portal exports
- **Documentation**: Human-readable schema documentation

## Features

### Export Schema to JSON
Export the complete schema of an existing Azure AI Search index to a JSON file.

**What's Exported:**
- All fields with their types, analyzers, and properties
- Scoring profiles with text weights and boost functions
- Suggesters with source fields
- Semantic search configuration (title, content, keyword fields)
- Vector search configuration (algorithms, profiles, compressions)

### Import Schema from JSON
Create a new Azure AI Search index from a JSON schema file.

**What's Created:**
- All fields as defined in JSON
- Scoring profiles
- Suggesters
- Semantic search configuration
- Vector search configuration
- BM25 similarity algorithm (k1=1.5, b=0.5)

## CLI Usage

### Export Current Index Schema

```bash
# Export to a specific file
python -m src.ingestor.cli --export-schema schema_backup.json

# Export to auto-generated timestamped file
# (Creates: backups/<index-name>_schema_<timestamp>.json)
python -m src.ingestor.cli --export-schema backups/my_schema.json
```

**Output:**
```
======================================================================
Exporting Index Schema to JSON
======================================================================
Exporting schema for index: alfred-experiment-index-2
✓ Index schema exported to: schema_backup.json
  - 24 fields
  - 2 scoring profiles
  - 1 suggesters
  - Semantic search configuration
  - Vector search configuration

SUCCESS: Schema exported to schema_backup.json

Export operation completed. Exiting.
```

### Import Schema to Create Index

```bash
# Import from JSON file (uses index name from .env)
python -m src.ingestor.cli --import-schema original_index.json

# Import with custom index name
# (Set AZURE_SEARCH_INDEX in .env first)
python -m src.ingestor.cli --import-schema schema_backup.json
```

**Output:**
```
======================================================================
Creating Index from JSON Schema
======================================================================
Target index name: alfred-experiment-index-2
JSON schema file: original_index.json
  Loaded schema from original_index.json
  - 24 fields
  - 2 scoring profiles
  - 1 suggesters
  Creating index 'alfred-experiment-index-2'...
✓ Index created successfully from JSON
   Checking index configuration...
   2 scoring profile(s) configured
   BM25 similarity configured
   Semantic search configured: default-semantic-config
   Semantic title field: title
   Semantic content fields: 2
   Semantic keyword fields: 5
   Suggester configured: default-suggester (2 fields)
   Vector compression configured
   All critical validations passed
✓ Index validation passed

SUCCESS: Index created from original_index.json

Import operation completed. Exiting.
```

## Programmatic Usage

### Export Schema

```python
from src.ingestor.index import IndexDeploymentManager

manager = IndexDeploymentManager(
    endpoint="https://your-search.search.windows.net",
    api_key="your-api-key",
    index_name="your-index-name"
)

# Export schema
output_file = manager.export_schema_to_json("schema_backup.json")
print(f"Schema exported to: {output_file}")
```

### Import Schema

```python
from src.ingestor.index import IndexDeploymentManager

manager = IndexDeploymentManager(
    endpoint="https://your-search.search.windows.net",
    api_key="your-api-key",
    index_name="new-index-name"
)

# Import schema (creates new index)
success = manager.create_index_from_json(
    json_file="schema_backup.json",
    skip_if_exists=True  # Skip if index already exists
)

if success:
    print("Index created successfully!")
```

## JSON Schema Format

The exported JSON follows this structure:

```json
{
  "name": "index-name",
  "fields": [
    {
      "name": "id",
      "type": "Edm.String",
      "key": true,
      "filterable": true
    },
    {
      "name": "content",
      "type": "Edm.String",
      "searchable": true,
      "analyzer": "standard.lucene"
    },
    {
      "name": "embeddings",
      "type": "Collection(Edm.Single)",
      "searchable": true,
      "vectorSearchDimensions": 1536,
      "vectorSearchProfileName": "myHnswProfile"
    }
  ],
  "scoringProfiles": [
    {
      "name": "productBoostingProfile",
      "functionAggregation": "sum",
      "text": {
        "weights": {
          "title": 3.0,
          "content": 1.0
        }
      },
      "functions": [
        {
          "type": "FreshnessScoringFunction",
          "fieldName": "publishedDate",
          "boost": 2.0,
          "interpolation": "linear",
          "boostingDuration": "P365D"
        }
      ]
    }
  ],
  "suggesters": [
    {
      "name": "default-suggester",
      "sourceFields": ["title", "product_family"]
    }
  ],
  "semantic": {
    "configurations": [
      {
        "name": "default-semantic-config",
        "prioritizedFields": {
          "titleField": {
            "fieldName": "title"
          },
          "contentFields": [
            {"fieldName": "content"},
            {"fieldName": "applicableTo"}
          ],
          "keywordsFields": [
            {"fieldName": "productTradeNames"},
            {"fieldName": "product_family"}
          ]
        }
      }
    ]
  },
  "vectorSearch": {
    "profiles": [
      {
        "name": "myHnswProfile",
        "algorithmConfigurationName": "myHnsw",
        "compressionName": "myCompression"
      }
    ],
    "algorithms": [
      {
        "name": "myHnsw",
        "kind": "HnswAlgorithmConfiguration",
        "parameters": {
          "m": 16,
          "efConstruction": 400,
          "efSearch": 500,
          "metric": "cosine"
        }
      }
    ],
    "compressions": [
      {
        "name": "myCompression",
        "kind": "ScalarQuantizationCompression",
        "rerankWithOriginalVectors": true,
        "defaultOversampling": 10.0
      }
    ]
  }
}
```

## Use Cases

### 1. Backup Before Changes

```bash
# Backup current schema before making changes
python -m src.ingestor.cli --export-schema backups/schema_before_update.json

# Make changes to index programmatically
# If something goes wrong, restore from backup:
python -m src.ingestor.cli --delete-index
python -m src.ingestor.cli --import-schema backups/schema_before_update.json
```

### 2. Migrate Between Environments

```bash
# Export from dev
python -m src.ingestor.cli --env .env.dev --export-schema dev_schema.json

# Import to prod (change index name in .env.prod first)
python -m src.ingestor.cli --env .env.prod --import-schema dev_schema.json
```

### 3. Use Existing Azure Portal JSON

If you have an existing index JSON from Azure Portal:

```bash
# Download JSON from Azure Portal
# Save as original_index.json

# Create index from that JSON
python -m src.ingestor.cli --import-schema original_index.json
```

### 4. Version Control

```bash
# Export schema to version control
python -m src.ingestor.cli --export-schema schemas/index_v1.json

# Commit to git
git add schemas/index_v1.json
git commit -m "Add index schema v1"

# Later, restore from version control
python -m src.ingestor.cli --import-schema schemas/index_v1.json
```

## Field Type Mapping

The import/export system handles these Azure Search field types:

| JSON Type | Python SDK Type |
|-----------|----------------|
| `Edm.String` | `SearchFieldDataType.String` |
| `Edm.Int32` | `SearchFieldDataType.Int32` |
| `Edm.Int64` | `SearchFieldDataType.Int64` |
| `Edm.Double` | `SearchFieldDataType.Double` |
| `Edm.Boolean` | `SearchFieldDataType.Boolean` |
| `Edm.DateTimeOffset` | `SearchFieldDataType.DateTimeOffset` |
| `Collection(Edm.String)` | `SearchFieldDataType.Collection(SearchFieldDataType.String)` |
| `Collection(Edm.Single)` | `SearchFieldDataType.Collection(SearchFieldDataType.Single)` (vectors) |

## Limitations

1. **Vectorizer Support**: Integrated vectorizers (AzureOpenAIVectorizer) are exported but may not import correctly if using older SDK versions that don't support this feature.

2. **Data Not Included**: Only schema is exported/imported - actual document data is NOT included. Use Azure Search data import/export tools for data migration.

3. **Custom Analyzers**: Custom analyzer definitions are not currently exported. Only built-in analyzers (standard.lucene, en.microsoft, keyword, etc.) are supported.

4. **Skillsets**: Index skillsets and indexers are not included in the schema export.

## Troubleshooting

### Export Fails with "Index does not exist"
**Solution**: Make sure the index exists before exporting. Use `--check-index` first:
```bash
python -m src.ingestor.cli --check-index
```

### Import Fails with "Index already exists"
**Solution**: Delete the existing index first or use a different index name:
```bash
python -m src.ingestor.cli --delete-index
python -m src.ingestor.cli --import-schema schema.json
```

### JSON Parse Error
**Solution**: Validate your JSON file:
```bash
python -c "import json; json.load(open('schema.json'))"
```

### Field Type Errors
**Solution**: Ensure field types use Azure Search EDM types (Edm.String, Edm.Int32, etc.), not plain Python types.

## Summary

✅ **Export**: Full schema backup to JSON
✅ **Import**: Create index from JSON file
✅ **CLI Integration**: Simple command-line interface
✅ **Version Control**: Track schema changes in git
✅ **Migration**: Move schemas between environments
✅ **Azure Portal Compatible**: Use existing JSON exports

**Status**: Ready to use for backup, migration, and version control of index schemas!
