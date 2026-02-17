"""Unit tests for SearchUploader class.

Tests cover:
- Initialization with SearchConfig
- Batch splitting (1000 documents per batch)
- Upload documents with/without embeddings
- Delete documents by filename
- Delete all documents
- Error handling and edge cases
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ingestor.config import SearchConfig
from ingestor.models import ChunkDocument, ChunkMetadata, DocumentMetadata, PageMetadata, ChunkArtifact
from ingestor.search_uploader import SearchUploader, MAX_BATCH_SIZE


@pytest.fixture
def search_config():
    """Create a test SearchConfig."""
    return SearchConfig(
        endpoint='https://test-service.search.windows.net',
        index_name='test-index',
        api_key='test-key'
    )


@pytest.fixture
def mock_chunk_doc():
    """Create a mock ChunkDocument."""
    return ChunkDocument(
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
            text='Test chunk text.',
            embedding=[0.1] * 1536
        ),
        chunk_artifact=ChunkArtifact(
            url='https://test.blob.core.windows.net/chunk1.json'
        ),
        tables=[],
        figures=[]
    )


@pytest.fixture
def mock_search_client():
    """Create a mock SearchClient."""
    mock_client = AsyncMock()
    mock_client.merge_or_upload_documents = AsyncMock()
    mock_client.search = AsyncMock()
    mock_client.delete_documents = AsyncMock()
    mock_client.close = AsyncMock()
    return mock_client


class TestSearchUploaderInit:
    """Tests for SearchUploader initialization."""

    @patch('ingestor.search_uploader.SearchClient')
    def test_init_with_config(self, mock_client_class, search_config):
        """Test initialization with SearchConfig."""
        uploader = SearchUploader(search_config)

        assert uploader.config == search_config
        assert uploader.max_batch_concurrency == 5
        mock_client_class.assert_called_once()

    @patch('ingestor.search_uploader.SearchClient')
    def test_init_with_custom_concurrency(self, mock_client_class, search_config):
        """Test initialization with custom max_batch_concurrency."""
        uploader = SearchUploader(search_config, max_batch_concurrency=10)

        assert uploader.max_batch_concurrency == 10


class TestSearchUploaderUpload:
    """Tests for document upload functionality."""

    @pytest.mark.asyncio
    @patch('ingestor.search_uploader.SearchClient')
    async def test_upload_empty_list(self, mock_client_class, search_config):
        """Test upload with empty document list."""
        uploader = SearchUploader(search_config)
        result = await uploader.upload_documents([])

        assert result == 0
        uploader.client.merge_or_upload_documents.assert_not_called()

    @pytest.mark.asyncio
    @patch('ingestor.search_uploader.SearchClient')
    async def test_upload_single_document(self, mock_client_class, search_config, mock_chunk_doc):
        """Test upload with a single document."""
        # Setup mock client
        mock_result = [Mock(succeeded=True, key='test-chunk-1')]
        mock_client_class.return_value.merge_or_upload_documents = AsyncMock(return_value=mock_result)

        uploader = SearchUploader(search_config)
        result = await uploader.upload_documents([mock_chunk_doc])

        assert result == 1
        uploader.client.merge_or_upload_documents.assert_called_once()

    @pytest.mark.asyncio
    @patch('ingestor.search_uploader.SearchClient')
    async def test_upload_without_embeddings(self, mock_client_class, search_config, mock_chunk_doc):
        """Test upload with include_embeddings=False."""
        mock_result = [Mock(succeeded=True, key='test-chunk-1')]
        mock_client_class.return_value.merge_or_upload_documents = AsyncMock(return_value=mock_result)

        uploader = SearchUploader(search_config)
        result = await uploader.upload_documents([mock_chunk_doc], include_embeddings=False)

        assert result == 1
        # Just verify the upload succeeded - the to_search_document handles embedding exclusion

    @pytest.mark.asyncio
    @patch('ingestor.search_uploader.SearchClient')
    async def test_upload_batch_splitting(self, mock_client_class, search_config, mock_chunk_doc):
        """Test batch splitting for documents > 1000."""
        # Create 2500 documents to test batch splitting
        num_docs = 2500
        chunk_docs = []
        for i in range(num_docs):
            doc = ChunkDocument(
                document=DocumentMetadata(
                    sourcefile='test.pdf',
                    storage_url='https://test.blob.core.windows.net/test.pdf'
                ),
                page=PageMetadata(
                    sourcepage=f'test.pdf#page={i}',
                    page_num=i
                ),
                chunk=ChunkMetadata(
                    chunk_id=f'test-chunk-{i}',
                    chunk_index_on_page=0,
                    text=f'Test chunk text {i}.',
                    embedding=[0.1] * 1536
                ),
                chunk_artifact=ChunkArtifact(
                    url=f'https://test.blob.core.windows.net/chunk{i}.json'
                ),
                tables=[],
                figures=[]
            )
            chunk_docs.append(doc)

        # Mock successful upload for each batch
        def mock_upload(documents):
            return [Mock(succeeded=True, key=doc['id']) for doc in documents]

        mock_client_class.return_value.merge_or_upload_documents = AsyncMock(side_effect=mock_upload)

        uploader = SearchUploader(search_config)
        result = await uploader.upload_documents(chunk_docs)

        # Should create 3 batches: 1000, 1000, 500
        assert result == num_docs
        assert uploader.client.merge_or_upload_documents.call_count == 3

        # Verify batch sizes
        calls = uploader.client.merge_or_upload_documents.call_args_list
        assert len(calls[0][1]['documents']) == 1000  # First batch
        assert len(calls[1][1]['documents']) == 1000  # Second batch
        assert len(calls[2][1]['documents']) == 500   # Third batch

    @pytest.mark.asyncio
    @patch('ingestor.search_uploader.SearchClient')
    async def test_upload_partial_failure(self, mock_client_class, search_config, mock_chunk_doc):
        """Test upload with some documents failing."""
        # Create 10 documents
        chunk_docs = [mock_chunk_doc] * 10

        # Mock 7 successful, 3 failed
        mock_result = [Mock(succeeded=True, key=f'chunk-{i}') for i in range(7)] + \
                      [Mock(succeeded=False, key=f'chunk-{i}', error_message='Test error') for i in range(7, 10)]
        mock_client_class.return_value.merge_or_upload_documents = AsyncMock(return_value=mock_result)

        uploader = SearchUploader(search_config)
        result = await uploader.upload_documents(chunk_docs)

        assert result == 7  # Only successful uploads counted

    @pytest.mark.asyncio
    @patch('ingestor.search_uploader.SearchClient')
    async def test_upload_exception_raised(self, mock_client_class, search_config, mock_chunk_doc):
        """Test upload with exception."""
        mock_client_class.return_value.merge_or_upload_documents = AsyncMock(
            side_effect=Exception('Test exception')
        )

        uploader = SearchUploader(search_config)

        with pytest.raises(Exception, match='Test exception'):
            await uploader.upload_documents([mock_chunk_doc])


class TestSearchUploaderDelete:
    """Tests for document deletion functionality."""

    @pytest.mark.asyncio
    @patch('ingestor.search_uploader.SearchClient')
    async def test_delete_by_filename_no_matches(self, mock_client_class, search_config):
        """Test delete_documents_by_filename with no matching documents."""
        # Mock search returning no results
        mock_search_result = AsyncMock()
        mock_search_result.get_count = AsyncMock(return_value=0)
        mock_search_result.__aiter__ = AsyncMock(return_value=iter([]))

        mock_client_class.return_value.search = AsyncMock(return_value=mock_search_result)

        uploader = SearchUploader(search_config)
        result = await uploader.delete_documents_by_filename('nonexistent.pdf')

        assert result == 0
        uploader.client.delete_documents.assert_not_called()

    @pytest.mark.asyncio
    @patch('ingestor.search_uploader.SearchClient')
    async def test_delete_by_filename_single_batch(self, mock_client_class, search_config):
        """Test delete_documents_by_filename with documents in single batch."""
        # Mock search returning 10 documents
        mock_docs = [{'id': f'test-chunk-{i}'} for i in range(10)]

        async def mock_search_iter(self):
            for doc in mock_docs:
                yield doc

        mock_search_result = AsyncMock()
        mock_search_result.get_count = AsyncMock(return_value=10)
        mock_search_result.__aiter__ = mock_search_iter

        mock_delete_result = [Mock(succeeded=True) for _ in range(10)]

        mock_client_class.return_value.search = AsyncMock(return_value=mock_search_result)
        mock_client_class.return_value.delete_documents = AsyncMock(return_value=mock_delete_result)

        uploader = SearchUploader(search_config)
        result = await uploader.delete_documents_by_filename('test.pdf')

        assert result == 10
        uploader.client.delete_documents.assert_called_once()

    @pytest.mark.asyncio
    @patch('ingestor.search_uploader.SearchClient')
    async def test_delete_by_filename_escapes_quotes(self, mock_client_class, search_config):
        """Test delete_documents_by_filename escapes single quotes in filename."""
        mock_search_result = AsyncMock()
        mock_search_result.get_count = AsyncMock(return_value=0)
        mock_search_result.__aiter__ = AsyncMock(return_value=iter([]))

        mock_client_class.return_value.search = AsyncMock(return_value=mock_search_result)

        uploader = SearchUploader(search_config)
        await uploader.delete_documents_by_filename("file's name.pdf")

        # Check that the filter properly escapes quotes
        call_args = uploader.client.search.call_args
        filter_arg = call_args[1]['filter']
        # Single quote should be escaped as two single quotes
        assert "file''s name" in filter_arg

    @pytest.mark.asyncio
    @patch('ingestor.search_uploader.SearchClient')
    @patch('asyncio.sleep', new_callable=AsyncMock)
    async def test_delete_by_filename_multiple_batches(self, mock_sleep, mock_client_class, search_config):
        """Test delete_documents_by_filename with > 1000 documents (multiple batches)."""
        # First call returns 1000 documents, second call returns 0
        mock_docs_batch1 = [{'id': f'test-chunk-{i}'} for i in range(1000)]

        call_count = 0

        async def mock_search_iter_batch1(self):
            for doc in mock_docs_batch1:
                yield doc

        async def mock_search_iter_empty(self):
            return
            yield  # Never reached

        def mock_search(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                mock_result = AsyncMock()
                mock_result.get_count = AsyncMock(return_value=1000)
                mock_result.__aiter__ = mock_search_iter_batch1
                return mock_result
            else:
                mock_result = AsyncMock()
                mock_result.get_count = AsyncMock(return_value=0)
                mock_result.__aiter__ = mock_search_iter_empty
                return mock_result

        mock_delete_result = [Mock(succeeded=True) for _ in range(1000)]

        mock_client_class.return_value.search = AsyncMock(side_effect=mock_search)
        mock_client_class.return_value.delete_documents = AsyncMock(return_value=mock_delete_result)

        uploader = SearchUploader(search_config)
        result = await uploader.delete_documents_by_filename('test.pdf')

        assert result == 1000
        assert uploader.client.delete_documents.call_count == 1
        # Should sleep between batches
        mock_sleep.assert_called()

    @pytest.mark.asyncio
    @patch('ingestor.search_uploader.SearchClient')
    async def test_delete_by_filename_exception(self, mock_client_class, search_config):
        """Test delete_documents_by_filename with exception."""
        mock_client_class.return_value.search = AsyncMock(
            side_effect=Exception('Test exception')
        )

        uploader = SearchUploader(search_config)

        with pytest.raises(Exception, match='Test exception'):
            await uploader.delete_documents_by_filename('test.pdf')

    @pytest.mark.asyncio
    @patch('ingestor.search_uploader.SearchClient')
    @patch('asyncio.sleep', new_callable=AsyncMock)
    async def test_delete_all_documents(self, mock_sleep, mock_client_class, search_config):
        """Test delete_all_documents."""
        # First call returns 100 documents, second call returns 0
        mock_docs = [{'id': f'test-chunk-{i}'} for i in range(100)]

        call_count = 0

        async def mock_search_iter_with_docs(self):
            for doc in mock_docs:
                yield doc

        async def mock_search_iter_empty(self):
            return
            yield  # Never reached

        def mock_search(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_result = AsyncMock()
            if call_count == 1:
                mock_result.__aiter__ = mock_search_iter_with_docs
            else:
                mock_result.__aiter__ = mock_search_iter_empty
            return mock_result

        mock_delete_result = [Mock(succeeded=True) for _ in range(100)]

        mock_client_class.return_value.search = AsyncMock(side_effect=mock_search)
        mock_client_class.return_value.delete_documents = AsyncMock(return_value=mock_delete_result)

        uploader = SearchUploader(search_config)
        result = await uploader.delete_all_documents()

        assert result == 100
        uploader.client.delete_documents.assert_called_once()


class TestSearchUploaderClose:
    """Tests for resource cleanup."""

    @pytest.mark.asyncio
    @patch('ingestor.search_uploader.SearchClient')
    async def test_close(self, mock_client_class, search_config):
        """Test close method."""
        mock_client = AsyncMock()
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client

        uploader = SearchUploader(search_config)
        await uploader.close()

        uploader.client.close.assert_called_once()


class TestSearchUploaderEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    @patch('ingestor.search_uploader.SearchClient')
    async def test_upload_exactly_1000_documents(self, mock_client_class, search_config, mock_chunk_doc):
        """Test upload with exactly MAX_BATCH_SIZE documents."""
        chunk_docs = [mock_chunk_doc] * 1000

        mock_result = [Mock(succeeded=True, key=f'chunk-{i}') for i in range(1000)]
        mock_client_class.return_value.merge_or_upload_documents = AsyncMock(return_value=mock_result)

        uploader = SearchUploader(search_config)
        result = await uploader.upload_documents(chunk_docs)

        assert result == 1000
        # Should be exactly 1 batch
        assert uploader.client.merge_or_upload_documents.call_count == 1

    @pytest.mark.asyncio
    @patch('ingestor.search_uploader.SearchClient')
    async def test_upload_1001_documents(self, mock_client_class, search_config, mock_chunk_doc):
        """Test upload with MAX_BATCH_SIZE + 1 documents."""
        chunk_docs = [mock_chunk_doc] * 1001

        def mock_upload(documents):
            return [Mock(succeeded=True, key=doc['id']) for doc in documents]

        mock_client_class.return_value.merge_or_upload_documents = AsyncMock(side_effect=mock_upload)

        uploader = SearchUploader(search_config)
        result = await uploader.upload_documents(chunk_docs)

        assert result == 1001
        # Should be 2 batches: 1000 and 1
        assert uploader.client.merge_or_upload_documents.call_count == 2

        calls = uploader.client.merge_or_upload_documents.call_args_list
        assert len(calls[0][1]['documents']) == 1000
        assert len(calls[1][1]['documents']) == 1
