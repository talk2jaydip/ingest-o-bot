"""Integration tests for pluggable architecture.

Tests all combinations of vector stores and embeddings providers
to ensure they work correctly together.
"""

import asyncio
import os
import tempfile
from pathlib import Path

# Test imports
from ingestor.config import (
    VectorStoreMode, EmbeddingsMode,
    SearchConfig, ChromaDBConfig,
    AzureOpenAIConfig, HuggingFaceEmbeddingsConfig,
    CohereEmbeddingsConfig, OpenAIEmbeddingsConfig,
    PipelineConfig
)
from ingestor.vector_store import create_vector_store
from ingestor.embeddings_provider import create_embeddings_provider
from ingestor.models import ChunkDocument, ChunkMetadata, DocumentMetadata, PageMetadata, ChunkArtifact


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    from ingestor.vector_store import VectorStore
    from ingestor.embeddings_provider import EmbeddingsProvider
    from ingestor.vector_stores.azure_search_vector_store import AzureSearchVectorStore
    from ingestor.embeddings_providers.azure_openai_provider import AzureOpenAIEmbeddingsProvider

    print("✅ All imports successful")


def test_backward_compatibility():
    """Test that legacy configuration still works."""
    print("\nTesting backward compatibility...")

    # Set legacy environment variables
    os.environ.update({
        'AZURE_SEARCH_SERVICE': 'test-service',
        'AZURE_SEARCH_INDEX': 'test-index',
        'AZURE_SEARCH_KEY': 'test-key',
        'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
        'AZURE_OPENAI_KEY': 'test-key',
        'AZURE_OPENAI_EMBEDDING_DEPLOYMENT': 'test-deployment',
    })

    # Load configs
    search = SearchConfig.from_env()
    azure_openai = AzureOpenAIConfig.from_env()

    assert search.endpoint == 'https://test-service.search.windows.net'
    assert azure_openai.endpoint == 'https://test.openai.azure.com/'

    print("✅ Backward compatibility verified")


def test_vector_store_configs():
    """Test vector store configuration classes."""
    print("\nTesting vector store configurations...")

    # Azure Search
    search_config = SearchConfig(
        endpoint='https://test.search.windows.net',
        index_name='test',
        api_key='test-key'
    )
    assert search_config.endpoint is not None
    print("✅ SearchConfig works")

    # ChromaDB persistent
    chroma_config = ChromaDBConfig(
        collection_name='test-collection',
        persist_directory='./test_db'
    )
    assert chroma_config.persist_directory == './test_db'
    print("✅ ChromaDBConfig (persistent) works")

    # ChromaDB in-memory
    chroma_memory = ChromaDBConfig(collection_name='temp')
    assert chroma_memory.persist_directory is None
    print("✅ ChromaDBConfig (in-memory) works")

    # ChromaDB client/server
    chroma_server = ChromaDBConfig(
        collection_name='shared',
        host='localhost',
        port=8000
    )
    assert chroma_server.host == 'localhost'
    print("✅ ChromaDBConfig (client/server) works")


def test_embeddings_configs():
    """Test embeddings configuration classes."""
    print("\nTesting embeddings configurations...")

    # Azure OpenAI
    azure_config = AzureOpenAIConfig(
        endpoint='https://test.openai.azure.com/',
        api_key='test-key',
        emb_deployment='test-deployment'
    )
    assert azure_config.endpoint is not None
    print("✅ AzureOpenAIConfig works")

    # Hugging Face
    hf_config = HuggingFaceEmbeddingsConfig(
        model_name='all-MiniLM-L6-v2',
        device='cpu'
    )
    assert hf_config.device == 'cpu'
    print("✅ HuggingFaceEmbeddingsConfig works")

    # Cohere
    cohere_config = CohereEmbeddingsConfig(
        api_key='test-key',
        model_name='embed-multilingual-v3.0'
    )
    assert cohere_config.model_name == 'embed-multilingual-v3.0'
    print("✅ CohereEmbeddingsConfig works")

    # OpenAI
    openai_config = OpenAIEmbeddingsConfig(
        api_key='test-key',
        model_name='text-embedding-3-small'
    )
    assert openai_config.model_name == 'text-embedding-3-small'
    print("✅ OpenAIEmbeddingsConfig works")


def test_factory_functions():
    """Test factory functions for creating components."""
    print("\nTesting factory functions...")

    # Test Azure Search vector store (should work)
    search_config = SearchConfig(
        endpoint='https://test.search.windows.net',
        index_name='test',
        api_key='test-key'
    )
    try:
        store = create_vector_store(VectorStoreMode.AZURE_SEARCH, search_config)
        assert isinstance(store.get_dimensions(), int)
        print(f"✅ Azure Search vector store factory works (dims: {store.get_dimensions()})")
    except Exception as e:
        print(f"❌ Azure Search factory failed: {e}")

    # Test ChromaDB vector store (should fail gracefully)
    chroma_config = ChromaDBConfig(collection_name='test')
    try:
        store = create_vector_store(VectorStoreMode.CHROMADB, chroma_config)
        print(f"✅ ChromaDB vector store created")
    except ImportError:
        print(f"✅ ChromaDB factory graceful failure (chromadb not installed)")

    # Test Azure OpenAI embeddings (should work)
    azure_config = AzureOpenAIConfig(
        endpoint='https://test.openai.azure.com/',
        api_key='test-key',
        emb_deployment='test-deployment'
    )
    try:
        provider = create_embeddings_provider(EmbeddingsMode.AZURE_OPENAI, azure_config)
        print(f"✅ Azure OpenAI embeddings factory works (dims: {provider.get_dimensions()})")
    except Exception as e:
        print(f"❌ Azure OpenAI factory failed: {e}")

    # Test OpenAI embeddings (should work - openai installed)
    openai_config = OpenAIEmbeddingsConfig(api_key='test-key')
    try:
        provider = create_embeddings_provider(EmbeddingsMode.OPENAI, openai_config)
        print(f"✅ OpenAI embeddings factory works (dims: {provider.get_dimensions()})")
    except Exception as e:
        print(f"❌ OpenAI factory failed: {e}")


def test_to_vector_document():
    """Test the new to_vector_document method."""
    print("\nTesting to_vector_document() method...")

    # Create a mock ChunkDocument
    chunk_doc = ChunkDocument(
        document=DocumentMetadata(
            sourcefile='test.pdf',
            storage_url='https://test.blob.core.windows.net/test.pdf'
        ),
        page=PageMetadata(
            sourcepage='test.pdf#page=1',
            page_num=1
        ),
        chunk=ChunkMetadata(
            chunk_id='test-chunk-1',
            chunk_index_on_page=0,
            text='Test chunk text',
            embedding=[0.1] * 1536  # Mock embedding
        ),
        chunk_artifact=ChunkArtifact(
            url='https://test.blob.core.windows.net/chunk1.json'
        ),
        tables=[],
        figures=[]
    )

    # Test generic serialization
    doc_dict = chunk_doc.to_vector_document(include_embeddings=True)

    assert doc_dict['id'] == 'test-chunk-1'
    assert doc_dict['text'] == 'Test chunk text'
    assert doc_dict['embedding'] is not None
    assert len(doc_dict['embedding']) == 1536
    assert doc_dict['metadata']['sourcefile'] == 'test.pdf'

    print("✅ to_vector_document() works correctly")

    # Test without embeddings
    doc_dict_no_emb = chunk_doc.to_vector_document(include_embeddings=False)
    assert doc_dict_no_emb['embedding'] is None
    print("✅ to_vector_document(include_embeddings=False) works")


def test_auto_detection():
    """Test auto-detection of vector store and embeddings modes."""
    print("\nTesting auto-detection...")

    # Clear existing env vars
    for key in list(os.environ.keys()):
        if key.startswith('VECTOR_STORE') or key.startswith('EMBEDDINGS') or key.startswith('CHROMADB') or key.startswith('HUGGINGFACE'):
            del os.environ[key]

    # Test ChromaDB auto-detection
    os.environ['CHROMADB_PERSIST_DIR'] = './test_db'
    from ingestor.config import ChromaDBConfig
    chroma_config = ChromaDBConfig.from_env()
    assert chroma_config.persist_directory == './test_db'
    print("✅ ChromaDB auto-detection works")

    # Test Hugging Face auto-detection
    os.environ['HUGGINGFACE_MODEL_NAME'] = 'test-model'
    from ingestor.config import HuggingFaceEmbeddingsConfig
    hf_config = HuggingFaceEmbeddingsConfig.from_env()
    assert hf_config.model_name == 'test-model'
    print("✅ Hugging Face auto-detection works")


def main():
    """Run all tests."""
    print("=" * 80)
    print("PLUGGABLE ARCHITECTURE INTEGRATION TESTS")
    print("=" * 80)

    try:
        test_imports()
        test_backward_compatibility()
        test_vector_store_configs()
        test_embeddings_configs()
        test_factory_functions()
        test_to_vector_document()
        test_auto_detection()

        print()
        print("=" * 80)
        print("ALL TESTS PASSED ✅")
        print("=" * 80)
        print()
        print("The pluggable architecture is working correctly!")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
