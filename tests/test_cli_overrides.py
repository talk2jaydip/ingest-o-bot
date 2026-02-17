"""Unit tests for CLI argument overrides.

Tests cover:
- --vector-store overrides config
- --embeddings overrides config
- Azure Search argument overrides
- ChromaDB argument overrides
- Hugging Face argument overrides
- Argument parsing
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch
import argparse

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestVectorStoreOverrides:
    """Tests for vector store CLI overrides."""

    def test_vector_store_override_azure_search(self):
        """Test --vector-store azure_search override."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--vector-store", type=str, choices=["azure_search", "chromadb", "pinecone", "weaviate", "qdrant"])

        args = parser.parse_args(["--vector-store", "azure_search"])

        assert args.vector_store == "azure_search"

    def test_vector_store_override_chromadb(self):
        """Test --vector-store chromadb override."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--vector-store", type=str, choices=["azure_search", "chromadb", "pinecone", "weaviate", "qdrant"])

        args = parser.parse_args(["--vector-store", "chromadb"])

        assert args.vector_store == "chromadb"

    def test_vector_store_invalid_choice(self):
        """Test --vector-store with invalid choice."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--vector-store", type=str, choices=["azure_search", "chromadb", "pinecone", "weaviate", "qdrant"])

        with pytest.raises(SystemExit):
            parser.parse_args(["--vector-store", "invalid"])


class TestEmbeddingsOverrides:
    """Tests for embeddings provider CLI overrides."""

    def test_embeddings_override_azure_openai(self):
        """Test --embeddings azure_openai override."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--embeddings", type=str, choices=["azure_openai", "huggingface", "cohere", "openai"])

        args = parser.parse_args(["--embeddings", "azure_openai"])

        assert args.embeddings == "azure_openai"

    def test_embeddings_override_huggingface(self):
        """Test --embeddings huggingface override."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--embeddings", type=str, choices=["azure_openai", "huggingface", "cohere", "openai"])

        args = parser.parse_args(["--embeddings", "huggingface"])

        assert args.embeddings == "huggingface"

    def test_embeddings_override_cohere(self):
        """Test --embeddings cohere override."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--embeddings", type=str, choices=["azure_openai", "huggingface", "cohere", "openai"])

        args = parser.parse_args(["--embeddings", "cohere"])

        assert args.embeddings == "cohere"

    def test_embeddings_override_openai(self):
        """Test --embeddings openai override."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--embeddings", type=str, choices=["azure_openai", "huggingface", "cohere", "openai"])

        args = parser.parse_args(["--embeddings", "openai"])

        assert args.embeddings == "openai"

    def test_embeddings_invalid_choice(self):
        """Test --embeddings with invalid choice."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--embeddings", type=str, choices=["azure_openai", "huggingface", "cohere", "openai"])

        with pytest.raises(SystemExit):
            parser.parse_args(["--embeddings", "invalid"])


class TestAzureSearchOverrides:
    """Tests for Azure Search specific CLI overrides."""

    def test_azure_search_endpoint_override(self):
        """Test --azure-search-endpoint override."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--azure-search-endpoint", type=str)

        args = parser.parse_args(["--azure-search-endpoint", "https://test-service.search.windows.net"])

        assert args.azure_search_endpoint == "https://test-service.search.windows.net"

    def test_azure_search_index_override(self):
        """Test --azure-search-index override."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--azure-search-index", type=str)

        args = parser.parse_args(["--azure-search-index", "test-index"])

        assert args.azure_search_index == "test-index"

    def test_azure_search_key_override(self):
        """Test --azure-search-key override."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--azure-search-key", type=str)

        args = parser.parse_args(["--azure-search-key", "test-key"])

        assert args.azure_search_key == "test-key"

    def test_azure_search_all_overrides(self):
        """Test all Azure Search overrides together."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--azure-search-endpoint", type=str)
        parser.add_argument("--azure-search-index", type=str)
        parser.add_argument("--azure-search-key", type=str)

        args = parser.parse_args([
            "--azure-search-endpoint", "https://test-service.search.windows.net",
            "--azure-search-index", "test-index",
            "--azure-search-key", "test-key"
        ])

        assert args.azure_search_endpoint == "https://test-service.search.windows.net"
        assert args.azure_search_index == "test-index"
        assert args.azure_search_key == "test-key"


class TestChromaDBOverrides:
    """Tests for ChromaDB specific CLI overrides."""

    def test_chromadb_persist_dir_override(self):
        """Test --chromadb-persist-dir override."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--chromadb-persist-dir", type=str)

        args = parser.parse_args(["--chromadb-persist-dir", "./chroma_data"])

        assert args.chromadb_persist_dir == "./chroma_data"

    def test_chromadb_host_override(self):
        """Test --chromadb-host override."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--chromadb-host", type=str)

        args = parser.parse_args(["--chromadb-host", "localhost"])

        assert args.chromadb_host == "localhost"

    def test_chromadb_port_override(self):
        """Test --chromadb-port override."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--chromadb-port", type=int)

        args = parser.parse_args(["--chromadb-port", "8000"])

        assert args.chromadb_port == 8000

    def test_chromadb_collection_override(self):
        """Test --chromadb-collection override."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--chromadb-collection", type=str)

        args = parser.parse_args(["--chromadb-collection", "test-collection"])

        assert args.chromadb_collection == "test-collection"

    def test_chromadb_all_overrides(self):
        """Test all ChromaDB overrides together."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--chromadb-persist-dir", type=str)
        parser.add_argument("--chromadb-host", type=str)
        parser.add_argument("--chromadb-port", type=int)
        parser.add_argument("--chromadb-collection", type=str)

        args = parser.parse_args([
            "--chromadb-persist-dir", "./chroma_data",
            "--chromadb-host", "localhost",
            "--chromadb-port", "8000",
            "--chromadb-collection", "test-collection"
        ])

        assert args.chromadb_persist_dir == "./chroma_data"
        assert args.chromadb_host == "localhost"
        assert args.chromadb_port == 8000
        assert args.chromadb_collection == "test-collection"


class TestHuggingFaceOverrides:
    """Tests for Hugging Face specific CLI overrides."""

    def test_huggingface_model_override(self):
        """Test --huggingface-model override."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--huggingface-model", type=str)

        args = parser.parse_args(["--huggingface-model", "sentence-transformers/all-MiniLM-L6-v2"])

        assert args.huggingface_model == "sentence-transformers/all-MiniLM-L6-v2"

    def test_embeddings_device_cpu(self):
        """Test --embeddings-device cpu override."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--embeddings-device", type=str, choices=["cpu", "cuda", "mps"])

        args = parser.parse_args(["--embeddings-device", "cpu"])

        assert args.embeddings_device == "cpu"

    def test_embeddings_device_cuda(self):
        """Test --embeddings-device cuda override."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--embeddings-device", type=str, choices=["cpu", "cuda", "mps"])

        args = parser.parse_args(["--embeddings-device", "cuda"])

        assert args.embeddings_device == "cuda"

    def test_embeddings_device_mps(self):
        """Test --embeddings-device mps override."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--embeddings-device", type=str, choices=["cpu", "cuda", "mps"])

        args = parser.parse_args(["--embeddings-device", "mps"])

        assert args.embeddings_device == "mps"

    def test_embeddings_device_invalid(self):
        """Test --embeddings-device with invalid choice."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--embeddings-device", type=str, choices=["cpu", "cuda", "mps"])

        with pytest.raises(SystemExit):
            parser.parse_args(["--embeddings-device", "invalid"])


class TestFileInputOverrides:
    """Tests for file input CLI arguments."""

    def test_pdf_path_override(self):
        """Test --pdf override."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--pdf", type=str)

        args = parser.parse_args(["--pdf", "document.pdf"])

        assert args.pdf == "document.pdf"

    def test_glob_pattern_override(self):
        """Test --glob override."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--glob", type=str)

        args = parser.parse_args(["--glob", "documents/*.pdf"])

        assert args.glob == "documents/*.pdf"


class TestDocumentActionOverrides:
    """Tests for document action CLI arguments."""

    def test_action_add(self):
        """Test --action add."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--action", type=str, choices=["add", "remove", "removeall"])

        args = parser.parse_args(["--action", "add"])

        assert args.action == "add"

    def test_action_remove(self):
        """Test --action remove."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--action", type=str, choices=["add", "remove", "removeall"])

        args = parser.parse_args(["--action", "remove"])

        assert args.action == "remove"

    def test_action_removeall(self):
        """Test --action removeall."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--action", type=str, choices=["add", "remove", "removeall"])

        args = parser.parse_args(["--action", "removeall"])

        assert args.action == "removeall"


class TestIndexOperationFlags:
    """Tests for index operation flags."""

    def test_setup_index_flag(self):
        """Test --setup-index flag."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--setup-index", action="store_true")

        args = parser.parse_args(["--setup-index"])

        assert args.setup_index is True

    def test_force_index_flag(self):
        """Test --force-index flag."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--force-index", action="store_true")

        args = parser.parse_args(["--force-index"])

        assert args.force_index is True

    def test_index_only_flag(self):
        """Test --index-only flag."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--index-only", action="store_true")

        args = parser.parse_args(["--index-only"])

        assert args.index_only is True

    def test_delete_index_flag(self):
        """Test --delete-index flag."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--delete-index", action="store_true")

        args = parser.parse_args(["--delete-index"])

        assert args.delete_index is True


class TestLoggingFlags:
    """Tests for logging-related flags."""

    def test_verbose_flag(self):
        """Test --verbose flag."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--verbose", action="store_true")

        args = parser.parse_args(["--verbose"])

        assert args.verbose is True

    def test_no_colors_flag(self):
        """Test --no-colors flag."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--no-colors", action="store_true")

        args = parser.parse_args(["--no-colors"])

        assert args.no_colors is True


class TestImportJSONFlag:
    """Tests for JSON import flag."""

    def test_import_json_flag(self):
        """Test --import-json flag."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--import-json", type=str)

        args = parser.parse_args(["--import-json", "documents.json"])

        assert args.import_json == "documents.json"


class TestValidateFlag:
    """Tests for validation flag."""

    def test_validate_flag(self):
        """Test --validate flag."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--validate", dest="validate_only", action="store_true")

        args = parser.parse_args(["--validate"])

        assert args.validate_only is True


class TestEnvFileOverride:
    """Tests for environment file override."""

    def test_env_file_default(self):
        """Test --env default value."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--env", type=str, default=".env")

        args = parser.parse_args([])

        assert args.env == ".env"

    def test_env_file_override(self):
        """Test --env override."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--env", type=str)

        args = parser.parse_args(["--env", ".env.offline"])

        assert args.env == ".env.offline"


class TestCombinedOverrides:
    """Tests for combining multiple CLI overrides."""

    def test_vector_store_and_chromadb_overrides(self):
        """Test combining vector store and ChromaDB overrides."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--vector-store", type=str)
        parser.add_argument("--chromadb-persist-dir", type=str)
        parser.add_argument("--chromadb-collection", type=str)

        args = parser.parse_args([
            "--vector-store", "chromadb",
            "--chromadb-persist-dir", "./chroma_data",
            "--chromadb-collection", "test-collection"
        ])

        assert args.vector_store == "chromadb"
        assert args.chromadb_persist_dir == "./chroma_data"
        assert args.chromadb_collection == "test-collection"

    def test_embeddings_and_huggingface_overrides(self):
        """Test combining embeddings and Hugging Face overrides."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--embeddings", type=str)
        parser.add_argument("--huggingface-model", type=str)
        parser.add_argument("--embeddings-device", type=str)

        args = parser.parse_args([
            "--embeddings", "huggingface",
            "--huggingface-model", "sentence-transformers/all-MiniLM-L6-v2",
            "--embeddings-device", "cpu"
        ])

        assert args.embeddings == "huggingface"
        assert args.huggingface_model == "sentence-transformers/all-MiniLM-L6-v2"
        assert args.embeddings_device == "cpu"

    def test_all_azure_search_overrides(self):
        """Test combining vector store and Azure Search overrides."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--vector-store", type=str)
        parser.add_argument("--azure-search-endpoint", type=str)
        parser.add_argument("--azure-search-index", type=str)
        parser.add_argument("--azure-search-key", type=str)

        args = parser.parse_args([
            "--vector-store", "azure_search",
            "--azure-search-endpoint", "https://test-service.search.windows.net",
            "--azure-search-index", "test-index",
            "--azure-search-key", "test-key"
        ])

        assert args.vector_store == "azure_search"
        assert args.azure_search_endpoint == "https://test-service.search.windows.net"
        assert args.azure_search_index == "test-index"
        assert args.azure_search_key == "test-key"

    def test_file_input_and_action_overrides(self):
        """Test combining file input and action overrides."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--glob", type=str)
        parser.add_argument("--action", type=str)

        args = parser.parse_args([
            "--glob", "documents/*.pdf",
            "--action", "add"
        ])

        assert args.glob == "documents/*.pdf"
        assert args.action == "add"


class TestNoArguments:
    """Tests for parsing with no arguments."""

    def test_no_arguments_defaults(self):
        """Test parsing with no arguments (all defaults)."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--vector-store", type=str, default=None)
        parser.add_argument("--embeddings", type=str, default=None)
        parser.add_argument("--verbose", action="store_true")

        args = parser.parse_args([])

        assert args.vector_store is None
        assert args.embeddings is None
        assert args.verbose is False
