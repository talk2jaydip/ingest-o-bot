# Index Improvements Summary

Summary of optimizations applied to `ingestor/index.py` for better hybrid retrieval.

---

## Changes Applied

### 1. BM25 Similarity Tuning ✅

**Purpose:** Better ranking for technical/medical documents with repeated terms and long content.

```python
similarity = BM25Similarity(
    k1=1.5,  # Increased from default 1.2 - boost term frequency importance
    b=0.5    # Reduced from default 0.75 - reduce length penalty for long manuals
)
```

**Impact:**
- Repeated technical terms (model numbers, product names) rank higher
- Long documents (manuals) not over-penalized vs short documents

---

### 2. Analyzer Updates ✅

**Purpose:** Allow users to search without typing hyphens; better title matching.

| Field | Old Analyzer | New Analyzer | Reason |
|-------|-------------|--------------|--------|
| `title` | `en.microsoft` | **`standard.lucene`** | Tokenized, no stemming (page headers) |
| `productTradeNames` | `keyword` | **`standard.lucene`** | Partial matching without hyphens |
| `content` | `en.microsoft` | ✅ Keep | Good for general English |
| `partNumber`, `model` | `keyword` | ✅ Keep | Exact identifiers |

**Impact:**
- Query "pacing therapies" matches "Pacing Therapies" (case-insensitive)
- Query "pacing" matches "Pacing Therapies" (partial match)
- No need to type exact hyphens in product names

---

### 3. Embeddings Field - Retrievable ✅

**Purpose:** Allow embeddings to be retrieved for debugging/inspection.

```python
SearchField(
    name="embeddings",
    searchable=True,
    retrievable=True,  # Now retrievable
    hidden=False,
    vector_search_dimensions=1536,
    vector_search_profile_name="vector-profile-optimized"
)
```

**Note:** For production, you can set `retrievable=False` to save bandwidth.

---

### 4. Vector Search Tuning ✅

**Purpose:** Improve recall while maintaining reasonable performance.

#### HNSW Parameters

| Parameter | Old | New | Impact |
|-----------|-----|-----|--------|
| `m` | 8 | **16** | More graph connections = better recall |
| `ef_construction` | 600 | **400** | Faster indexing, still high quality |
| `ef_search` | 800 | **500** | Better query speed, good accuracy |

#### Scalar Quantization

| Parameter | Old | New | Impact |
|-----------|-----|-----|--------|
| `default_oversampling` | 10.0 | **20.0** | Better recall with int8 compression |

**Impact:**
- Better vector search recall (finds more relevant results)
- Faster indexing (ef_construction reduced)
- Faster queries (ef_search optimized)

---

### 5. Enhanced Validation ✅

Added comprehensive validation checks:

- ✓ BM25 similarity configured
- ✓ Title field analyzer is `standard.lucene`
- ✓ Embeddings field is retrievable
- ✓ Scoring profiles present
- ✓ Semantic configuration correct
- ✓ Vector compression enabled
- ✓ Vector algorithms configured

---

## Deployment Instructions

### Step 1: Dry Run
```bash
python ingestor/index.py --mode deploy --dry-run --verbose
```

### Step 2: Backup
```bash
python ingestor/index.py --mode backup
```

### Step 3: Deploy
```bash
python ingestor/index.py --mode deploy --force --verbose
```

**WARNING:** `--force` deletes the existing index and all data!

### Step 4: Validate
```bash
python ingestor/index.py --mode validate --verbose
```

---

## Expected Results

### Keyword Search (BM25)
- ✅ Works without hyphens: "pacing therapies" matches "Pacing-Therapies"
- ✅ Better ranking for long documents
- ✅ Repeated technical terms rank higher

### Vector Search
- ✅ Better recall (m=16)
- ✅ Faster queries (ef_search=500)
- ✅ Better int8 quantization accuracy (oversampling=20)

### Hybrid Search (Recommended)
- ✅ Combines BM25 + vector for best results
- ✅ Semantic reranking for top results
- ✅ Optimized for RAG applications

---

## Testing Queries

After deployment, test these scenarios:

```python
# 1. Simple keyword (should work without hyphens)
"pacing therapies"

# 2. Product name (should match partial)
"pacemaker"

# 3. Part number (should be exact)
"A2105"

# 4. Hybrid (keyword + vector)
# Use your RAG app with both text query and vector

# 5. Semantic ranking
# Enable semantic reranking in your queries
```

---

## Monitoring

After deployment, monitor:

1. **Query latency** - Should be similar or faster
2. **Relevance** - Test with real user queries
3. **Recall** - Check if expected documents are found
4. **Index size** - Should be similar (compression enabled)

---

## Rollback

If issues occur:

1. Check `backups/` folder for latest backup
2. Use Azure Portal to recreate index from backup JSON
3. Or use REST API to restore configuration

---

## Files Modified

- `ingestor/index.py` - Main index deployment script
- `ingestor/docs/06_INDEX_VALIDATION.md` - This guide

