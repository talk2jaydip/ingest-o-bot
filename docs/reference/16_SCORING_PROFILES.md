# Scoring Profiles Guide

Guide to using the two scoring profiles in your Azure AI Search index.

---

## Available Scoring Profiles

Your index now has **2 scoring profiles** optimized for different use cases:

### 1. `productBoostingProfile` - Product-Focused Search

**Best for:** Product catalog searches, part number lookups, model searches

**Field Weights:**
| Field | Weight | Purpose |
|-------|--------|---------|
| `title` | 3.0 | Page headers (highest) |
| `productTradeNames` | 2.5 | Product names |
| `partNumber` | 2.5 | Part numbers |
| `model` | 2.0 | Model identifiers |
| `product_family` | 2.0 | Product families |
| `applicableTo` | 1.8 | Applicable devices |
| `filename` | 1.5 | Document names |
| `content` | 1.0 | Main content (baseline) |

**Functions:**
- **Freshness boost:** 2.0x for documents published within last 365 days

**Use when:**
- User searches for specific products
- Looking up part/model numbers
- Filtering by product family

---

### 2. `contentRAGProfile` - Content-Focused RAG

**Best for:** General questions, RAG applications, semantic queries

**Field Weights:**
| Field | Weight | Purpose |
|-------|--------|---------|
| `content` | 3.0 | Main content (highest) |
| `title` | 2.5 | Page headers |
| `applicableTo` | 2.0 | Context/applicability |
| `productTradeNames` | 1.5 | Product mentions |
| `product_family` | 1.5 | Family mentions |
| `category` | 1.2 | Document category |
| `filename` | 1.0 | Document name (baseline) |

**Functions:**
- **Freshness boost:** 1.5x for recent documents (less aggressive than product profile)

**Use when:**
- General "how to" questions
- RAG/chatbot queries
- Semantic search
- Content-based retrieval

---

## How to Use in Queries

### Python SDK

```python
from azure.search.documents import SearchClient

client = SearchClient(endpoint, index_name, credential)

# Use product profile
results = client.search(
    search_text="pacemaker model A2105",
    scoring_profile="productBoostingProfile",
    top=10
)

# Use content profile for RAG
results = client.search(
    search_text="how to configure pacing therapy",
    scoring_profile="contentRAGProfile",
    top=10
)
```

### REST API

```bash
# Product-focused search
curl -X POST "https://your-service.search.windows.net/indexes/myproject-index/docs/search?api-version=2024-07-01" \
  -H "api-key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "search": "pacemaker A2105",
    "scoringProfile": "productBoostingProfile",
    "top": 10
  }'

# Content-focused RAG search
curl -X POST "https://your-service.search.windows.net/indexes/myproject-index/docs/search?api-version=2024-07-01" \
  -H "api-key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "search": "how to configure pacing therapy",
    "scoringProfile": "contentRAGProfile",
    "queryType": "semantic",
    "semanticConfiguration": "my-semantic-config",
    "top": 10
  }'
```

---

## Semantic Configuration

Your semantic config now includes:

**Title Field:**
- `title` (page headers extracted from documents)

**Content Fields:**
- `content` - Main text content
- `applicableTo` - Device applicability context

**Keywords Fields:**
- `productTradeNames` - Product names
- `product_family` - Product families
- `partNumber` - Part numbers
- `model` - Model identifiers
- `category` - Document categories

---

## Hybrid Search Recommendation

For **best RAG results**, use this combination:

```python
# Hybrid: BM25 + Vector + Semantic
results = client.search(
    search_text="pacing therapy configuration",
    vector_queries=[{
        "kind": "vector",
        "vector": query_embedding,  # From Azure OpenAI
        "k": 50,
        "fields": "embeddings"
    }],
    query_type="semantic",
    semantic_configuration_name="my-semantic-config",
    scoring_profile="contentRAGProfile",  # Use content profile for RAG
    top=10
)
```

This combines:
1. **BM25** keyword matching (with optimized k1=1.5, b=0.5)
2. **Vector** semantic similarity
3. **Semantic reranking** for top results
4. **Scoring profile** for field weighting

---

## When to Use Which Profile

| Query Type | Profile | Example |
|------------|---------|---------|
| Product lookup | `productBoostingProfile` | "Find pacemaker model A2105" |
| Part number | `productBoostingProfile` | "What is part number 12345?" |
| General question | `contentRAGProfile` | "How do I configure pacing therapy?" |
| Technical procedure | `contentRAGProfile` | "Explain the implantation procedure" |
| Troubleshooting | `contentRAGProfile` | "Device not responding to commands" |

---

## Testing Profiles

After deployment, test both profiles:

```python
# Test 1: Product search
query = "pacemaker A2105"
results_product = search(query, profile="productBoostingProfile")
results_content = search(query, profile="contentRAGProfile")

# Compare which gives better results for product queries

# Test 2: Content search
query = "how to configure pacing therapy"
results_product = search(query, profile="productBoostingProfile")
results_content = search(query, profile="contentRAGProfile")

# Compare which gives better results for content queries
```

---

## Profile Selection Logic

Implement automatic profile selection in your RAG app:

```python
def select_scoring_profile(query: str) -> str:
    """Select appropriate scoring profile based on query."""
    
    # Check for product/part number patterns
    if re.search(r'\b[A-Z]\d{4}\b', query):  # Model pattern
        return "productBoostingProfile"
    
    if re.search(r'\bpart\s+number\b', query, re.IGNORECASE):
        return "productBoostingProfile"
    
    if re.search(r'\bmodel\b', query, re.IGNORECASE):
        return "productBoostingProfile"
    
    # Default to content profile for general queries
    return "contentRAGProfile"
```

