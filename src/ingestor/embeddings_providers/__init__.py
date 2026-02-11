"""Embeddings provider implementations.

This package contains concrete implementations of the EmbeddingsProvider ABC.
"""

from .azure_openai_provider import AzureOpenAIEmbeddingsProvider

__all__ = [
    'AzureOpenAIEmbeddingsProvider',
]
