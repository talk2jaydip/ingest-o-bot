"""Plugin system for registering custom vector stores and embeddings providers.

Allows users to extend ingest-o-bot with custom implementations without modifying core code.

Example usage:
    # In user's plugin file
    from ingestor.plugin_registry import register_vector_store
    from ingestor.vector_store import VectorStore

    @register_vector_store("myvectordb")
    class MyVectorDBStore(VectorStore):
        # Implementation...

    # Then use via environment or CLI
    VECTOR_STORE_MODE=myvectordb python -m ingestor.cli --glob "*.pdf"
"""

from typing import Dict, Type, Callable
import importlib
import sys

from .vector_store import VectorStore
from .embeddings_provider import EmbeddingsProvider
from .logging_utils import get_logger

logger = get_logger(__name__)

# Global registries
_vector_store_registry: Dict[str, Type[VectorStore]] = {}
_embeddings_provider_registry: Dict[str, Type[EmbeddingsProvider]] = {}


def register_vector_store(name: str) -> Callable:
    """Decorator to register a custom vector store implementation.

    Args:
        name: Unique identifier for this vector store (e.g., "myvectordb")

    Returns:
        Decorator function

    Example:
        @register_vector_store("myvectordb")
        class MyVectorDB(VectorStore):
            pass
    """
    def decorator(cls: Type[VectorStore]) -> Type[VectorStore]:
        if not issubclass(cls, VectorStore):
            raise TypeError(f"{cls.__name__} must inherit from VectorStore")

        _vector_store_registry[name.lower()] = cls
        logger.info(f"Registered vector store plugin: {name} -> {cls.__name__}")
        return cls

    return decorator


def register_embeddings_provider(name: str) -> Callable:
    """Decorator to register a custom embeddings provider implementation.

    Args:
        name: Unique identifier for this provider (e.g., "myembeddings")

    Returns:
        Decorator function

    Example:
        @register_embeddings_provider("myembeddings")
        class MyEmbeddings(EmbeddingsProvider):
            pass
    """
    def decorator(cls: Type[EmbeddingsProvider]) -> Type[EmbeddingsProvider]:
        if not issubclass(cls, EmbeddingsProvider):
            raise TypeError(f"{cls.__name__} must inherit from EmbeddingsProvider")

        _embeddings_provider_registry[name.lower()] = cls
        logger.info(f"Registered embeddings provider plugin: {name} -> {cls.__name__}")
        return cls

    return decorator


def get_vector_store_class(name: str) -> Type[VectorStore]:
    """Get registered vector store class by name.

    Args:
        name: Vector store identifier

    Returns:
        VectorStore class

    Raises:
        ValueError: If name not registered
    """
    cls = _vector_store_registry.get(name.lower())
    if cls is None:
        raise ValueError(
            f"Unknown vector store: {name}. "
            f"Registered: {list(_vector_store_registry.keys())}"
        )
    return cls


def get_embeddings_provider_class(name: str) -> Type[EmbeddingsProvider]:
    """Get registered embeddings provider class by name.

    Args:
        name: Provider identifier

    Returns:
        EmbeddingsProvider class

    Raises:
        ValueError: If name not registered
    """
    cls = _embeddings_provider_registry.get(name.lower())
    if cls is None:
        raise ValueError(
            f"Unknown embeddings provider: {name}. "
            f"Registered: {list(_embeddings_provider_registry.keys())}"
        )
    return cls


def list_vector_stores() -> list[str]:
    """List all registered vector store names."""
    return list(_vector_store_registry.keys())


def list_embeddings_providers() -> list[str]:
    """List all registered embeddings provider names."""
    return list(_embeddings_provider_registry.keys())


def load_plugin_module(module_path: str):
    """Load a Python module containing plugins.

    Args:
        module_path: Python module path (e.g., "my_plugins.vector_stores")

    Raises:
        ImportError: If module cannot be loaded
    """
    try:
        importlib.import_module(module_path)
        logger.info(f"Loaded plugin module: {module_path}")
    except ImportError as e:
        logger.error(f"Failed to load plugin module {module_path}: {e}")
        raise


def discover_plugins():
    """Discover and load plugins from entry points.

    Looks for entry points in the 'ingestor.plugins' group.
    Users can register plugins via setup.py/pyproject.toml:

    [project.entry-points."ingestor.plugins"]
    myplugin = "my_package.plugins"
    """
    try:
        # Python 3.10+ uses importlib.metadata
        from importlib.metadata import entry_points

        # Get plugins group
        plugins = entry_points(group='ingestor.plugins')

        for entry_point in plugins:
            try:
                entry_point.load()
                logger.info(f"Loaded plugin: {entry_point.name}")
            except Exception as e:
                logger.warning(f"Failed to load plugin {entry_point.name}: {e}")

    except ImportError:
        # Fallback for older Python versions
        logger.debug("Entry point discovery not available")
