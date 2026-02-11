# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Pluggable Architecture**: Support for multiple vector stores (Azure AI Search, ChromaDB) and embedding providers (Azure OpenAI, Hugging Face, Cohere, OpenAI)
- **Dynamic Chunking**: Automatic chunk size adjustment based on embedding model token limits
- **Environment Parameter Validation**: Detects typos and misconfigurations in environment variables
- **Offline Mode**: Full offline support with ChromaDB + Hugging Face embeddings
- **Updated Default Model**: Changed to jina-embeddings-v2-base-en (768 dims, 8192 max tokens)

### Changed
- Upgraded default Hugging Face embedding model to multilingual-e5-large (1024 dims)
- Improved chunking logic to prevent truncation with buffer calculation
- Enhanced CLI with --env flag for easy configuration testing

### Fixed
- Chunking bug that could cause truncation with small-token models
- Pipeline integration with pluggable vector stores for delete operations
- ChromaDB local file URL support for offline mode

## [0.1.0] - 2026-02-06

### Added

#### Core Features
- Multi-format document processing (PDF, DOCX, PPTX, TXT, MD, HTML, JSON, CSV)
- Azure Document Intelligence integration for intelligent text, table, and figure extraction
- Layout-aware chunking with token-first approach (default: 500 tokens per chunk, dynamically adjusted based on model limits)
- Client-side embedding generation with Azure OpenAI
- Support for text-embedding-3-* models with custom dimensions
- Direct upload to Azure AI Search with BM25 + vector search
- GPT-4o figure captioning and visual media description
- Page-by-page PDF splitting for direct citations
- Document actions: add, remove, removeall

#### Index Management
- Separate index operations (deploy, update, delete) independent of ingestion
- Graceful error handling for missing resources
- BM25 similarity optimized for technical/medical documents
- Vector search with HNSW and scalar quantization
- Semantic search with enhanced content ranking
- Configurable retry logic (default: 3 attempts)

#### Interfaces
- Command-line interface (CLI) with comprehensive options
- Gradio web UI for visual configuration and monitoring
- Real-time processing logs and progress tracking
- Artifacts browser for viewing extracted content

#### Storage & Configuration
- Flexible input: local filesystem or Azure Blob Storage
- Azure Key Vault integration for secrets management
- Comprehensive environment variable configuration
- Support for multiple configuration scenarios

#### Documentation
- Complete documentation structure with guides and reference
- Quick start guide for 5-minute setup
- Configuration matrix for all input/output scenarios
- Technical reference for all components
- Troubleshooting guide

### Infrastructure
- Python package structure with pyproject.toml
- Proper dependency management
- .gitignore for common Python and Azure artifacts
- Async throughout for optimal performance
- Comprehensive logging infrastructure

## [Unreleased]

### Planned
- Unit and integration tests
- Performance benchmarking tools
- Docker containerization
- CI/CD pipeline
- Additional file format support
- Batch processing optimizations
- Enhanced error recovery mechanisms

---

## Release Notes

### Version 0.1.0

This is the initial release of Ingestor, providing a complete document ingestion pipeline for Azure AI Search with pluggable architecture. The pipeline processes documents through Azure Document Intelligence, generates embeddings with multiple providers (Azure OpenAI, Hugging Face, Cohere, OpenAI), and uploads to multiple vector stores (Azure AI Search, ChromaDB) without requiring indexers or skillsets.

**Key Highlights:**
- Fully async pipeline for optimal performance
- Layout-aware chunking respecting document structure
- Support for custom embedding dimensions
- Comprehensive web UI for monitoring and configuration
- Production-ready with Key Vault integration

**Requirements:**
- Python 3.10+
- Azure Document Intelligence
- Azure AI Search
- Azure OpenAI

**Known Limitations:**
- Large files (>50MB) may require increased memory
- Concurrent processing limited by Azure service quotas
- Web UI currently single-user only

---

For upgrade instructions and migration guides, see the [documentation](docs/INDEX.md).
