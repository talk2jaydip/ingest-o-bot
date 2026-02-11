# Architecture & Implementation

## Overview

ingestor is a flexible document ingestion pipeline with pluggable architecture that:
1. Reads documents from local filesystem or Azure Blob Storage
2. Extracts content using Azure Document Intelligence or MarkItDown
3. Chunks text with layout awareness and dynamic token adjustment
4. Generates embeddings using pluggable providers (Azure OpenAI, Hugging Face, Cohere, OpenAI)
5. Uploads to pluggable vector stores (Azure AI Search, ChromaDB) - no indexers/skillsets required

---

## Pipeline Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Input Source  │────▶│   DI Extractor   │────▶│     Chunker     │
│ (Local / Blob)  │     │(Doc Intelligence)│     │  (Dynamic +     │
└─────────────────┘     │   / MarkItDown   │     │  Layout-Aware)  │
                        └──────────────────┘     └─────────────────┘
                                                          │
                        ┌──────────────────┐              ▼
                        │  Vector Store    │◀────┌─────────────────┐
                        │ (Azure Search /  │     │   Embeddings    │
                        │    ChromaDB)     │     │  (Pluggable)    │
                        └──────────────────┘     └─────────────────┘
```

---

## Module Responsibilities

### Core Pipeline

| Module | Responsibility |
|--------|----------------|
| `pipeline.py` | Orchestrates the entire flow |
| `config.py` | Loads and validates configuration |
| `cli.py` | Command-line interface |

### Input/Output

| Module | Responsibility |
|--------|----------------|
| `input_source.py` | Lists and reads input files (local/blob) |
| `artifact_storage.py` | Stores processed artifacts (local/blob) |
| `search_uploader.py` | Uploads to Azure AI Search |

### Processing

| Module | Responsibility |
|--------|----------------|
| `di_extractor.py` | Extracts content via Document Intelligence |
| `office_extractor.py` | Extracts content via MarkItDown |
| `chunker.py` | Splits text into chunks with dynamic adjustment |
| `embeddings_provider.py` | Abstract interface for embeddings providers |
| `embeddings_providers/` | Implementations: Azure OpenAI, Hugging Face, Cohere, OpenAI |
| `vector_store.py` | Abstract interface for vector stores |
| `vector_stores/` | Implementations: Azure AI Search, ChromaDB |
| `table_renderer.py` | Renders tables as text |
| `media_describer.py` | Describes images with GPT-4o |
| `page_splitter.py` | Splits PDFs into per-page files |

### Data Models

| Module | Responsibility |
|--------|----------------|
| `models.py` | Data classes for chunks, pages, metadata |
| `logging_utils.py` | Structured logging |

---

## Data Flow

### 1. Input Reading

```python
async for filename, content, source_url in input_source.list_files():
    # Process each file
```

Supports: PDF, TXT, MD, HTML, JSON, CSV

### 2. Extraction (PDF)

```python
pages = await di_extractor.extract_document(pdf_bytes, filename)
# Returns: list[ExtractedPage] with text, tables, figures
```

### 3. Chunking

```python
chunks = chunker.chunk_pages(pages)
# Returns: list[TextChunk] with text, page info, embedded tables/figures
```

### 4. Embedding

```python
embeddings = await embeddings_gen.generate_embeddings_batch(texts)
# Returns: list[list[float]] - embedding vectors
```

### 5. Indexing

```python
count = await search_uploader.upload_documents(chunk_docs)
# Uses batch upload with merge_or_upload
```

---

## Key Design Decisions

### No Indexers/Skillsets

Unlike the full prepdocslib, this library:
- Uploads documents **directly** to an existing index
- Does not create or manage Azure Search indexers
- Does not use built-in or custom skillsets
- Runs entirely locally or as a simple script

### Dual Environment Variable Support

Supports both naming conventions for backward compatibility:
```python
# Example: Both are supported
AZURE_SEARCH_SERVICE=your-service
# or
AZURE_SEARCH_ENDPOINT=https://your-service.search.windows.net
```

Generic parameter names (without AZURE_ prefix) are also supported for chunking and some other settings.

### Async Throughout

All I/O operations are async:
```python
async with BlobServiceClient(...) as client:
    await client.upload_blob(...)
```

### Configurable Modes

Key behaviors are configurable:
- Input: local vs blob
- Artifacts: local vs blob
- Embeddings: client-side vs integrated vectorization
- Actions: add, remove, removeall

---

## Search Document Schema

Matches `my_index.json`:

```json
{
  "id": "docname_page1_chunk1",
  "content": "The actual text...",
  "embeddings": [0.123, ...],
  "filename": "document.pdf",
  "sourcefile": "document",
  "sourcepage": "document/pages/page-0001.pdf#page=1",
  "pageNumber": 1,
  "storageUrl": "https://...page-0001.pdf",
  "url": "https://...document.pdf",
  "category": null,
  "title": "Page Header"
}
```

---

## Error Handling

### Retry Logic

All external API calls use tenacity:

```python
async for attempt in AsyncRetrying(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_random_exponential(min=15, max=60),
    stop=stop_after_attempt(3)
):
    with attempt:
        result = await api_call()
```

### Graceful Degradation

- If figure extraction fails, continues without figures
- If media description fails, chunk still indexed
- Individual file failures don't stop the pipeline

---

## Concurrency Control

Uses semaphores to limit concurrent API calls:

```python
semaphore = asyncio.Semaphore(max_concurrency)
async with semaphore:
    await api_call()
```

Configurable via:
- `AZURE_DI_MAX_CONCURRENCY` (default: 3)
- `AZURE_OPENAI_MAX_CONCURRENCY` (default: 5)

