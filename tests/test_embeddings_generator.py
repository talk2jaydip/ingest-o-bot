"""Unit tests for EmbeddingsGenerator class.

Tests cover:
- Initialization with AzureOpenAIConfig
- Token calculation with tiktoken
- Batch splitting logic (8100 tokens, 16 items max)
- Single embedding generation
- Batch embedding generation
- Dimensions for different models
- Error handling and retries
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ingestor.config import AzureOpenAIConfig
from ingestor.embeddings import EmbeddingsGenerator, EmbeddingBatch


@pytest.fixture
def azure_openai_config():
    """Create a test AzureOpenAIConfig."""
    return AzureOpenAIConfig(
        endpoint='https://test.openai.azure.com/',
        api_key='test-key',
        emb_deployment='text-embedding-ada-002',
        emb_model_name='text-embedding-ada-002',
        api_version='2023-05-15'
    )


@pytest.fixture
def azure_openai_config_3_small():
    """Create a test AzureOpenAIConfig for text-embedding-3-small."""
    return AzureOpenAIConfig(
        endpoint='https://test.openai.azure.com/',
        api_key='test-key',
        emb_deployment='text-embedding-3-small',
        emb_model_name='text-embedding-3-small',
        emb_dimensions=512,  # Custom dimensions
        api_version='2023-05-15'
    )


@pytest.fixture
def mock_openai_client():
    """Create a mock AsyncAzureOpenAI client."""
    mock_client = AsyncMock()
    mock_client.embeddings = AsyncMock()
    mock_client.close = AsyncMock()
    return mock_client


class TestEmbeddingsGeneratorInit:
    """Tests for EmbeddingsGenerator initialization."""

    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    def test_init_with_config(self, mock_client_class, azure_openai_config):
        """Test initialization with AzureOpenAIConfig."""
        generator = EmbeddingsGenerator(azure_openai_config)

        assert generator.config == azure_openai_config
        assert generator.deployment == 'text-embedding-ada-002'
        assert generator.model_name == 'text-embedding-ada-002'
        assert generator.dimensions is None
        assert generator.disable_batch is False
        assert generator.max_retries == 3
        mock_client_class.assert_called_once()

    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    def test_init_with_custom_dimensions(self, mock_client_class, azure_openai_config_3_small):
        """Test initialization with custom dimensions."""
        generator = EmbeddingsGenerator(azure_openai_config_3_small)

        assert generator.dimensions == 512

    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    def test_init_with_disable_batch(self, mock_client_class, azure_openai_config):
        """Test initialization with disable_batch=True."""
        generator = EmbeddingsGenerator(azure_openai_config, disable_batch=True)

        assert generator.disable_batch is True

    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    def test_init_with_custom_max_retries(self, mock_client_class, azure_openai_config):
        """Test initialization with custom max_retries."""
        generator = EmbeddingsGenerator(azure_openai_config, max_retries=5)

        assert generator.max_retries == 5


class TestTokenCalculation:
    """Tests for token counting functionality."""

    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    def test_calculate_token_length(self, mock_client_class, azure_openai_config):
        """Test token calculation for text."""
        generator = EmbeddingsGenerator(azure_openai_config)

        # Short text
        short_text = "Hello world"
        tokens = generator._calculate_token_length(short_text)
        assert tokens > 0
        assert tokens < 10

        # Longer text
        long_text = "This is a much longer text that should have more tokens " * 10
        long_tokens = generator._calculate_token_length(long_text)
        assert long_tokens > tokens

    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    def test_calculate_token_length_empty(self, mock_client_class, azure_openai_config):
        """Test token calculation for empty string."""
        generator = EmbeddingsGenerator(azure_openai_config)

        tokens = generator._calculate_token_length("")
        assert tokens == 0


class TestBatchSplitting:
    """Tests for batch splitting logic."""

    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    def test_split_text_single_batch(self, mock_client_class, azure_openai_config):
        """Test batch splitting with texts fitting in one batch."""
        generator = EmbeddingsGenerator(azure_openai_config)

        texts = ["Short text"] * 10
        batches = generator.split_text_into_batches(texts)

        assert len(batches) == 1
        assert len(batches[0].texts) == 10
        assert batches[0].token_length > 0

    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    def test_split_text_by_count(self, mock_client_class, azure_openai_config):
        """Test batch splitting when count limit (16) is reached."""
        generator = EmbeddingsGenerator(azure_openai_config)

        # Create 20 short texts (will hit 16-item limit before token limit)
        texts = ["Short text"] * 20
        batches = generator.split_text_into_batches(texts)

        # Should create 2 batches: 16 + 4
        assert len(batches) == 2
        assert len(batches[0].texts) == 16
        assert len(batches[1].texts) == 4

    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    def test_split_text_by_tokens(self, mock_client_class, azure_openai_config):
        """Test batch splitting when token limit (8100) is reached."""
        generator = EmbeddingsGenerator(azure_openai_config)

        # Create texts with many tokens (simulate 1000 tokens each)
        # Use repetitive text to approximate token count
        long_text = "word " * 200  # Approximately 200+ tokens
        texts = [long_text] * 50  # 50 texts * 200+ tokens = 10,000+ tokens

        batches = generator.split_text_into_batches(texts)

        # Should create multiple batches due to token limit
        assert len(batches) > 1

        # Each batch should have <= 16 items
        for batch in batches:
            assert len(batch.texts) <= 16

        # Each batch should have token_length calculated
        for batch in batches:
            assert batch.token_length > 0

    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    def test_split_text_empty_list(self, mock_client_class, azure_openai_config):
        """Test batch splitting with empty list."""
        generator = EmbeddingsGenerator(azure_openai_config)

        batches = generator.split_text_into_batches([])

        assert len(batches) == 0

    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    def test_split_text_single_item(self, mock_client_class, azure_openai_config):
        """Test batch splitting with single item."""
        generator = EmbeddingsGenerator(azure_openai_config)

        batches = generator.split_text_into_batches(["Single text"])

        assert len(batches) == 1
        assert len(batches[0].texts) == 1

    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    def test_split_text_unsupported_model(self, mock_client_class):
        """Test batch splitting with unsupported model (should create single-item batches)."""
        config = AzureOpenAIConfig(
            endpoint='https://test.openai.azure.com/',
            api_key='test-key',
            emb_deployment='unsupported-model',
            emb_model_name='unsupported-model'
        )
        generator = EmbeddingsGenerator(config)

        texts = ["Text 1", "Text 2", "Text 3"]
        batches = generator.split_text_into_batches(texts)

        # Should create single-item batches for unsupported models
        assert len(batches) == 3
        for batch in batches:
            assert len(batch.texts) == 1


class TestSingleEmbedding:
    """Tests for single embedding generation."""

    @pytest.mark.asyncio
    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    async def test_generate_embedding(self, mock_client_class, azure_openai_config):
        """Test single embedding generation."""
        # Mock the embeddings API response
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3] * 512)]  # 1536 dimensions

        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        generator = EmbeddingsGenerator(azure_openai_config)
        embedding = await generator.generate_embedding("Test text")

        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)
        mock_client.embeddings.create.assert_called_once()

    @pytest.mark.asyncio
    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    async def test_generate_embedding_with_dimensions(self, mock_client_class, azure_openai_config_3_small):
        """Test single embedding generation with custom dimensions."""
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2] * 256)]  # 512 dimensions

        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        generator = EmbeddingsGenerator(azure_openai_config_3_small)
        embedding = await generator.generate_embedding("Test text")

        assert len(embedding) == 512

        # Verify dimensions parameter was passed
        call_args = mock_client.embeddings.create.call_args
        assert call_args[1].get('dimensions') == 512

    @pytest.mark.asyncio
    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    async def test_generate_embedding_empty_text(self, mock_client_class, azure_openai_config):
        """Test single embedding generation with empty text."""
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.0] * 1536)]

        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        generator = EmbeddingsGenerator(azure_openai_config)
        embedding = await generator.generate_embedding("")

        assert len(embedding) == 1536


class TestBatchEmbeddings:
    """Tests for batch embedding generation."""

    @pytest.mark.asyncio
    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    async def test_generate_embeddings_batch(self, mock_client_class, azure_openai_config):
        """Test batch embedding generation."""
        texts = ["Text 1", "Text 2", "Text 3"]

        # Mock the embeddings API response
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1] * 1536),
            Mock(embedding=[0.2] * 1536),
            Mock(embedding=[0.3] * 1536)
        ]

        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        generator = EmbeddingsGenerator(azure_openai_config)
        embeddings = await generator.generate_embeddings_batch(texts)

        assert len(embeddings) == 3
        for emb in embeddings:
            assert len(emb) == 1536

    @pytest.mark.asyncio
    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    async def test_generate_embeddings_batch_empty_list(self, mock_client_class, azure_openai_config):
        """Test batch embedding generation with empty list."""
        generator = EmbeddingsGenerator(azure_openai_config)
        embeddings = await generator.generate_embeddings_batch([])

        assert embeddings == []

    @pytest.mark.asyncio
    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    async def test_generate_embeddings_batch_disabled(self, mock_client_class, azure_openai_config):
        """Test batch embedding generation with disable_batch=True."""
        texts = ["Text 1", "Text 2"]

        # Mock the single embedding API response
        def mock_create(**kwargs):
            mock_response = Mock()
            mock_response.data = [Mock(embedding=[0.1] * 1536)]
            return mock_response

        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(side_effect=mock_create)
        mock_client_class.return_value = mock_client

        generator = EmbeddingsGenerator(azure_openai_config, disable_batch=True)
        embeddings = await generator.generate_embeddings_batch(texts)

        assert len(embeddings) == 2
        # Should call the API twice (once per text)
        assert mock_client.embeddings.create.call_count == 2

    @pytest.mark.asyncio
    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    async def test_generate_embeddings_batch_large_input(self, mock_client_class, azure_openai_config):
        """Test batch embedding generation with > 16 texts."""
        texts = [f"Text {i}" for i in range(50)]

        # Mock the embeddings API response for each batch
        def mock_create(**kwargs):
            input_texts = kwargs.get('input', [])
            num_texts = len(input_texts) if isinstance(input_texts, list) else 1
            mock_response = Mock()
            mock_response.data = [Mock(embedding=[0.1] * 1536) for _ in range(num_texts)]
            return mock_response

        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(side_effect=mock_create)
        mock_client_class.return_value = mock_client

        generator = EmbeddingsGenerator(azure_openai_config)
        embeddings = await generator.generate_embeddings_batch(texts)

        assert len(embeddings) == 50
        # Should create multiple batches (50 texts / 16 max = 4 batches)
        assert mock_client.embeddings.create.call_count >= 3


class TestDimensions:
    """Tests for dimension calculation."""

    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    def test_get_dimensions_ada_002(self, mock_client_class):
        """Test dimensions for ada-002 model."""
        config = AzureOpenAIConfig(
            endpoint='https://test.openai.azure.com/',
            api_key='test-key',
            emb_deployment='text-embedding-ada-002',
            emb_model_name='text-embedding-ada-002'
        )
        generator = EmbeddingsGenerator(config)

        assert generator.get_dimensions() == 1536

    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    def test_get_dimensions_3_small_default(self, mock_client_class):
        """Test dimensions for 3-small model (default)."""
        config = AzureOpenAIConfig(
            endpoint='https://test.openai.azure.com/',
            api_key='test-key',
            emb_deployment='text-embedding-3-small',
            emb_model_name='text-embedding-3-small'
        )
        generator = EmbeddingsGenerator(config)

        assert generator.get_dimensions() == 1536

    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    def test_get_dimensions_3_small_custom(self, mock_client_class):
        """Test dimensions for 3-small model with custom dimensions."""
        config = AzureOpenAIConfig(
            endpoint='https://test.openai.azure.com/',
            api_key='test-key',
            emb_deployment='text-embedding-3-small',
            emb_model_name='text-embedding-3-small',
            emb_dimensions=512
        )
        generator = EmbeddingsGenerator(config)

        assert generator.get_dimensions() == 512

    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    def test_get_dimensions_3_large_default(self, mock_client_class):
        """Test dimensions for 3-large model (default)."""
        config = AzureOpenAIConfig(
            endpoint='https://test.openai.azure.com/',
            api_key='test-key',
            emb_deployment='text-embedding-3-large',
            emb_model_name='text-embedding-3-large'
        )
        generator = EmbeddingsGenerator(config)

        assert generator.get_dimensions() == 3072

    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    def test_get_model_name(self, mock_client_class, azure_openai_config):
        """Test get_model_name method."""
        generator = EmbeddingsGenerator(azure_openai_config)

        assert generator.get_model_name() == 'text-embedding-ada-002'


class TestErrorHandling:
    """Tests for error handling and retries."""

    @pytest.mark.asyncio
    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    async def test_generate_embedding_rate_limit_retry(self, mock_client_class, azure_openai_config):
        """Test retry logic for rate limit errors."""
        from openai import RateLimitError

        # First call raises RateLimitError, second succeeds
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]

        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(
            side_effect=[
                RateLimitError(response=Mock(status_code=429), body={}),
                mock_response
            ]
        )
        mock_client_class.return_value = mock_client

        generator = EmbeddingsGenerator(azure_openai_config, max_retries=3)

        # Should succeed after retry
        with patch('ingestor.embeddings.wait_random_exponential') as mock_wait:
            # Speed up the test by removing wait time
            mock_wait.return_value = lambda x: 0
            embedding = await generator.generate_embedding("Test text")

        assert len(embedding) == 1536
        # Should have been called twice (first failed, second succeeded)
        assert mock_client.embeddings.create.call_count == 2

    @pytest.mark.asyncio
    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    async def test_generate_embedding_max_retries_exceeded(self, mock_client_class, azure_openai_config):
        """Test failure after max retries exceeded."""
        from openai import RateLimitError
        from tenacity import RetryError

        # Always raise RateLimitError
        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(
            side_effect=RateLimitError(response=Mock(status_code=429), body={})
        )
        mock_client_class.return_value = mock_client

        generator = EmbeddingsGenerator(azure_openai_config, max_retries=2)

        # Should fail after max retries
        with pytest.raises((RateLimitError, RetryError)):
            with patch('ingestor.embeddings.wait_random_exponential') as mock_wait:
                mock_wait.return_value = lambda x: 0
                await generator.generate_embedding("Test text")


class TestClose:
    """Tests for resource cleanup."""

    @pytest.mark.asyncio
    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    async def test_close(self, mock_client_class, azure_openai_config):
        """Test close method."""
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        generator = EmbeddingsGenerator(azure_openai_config)
        await generator.close()

        mock_client.close.assert_called_once()


class TestDimensionsArgs:
    """Tests for dimensions argument handling."""

    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    def test_get_dimensions_args_ada_002(self, mock_client_class):
        """Test dimensions args for ada-002 (should return empty dict)."""
        config = AzureOpenAIConfig(
            endpoint='https://test.openai.azure.com/',
            api_key='test-key',
            emb_deployment='text-embedding-ada-002',
            emb_model_name='text-embedding-ada-002',
            emb_dimensions=1536
        )
        generator = EmbeddingsGenerator(config)

        args = generator._get_dimensions_args()
        # ada-002 doesn't support custom dimensions
        assert args == {}

    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    def test_get_dimensions_args_3_small(self, mock_client_class):
        """Test dimensions args for 3-small with custom dimensions."""
        config = AzureOpenAIConfig(
            endpoint='https://test.openai.azure.com/',
            api_key='test-key',
            emb_deployment='text-embedding-3-small',
            emb_model_name='text-embedding-3-small',
            emb_dimensions=512
        )
        generator = EmbeddingsGenerator(config)

        args = generator._get_dimensions_args()
        assert args == {'dimensions': 512}

    @patch('ingestor.embeddings.AsyncAzureOpenAI')
    def test_get_dimensions_args_3_small_no_custom(self, mock_client_class):
        """Test dimensions args for 3-small without custom dimensions."""
        config = AzureOpenAIConfig(
            endpoint='https://test.openai.azure.com/',
            api_key='test-key',
            emb_deployment='text-embedding-3-small',
            emb_model_name='text-embedding-3-small'
        )
        generator = EmbeddingsGenerator(config)

        args = generator._get_dimensions_args()
        # No custom dimensions specified
        assert args == {}
