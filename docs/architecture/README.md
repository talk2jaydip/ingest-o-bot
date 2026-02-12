# Ingestor Architecture Documentation

This directory contains comprehensive architecture diagrams and documentation for the Ingestor library.

## 📊 Available Diagrams

### High-Level Architecture
- **[High-Level Architecture](01_HIGH_LEVEL_ARCHITECTURE.md)** - System overview with all major components
- **[Component Interaction Diagram](02_COMPONENT_INTERACTIONS.md)** - Detailed component relationships
- **[Data Flow Diagram](03_DATA_FLOW.md)** - End-to-end data processing flow
- **[Pluggable Architecture](07_PLUGGABLE_ARCHITECTURE.md)** - Embeddings & vector store combinations

### Sequence Diagrams
- **[Document Ingestion Sequence](04_SEQUENCE_DOCUMENT_INGESTION.md)** - ADD workflow step-by-step
- **[Document Removal Sequence](05_SEQUENCE_DOCUMENT_REMOVAL.md)** - REMOVE workflow
- **[Index Management Sequence](06_SEQUENCE_INDEX_MANAGEMENT.md)** - Index setup and deletion

### DrawIO Diagrams
- **[DrawIO Architecture](07_DRAWIO_ARCHITECTURE.drawio)** - Editable architecture diagram (legacy)

## 📖 Quick Navigation

### For Developers
Start with the [High-Level Architecture](01_HIGH_LEVEL_ARCHITECTURE.md) to understand the system overview, then explore specific components in the [Component Interaction Diagram](02_COMPONENT_INTERACTIONS.md). To understand the pluggable architecture, see [Pluggable Architecture](07_PLUGGABLE_ARCHITECTURE.md).

### For Integration
Review the [Sequence Diagrams](04_SEQUENCE_DOCUMENT_INGESTION.md) to understand the workflow and integration points. For embedding and vector store options, see [Pluggable Architecture](07_PLUGGABLE_ARCHITECTURE.md).

### For Operations
Check the [Data Flow Diagram](03_DATA_FLOW.md) to understand how data moves through the system and where bottlenecks may occur.

### For Configuration
See [Pluggable Architecture](07_PLUGGABLE_ARCHITECTURE.md) for all supported combinations of embeddings providers and vector stores, including cloud, hybrid, and fully offline setups.

## 🔗 Related Documentation
- [Technical Reference](../reference/) - Detailed technical specifications
- [Configuration Guide](../guides/CONFIGURATION.md) - Configuration options
- [Performance Tuning](../guides/PERFORMANCE_TUNING.md) - Optimization strategies
- [Logging Guide](../LOGGING_GUIDE.md) - Centralized logging system and best practices

---

**Note**: All Mermaid diagrams can be viewed directly in GitHub and most modern markdown viewers.
