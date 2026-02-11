"""Embeddings provider implementations.

This package contains concrete implementations of the EmbeddingsProvider ABC.
"""

from .azure_openai_provider import AzureOpenAIEmbeddingsProvider

# Optional providers - only import if dependencies available
__all__ = ['AzureOpenAIEmbeddingsProvider']

try:
    from .huggingface_provider import HuggingFaceEmbeddingsProvider
    __all__.append('HuggingFaceEmbeddingsProvider')
except ImportError:
    pass

try:
    from .cohere_provider import CohereEmbeddingsProvider
    __all__.append('CohereEmbeddingsProvider')
except ImportError:
    pass

try:
    from .openai_provider import OpenAIEmbeddingsProvider
    __all__.append('OpenAIEmbeddingsProvider')
except ImportError:
    pass
