# Pluggable Architecture

## Overview

Ingest-o-bot implements a fully pluggable architecture that allows you to mix and match different embeddings providers and vector stores. This enables scenarios from fully cloud-based to completely offline processing, with flexible cost optimization.

## Architecture Layers

```mermaid
graph TB
    subgraph "Application Layer"
        APP[Pipeline / CLI / UI]
    end

    subgraph "Abstraction Layer"
        EMBABS[EmbeddingsProvider ABC<br/>---<br/>+ generate_embedding<br/>+ generate_embeddings_batch<br/>+ get_dimensions<br/>+ get_model_name<br/>+ get_max_seq_length]

        VSABS[VectorStore ABC<br/>---<br/>+ upload_documents<br/>+ delete_documents_by_filename<br/>+ delete_all_documents<br/>+ search<br/>+ get_dimensions]
    end

    subgraph "Embeddings Implementations"
        AZOAI[Azure OpenAI<br/>---<br/>1536/3072 dims<br/>8191 tokens<br/>Cloud]

        HF[Hugging Face<br/>---<br/>384-1024 dims<br/>256-8192 tokens<br/>Local CPU/GPU]

        COHERE[Cohere<br/>---<br/>1024 dims<br/>512 tokens<br/>Cloud API<br/>100+ languages]

        OAI[OpenAI<br/>---<br/>1536/3072 dims<br/>8191 tokens<br/>Cloud]
    end

    subgraph "Vector Store Implementations"
        AZSEARCH[Azure AI Search<br/>---<br/>Cloud index<br/>Integrated vectorization<br/>Enterprise scale]

        CHROMA[ChromaDB<br/>---<br/>Persistent: Local disk<br/>In-memory: Testing<br/>Client: Remote server]
    end

    subgraph "External Services & Models"
        AZOAIAPI[Azure OpenAI API]
        COHEREAPI[Cohere API]
        OAIAPI[OpenAI API]
        HFMODELS[Hugging Face Models<br/>Local cache]
        AZSRV[Azure Search Service]
        CHROMASRV[ChromaDB Server<br/>Optional]
    end

    APP --> EMBABS
    APP --> VSABS

    EMBABS -.implements.-> AZOAI
    EMBABS -.implements.-> HF
    EMBABS -.implements.-> COHERE
    EMBABS -.implements.-> OAI

    VSABS -.implements.-> AZSEARCH
    VSABS -.implements.-> CHROMA

    AZOAI <-->|API calls| AZOAIAPI
    HF <-->|load models| HFMODELS
    COHERE <-->|API calls| COHEREAPI
    OAI <-->|API calls| OAIAPI

    AZSEARCH <-->|index ops| AZSRV
    CHROMA <-->|optional| CHROMASRV

    classDef app fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef abs fill:#fff3e0,stroke:#e65100,stroke-width:3px
    classDef impl fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef ext fill:#e3f2fd,stroke:#0d47a1,stroke-width:2px

    class APP app
    class EMBABS,VSABS abs
    class AZOAI,HF,COHERE,OAI,AZSEARCH,CHROMA impl
    class AZOAIAPI,COHEREAPI,OAIAPI,HFMODELS,AZSRV,CHROMASRV ext
```

## Supported Combinations

### All 8 Combinations (4 Embeddings × 2 Vector Stores)

```mermaid
graph LR
    subgraph "Embeddings Providers"
        E1[Azure OpenAI<br/>Cloud]
        E2[Hugging Face<br/>Local]
        E3[Cohere<br/>Cloud]
        E4[OpenAI<br/>Cloud]
    end

    subgraph "Vector Stores"
        V1[Azure AI Search<br/>Cloud]
        V2[ChromaDB<br/>Local/Remote]
    end

    E1 -.->|Combo 1| V1
    E1 -.->|Combo 5| V2
    E2 -.->|Combo 2| V1
    E2 -.->|Combo 6| V2
    E3 -.->|Combo 3| V1
    E3 -.->|Combo 7| V2
    E4 -.->|Combo 4| V1
    E4 -.->|Combo 8| V2

    classDef cloud fill:#e3f2fd,stroke:#0d47a1,stroke-width:2px
    classDef local fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef hybrid fill:#fff3e0,stroke:#e65100,stroke-width:2px

    class E1,E3,E4,V1 cloud
    class E2,V2 local
```

### Combination Details

| # | Embeddings | Vector Store | Cloud | Offline | Use Case |
|---|------------|--------------|-------|---------|----------|
| 1 | Azure OpenAI | Azure Search | Yes | No | **Production Cloud** (Default)<br/>Enterprise-grade, fully managed |
| 2 | Hugging Face | Azure Search | Partial | No | **Hybrid Cost Savings**<br/>Free embeddings, cloud storage |
| 3 | Cohere | Azure Search | Yes | No | **Multilingual Cloud**<br/>100+ languages, cloud storage |
| 4 | OpenAI | Azure Search | Yes | No | **Native OpenAI**<br/>OpenAI embeddings, Azure storage |
| 5 | Azure OpenAI | ChromaDB | Partial | No | **Local Storage**<br/>Cloud embeddings, local database |
| 6 | Hugging Face | ChromaDB | No | Yes | **Fully Offline**<br/>Zero cloud dependencies |
| 7 | Cohere | ChromaDB | Partial | No | **Multilingual Local**<br/>Cloud embeddings, local storage |
| 8 | OpenAI | ChromaDB | Partial | No | **OpenAI + Local**<br/>OpenAI embeddings, local storage |

## Component Specifications

### Embeddings Providers

#### Azure OpenAI Provider
```yaml
Class: AzureOpenAIProvider
Module: embeddings_providers.azure_openai_provider
Models:
  - text-embedding-ada-002 (1536 dims)
  - text-embedding-3-small (1536 dims)
  - text-embedding-3-large (3072 dims)
Max Tokens: 8191
Execution: Cloud API
Cost: Pay per 1K tokens
Dependencies:
  - openai (Azure)
  - azure-identity
Environment Variables:
  - AZURE_OPENAI_ENDPOINT
  - AZURE_OPENAI_EMBEDDING_DEPLOYMENT
  - AZURE_OPENAI_API_KEY (or managed identity)
```

#### Hugging Face Provider
```yaml
Class: HuggingFaceProvider
Module: embeddings_providers.huggingface_provider
Models:
  - all-MiniLM-L6-v2 (384 dims, 256 tokens)
  - jina-embeddings-v2-base-en (768 dims, 8192 tokens) [Default]
  - multilingual-e5-large (1024 dims, 512 tokens)
  - BGE-large (1024 dims, 512 tokens)
Execution: Local (CPU/GPU/MPS)
Cost: Free (compute only)
Dependencies:
  - sentence-transformers
  - torch
Model Cache: ~/.cache/huggingface/
Environment Variables:
  - HUGGINGFACE_MODEL_NAME (default: jina-embeddings-v2-base-en)
  - HUGGINGFACE_DEVICE (cpu/cuda/mps)
```

#### Cohere Provider
```yaml
Class: CohereProvider
Module: embeddings_providers.cohere_provider
Models:
  - embed-multilingual-v3.0 (1024 dims)
Max Tokens: 512
Languages: 100+
Execution: Cloud API
Cost: Pay per 1M tokens
Batch Size: 96 texts per request
Dependencies:
  - cohere
Environment Variables:
  - COHERE_API_KEY
  - COHERE_MODEL (default: embed-multilingual-v3.0)
```

#### OpenAI Provider
```yaml
Class: OpenAIProvider
Module: embeddings_providers.openai_provider
Models:
  - text-embedding-3-small (1536 dims)
  - text-embedding-3-large (3072 dims)
  - text-embedding-ada-002 (1536 dims)
Max Tokens: 8191
Execution: Cloud API (non-Azure)
Cost: Pay per 1K tokens
Dependencies:
  - openai
Environment Variables:
  - OPENAI_API_KEY
  - OPENAI_EMBEDDING_MODEL
```

### Vector Stores

#### Azure AI Search Vector Store
```yaml
Class: AzureSearchVectorStore
Module: vector_stores.azure_search_vector_store
Features:
  - Integrated vectorization (server-side)
  - Client-side vectorization
  - Semantic ranking
  - Hybrid search (vector + keyword)
  - Scoring profiles
Scale: Enterprise (billions of vectors)
Batch Size: 1000 documents
Dependencies:
  - azure-search-documents
  - azure-identity
Environment Variables:
  - AZURE_SEARCH_SERVICE
  - AZURE_SEARCH_INDEX
  - AZURE_SEARCH_API_KEY (or managed identity)
  - INTEGRATED_VECTORIZATION (true/false)
```

#### ChromaDB Vector Store
```yaml
Class: ChromaDBVectorStore
Module: vector_stores.chromadb_vector_store
Modes:
  - Persistent: Local disk storage
  - In-memory: Ephemeral (testing)
  - Client/Server: Remote ChromaDB
Features:
  - Metadata filtering
  - Similarity search
  - HNSW indexing
  - Cosine/L2/IP distance metrics
Scale: Small to medium (millions of vectors)
Batch Size: Configurable (default: 100)
Dependencies:
  - chromadb
Environment Variables:
  - CHROMADB_PERSIST_DIR (persistent mode)
  - CHROMADB_IN_MEMORY=true (in-memory mode)
  - CHROMADB_HOST/PORT/AUTH (client mode)
```

## Configuration Examples

### 1. Production Cloud (Default)
```bash
# Azure OpenAI + Azure Search
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_SEARCH_SERVICE=your-search-service
AZURE_SEARCH_INDEX=documents
```

### 2. Fully Offline
```bash
# Hugging Face + ChromaDB
VECTOR_STORE_MODE=chromadb
CHROMADB_PERSIST_DIR=./chroma_db
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=jinaai/jina-embeddings-v2-base-en
```

### 3. Cost Optimized
```bash
# Hugging Face (free) + Azure Search
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=jinaai/jina-embeddings-v2-base-en
AZURE_SEARCH_SERVICE=your-search-service
AZURE_SEARCH_INDEX=documents
```

### 4. Multilingual
```bash
# Cohere (100+ languages) + Azure Search
EMBEDDINGS_MODE=cohere
COHERE_API_KEY=your-cohere-key
AZURE_SEARCH_SERVICE=your-search-service
AZURE_SEARCH_INDEX=documents
```

### 5. Development/Testing
```bash
# Hugging Face + ChromaDB (in-memory)
VECTOR_STORE_MODE=chromadb
CHROMADB_IN_MEMORY=true
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```

## Factory Pattern

### Auto-Detection Flow

```mermaid
graph TB
    START[Pipeline Initialization]

    CHECKEMB{EMBEDDINGS_MODE<br/>set?}
    CHECKAZOAI{Azure OpenAI<br/>config present?}
    CHECKHF{Hugging Face<br/>config present?}
    CHECKCOHERE{Cohere<br/>config present?}
    CHECKOAI{OpenAI<br/>config present?}

    EMBFACTORY[create_embeddings_provider]
    AZOAIEMB[Azure OpenAI Provider]
    HFEMB[Hugging Face Provider]
    COHEREEMB[Cohere Provider]
    OAIEMB[OpenAI Provider]

    CHECKVS{VECTOR_STORE_MODE<br/>set?}
    CHECKAZSEARCH{Azure Search<br/>config present?}
    CHECKCHROMA{ChromaDB<br/>config present?}

    VSFACTORY[create_vector_store]
    AZSEARCHVS[Azure Search Vector Store]
    CHROMAVS[ChromaDB Vector Store]

    ERROR[Error: No config found]
    PIPELINE[Pipeline Ready]

    START --> CHECKEMB
    CHECKEMB -->|Yes| EMBFACTORY
    CHECKEMB -->|No| CHECKAZOAI
    CHECKAZOAI -->|Yes| AZOAIEMB
    CHECKAZOAI -->|No| CHECKHF
    CHECKHF -->|Yes| HFEMB
    CHECKHF -->|No| CHECKCOHERE
    CHECKCOHERE -->|Yes| COHEREEMB
    CHECKCOHERE -->|No| CHECKOAI
    CHECKOAI -->|Yes| OAIEMB
    CHECKOAI -->|No| ERROR

    EMBFACTORY --> AZOAIEMB
    EMBFACTORY --> HFEMB
    EMBFACTORY --> COHEREEMB
    EMBFACTORY --> OAIEMB

    AZOAIEMB --> CHECKVS
    HFEMB --> CHECKVS
    COHEREEMB --> CHECKVS
    OAIEMB --> CHECKVS

    CHECKVS -->|Yes| VSFACTORY
    CHECKVS -->|No| CHECKAZSEARCH
    CHECKAZSEARCH -->|Yes| AZSEARCHVS
    CHECKAZSEARCH -->|No| CHECKCHROMA
    CHECKCHROMA -->|Yes| CHROMAVS
    CHECKCHROMA -->|No| ERROR

    VSFACTORY --> AZSEARCHVS
    VSFACTORY --> CHROMAVS

    AZSEARCHVS --> PIPELINE
    CHROMAVS --> PIPELINE

    classDef config fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef provider fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef error fill:#ffebee,stroke:#c62828,stroke-width:2px
    classDef success fill:#e1f5ff,stroke:#01579b,stroke-width:2px

    class CHECKEMB,CHECKVS,CHECKAZOAI,CHECKHF,CHECKCOHERE,CHECKOAI,CHECKAZSEARCH,CHECKCHROMA config
    class EMBFACTORY,VSFACTORY,AZOAIEMB,HFEMB,COHEREEMB,OAIEMB,AZSEARCHVS,CHROMAVS provider
    class ERROR error
    class PIPELINE success
```

## Extensibility

### Adding New Embeddings Provider

```python
# 1. Implement the ABC
from ingestor.embeddings_provider import EmbeddingsProvider

class MyEmbeddingsProvider(EmbeddingsProvider):
    async def generate_embedding(self, text: str) -> list[float]:
        # Your implementation
        pass

    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        # Your implementation
        pass

    def get_dimensions(self) -> int:
        return 768  # Your model dimensions

    def get_model_name(self) -> str:
        return "my-model-name"

    def get_max_seq_length(self) -> int:
        return 512  # Your model max tokens

# 2. Add to factory function in embeddings_provider.py
def create_embeddings_provider(config: PipelineConfig) -> EmbeddingsProvider:
    # Add your detection logic
    if config.my_provider_config:
        return MyEmbeddingsProvider(config)
    # ... existing logic
```

### Adding New Vector Store

```python
# 1. Implement the ABC
from ingestor.vector_store import VectorStore

class MyVectorStore(VectorStore):
    async def upload_documents(self, chunk_docs, include_embeddings=True) -> int:
        # Your implementation
        pass

    async def delete_documents_by_filename(self, filename: str) -> int:
        # Your implementation
        pass

    async def delete_all_documents(self) -> int:
        # Your implementation
        pass

    async def search(self, query: str, top_k: int = 10, filters=None) -> list[dict]:
        # Your implementation
        pass

    def get_dimensions(self) -> int:
        return self.dimensions

# 2. Add to factory function in vector_store.py
def create_vector_store(config: PipelineConfig, embeddings_provider) -> VectorStore:
    # Add your detection logic
    if config.my_store_config:
        return MyVectorStore(config)
    # ... existing logic
```

## Benefits

### Flexibility
- Choose the best provider for your use case
- Switch providers without code changes
- Test locally before deploying to cloud

### Cost Optimization
- Use free local models for development
- Mix free embeddings with cloud storage
- Scale embeddings independently from storage

### Data Privacy
- Process sensitive documents fully offline
- Keep embeddings on-premises
- Control data residency

### Multilingual Support
- Use Cohere for 100+ languages
- Switch models based on content language
- Optimize for specific language families

### Development Speed
- Rapid iteration with local setup
- No cloud dependencies for testing
- Fast model switching

## Performance Considerations

### Embeddings Performance

| Provider | Latency | Throughput | Cost |
|----------|---------|------------|------|
| Azure OpenAI | 50-200ms | High (concurrent) | $0.0001/1K tokens |
| Hugging Face | 10-100ms | Medium (GPU) / Low (CPU) | Free (compute) |
| Cohere | 50-150ms | Very High (batch 96) | $0.0001/1K tokens |
| OpenAI | 50-200ms | High (concurrent) | $0.0001/1K tokens |

### Vector Store Performance

| Store | Write Speed | Search Speed | Scale | Cost |
|-------|-------------|--------------|-------|------|
| Azure Search | Very High | Very High | Billions | $$$ per month |
| ChromaDB | High | High | Millions | Free (storage) |

## Related Documentation

- [Vector Stores Guide](../guides/VECTOR_STORES_GUIDE.md) - Detailed vector store comparison
- [Embeddings Providers Guide](../guides/EMBEDDINGS_PROVIDERS_GUIDE.md) - Detailed embeddings comparison
- [Configuration Examples](../guides/CONFIGURATION_EXAMPLES.md) - All configuration scenarios
- [High-Level Architecture](01_HIGH_LEVEL_ARCHITECTURE.md) - System overview
- [Component Interactions](02_COMPONENT_INTERACTIONS.md) - Component relationships
- [Data Flow](03_DATA_FLOW.md) - End-to-end processing

## Examples

See the [examples directory](../../examples/) for working code:
- `offline_chromadb_huggingface.py` - Fully offline setup
- `azure_search_cohere.py` - Cloud hybrid setup
- `notebooks/09_pluggable_architecture.ipynb` - Interactive tutorial
