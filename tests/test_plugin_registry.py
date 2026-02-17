"""Unit tests for plugin registry system.

Tests cover:
- register_vector_store decorator
- register_embeddings_provider decorator
- get_vector_store_class()
- get_embeddings_provider_class()
- list_vector_stores() and list_embeddings_providers()
- Error handling for unknown plugins
- Type validation (must inherit from ABC)
"""

import sys
from pathlib import Path
from typing import Optional
from unittest.mock import Mock, patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ingestor.plugin_registry import (
    register_vector_store,
    register_embeddings_provider,
    get_vector_store_class,
    get_embeddings_provider_class,
    list_vector_stores,
    list_embeddings_providers,
    load_plugin_module,
    _vector_store_registry,
    _embeddings_provider_registry
)
from ingestor.vector_store import VectorStore
from ingestor.embeddings_provider import EmbeddingsProvider


@pytest.fixture(autouse=True)
def clear_registries():
    """Clear plugin registries before each test."""
    _vector_store_registry.clear()
    _embeddings_provider_registry.clear()
    yield
    # Clear again after test
    _vector_store_registry.clear()
    _embeddings_provider_registry.clear()


class TestRegisterVectorStore:
    """Tests for register_vector_store decorator."""

    def test_register_valid_vector_store(self):
        """Test registering a valid vector store."""
        @register_vector_store("test_store")
        class TestVectorStore(VectorStore):
            async def upload_documents(self, chunk_docs, include_embeddings=True):
                return 0

            async def delete_documents_by_filename(self, filename):
                return 0

            async def delete_all_documents(self):
                return 0

            async def search(self, query, top_k=10, filters=None):
                return []

            def get_dimensions(self):
                return 1536

        # Verify registration
        assert "test_store" in _vector_store_registry
        assert _vector_store_registry["test_store"] == TestVectorStore

    def test_register_vector_store_case_insensitive(self):
        """Test that registration is case-insensitive."""
        @register_vector_store("TestStore")
        class TestVectorStore(VectorStore):
            async def upload_documents(self, chunk_docs, include_embeddings=True):
                return 0

            async def delete_documents_by_filename(self, filename):
                return 0

            async def delete_all_documents(self):
                return 0

            async def search(self, query, top_k=10, filters=None):
                return []

            def get_dimensions(self):
                return 1536

        # Should be stored in lowercase
        assert "teststore" in _vector_store_registry
        assert "TestStore" not in _vector_store_registry

    def test_register_non_vector_store_raises_error(self):
        """Test registering a class that doesn't inherit from VectorStore."""
        with pytest.raises(TypeError, match="must inherit from VectorStore"):
            @register_vector_store("invalid_store")
            class NotAVectorStore:
                pass

    def test_register_multiple_vector_stores(self):
        """Test registering multiple vector stores."""
        @register_vector_store("store1")
        class Store1(VectorStore):
            async def upload_documents(self, chunk_docs, include_embeddings=True):
                return 0

            async def delete_documents_by_filename(self, filename):
                return 0

            async def delete_all_documents(self):
                return 0

            async def search(self, query, top_k=10, filters=None):
                return []

            def get_dimensions(self):
                return 1536

        @register_vector_store("store2")
        class Store2(VectorStore):
            async def upload_documents(self, chunk_docs, include_embeddings=True):
                return 0

            async def delete_documents_by_filename(self, filename):
                return 0

            async def delete_all_documents(self):
                return 0

            async def search(self, query, top_k=10, filters=None):
                return []

            def get_dimensions(self):
                return 1536

        assert len(_vector_store_registry) == 2
        assert "store1" in _vector_store_registry
        assert "store2" in _vector_store_registry


class TestRegisterEmbeddingsProvider:
    """Tests for register_embeddings_provider decorator."""

    def test_register_valid_embeddings_provider(self):
        """Test registering a valid embeddings provider."""
        @register_embeddings_provider("test_embeddings")
        class TestEmbeddings(EmbeddingsProvider):
            async def generate_embedding(self, text):
                return [0.1] * 1536

            async def generate_embeddings_batch(self, texts):
                return [[0.1] * 1536 for _ in texts]

            def get_dimensions(self):
                return 1536

            def get_model_name(self):
                return "test-model"

        # Verify registration
        assert "test_embeddings" in _embeddings_provider_registry
        assert _embeddings_provider_registry["test_embeddings"] == TestEmbeddings

    def test_register_embeddings_provider_case_insensitive(self):
        """Test that registration is case-insensitive."""
        @register_embeddings_provider("TestEmbeddings")
        class TestEmbeddings(EmbeddingsProvider):
            async def generate_embedding(self, text):
                return [0.1] * 1536

            async def generate_embeddings_batch(self, texts):
                return [[0.1] * 1536 for _ in texts]

            def get_dimensions(self):
                return 1536

            def get_model_name(self):
                return "test-model"

        # Should be stored in lowercase
        assert "testembeddings" in _embeddings_provider_registry
        assert "TestEmbeddings" not in _embeddings_provider_registry

    def test_register_non_embeddings_provider_raises_error(self):
        """Test registering a class that doesn't inherit from EmbeddingsProvider."""
        with pytest.raises(TypeError, match="must inherit from EmbeddingsProvider"):
            @register_embeddings_provider("invalid_embeddings")
            class NotAnEmbeddingsProvider:
                pass

    def test_register_multiple_embeddings_providers(self):
        """Test registering multiple embeddings providers."""
        @register_embeddings_provider("embeddings1")
        class Embeddings1(EmbeddingsProvider):
            async def generate_embedding(self, text):
                return [0.1] * 1536

            async def generate_embeddings_batch(self, texts):
                return [[0.1] * 1536 for _ in texts]

            def get_dimensions(self):
                return 1536

            def get_model_name(self):
                return "model1"

        @register_embeddings_provider("embeddings2")
        class Embeddings2(EmbeddingsProvider):
            async def generate_embedding(self, text):
                return [0.2] * 1536

            async def generate_embeddings_batch(self, texts):
                return [[0.2] * 1536 for _ in texts]

            def get_dimensions(self):
                return 1536

            def get_model_name(self):
                return "model2"

        assert len(_embeddings_provider_registry) == 2
        assert "embeddings1" in _embeddings_provider_registry
        assert "embeddings2" in _embeddings_provider_registry


class TestGetVectorStoreClass:
    """Tests for get_vector_store_class function."""

    def test_get_registered_vector_store(self):
        """Test getting a registered vector store class."""
        @register_vector_store("test_store")
        class TestVectorStore(VectorStore):
            async def upload_documents(self, chunk_docs, include_embeddings=True):
                return 0

            async def delete_documents_by_filename(self, filename):
                return 0

            async def delete_all_documents(self):
                return 0

            async def search(self, query, top_k=10, filters=None):
                return []

            def get_dimensions(self):
                return 1536

        cls = get_vector_store_class("test_store")
        assert cls == TestVectorStore

    def test_get_vector_store_case_insensitive(self):
        """Test getting vector store with different case."""
        @register_vector_store("test_store")
        class TestVectorStore(VectorStore):
            async def upload_documents(self, chunk_docs, include_embeddings=True):
                return 0

            async def delete_documents_by_filename(self, filename):
                return 0

            async def delete_all_documents(self):
                return 0

            async def search(self, query, top_k=10, filters=None):
                return []

            def get_dimensions(self):
                return 1536

        # Should work with different casing
        cls = get_vector_store_class("TEST_STORE")
        assert cls == TestVectorStore

    def test_get_unknown_vector_store_raises_error(self):
        """Test getting an unregistered vector store raises ValueError."""
        with pytest.raises(ValueError, match="Unknown vector store: nonexistent"):
            get_vector_store_class("nonexistent")


class TestGetEmbeddingsProviderClass:
    """Tests for get_embeddings_provider_class function."""

    def test_get_registered_embeddings_provider(self):
        """Test getting a registered embeddings provider class."""
        @register_embeddings_provider("test_embeddings")
        class TestEmbeddings(EmbeddingsProvider):
            async def generate_embedding(self, text):
                return [0.1] * 1536

            async def generate_embeddings_batch(self, texts):
                return [[0.1] * 1536 for _ in texts]

            def get_dimensions(self):
                return 1536

            def get_model_name(self):
                return "test-model"

        cls = get_embeddings_provider_class("test_embeddings")
        assert cls == TestEmbeddings

    def test_get_embeddings_provider_case_insensitive(self):
        """Test getting embeddings provider with different case."""
        @register_embeddings_provider("test_embeddings")
        class TestEmbeddings(EmbeddingsProvider):
            async def generate_embedding(self, text):
                return [0.1] * 1536

            async def generate_embeddings_batch(self, texts):
                return [[0.1] * 1536 for _ in texts]

            def get_dimensions(self):
                return 1536

            def get_model_name(self):
                return "test-model"

        # Should work with different casing
        cls = get_embeddings_provider_class("TEST_EMBEDDINGS")
        assert cls == TestEmbeddings

    def test_get_unknown_embeddings_provider_raises_error(self):
        """Test getting an unregistered embeddings provider raises ValueError."""
        with pytest.raises(ValueError, match="Unknown embeddings provider: nonexistent"):
            get_embeddings_provider_class("nonexistent")


class TestListFunctions:
    """Tests for list_vector_stores and list_embeddings_providers."""

    def test_list_vector_stores_empty(self):
        """Test listing vector stores when none registered."""
        stores = list_vector_stores()
        assert stores == []

    def test_list_vector_stores_with_registrations(self):
        """Test listing vector stores after registration."""
        @register_vector_store("store1")
        class Store1(VectorStore):
            async def upload_documents(self, chunk_docs, include_embeddings=True):
                return 0

            async def delete_documents_by_filename(self, filename):
                return 0

            async def delete_all_documents(self):
                return 0

            async def search(self, query, top_k=10, filters=None):
                return []

            def get_dimensions(self):
                return 1536

        @register_vector_store("store2")
        class Store2(VectorStore):
            async def upload_documents(self, chunk_docs, include_embeddings=True):
                return 0

            async def delete_documents_by_filename(self, filename):
                return 0

            async def delete_all_documents(self):
                return 0

            async def search(self, query, top_k=10, filters=None):
                return []

            def get_dimensions(self):
                return 1536

        stores = list_vector_stores()
        assert len(stores) == 2
        assert "store1" in stores
        assert "store2" in stores

    def test_list_embeddings_providers_empty(self):
        """Test listing embeddings providers when none registered."""
        providers = list_embeddings_providers()
        assert providers == []

    def test_list_embeddings_providers_with_registrations(self):
        """Test listing embeddings providers after registration."""
        @register_embeddings_provider("embeddings1")
        class Embeddings1(EmbeddingsProvider):
            async def generate_embedding(self, text):
                return [0.1] * 1536

            async def generate_embeddings_batch(self, texts):
                return [[0.1] * 1536 for _ in texts]

            def get_dimensions(self):
                return 1536

            def get_model_name(self):
                return "model1"

        @register_embeddings_provider("embeddings2")
        class Embeddings2(EmbeddingsProvider):
            async def generate_embedding(self, text):
                return [0.2] * 1536

            async def generate_embeddings_batch(self, texts):
                return [[0.2] * 1536 for _ in texts]

            def get_dimensions(self):
                return 1536

            def get_model_name(self):
                return "model2"

        providers = list_embeddings_providers()
        assert len(providers) == 2
        assert "embeddings1" in providers
        assert "embeddings2" in providers


class TestLoadPluginModule:
    """Tests for load_plugin_module function."""

    @patch('ingestor.plugin_registry.importlib.import_module')
    def test_load_plugin_module_success(self, mock_import):
        """Test successful plugin module loading."""
        mock_import.return_value = Mock()

        load_plugin_module("my_plugins.vector_stores")

        mock_import.assert_called_once_with("my_plugins.vector_stores")

    @patch('ingestor.plugin_registry.importlib.import_module')
    def test_load_plugin_module_import_error(self, mock_import):
        """Test plugin module loading with ImportError."""
        mock_import.side_effect = ImportError("Module not found")

        with pytest.raises(ImportError, match="Module not found"):
            load_plugin_module("nonexistent.module")


class TestOverwriteRegistration:
    """Tests for overwriting existing registrations."""

    def test_overwrite_vector_store_registration(self):
        """Test that registering same name twice overwrites."""
        @register_vector_store("test_store")
        class Store1(VectorStore):
            async def upload_documents(self, chunk_docs, include_embeddings=True):
                return 1

            async def delete_documents_by_filename(self, filename):
                return 0

            async def delete_all_documents(self):
                return 0

            async def search(self, query, top_k=10, filters=None):
                return []

            def get_dimensions(self):
                return 1536

        @register_vector_store("test_store")
        class Store2(VectorStore):
            async def upload_documents(self, chunk_docs, include_embeddings=True):
                return 2

            async def delete_documents_by_filename(self, filename):
                return 0

            async def delete_all_documents(self):
                return 0

            async def search(self, query, top_k=10, filters=None):
                return []

            def get_dimensions(self):
                return 1536

        # Should get the second registration
        cls = get_vector_store_class("test_store")
        assert cls == Store2

    def test_overwrite_embeddings_provider_registration(self):
        """Test that registering same name twice overwrites."""
        @register_embeddings_provider("test_embeddings")
        class Embeddings1(EmbeddingsProvider):
            async def generate_embedding(self, text):
                return [0.1] * 1536

            async def generate_embeddings_batch(self, texts):
                return [[0.1] * 1536 for _ in texts]

            def get_dimensions(self):
                return 1536

            def get_model_name(self):
                return "model1"

        @register_embeddings_provider("test_embeddings")
        class Embeddings2(EmbeddingsProvider):
            async def generate_embedding(self, text):
                return [0.2] * 1536

            async def generate_embeddings_batch(self, texts):
                return [[0.2] * 1536 for _ in texts]

            def get_dimensions(self):
                return 3072

            def get_model_name(self):
                return "model2"

        # Should get the second registration
        cls = get_embeddings_provider_class("test_embeddings")
        assert cls == Embeddings2


class TestDecoratorReturnValue:
    """Tests that decorators return the original class."""

    def test_vector_store_decorator_returns_class(self):
        """Test that decorator returns the original class."""
        @register_vector_store("test_store")
        class TestStore(VectorStore):
            async def upload_documents(self, chunk_docs, include_embeddings=True):
                return 0

            async def delete_documents_by_filename(self, filename):
                return 0

            async def delete_all_documents(self):
                return 0

            async def search(self, query, top_k=10, filters=None):
                return []

            def get_dimensions(self):
                return 1536

        # Decorator should return the class unchanged
        assert TestStore.__name__ == "TestStore"

    def test_embeddings_provider_decorator_returns_class(self):
        """Test that decorator returns the original class."""
        @register_embeddings_provider("test_embeddings")
        class TestEmbeddings(EmbeddingsProvider):
            async def generate_embedding(self, text):
                return [0.1] * 1536

            async def generate_embeddings_batch(self, texts):
                return [[0.1] * 1536 for _ in texts]

            def get_dimensions(self):
                return 1536

            def get_model_name(self):
                return "test-model"

        # Decorator should return the class unchanged
        assert TestEmbeddings.__name__ == "TestEmbeddings"
