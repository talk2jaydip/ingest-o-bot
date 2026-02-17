"""Unit tests for JSON importer functionality.

Tests cover:
- Valid JSON loading and validation
- Array format validation
- Required fields validation
- Error handling (missing file, invalid format, missing fields)
- Batch splitting for large uploads
- Upload success and failure scenarios
"""

import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ingestor.config import SearchConfig
from ingestor.json_importer import import_json_to_azure_search, MAX_BATCH_SIZE


@pytest.fixture
def search_config():
    """Create a test SearchConfig."""
    return SearchConfig(
        endpoint='https://test-service.search.windows.net',
        index_name='test-index',
        api_key='test-key'
    )


@pytest.fixture
def valid_json_data():
    """Create valid JSON data."""
    return [
        {
            'id': 'doc1-chunk1',
            'content': 'First document content.',
            'embeddings': [0.1] * 1536,
            'filename': 'doc1.pdf',
            'sourcepage': 'doc1.pdf-1',
            'sourcefile': 'doc1',
            'pageNumber': 1
        },
        {
            'id': 'doc1-chunk2',
            'content': 'Second document content.',
            'embeddings': [0.2] * 1536,
            'filename': 'doc1.pdf',
            'sourcepage': 'doc1.pdf-1',
            'sourcefile': 'doc1',
            'pageNumber': 1
        }
    ]


@pytest.fixture
def temp_json_file(valid_json_data):
    """Create a temporary JSON file with valid data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(valid_json_data, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


class TestJSONLoading:
    """Tests for JSON file loading."""

    @pytest.mark.asyncio
    @patch('ingestor.json_importer.SearchClient')
    async def test_load_valid_json(self, mock_client_class, search_config, temp_json_file):
        """Test loading valid JSON file."""
        mock_result = [Mock(succeeded=True) for _ in range(2)]
        mock_client = AsyncMock()
        mock_client.merge_or_upload_documents = AsyncMock(return_value=mock_result)
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await import_json_to_azure_search(temp_json_file, search_config)

        assert result == 2
        mock_client.merge_or_upload_documents.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_missing_file(self, search_config):
        """Test loading non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match='JSON file not found'):
            await import_json_to_azure_search('nonexistent.json', search_config)

    @pytest.mark.asyncio
    async def test_load_invalid_json_format(self, search_config):
        """Test loading file with invalid JSON format."""
        # Create file with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            f.write('{ invalid json }')
            temp_path = f.name

        try:
            with pytest.raises(json.JSONDecodeError):
                await import_json_to_azure_search(temp_path, search_config)
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestJSONValidation:
    """Tests for JSON data validation."""

    @pytest.mark.asyncio
    async def test_validate_not_array(self, search_config):
        """Test validation fails when JSON is not an array."""
        # Create file with object instead of array
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump({'id': 'doc1', 'content': 'test'}, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match='JSON must be an array'):
                await import_json_to_azure_search(temp_path, search_config)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_validate_item_not_object(self, search_config):
        """Test validation fails when array item is not an object."""
        # Create file with array of non-objects
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(['string1', 'string2'], f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match='Document at index 0 is not an object'):
                await import_json_to_azure_search(temp_path, search_config)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_validate_missing_id_field(self, search_config):
        """Test validation fails when 'id' field is missing."""
        data = [
            {
                'content': 'Test content',
                # Missing 'id' field
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="missing required field: 'id'"):
                await import_json_to_azure_search(temp_path, search_config)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_validate_missing_content_field(self, search_config):
        """Test validation fails when 'content' field is missing."""
        data = [
            {
                'id': 'doc1',
                # Missing 'content' field
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="missing required field: 'content'"):
                await import_json_to_azure_search(temp_path, search_config)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    @patch('ingestor.json_importer.SearchClient')
    async def test_validate_empty_array(self, mock_client_class, search_config):
        """Test validation passes with empty array (no documents to upload)."""
        data = []

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            mock_client = AsyncMock()
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await import_json_to_azure_search(temp_path, search_config)

            # Should return 0 without attempting upload
            assert result == 0
            mock_client.merge_or_upload_documents.assert_not_called()
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestBatchUploading:
    """Tests for batch upload functionality."""

    @pytest.mark.asyncio
    @patch('ingestor.json_importer.SearchClient')
    async def test_upload_single_batch(self, mock_client_class, search_config, temp_json_file):
        """Test upload with documents fitting in single batch."""
        mock_result = [Mock(succeeded=True) for _ in range(2)]
        mock_client = AsyncMock()
        mock_client.merge_or_upload_documents = AsyncMock(return_value=mock_result)
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await import_json_to_azure_search(temp_json_file, search_config)

        assert result == 2
        # Should be called once for single batch
        assert mock_client.merge_or_upload_documents.call_count == 1

    @pytest.mark.asyncio
    @patch('ingestor.json_importer.SearchClient')
    async def test_upload_multiple_batches(self, mock_client_class, search_config):
        """Test upload with documents requiring multiple batches."""
        # Create 2500 documents (will require 3 batches: 1000, 1000, 500)
        data = [
            {
                'id': f'doc-{i}',
                'content': f'Content {i}',
            }
            for i in range(2500)
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            def mock_upload(documents):
                return [Mock(succeeded=True) for _ in documents]

            mock_client = AsyncMock()
            mock_client.merge_or_upload_documents = AsyncMock(side_effect=mock_upload)
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await import_json_to_azure_search(temp_path, search_config)

            assert result == 2500
            # Should be called 3 times (3 batches)
            assert mock_client.merge_or_upload_documents.call_count == 3

            # Verify batch sizes
            calls = mock_client.merge_or_upload_documents.call_args_list
            assert len(calls[0][1]['documents']) == 1000
            assert len(calls[1][1]['documents']) == 1000
            assert len(calls[2][1]['documents']) == 500
        finally:
            Path(temp_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    @patch('ingestor.json_importer.SearchClient')
    async def test_upload_exactly_1000_documents(self, mock_client_class, search_config):
        """Test upload with exactly MAX_BATCH_SIZE documents."""
        data = [
            {
                'id': f'doc-{i}',
                'content': f'Content {i}',
            }
            for i in range(1000)
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            mock_result = [Mock(succeeded=True) for _ in range(1000)]
            mock_client = AsyncMock()
            mock_client.merge_or_upload_documents = AsyncMock(return_value=mock_result)
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await import_json_to_azure_search(temp_path, search_config)

            assert result == 1000
            # Should be exactly 1 batch
            assert mock_client.merge_or_upload_documents.call_count == 1
        finally:
            Path(temp_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    @patch('ingestor.json_importer.SearchClient')
    async def test_upload_1001_documents(self, mock_client_class, search_config):
        """Test upload with MAX_BATCH_SIZE + 1 documents."""
        data = [
            {
                'id': f'doc-{i}',
                'content': f'Content {i}',
            }
            for i in range(1001)
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            def mock_upload(documents):
                return [Mock(succeeded=True) for _ in documents]

            mock_client = AsyncMock()
            mock_client.merge_or_upload_documents = AsyncMock(side_effect=mock_upload)
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await import_json_to_azure_search(temp_path, search_config)

            assert result == 1001
            # Should be 2 batches: 1000 and 1
            assert mock_client.merge_or_upload_documents.call_count == 2

            calls = mock_client.merge_or_upload_documents.call_args_list
            assert len(calls[0][1]['documents']) == 1000
            assert len(calls[1][1]['documents']) == 1
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestUploadResults:
    """Tests for upload success/failure handling."""

    @pytest.mark.asyncio
    @patch('ingestor.json_importer.SearchClient')
    async def test_upload_all_succeed(self, mock_client_class, search_config, temp_json_file):
        """Test upload where all documents succeed."""
        mock_result = [Mock(succeeded=True) for _ in range(2)]
        mock_client = AsyncMock()
        mock_client.merge_or_upload_documents = AsyncMock(return_value=mock_result)
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await import_json_to_azure_search(temp_json_file, search_config)

        assert result == 2

    @pytest.mark.asyncio
    @patch('ingestor.json_importer.SearchClient')
    async def test_upload_partial_failure(self, mock_client_class, search_config):
        """Test upload where some documents fail."""
        data = [
            {'id': f'doc-{i}', 'content': f'Content {i}'}
            for i in range(10)
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            # 7 succeed, 3 fail
            mock_result = [Mock(succeeded=True) for _ in range(7)] + \
                         [Mock(succeeded=False, key=f'doc-{i}', error_message='Test error') for i in range(7, 10)]

            mock_client = AsyncMock()
            mock_client.merge_or_upload_documents = AsyncMock(return_value=mock_result)
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await import_json_to_azure_search(temp_path, search_config)

            # Should return count of successful uploads only
            assert result == 7
        finally:
            Path(temp_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    @patch('ingestor.json_importer.SearchClient')
    async def test_upload_all_fail(self, mock_client_class, search_config, temp_json_file):
        """Test upload where all documents fail."""
        mock_result = [
            Mock(succeeded=False, key=f'doc-{i}', error_message='Test error')
            for i in range(2)
        ]

        mock_client = AsyncMock()
        mock_client.merge_or_upload_documents = AsyncMock(return_value=mock_result)
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await import_json_to_azure_search(temp_json_file, search_config)

        assert result == 0


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    @patch('ingestor.json_importer.SearchClient')
    async def test_upload_exception(self, mock_client_class, search_config, temp_json_file):
        """Test exception during upload."""
        mock_client = AsyncMock()
        mock_client.merge_or_upload_documents = AsyncMock(
            side_effect=Exception('Upload failed')
        )
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client

        with pytest.raises(Exception, match='Upload failed'):
            await import_json_to_azure_search(temp_json_file, search_config)

        # Ensure client is closed even on exception
        mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    @patch('ingestor.json_importer.SearchClient')
    async def test_client_closed_on_success(self, mock_client_class, search_config, temp_json_file):
        """Test that client is properly closed on success."""
        mock_result = [Mock(succeeded=True) for _ in range(2)]
        mock_client = AsyncMock()
        mock_client.merge_or_upload_documents = AsyncMock(return_value=mock_result)
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client

        await import_json_to_azure_search(temp_json_file, search_config)

        mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_unicode_content(self, search_config):
        """Test handling of unicode content in JSON."""
        data = [
            {
                'id': 'doc1',
                'content': 'Content with unicode: 你好世界 🌍',
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
            temp_path = f.name

        try:
            with patch('ingestor.json_importer.SearchClient') as mock_client_class:
                mock_result = [Mock(succeeded=True)]
                mock_client = AsyncMock()
                mock_client.merge_or_upload_documents = AsyncMock(return_value=mock_result)
                mock_client.close = AsyncMock()
                mock_client_class.return_value = mock_client

                result = await import_json_to_azure_search(temp_path, search_config)

                assert result == 1
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestOptionalFields:
    """Tests for optional fields in documents."""

    @pytest.mark.asyncio
    @patch('ingestor.json_importer.SearchClient')
    async def test_upload_without_embeddings(self, mock_client_class, search_config):
        """Test upload of documents without embeddings field (for integrated vectorization)."""
        data = [
            {
                'id': 'doc1',
                'content': 'Content without embeddings',
                'filename': 'test.pdf',
                # No embeddings field
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            mock_result = [Mock(succeeded=True)]
            mock_client = AsyncMock()
            mock_client.merge_or_upload_documents = AsyncMock(return_value=mock_result)
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await import_json_to_azure_search(temp_path, search_config)

            assert result == 1
        finally:
            Path(temp_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    @patch('ingestor.json_importer.SearchClient')
    async def test_upload_with_extra_fields(self, mock_client_class, search_config):
        """Test upload of documents with extra custom fields."""
        data = [
            {
                'id': 'doc1',
                'content': 'Content',
                'custom_field_1': 'Custom value 1',
                'custom_field_2': 123,
                'custom_field_3': ['tag1', 'tag2'],
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            mock_result = [Mock(succeeded=True)]
            mock_client = AsyncMock()
            mock_client.merge_or_upload_documents = AsyncMock(return_value=mock_result)
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await import_json_to_azure_search(temp_path, search_config)

            assert result == 1

            # Verify extra fields were included in upload
            call_args = mock_client.merge_or_upload_documents.call_args
            uploaded_doc = call_args[1]['documents'][0]
            assert uploaded_doc['custom_field_1'] == 'Custom value 1'
            assert uploaded_doc['custom_field_2'] == 123
            assert uploaded_doc['custom_field_3'] == ['tag1', 'tag2']
        finally:
            Path(temp_path).unlink(missing_ok=True)
