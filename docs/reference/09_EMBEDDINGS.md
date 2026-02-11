# Embedding Modes: Client-Side vs Integrated Vectorization

The `ingestor` library supports two modes for generating embeddings for your document chunks:

## 🎯 Quick Comparison

| Feature | Client-Side Embeddings | Integrated Vectorization |
|---------|------------------------|--------------------------|
| **Configuration** | `AZURE_USE_INTEGRATED_VECTORIZATION=false` | `AZURE_USE_INTEGRATED_VECTORIZATION=true` |
| **Embedding Generation** | Your machine (before upload) | Azure Search (after upload) |
| **OpenAI API Calls** | You manage and pay | Azure Search manages |
| **Upload Speed** | Slower (must generate embeddings first) | Faster (upload immediately) |
| **Control** | Full control over process | Azure handles automatically |
| **Visibility** | See embedding generation progress | Background processing |
| **Best For** | Testing, debugging, custom logic | Production, scale, simplicity |

---

## Mode 1: Client-Side Embeddings (Default)

**Configuration:**
```bash
AZURE_USE_INTEGRATED_VECTORIZATION=false
```

**How it works:**
```
1. Extract content from PDF (Document Intelligence)
2. Chunk text into searchable units
3. Generate embeddings locally (Azure OpenAI API)
   └─> You make direct API calls to Azure OpenAI
   └─> Embeddings generated for each chunk
4. Upload documents WITH embeddings to Azure Search
```

**Pros:**
- ✅ **Full control** - You manage the entire embedding process
- ✅ **Visibility** - See exactly when and how embeddings are generated
- ✅ **Debugging** - Easier to troubleshoot embedding issues
- ✅ **Custom logic** - Can modify or validate embeddings before upload
- ✅ **Direct costs** - Clear visibility of OpenAI API usage

**Cons:**
- ⚠️ **Slower** - Must generate all embeddings before upload
- ⚠️ **More code** - You handle errors, retries, rate limits
- ⚠️ **Concurrency management** - You control parallelism
- ⚠️ **Rate limits** - Need to handle OpenAI rate limiting

**When to use:**
- Local development and testing
- When you need to inspect or modify embeddings
- When you want direct control over embedding generation
- When debugging embedding-related issues

---

## Mode 2: Integrated Vectorization

**Configuration:**
```bash
AZURE_USE_INTEGRATED_VECTORIZATION=true
```

**How it works:**
```
1. Extract content from PDF (Document Intelligence)
2. Chunk text into searchable units
3. Upload documents WITHOUT embeddings to Azure Search
4. Azure Search generates embeddings automatically in background
   └─> Azure Search calls Azure OpenAI for you
   └─> Embeddings generated asynchronously
   └─> Documents searchable immediately (embeddings added when ready)
```

**Pros:**
- ✅ **Faster ingestion** - Upload immediately without waiting for embeddings
- ✅ **Less code** - Azure handles embedding generation, retries, rate limits
- ✅ **Better for production** - Azure manages scale and reliability
- ✅ **Automatic retry** - Azure handles transient failures
- ✅ **No rate limit management** - Azure handles OpenAI throttling

**Cons:**
- ⚠️ **Less visibility** - Can't see embedding generation progress
- ⚠️ **Async processing** - Embeddings generated in background
- ⚠️ **Requires vectorizer config** - Index must have vectorizer configured
- ⚠️ **Bundled costs** - Embedding costs included in Search service

**When to use:**
- Production deployments
- Large-scale ingestion (many documents)
- When you want to minimize ingestion time
- When you prefer Azure to manage the embedding lifecycle

---

## 🔧 How to Switch Between Modes

### Option 1: Environment Variable

**Client-Side:**
```bash
AZURE_USE_INTEGRATED_VECTORIZATION=false
```

**Integrated:**
```bash
AZURE_USE_INTEGRATED_VECTORIZATION=true
```

### Option 2: Test Both Modes

You can create separate environment files:

**env.client-side:**
```bash
# Use client-side embeddings
AZURE_USE_INTEGRATED_VECTORIZATION=false
# ... other config ...
```

**env.integrated:**
```bash
# Use integrated vectorization
AZURE_USE_INTEGRATED_VECTORIZATION=true
# ... other config ...
```

Then switch between them:
```bash
# Test with client-side
cp env.client-side .env
python -m cli

# Test with integrated
cp env.integrated .env
python -m cli
```

---

## 📊 Performance Impact

### Example: 100-page PDF document

**Client-Side Embeddings:**
```
Extract: 10 seconds
Chunk: 2 seconds
Embed: 15 seconds ← Waiting for OpenAI API
Upload: 3 seconds
────────────────────
Total: 30 seconds
```

**Integrated Vectorization:**
```
Extract: 10 seconds
Chunk: 2 seconds
Upload: 3 seconds ← Documents indexed immediately
(Embeddings: generated in background)
────────────────────
Total: 15 seconds
```

**Speedup:** ~50% faster ingestion with integrated vectorization

---

## 🔍 Index Configuration Requirements

### For Client-Side Embeddings:
No special index configuration required. Your index just needs an `embeddings` field:

```json
{
  "name": "embeddings",
  "type": "Collection(Edm.Single)",
  "dimensions": 1536,
  "vectorSearchProfile": "vector-profile"
}
```

### For Integrated Vectorization:
Your index must have a **vectorizer** configured (already present in `my_index.json`):

```json
{
  "vectorSearch": {
    "vectorizers": [{
      "name": "vectorizer-name",
      "kind": "azureOpenAI",
      "azureOpenAIParameters": {
        "resourceUri": "https://your-openai.openai.azure.com",
        "deploymentId": "text-embedding-ada-002",
        "apiKey": "<your-key>"
      }
    }]
  }
}
```

✅ **Good news:** Your `my_index.json` already has this configured!

---

## ⚠️ Important Notes

### What Integrated Vectorization is NOT:
- ❌ **NOT using indexers** - We still upload documents directly
- ❌ **NOT using skillsets** - No cloud ingestion pipeline
- ❌ **NOT using blob monitoring** - No automatic document detection
- ✅ **JUST using the vectorizer** - Index-level embedding generation

### Both modes:
- ✅ Upload documents directly to Azure Search
- ✅ No indexers or skillsets
- ✅ Full control over what gets indexed
- ✅ Same chunking and extraction logic
- ✅ Same document metadata and structure

**The ONLY difference:** Where and when embeddings are generated.

---

## 🎯 Recommendation

### Use **Client-Side Embeddings** when:
- Developing and testing locally
- Need to inspect or debug embeddings
- Want full control over the embedding process
- Working with small document sets
- Need to validate embeddings before indexing

### Use **Integrated Vectorization** when:
- Deploying to production
- Processing large document collections
- Want faster ingestion times
- Prefer Azure to handle embedding lifecycle
- Don't need to inspect embeddings during ingestion

---

## 📝 Example Usage

### Test Both Modes with Same PDF

**1. Test with client-side embeddings:**
```bash
# env.test
AZURE_USE_INTEGRATED_VECTORIZATION=false

# Run
python -m cli
# Expected: "Generating embeddings client-side..."
```

**2. Test with integrated vectorization:**
```bash
# env.test
AZURE_USE_INTEGRATED_VECTORIZATION=true

# Run
python -m cli
# Expected: "Using integrated vectorization - skipping client-side embedding generation"
```

**3. Compare logs:**
```bash
# Client-side logs will show:
# "Generating embeddings for 50 chunks"
# "Generated 50 embeddings"

# Integrated logs will show:
# "Using integrated vectorization - skipping client-side embedding generation"
# "Indexing 50 chunks to Azure AI Search"
```

---

## 🔗 References

- [Azure AI Search Integrated Vectorization](https://learn.microsoft.com/en-us/azure/search/vector-search-integrated-vectorization)
- [Azure OpenAI Embeddings](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/embeddings)
- [Vector Search in Azure AI Search](https://learn.microsoft.com/en-us/azure/search/vector-search-overview)

---

## ❓ FAQ

**Q: Do I need to change my index schema to switch modes?**  
A: No! Your existing index works with both modes. For integrated vectorization, make sure the vectorizer is configured (it already is in `my_index.json`).

**Q: Can I switch modes for different documents?**  
A: Yes! The mode is determined at runtime from your environment configuration.

**Q: Which mode is faster?**  
A: Integrated vectorization is faster for ingestion (~50% speedup), but both modes produce the same search results.

**Q: Which mode costs less?**  
A: Costs are similar (same OpenAI API calls), but integrated vectorization may be slightly more efficient due to Azure's batching and retry logic.

**Q: Can I see the embeddings with integrated vectorization?**  
A: Not during ingestion, but you can retrieve them later from the search index using the Search API.

**Q: What if Azure Search fails to generate embeddings?**  
A: Azure Search handles retries automatically. If generation fails, the document is still searchable via text search, just not via vector search until embeddings are generated.

