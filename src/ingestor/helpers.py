"""Convenience functions for common operations."""

import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

from .pipeline import Pipeline
from .config import PipelineConfig, InputMode, ArtifactsMode
from .models import PipelineStatus
from .config_builder import ConfigBuilder


def create_config(
    input_glob: Optional[str] = None,
    azure_search_index: Optional[str] = None,
    env_path: Optional[str] = None,
    use_env: bool = True,
    **kwargs
) -> PipelineConfig:
    """Create PipelineConfig with sensible defaults.

    This helper provides three ways to create config:
    1. Load from environment variables (.env file)
    2. Build programmatically using ConfigBuilder
    3. Hybrid approach: load from env then override specific values

    Args:
        input_glob: Glob pattern for local files (e.g., "docs/*.pdf")
        azure_search_index: Azure AI Search index name
        env_path: Path to .env file (optional, default searches for .env)
        use_env: If True, load from environment first (default: True)
        **kwargs: Additional config parameters. Supports nested updates:
            - Top-level attributes: document_action="remove"
            - Nested attributes: chunking_max_tokens=1000
            - Nested objects: search=SearchConfig(...)

    Returns:
        Configured PipelineConfig instance

    Examples:
        # Load from .env and override specific values
        >>> config = create_config(
        ...     input_glob="documents/*.pdf",
        ...     azure_search_index="my-index",
        ...     chunking_max_tokens=1000
        ... )

        # Build from scratch without environment
        >>> config = create_config(
        ...     use_env=False,
        ...     input_glob="docs/*.pdf",
        ...     search_service_name="my-service",
        ...     search_index_name="my-index",
        ...     search_api_key="key123"
        ... )

        # Load from custom .env file
        >>> config = create_config(
        ...     env_path=".env.production",
        ...     azure_search_index="prod-index"
        ... )
    """
    # Start with environment config if requested
    if use_env:
        try:
            # Load .env file if env_path specified
            if env_path:
                from dotenv import load_dotenv
                load_dotenv(dotenv_path=env_path, override=True)

            config = PipelineConfig.from_env()
        except Exception as e:
            # If env loading fails and we have required params in kwargs, continue
            # Otherwise, raise the error
            if not _has_minimal_config_in_kwargs(kwargs):
                raise ValueError(
                    f"Failed to load config from environment: {e}\n"
                    "Either fix .env file or provide config via kwargs with use_env=False"
                )
            # Create empty config to populate from kwargs
            config = None
    else:
        config = None

    # If no config from env, we need to build from kwargs
    if config is None:
        config = _build_config_from_kwargs(
            input_glob=input_glob,
            azure_search_index=azure_search_index,
            **kwargs
        )
    else:
        # Override env config with provided parameters
        if input_glob:
            config.input.mode = InputMode.LOCAL
            config.input.local_glob = input_glob
        if azure_search_index:
            config.search.index_name = azure_search_index

        # Apply additional kwargs (supports nested attribute updates)
        config = _apply_kwargs_to_config(config, kwargs)

    return config


def _has_minimal_config_in_kwargs(kwargs: Dict[str, Any]) -> bool:
    """Check if kwargs contain minimal required config to build without env."""
    # Check for search config
    has_search = any(k.startswith("search_") for k in kwargs)
    return has_search


def _build_config_from_kwargs(
    input_glob: Optional[str] = None,
    azure_search_index: Optional[str] = None,
    **kwargs
) -> PipelineConfig:
    """Build config from scratch using ConfigBuilder and kwargs.

    Supports prefixed parameters for nested configs:
    - search_service_name, search_index_name, search_api_key
    - document_intelligence_endpoint, document_intelligence_key
    - azure_openai_endpoint, azure_openai_api_key, azure_openai_embedding_deployment
    - chunking_max_tokens, chunking_overlap_percent
    """
    builder = ConfigBuilder()

    # Configure search
    if "search_service_name" in kwargs and "search_index_name" in kwargs:
        builder.with_search(
            service_name=kwargs.pop("search_service_name"),
            index_name=kwargs.pop("search_index_name"),
            api_key=kwargs.pop("search_api_key", None)
        )
    elif "search_endpoint" in kwargs and "search_index_name" in kwargs:
        builder.with_search_endpoint(
            endpoint=kwargs.pop("search_endpoint"),
            index_name=kwargs.pop("search_index_name"),
            api_key=kwargs.pop("search_api_key", None)
        )
    elif azure_search_index:
        # Need more info for search
        raise ValueError(
            "azure_search_index provided but missing search service details. "
            "Provide search_service_name or search_endpoint"
        )

    # Configure Document Intelligence
    if "document_intelligence_endpoint" in kwargs:
        builder.with_document_intelligence(
            endpoint=kwargs.pop("document_intelligence_endpoint"),
            key=kwargs.pop("document_intelligence_key", None),
            max_concurrency=kwargs.pop("document_intelligence_max_concurrency", 3)
        )

    # Configure Azure OpenAI
    if "azure_openai_endpoint" in kwargs:
        builder.with_azure_openai(
            endpoint=kwargs.pop("azure_openai_endpoint"),
            api_key=kwargs.pop("azure_openai_api_key"),
            embedding_deployment=kwargs.pop("azure_openai_embedding_deployment"),
            embedding_model=kwargs.pop("azure_openai_embedding_model", "text-embedding-ada-002"),
            embedding_dimensions=kwargs.pop("azure_openai_embedding_dimensions", None),
            chat_deployment=kwargs.pop("azure_openai_chat_deployment", None),
            max_concurrency=kwargs.pop("azure_openai_max_concurrency", 5)
        )

    # Configure input
    if input_glob:
        artifacts_dir = kwargs.pop("artifacts_dir", "./artifacts")
        builder.with_local_files(input_glob, artifacts_dir)
    elif "blob_account_url" in kwargs:
        builder.with_blob_input(
            account_url=kwargs.pop("blob_account_url"),
            container_in=kwargs.pop("blob_container_in"),
            prefix=kwargs.pop("blob_prefix", ""),
            account_key=kwargs.pop("blob_account_key", None),
            connection_string=kwargs.pop("blob_connection_string", None)
        )

    # Configure chunking
    if any(k.startswith("chunking_") for k in kwargs):
        builder.with_chunking(
            max_tokens=kwargs.pop("chunking_max_tokens", 500),
            max_chars=kwargs.pop("chunking_max_chars", 1000),
            overlap_percent=kwargs.pop("chunking_overlap_percent", 10),
            cross_page_overlap=kwargs.pop("chunking_cross_page_overlap", False),
            disable_char_limit=kwargs.pop("chunking_disable_char_limit", False)
        )

    # Configure performance
    if any(k.startswith("performance_") for k in kwargs):
        builder.with_performance(
            max_workers=kwargs.pop("performance_max_workers", 4),
            embed_batch_size=kwargs.pop("performance_embed_batch_size", 128),
            upload_batch_size=kwargs.pop("performance_upload_batch_size", 1000)
        )

    # Apply remaining kwargs to built config
    config = builder.build()
    return _apply_kwargs_to_config(config, kwargs)


def _apply_kwargs_to_config(config: PipelineConfig, kwargs: Dict[str, Any]) -> PipelineConfig:
    """Apply kwargs to existing config, supporting nested attribute updates."""
    for key, value in kwargs.items():
        # Handle nested config updates with underscore notation
        # e.g., chunking_max_tokens -> config.chunking.max_tokens
        if "_" in key:
            parts = key.split("_", 1)
            if hasattr(config, parts[0]):
                nested_obj = getattr(config, parts[0])
                nested_key = parts[1]
                if hasattr(nested_obj, nested_key):
                    setattr(nested_obj, nested_key, value)
                    continue

        # Direct top-level attribute
        if hasattr(config, key):
            setattr(config, key, value)

    return config


async def run_pipeline(
    config: Optional[PipelineConfig] = None,
    **kwargs
) -> PipelineStatus:
    """Run ingestion pipeline with given configuration.

    Args:
        config: PipelineConfig instance (if None, loads from environment)
        **kwargs: Config parameters (passed to create_config)

    Returns:
        PipelineStatus with results

    Example:
        >>> status = await run_pipeline(input_glob="docs/*.pdf")
        >>> print(f"Processed {status.successful_documents} documents")
    """
    if config is None:
        config = create_config(**kwargs)

    pipeline = Pipeline(config)
    try:
        return await pipeline.run()
    finally:
        await pipeline.close()


def sync_run_pipeline(
    config: Optional[PipelineConfig] = None,
    **kwargs
) -> PipelineStatus:
    """Synchronous wrapper for run_pipeline().

    Example:
        >>> status = sync_run_pipeline(input_glob="docs/*.pdf")
    """
    return asyncio.run(run_pipeline(config, **kwargs))
