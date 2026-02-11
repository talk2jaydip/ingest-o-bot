"""Vector store implementations.

This package contains concrete implementations of the VectorStore ABC.
"""

from .azure_search_vector_store import AzureSearchVectorStore

# ChromaDB is optional - only import if available
try:
    from .chromadb_vector_store import ChromaDBVectorStore
    __all__ = ['AzureSearchVectorStore', 'ChromaDBVectorStore']
except ImportError:
    __all__ = ['AzureSearchVectorStore']
