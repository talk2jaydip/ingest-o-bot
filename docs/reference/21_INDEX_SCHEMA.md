# Azure AI Search Index Schema Reference

Complete reference for the ingestor library's Azure AI Search index schema, including all fields, configurations, and best practices.

---

## Table of Contents

- [Overview](#overview)
- [Index Fields](#index-fields)
- [Field Analyzers](#field-analyzers)
- [Semantic Configuration](#semantic-configuration)
- [Scoring Profiles](#scoring-profiles)
- [Vector Search Configuration](#vector-search-configuration)
- [Suggesters](#suggesters)
- [BM25 Similarity Settings](#bm25-similarity-settings)
- [Creating the Index](#creating-the-index)
- [Field Usage Examples](#field-usage-examples)

---

## Overview

The ingestor library uses a comprehensive Azure AI Search index schema optimized for:
- **Hybrid search**: Combines full-text, semantic, and vector search
- **Product/medical/technical documents**: Specialized fields for equipment, manuals, specifications
- **Multilingual support**: Language and country filtering
- **Temporal relevance**: Freshness scoring based on publish dates
- **Faceted navigation**: Filterable fields for UI refinement

**Index Statistics:**
- **21 fields total**
- **2 scoring profiles** (product-focused and content-focused)
- **1 suggester** for autocomplete
- **1 semantic configuration** with title, content, and keyword fields
- **Vector search** with HNSW algorithm and scalar quantization compression

---

## Index Fields

### Core Document Fields

| Field Name | Type | Key | Searchable | Filterable | Sortable | Facetable | Analyzer | Purpose |
|------------|------|-----|------------|------------|----------|-----------|----------|---------|
| **id** | `String` | ✓ | ✗ | ✓ | ✗ | ✗ | N/A | Unique document identifier (format: `filename-page-chunk`) |
| **content** | `String` | ✗ | ✓ | ✗ | ✗ | ✗ | `en.microsoft` | Main text content of the chunk (primary search field) |
| **embeddings** | `Collection(Single)` | ✗ | ✓ | ✗ | ✗ | ✗ | N/A | Vector embeddings (1536 dimensions for OpenAI ada-002/3-large) |

**Notes:**
- **id**: Generated as `{filename}-page{pageNumber}-chunk{chunkIndex}` (e.g., `manual.pdf-page1-chunk0`)
- **content**: Indexed with Microsoft English analyzer for stemming and stopword removal
- **embeddings**:
  - Made **retrievable** (not hidden) for debugging and inspection
  - Uses `vector-profile-optimized` with HNSW + scalar quantization
  - Dimensions: 1536 (standard for OpenAI text-embedding-ada-002 and text-embedding-3-large)

---

### Metadata Fields

| Field Name | Type | Searchable | Filterable | Sortable | Facetable | Analyzer | Purpose |
|------------|------|------------|------------|----------|-----------|----------|---------|
| **filename** | `String` | ✓ | ✓ | ✓ | ✓ | `keyword` | Original document filename |
| **sourcefile** | `String` | ✓ | ✓ | ✓ | ✗ | `keyword` | Source file path (same as filename for local files) |
| **sourcepage** | `String` | ✓ | ✓ | ✓ | ✗ | `keyword` | Page identifier in source document |
| **url** | `String` | ✗ | ✓ | ✓ | ✗ | N/A | Public URL to the source document (if available) |
| **storageUrl** | `String` | ✗ | ✗ | ✗ | ✗ | N/A | Azure Blob Storage URL (private, not searchable) |
| **pageNumber** | `Int32` | ✗ | ✓ | ✓ | ✗ | N/A | Page number in the original document |
| **publishedDate** | `DateTimeOffset` | ✗ | ✓ | ✓ | ✓ | N/A | Document publication date (used for freshness scoring) |

**Notes:**
- **filename**: Exact match with keyword analyzer (no tokenization)
- **sourcepage**: Format: `{filename}#page={pageNumber}` (e.g., `manual.pdf#page=5`)
- **publishedDate**: ISO 8601 format, used in freshness scoring functions

---

### Product/Equipment Fields

| Field Name | Type | Searchable | Filterable | Facetable | Analyzer | Purpose |
|------------|------|------------|------------|-----------|----------|---------|
| **title** | `String` | ✓ | ✓ (sort) | ✗ | `standard.lucene` | Page title/header (semantic title field) |
| **productTradeNames** | `Collection(String)` | ✓ | ✓ | ✓ | `standard.lucene` | Product names (e.g., "Pacemaker Model 5000") |
| **product_family** | `Collection(String)` | ✓ | ✓ | ✓ | `en.microsoft` | Product families (e.g., "Cardiac Rhythm Management") |
| **prod_from_url** | `String` | ✓ | ✓ (sort) | ✓ | `keyword` | Product extracted from URL path |
| **partNumber** | `String` | ✓ | ✓ (sort) | ✗ | `keyword` | Part/model number (exact match) |
| **model** | `Collection(String)` | ✓ | ✓ | ✓ | `keyword` | Model identifiers (exact match) |
| **applicableTo** | `Collection(String)` | ✓ | ✓ | ✓ | `en.microsoft` | Equipment/procedures this applies to |
| **category** | `String` | ✓ | ✓ (sort) | ✓ | `en.microsoft` | Document category (e.g., "Manual", "Specification") |
| **literatureType** | `Collection(String)` | ✓ | ✓ | ✓ | `keyword` | Document type classification |

**Notes:**
- **title**: Tokenized without stemming (preserves original terms in headers)
- **productTradeNames**: Allows partial matching (e.g., "pacemaker" matches without hyphens)
- **partNumber & model**: Keyword analyzer ensures exact matching for IDs
- **applicableTo**: Additional semantic context for "what equipment is this relevant to?"

---

### Localization Fields

| Field Name | Type | Searchable | Filterable | Facetable | Analyzer | Purpose |
|------------|------|------------|------------|-----------|----------|---------|
| **country** | `Collection(String)` | ✓ | ✓ | ✓ | `keyword` | Target countries (e.g., ["US", "CA", "GB"]) |
| **language** | `String` | ✓ | ✓ (sort) | ✓ | `keyword` | Document language (e.g., "en", "es", "fr") |

**Notes:**
- **country**: Supports multiple countries per document
- **language**: ISO 639-1 language codes

---

## Field Analyzers

Analyzers determine how text is tokenized and indexed.

### Analyzer Comparison

| Analyzer | Tokenization | Stemming | Stopwords | Use Case | Example Fields |
|----------|--------------|----------|-----------|----------|----------------|
| **en.microsoft** | Yes | Yes | Yes | Natural language content | `content`, `product_family`, `applicableTo`, `category` |
| **standard.lucene** | Yes | No | No | Headers and names | `title`, `productTradeNames` |
| **keyword** | No (exact match) | No | No | IDs and exact values | `filename`, `partNumber`, `model`, `country`, `language` |

### Analyzer Details

#### 1. **en.microsoft** (Microsoft English)
- **Tokenizes**: Splits on whitespace and punctuation
- **Lowercases**: Normalizes to lowercase
- **Stems**: `running` → `run`, `doctors` → `doctor`
- **Removes stopwords**: Filters common words like "the", "and", "is"
- **Best for**: Main content fields where semantic understanding matters

**Example:**
```
Input:  "The doctors are running comprehensive tests"
Tokens: ["doctor", "run", "comprehensive", "test"]
```

#### 2. **standard.lucene** (Standard Lucene)
- **Tokenizes**: Splits on whitespace and punctuation
- **Lowercases**: Normalizes to lowercase
- **No stemming**: Preserves original word forms
- **No stopword removal**: Keeps all words
- **Best for**: Titles, headers, and product names where exact phrasing matters

**Example:**
```
Input:  "Pacemaker Model 5000"
Tokens: ["pacemaker", "model", "5000"]
```

#### 3. **keyword** (No Tokenization)
- **Exact match only**: Entire string treated as single token
- **Case-sensitive option**: Can be configured
- **Best for**: IDs, part numbers, country codes, filenames

**Example:**
```
Input:  "PM-5000-XL"
Token:  ["PM-5000-XL"]  (stored exactly as-is)
```

---

## Semantic Configuration

Azure AI Search's semantic ranker uses AI models to improve relevance by understanding query intent.

### Configuration: `my-semantic-config`

```python
SemanticConfiguration(
    name="my-semantic-config",
    prioritized_fields=SemanticPrioritizedFields(
        title_field=SemanticField(field_name="title"),
        content_fields=[
            SemanticField(field_name="content"),
            SemanticField(field_name="applicableTo")
        ],
        keywords_fields=[
            SemanticField(field_name="productTradeNames"),
            SemanticField(field_name="product_family"),
            SemanticField(field_name="partNumber"),
            SemanticField(field_name="model"),
            SemanticField(field_name="category")
        ]
    )
)
```

### Field Roles

| Role | Field Name | Purpose in Semantic Ranking |
|------|------------|----------------------------|
| **Title** | `title` | Document structure and section identification |
| **Content** | `content` | Primary semantic understanding |
| **Content** | `applicableTo` | Additional context (equipment relevance) |
| **Keywords** | `productTradeNames` | Product identification |
| **Keywords** | `product_family` | Product categorization |
| **Keywords** | `partNumber` | Specific model identification |
| **Keywords** | `model` | Model/version identification |
| **Keywords** | `category` | Document type classification |

### How Semantic Search Works

1. **Title field**: Used to understand document structure (which section/page this is)
2. **Content fields**: Analyzed for query intent and semantic relevance
3. **Keyword fields**: Used for entity recognition and boosting specific product/model matches

**Usage:**
```python
# Enable semantic ranking in query
results = search_client.search(
    search_text="pacemaker battery replacement procedure",
    query_type="semantic",
    semantic_configuration_name="my-semantic-config",
    top=10
)
```

---

## Scoring Profiles

Scoring profiles boost relevance based on field importance and freshness.

### Profile 1: `productBoostingProfile`

**Use case**: Product-focused searches (e.g., "Find Model XYZ specifications")

```python
ScoringProfile(
    name="productBoostingProfile",
    text_weights=TextWeights(weights={
        "title": 3.0,
        "productTradeNames": 2.5,
        "product_family": 2.0,
        "partNumber": 2.5,
        "model": 2.0,
        "content": 1.0,
        "filename": 1.5,
        "applicableTo": 1.8
    }),
    functions=[
        FreshnessScoringFunction(
            field_name="publishedDate",
            boost=2.0,
            parameters=FreshnessScoringParameters(boosting_duration="P365D")
        )
    ]
)
```

**Field Weights:**
- **title (3.0)**: Page headers are very important
- **productTradeNames (2.5)**: Product names highly relevant
- **partNumber (2.5)**: Exact model matches are critical
- **product_family (2.0)**: Product families matter
- **model (2.0)**: Model identifiers important
- **applicableTo (1.8)**: "What equipment is this for?" context
- **filename (1.5)**: Filename can indicate relevance
- **content (1.0)**: Baseline relevance

**Freshness Boost:**
- **boost=2.0**: Documents within 1 year get 2x score boost
- **boosting_duration="P365D"**: Linear decay over 365 days

**When to use:**
```python
results = search_client.search(
    search_text="pacemaker model 5000",
    scoring_profile="productBoostingProfile",
    top=10
)
```

---

### Profile 2: `contentRAGProfile`

**Use case**: Content-focused RAG queries (e.g., "How to replace batteries?")

```python
ScoringProfile(
    name="contentRAGProfile",
    text_weights=TextWeights(weights={
        "content": 3.0,
        "title": 2.5,
        "applicableTo": 2.0,
        "productTradeNames": 1.5,
        "product_family": 1.5,
        "category": 1.2,
        "filename": 1.0
    }),
    functions=[
        FreshnessScoringFunction(
            field_name="publishedDate",
            boost=1.5,
            parameters=FreshnessScoringParameters(boosting_duration="P365D")
        )
    ]
)
```

**Field Weights:**
- **content (3.0)**: Main content is most important for RAG
- **title (2.5)**: Section headers provide context
- **applicableTo (2.0)**: Equipment context matters
- **productTradeNames (1.5)**: Product names relevant but not primary
- **product_family (1.5)**: Product families provide context
- **category (1.2)**: Document type matters
- **filename (1.0)**: Baseline relevance

**Freshness Boost:**
- **boost=1.5**: Moderate boost for newer documents
- **boosting_duration="P365D"**: Linear decay over 365 days

**When to use:**
```python
results = search_client.search(
    search_text="battery replacement procedure steps",
    scoring_profile="contentRAGProfile",
    top=10
)
```

---

## Vector Search Configuration

Vector search enables semantic similarity matching using embeddings.

### HNSW Algorithm

**Hierarchical Navigable Small World (HNSW)** - Fast approximate nearest neighbor search

```python
HnswAlgorithmConfiguration(
    name="vector-config-optimized",
    parameters=HnswParameters(
        metric=VectorSearchAlgorithmMetric.COSINE,
        m=16,              # Graph connectivity (default: 4, optimized: 16)
        ef_construction=400,  # Indexing quality (default: 400, optimized: 400)
        ef_search=500      # Search quality (default: 400, optimized: 500)
    )
)
```

**Parameters:**
- **metric=COSINE**: Use cosine similarity for vector comparisons
- **m=16**: Each node connects to 16 neighbors (higher = better recall, slower indexing)
- **ef_construction=400**: Build graph quality (higher = better accuracy, slower indexing)
- **ef_search=500**: Search quality (higher = better accuracy, slower queries)

**Trade-offs:**
| Parameter | Low Value | High Value |
|-----------|-----------|------------|
| **m** | Faster indexing, lower recall | Slower indexing, better recall |
| **ef_construction** | Fast index build, lower quality | Slow index build, high quality |
| **ef_search** | Fast queries, lower recall | Slower queries, better recall |

---

### Scalar Quantization Compression

**Reduces storage by ~75%** by converting float32 embeddings to int8.

```python
ScalarQuantizationCompression(
    compression_name="scalar-quantization",
    rescoring_options=RescoringOptions(
        enable_rescoring=True,
        default_oversampling=20.0,  # Fetch 20x candidates for rescoring
        rescore_storage_method=VectorSearchCompressionRescoreStorageMethod.PRESERVE_ORIGINALS
    ),
    parameters=ScalarQuantizationParameters(
        quantized_data_type="int8"
    )
)
```

**How it works:**
1. **Quantize**: Convert float32 (4 bytes) → int8 (1 byte) per dimension
2. **Oversample**: Retrieve 20x candidates using compressed vectors
3. **Rescore**: Re-rank using original float32 vectors for accuracy

**Storage savings:**
- **Before**: 1536 dimensions × 4 bytes = 6,144 bytes/document
- **After**: 1536 dimensions × 1 byte = 1,536 bytes/document (75% reduction)
- **Trade-off**: Slightly slower queries due to rescoring, but minimal accuracy loss

---

### Vector Search Profile

Combines algorithm and compression:

```python
VectorSearchProfile(
    name="vector-profile-optimized",
    algorithm_configuration_name="vector-config-optimized",
    compression_name="scalar-quantization"
)
```

**Usage:**
```python
# Vector search with hybrid query
results = search_client.search(
    search_text="battery replacement",
    vector_queries=[VectorizedQuery(
        vector=query_embedding,  # 1536-dimensional vector
        k_nearest_neighbors=50,
        fields="embeddings"
    )],
    top=10
)
```

---

### Integrated Vectorizer (Optional)

If OpenAI credentials are provided, an **integrated vectorizer** can be configured to generate embeddings server-side:

```python
AzureOpenAIVectorizer(
    vectorizer_name=f"vectorizer-{index_name}",
    parameters=AzureOpenAIVectorizerParameters(
        resource_url="https://your-openai.openai.azure.com",
        deployment_name="text-embedding-ada-002",
        api_key="your-key",
        model_name="text-embedding-ada-002"
    )
)
```

**Note**: The ingestor library performs **client-side** embedding generation by default (not using integrated vectorizer).

---

## Suggesters

Suggesters enable autocomplete/typeahead functionality.

### Configuration: `product-suggester`

```python
SearchSuggester(
    name="product-suggester",
    source_fields=["title", "product_family"]
)
```

**Notes:**
- **Source fields**: Only `title` and `product_family` (default/language analyzers required)
- **Cannot use**: Fields with `keyword` analyzer (like `partNumber`, `productTradeNames`)

**Usage:**
```python
# Autocomplete suggestions
suggestions = search_client.suggest(
    search_text="pacema",
    suggester_name="product-suggester",
    top=10
)
# Returns: ["Pacemaker Model 5000", "Pacemaker CRT-D", ...]
```

---

## BM25 Similarity Settings

**BM25 (Best Match 25)** is the ranking algorithm for full-text search.

### Configuration

```python
BM25SimilarityAlgorithm(
    k1=1.5,  # Term frequency saturation (default: 1.2, optimized: 1.5)
    b=0.5    # Document length normalization (default: 0.75, optimized: 0.5)
)
```

### Parameters

| Parameter | Default | Optimized | Effect |
|-----------|---------|-----------|--------|
| **k1** | 1.2 | 1.5 | Higher = more weight to term frequency (repeated terms matter more) |
| **b** | 0.75 | 0.5 | Lower = reduce document length penalty (long manuals not penalized) |

### Why These Settings?

**k1=1.5** (increased from 1.2):
- Technical/medical documents often repeat important terms (e.g., "pacemaker" appears many times in manual)
- Higher k1 gives more credit to term frequency, benefiting specialized vocabulary

**b=0.5** (decreased from 0.75):
- Long manuals (100+ pages) shouldn't be penalized just for length
- Lower b reduces length normalization, helping long comprehensive documents rank well

**Comparison:**
```
Document A: 100-page manual, 10 mentions of "pacemaker"
Document B: 5-page summary, 3 mentions of "pacemaker"

Default (k1=1.2, b=0.75): Document B might rank higher (shorter = bonus)
Optimized (k1=1.5, b=0.5): Document A ranks higher (more term frequency, less length penalty)
```

---

## Creating the Index

### Method 1: Using CLI (Recommended)

```bash
# Create index with environment variables
ingestor --setup-index

# Create index and process documents
ingestor --setup-index --glob "documents/*.pdf"

# Force recreate (WARNING: deletes all data)
ingestor --setup-index --force-index --glob "documents/*.pdf"
```

**Required environment variables:**
```bash
AZURE_SEARCH_SERVICE=your-service-name
AZURE_SEARCH_KEY=your-api-key
AZURE_SEARCH_INDEX=your-index-name
```

**Optional (for integrated vectorizer):**
```bash
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_KEY=your-openai-key
```

---

### Method 2: Using Python Library

```python
from ingestor import IndexDeploymentManager

# Create index manager
manager = IndexDeploymentManager(
    endpoint="https://your-service.search.windows.net",
    api_key="your-api-key",
    index_name="documents-index",
    verbose=True
)

# Deploy index
success = manager.deploy_index(
    force=False,           # Set True to delete and recreate
    dry_run=False,         # Set True to preview changes
    skip_if_exists=True    # Set False to fail if index exists
)

if success:
    print("Index deployed successfully!")
```

---

### Method 3: Using Python Script Directly

```bash
# From index.py
python src/ingestor/index.py --mode deploy --verbose

# With OpenAI for integrated vectorizer
python src/ingestor/index.py \
    --mode deploy \
    --searchservice your-service \
    --searchkey your-key \
    --index-name my-index \
    --openai-endpoint https://your-openai.openai.azure.com \
    --openai-deployment text-embedding-ada-002 \
    --openai-key your-openai-key
```

---

## Field Usage Examples

### Example 1: Product-Specific Search

**Query**: "Find specifications for Pacemaker Model 5000"

**Search request:**
```python
results = search_client.search(
    search_text="specifications pacemaker model 5000",
    filter="productTradeNames/any(p: p eq 'Pacemaker Model 5000')",
    scoring_profile="productBoostingProfile",
    select=["id", "title", "content", "productTradeNames", "partNumber", "pageNumber"],
    top=10
)
```

**Why these fields?**
- **filter**: Exact match on product name
- **scoring_profile**: Product-focused ranking
- **select**: Return relevant metadata

---

### Example 2: Content-Based RAG Query

**Query**: "How to replace pacemaker batteries?"

**Search request:**
```python
results = search_client.search(
    search_text="battery replacement procedure steps",
    scoring_profile="contentRAGProfile",
    query_type="semantic",
    semantic_configuration_name="my-semantic-config",
    select=["id", "content", "title", "sourcepage", "filename"],
    top=5
)
```

**Why these fields?**
- **scoring_profile**: Content-focused ranking
- **query_type="semantic"**: Use AI reranking
- **select**: Fields needed for RAG context

---

### Example 3: Hybrid Vector + Keyword Search

**Query**: "Implantation procedure for cardiac devices"

**Search request:**
```python
# Generate embedding for query
query_embedding = openai_client.embeddings.create(
    input="implantation procedure cardiac devices",
    model="text-embedding-ada-002"
).data[0].embedding

# Hybrid search
results = search_client.search(
    search_text="implantation procedure cardiac devices",
    vector_queries=[VectorizedQuery(
        vector=query_embedding,
        k_nearest_neighbors=50,
        fields="embeddings"
    )],
    filter="category eq 'Manual' or category eq 'Procedure'",
    select=["id", "content", "title", "category", "productTradeNames"],
    top=10
)
```

**Why hybrid?**
- **search_text**: Keyword matching for explicit terms
- **vector_queries**: Semantic similarity for conceptual matches
- **filter**: Restrict to relevant document types

---

### Example 4: Faceted Search

**Scenario**: Browse documents by country, language, and product family

**Search request:**
```python
results = search_client.search(
    search_text="*",  # All documents
    filter="country/any(c: c eq 'US') and language eq 'en'",
    facets=[
        "product_family,count:20",
        "category,count:10",
        "literatureType,count:10"
    ],
    top=50
)

# Access facets
for facet_name, facet_results in results.get_facets().items():
    print(f"{facet_name}:")
    for facet in facet_results:
        print(f"  {facet['value']}: {facet['count']} documents")
```

**Why faceting?**
- **Discoverable navigation**: Users can refine by categories
- **Facets**: Show counts for each value
- **Filterable fields**: Enable drill-down

---

## Best Practices

### 1. Field Selection

✅ **Do:**
- Use `content` for main text
- Use `title` for section headers
- Use `keyword` analyzer for IDs (partNumber, model, filename)
- Use `en.microsoft` for natural language fields

❌ **Don't:**
- Put long text in facetable fields (performance impact)
- Use searchable fields you don't need (increases index size)

---

### 2. Scoring Profiles

✅ **Do:**
- Use `productBoostingProfile` for product-specific searches
- Use `contentRAGProfile` for general content queries
- Adjust field weights based on your use case

❌ **Don't:**
- Use scoring profiles with semantic ranking (they don't combine)
- Over-boost fields (can skew results)

---

### 3. Vector Search

✅ **Do:**
- Use hybrid search (text + vector) for best results
- Set `k_nearest_neighbors` to 50-100 for good recall
- Use compression for large indexes (saves 75% storage)

❌ **Don't:**
- Use vector-only search (misses exact term matches)
- Set `ef_search` too low (< 100) for accuracy-critical scenarios

---

### 4. Semantic Search

✅ **Do:**
- Use semantic ranking for natural language queries
- Combine with filters for best precision
- Use for top 10-50 results (semantic ranking is expensive)

❌ **Don't:**
- Use semantic ranking for keyword/ID searches
- Apply semantic ranking to thousands of results (slow + expensive)

---

### 5. Index Maintenance

✅ **Do:**
- Backup index before schema changes (`ingestor --index-only --force-index` creates backup)
- Test changes in dev environment first
- Monitor index size and query performance

❌ **Don't:**
- Delete index without backup
- Change field types without recreating index (not supported)

---

## Related Documentation

- [Index Deployment Guide](../guides/INDEX_DEPLOYMENT_GUIDE.md) - How to deploy and manage indexes
- [Configuration Guide](../guides/CONFIGURATION.md) - Environment variables and settings
- [Quick Start Guide](../guides/QUICKSTART.md) - Getting started
- [API Reference](../reference/) - Full API documentation

---

## Support

For issues or questions:
- 📖 [Documentation Index](../INDEX.md)
- 🐛 [Report Issues](https://github.com/yourusername/ingestor/issues)
- 💬 [Discussions](https://github.com/yourusername/ingestor/discussions)

---

**Last Updated**: February 2025 (ingestor v0.2.0)
