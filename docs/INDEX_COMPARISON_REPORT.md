# Index Schema Comparison Report

**Date:** 2026-02-17
**Original Index:** `alfred-experiment-index`
**Current Index:** `alfred-experiment-index-2`

---

## Summary

✅ **Fields:** MATCH (24 fields each)
✅ **Scoring Profiles:** MATCH (2 profiles: productBoostingProfile, contentRAGProfile)
⚠️ **Suggester Name:** DIFFERENT
⚠️ **Semantic Config Name:** DIFFERENT
✅ **Vector Search:** MATCH (configuration equivalent)

---

## Detailed Comparison

### Index Names
- **Original:** `alfred-experiment-index`
- **Current:** `alfred-experiment-index-2`

### Fields (24 total - ALL MATCH)

Both indexes have the same 24 fields:
1. `id` (Edm.String) - Key field
2. `content` (Edm.String) - Searchable text
3. `embeddings` (Collection(Edm.Single)) - 1536 dimensions
4. `filename` (Edm.String) - Keyword analyzer
5. `url` (Edm.String)
6. `country` (Edm.String) - Keyword analyzer
7. `language` (Edm.String) - Keyword analyzer
8. `product_family` (Edm.String) - en.microsoft analyzer
9. `productTradeNames` (Edm.String) - standard.lucene analyzer
10. `prod_from_url` (Edm.String) - Keyword analyzer
11. `title` (Edm.String) - standard.lucene analyzer
12. `literatureType` (Edm.String) - Keyword analyzer
13. `partNumber` (Edm.String) - Keyword analyzer
14. `applicableTo` (Edm.String) - en.microsoft analyzer
15. `model` (Edm.String) - Keyword analyzer
16. `publishedDate` (Edm.DateTimeOffset)
17. `pageNumber` (Edm.Int32)
18. `category` (Edm.String) - en.microsoft analyzer
19. `sourcepage` (Edm.String) - Keyword analyzer
20. `sourcefile` (Edm.String) - Keyword analyzer
21. `storageUrl` (Edm.String)
22. `has_figures` (Edm.Boolean)
23. `figure_urls` (Collection(Edm.String))
24. `has_tables` (Edm.Boolean)

**Status:** ✅ All field types, analyzers, and attributes match

### Scoring Profiles (MATCH)

Both indexes have the same 2 scoring profiles:

#### 1. productBoostingProfile
**Weights:**
- title: 3
- productTradeNames: 2.5
- product_family: 2
- partNumber: 2.5
- model: 2
- filename: 1.5
- applicableTo: 1.8
- content: 1

**Freshness Function:**
- Field: publishedDate
- Boost: 2
- Duration: P365D (1 year)

#### 2. contentRAGProfile
**Weights:**
- content: 3
- title: 2.5
- applicableTo: 2
- productTradeNames: 1.5
- product_family: 1.5
- category: 1.2
- filename: 1

**Freshness Function:**
- Field: publishedDate
- Boost: 1.5
- Duration: P365D (1 year)

**Status:** ✅ Both profiles match exactly

### Suggesters (NAME DIFFERENT, FIELDS MATCH)

| Property | Original | Current |
|----------|----------|---------|
| Name | `product-suggester` | `default-suggester` |
| Source Fields | `['title', 'product_family']` | `['title', 'product_family']` |
| Search Mode | analyzingInfixMatching | analyzingInfixMatching |

**Status:** ⚠️ Name differs, but functionality is the same

### Semantic Search Configuration (NAME DIFFERENT, FIELDS MATCH)

| Property | Original | Current |
|----------|----------|---------|
| Name | `alfred-semantic-config` | `default-semantic-config` |
| Title Field | title | title |
| Content Fields | content, applicableTo | content, applicableTo |
| Keywords Fields | productTradeNames, product_family, partNumber, model, category | productTradeNames, product_family, partNumber, model, category |

**Status:** ⚠️ Name differs, but fields and configuration match

### Vector Search Configuration (MATCH)

#### Algorithm (HNSW)
- **Name:** vector-config-optimized
- **Metric:** cosine
- **m:** 16
- **efConstruction:** 400
- **efSearch:** 500

**Status:** ✅ Match

#### Profile
- **Name:** vector-profile-optimized
- **Algorithm:** vector-config-optimized
- **Vectorizer:** vectorizer-{index-name}
- **Compression:** scalar-quantization (int8)

**Status:** ✅ Match

#### Vectorizer (Azure OpenAI)
- **Deployment:** text-embedding-ada-002
- **Model:** text-embedding-ada-002
- **Dimensions:** 1536

**Status:** ✅ Match

### BM25 Similarity (MATCH)

| Parameter | Original | Current |
|-----------|----------|---------|
| k1 | 1.5 | 1.5 |
| b | 0.5 | 0.5 |

**Status:** ✅ Match

---

## Differences Explained

### 1. Suggester Name Difference

**Original:** `product-suggester`
**Current:** `default-suggester`

**Impact:** ⚠️ Minor - Only affects the suggester name in API calls. The actual functionality (source fields) is identical.

**How to fix:** Can be configured via environment variable:
```bash
AZURE_SEARCH_SUGGESTER_NAME=product-suggester
```

### 2. Semantic Config Name Difference

**Original:** `alfred-semantic-config`
**Current:** `default-semantic-config`

**Impact:** ⚠️ Minor - Only affects the configuration name when calling semantic search. The actual semantic fields are identical.

**How to fix:** Can be configured via environment variable:
```bash
AZURE_SEARCH_SEMANTIC_CONFIG_NAME=alfred-semantic-config
```

### 3. Retrievable Field Attribute

**Technical Note:** All fields show `retrievable: True` in original vs `None` in current export. This is a serialization difference only - `None` means the field uses the default value (true). Functionally, they are identical.

---

## Conclusion

### ✅ What Matches (Critical)
- All 24 fields with correct types and analyzers
- Both scoring profiles (productBoostingProfile, contentRAGProfile)
- Vector search configuration (HNSW algorithm, compression)
- Semantic search field mappings
- BM25 similarity parameters

### ⚠️ What Differs (Non-Critical)
- Suggester name: `product-suggester` → `default-suggester`
- Semantic config name: `alfred-semantic-config` → `default-semantic-config`

### Recommendation

**Status: ✅ FUNCTIONALLY EQUIVALENT**

The current index schema matches the original in all critical aspects. The naming differences (suggester and semantic config) are cosmetic and can be configured if needed.

To match the original names exactly, add to your `.env`:
```bash
# Index Schema Customization (Optional)
AZURE_SEARCH_SEMANTIC_CONFIG_NAME=alfred-semantic-config
AZURE_SEARCH_SUGGESTER_NAME=product-suggester
AZURE_SEARCH_SCORING_PROFILES=productBoostingProfile,contentRAGProfile
```

**Note:** These are already configured in lines 111-113 of your `.env` file but commented out. You can uncomment them to use the original names.

---

## Files Generated

- `current_index_schema.json` - Full export of current index
- `oringal_index.json` - Original index schema (already existed)
- `export_and_compare.py` - Comparison script
- `INDEX_COMPARISON_REPORT.md` - This report
