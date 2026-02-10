"""Ingestor - Document ingestion pipeline for Azure AI Search.

A Python library for ingesting multi-format documents into Azure AI Search
with intelligent chunking, embeddings, and layout-aware processing.

Basic Usage:
    >>> from ingestor import Pipeline, PipelineConfig
    >>>
    >>> # Load config from .env
    >>> config = PipelineConfig.from_env()
    >>>
    >>> # Run pipeline
    >>> pipeline = Pipeline(config)
    >>> status = await pipeline.run()

Convenience Usage:
    >>> from ingestor import run_pipeline
    >>>
    >>> # One-liner execution
    >>> status = await run_pipeline(input_glob="docs/*.pdf")

See documentation at: https://github.com/yourusername/ingestor
"""

from .__version__ import __version__, __version_info__

# Core classes
from .pipeline import Pipeline
from .config import (
    PipelineConfig,
    SearchConfig,
    DocumentIntelligenceConfig,
    OfficeExtractorConfig,
    AzureOpenAIConfig,
    InputConfig,
    ArtifactsConfig,
    ChunkingConfig,
    PerformanceConfig,
    AzureCredentials,
    KeyVaultConfig,
    ContentUnderstandingConfig,
    InputMode,
    ArtifactsMode,
    DocumentAction,
    TableRenderMode,
    MediaDescriberMode,
    OfficeExtractorMode,
    load_config,
)

# Configuration builder
from .config_builder import ConfigBuilder

# Data models
from .models import (
    DocumentMetadata,
    PageMetadata,
    ChunkMetadata,
    ChunkDocument,
    IngestionResult,
    PipelineStatus,
    TableReference,
    FigureReference,
)

# Convenience functions
from .helpers import (
    create_config,
    run_pipeline,
    sync_run_pipeline,
)

# Index management
from .index import IndexDeploymentManager

__all__ = [
    # Version
    "__version__",
    "__version_info__",

    # Core
    "Pipeline",
    "PipelineConfig",

    # Configuration classes
    "SearchConfig",
    "DocumentIntelligenceConfig",
    "OfficeExtractorConfig",
    "AzureOpenAIConfig",
    "InputConfig",
    "ArtifactsConfig",
    "ChunkingConfig",
    "PerformanceConfig",
    "AzureCredentials",
    "KeyVaultConfig",
    "ContentUnderstandingConfig",

    # Configuration builder
    "ConfigBuilder",

    # Configuration enums
    "InputMode",
    "ArtifactsMode",
    "DocumentAction",
    "TableRenderMode",
    "MediaDescriberMode",
    "OfficeExtractorMode",

    # Models
    "DocumentMetadata",
    "PageMetadata",
    "ChunkMetadata",
    "ChunkDocument",
    "IngestionResult",
    "PipelineStatus",
    "TableReference",
    "FigureReference",

    # Helper functions
    "create_config",
    "run_pipeline",
    "sync_run_pipeline",
    "load_config",

    # Index management
    "IndexDeploymentManager",
]
