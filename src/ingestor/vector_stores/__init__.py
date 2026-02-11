"""Vector store implementations.

This package contains concrete implementations of the VectorStore ABC.
"""

from .azure_search_vector_store import AzureSearchVectorStore

__all__ = [
    'AzureSearchVectorStore',
]
