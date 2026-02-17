"""Unit tests for IndexDeploymentManager class.

Tests cover:
- Initialization
- Index existence check
- Index creation with field configuration
- Vectorizer setup with/without OpenAI credentials
- Scoring profiles and semantic search configuration
- BM25 similarity configuration
- Error handling
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ingestor.index import IndexDeploymentManager


@pytest.fixture
def basic_manager_params():
    """Basic parameters for IndexDeploymentManager."""
    return {
        'endpoint': 'https://test-service.search.windows.net',
        'api_key': 'test-key',
        'index_name': 'test-index'
    }


@pytest.fixture
def manager_with_openai_params():
    """Parameters for IndexDeploymentManager with OpenAI credentials."""
    return {
        'endpoint': 'https://test-service.search.windows.net',
        'api_key': 'test-key',
        'index_name': 'test-index',
        'openai_endpoint': 'https://test.openai.azure.com/',
        'openai_deployment': 'text-embedding-ada-002',
        'openai_key': 'openai-test-key'
    }


class TestIndexDeploymentManagerInit:
    """Tests for IndexDeploymentManager initialization."""

    @patch('ingestor.index.SearchIndexClient')
    def test_init_basic(self, mock_client_class, basic_manager_params):
        """Test initialization with basic parameters."""
        manager = IndexDeploymentManager(**basic_manager_params)

        assert manager.endpoint == 'https://test-service.search.windows.net'
        assert manager.api_key == 'test-key'
        assert manager.index_name == 'test-index'
        assert manager.openai_endpoint is None
        assert manager.openai_deployment is None
        assert manager.openai_key is None
        assert manager.verbose is False
        mock_client_class.assert_called_once()

    @patch('ingestor.index.SearchIndexClient')
    def test_init_with_openai(self, mock_client_class, manager_with_openai_params):
        """Test initialization with OpenAI credentials."""
        manager = IndexDeploymentManager(**manager_with_openai_params)

        assert manager.openai_endpoint == 'https://test.openai.azure.com/'
        assert manager.openai_deployment == 'text-embedding-ada-002'
        assert manager.openai_key == 'openai-test-key'

    @patch('ingestor.index.SearchIndexClient')
    def test_init_with_verbose(self, mock_client_class, basic_manager_params):
        """Test initialization with verbose=True."""
        manager = IndexDeploymentManager(**basic_manager_params, verbose=True)

        assert manager.verbose is True

    @patch('ingestor.index.SearchIndexClient')
    @patch('os.makedirs')
    def test_init_creates_backup_dir(self, mock_makedirs, mock_client_class, basic_manager_params):
        """Test that initialization creates backup directory."""
        manager = IndexDeploymentManager(**basic_manager_params)

        assert manager.backup_dir == 'backups'
        mock_makedirs.assert_called_once_with('backups', exist_ok=True)


class TestIndexExists:
    """Tests for index_exists method."""

    @patch('ingestor.index.SearchIndexClient')
    def test_index_exists_true(self, mock_client_class, basic_manager_params):
        """Test index_exists returns True when index exists."""
        mock_client = Mock()
        mock_client.get_index = Mock(return_value=Mock())
        mock_client_class.return_value = mock_client

        manager = IndexDeploymentManager(**basic_manager_params)
        result = manager.index_exists()

        assert result is True
        mock_client.get_index.assert_called_once_with('test-index')

    @patch('ingestor.index.SearchIndexClient')
    def test_index_exists_false(self, mock_client_class, basic_manager_params):
        """Test index_exists returns False when index doesn't exist."""
        mock_client = Mock()
        mock_client.get_index = Mock(side_effect=Exception('Not found'))
        mock_client_class.return_value = mock_client

        manager = IndexDeploymentManager(**basic_manager_params)
        result = manager.index_exists()

        assert result is False


class TestCreateImprovedIndex:
    """Tests for create_improved_index method."""

    @patch('ingestor.index.SearchIndexClient')
    @patch('ingestor.index.HAVE_AZURE_OPENAI_VECTORIZER', False)
    def test_create_index_without_vectorizer(self, mock_client_class, basic_manager_params):
        """Test index creation without vectorizer."""
        manager = IndexDeploymentManager(**basic_manager_params)
        index = manager.create_improved_index()

        # Verify index properties
        assert index.name == 'test-index'
        assert len(index.fields) > 0

        # Check for required fields
        field_names = [field.name for field in index.fields]
        assert 'id' in field_names
        assert 'content' in field_names
        assert 'embeddings' in field_names
        assert 'filename' in field_names
        assert 'sourcefile' in field_names
        assert 'sourcepage' in field_names
        assert 'title' in field_names
        assert 'pageNumber' in field_names

        # Verify scoring profiles exist
        assert index.scoring_profiles is not None
        assert len(index.scoring_profiles) > 0
        profile_names = [p.name for p in index.scoring_profiles]
        assert 'contentRAGProfile' in profile_names

        # Verify semantic search configuration
        assert index.semantic_search is not None
        assert len(index.semantic_search.configurations) > 0

        # Verify vector search configuration
        assert index.vector_search is not None
        assert len(index.vector_search.algorithms) > 0
        assert len(index.vector_search.profiles) > 0
        assert len(index.vector_search.compressions) > 0

        # Verify BM25 similarity
        assert index.similarity is not None

    @patch('ingestor.index.SearchIndexClient')
    @patch('ingestor.index.HAVE_AZURE_OPENAI_VECTORIZER', True)
    @patch('ingestor.index.AzureOpenAIVectorizer')
    def test_create_index_with_vectorizer(self, mock_vectorizer_class, mock_client_class, manager_with_openai_params):
        """Test index creation with integrated vectorizer."""
        manager = IndexDeploymentManager(**manager_with_openai_params)
        index = manager.create_improved_index()

        # Verify vectorizer was created
        mock_vectorizer_class.assert_called_once()

        # Verify vectorizers list is not empty
        assert len(index.vector_search.vectorizers) > 0

    @patch('ingestor.index.SearchIndexClient')
    def test_create_index_field_configuration(self, mock_client_class, basic_manager_params):
        """Test that fields are configured correctly."""
        manager = IndexDeploymentManager(**basic_manager_params)
        index = manager.create_improved_index()

        # Find specific fields and check their properties
        id_field = next(f for f in index.fields if f.name == 'id')
        assert id_field.key is True

        content_field = next(f for f in index.fields if f.name == 'content')
        assert content_field.searchable is True

        embeddings_field = next(f for f in index.fields if f.name == 'embeddings')
        assert embeddings_field.searchable is True
        assert embeddings_field.vector_search_dimensions == 1536

        filename_field = next(f for f in index.fields if f.name == 'filename')
        assert filename_field.filterable is True
        assert filename_field.sortable is True
        assert filename_field.facetable is True

    @patch('ingestor.index.SearchIndexClient')
    def test_create_index_scoring_profile(self, mock_client_class, basic_manager_params):
        """Test scoring profile configuration."""
        manager = IndexDeploymentManager(**basic_manager_params)
        index = manager.create_improved_index()

        profile = next(p for p in index.scoring_profiles if p.name == 'contentRAGProfile')
        assert profile.text_weights is not None
        assert 'content' in profile.text_weights.weights
        assert 'title' in profile.text_weights.weights
        assert profile.text_weights.weights['content'] == 3.0

    @patch('ingestor.index.SearchIndexClient')
    def test_create_index_semantic_config(self, mock_client_class, basic_manager_params):
        """Test semantic search configuration."""
        manager = IndexDeploymentManager(**basic_manager_params)
        index = manager.create_improved_index()

        semantic_config = index.semantic_search.configurations[0]
        assert semantic_config.name == 'default-semantic-config'
        assert semantic_config.prioritized_fields.title_field is not None
        assert semantic_config.prioritized_fields.title_field.field_name == 'title'
        assert len(semantic_config.prioritized_fields.content_fields) > 0
        assert len(semantic_config.prioritized_fields.keywords_fields) > 0

    @patch('ingestor.index.SearchIndexClient')
    def test_create_index_vector_search(self, mock_client_class, basic_manager_params):
        """Test vector search configuration."""
        manager = IndexDeploymentManager(**basic_manager_params)
        index = manager.create_improved_index()

        # Verify HNSW algorithm
        assert len(index.vector_search.algorithms) > 0
        algorithm = index.vector_search.algorithms[0]
        assert algorithm.name == 'vector-config-optimized'

        # Verify vector search profile
        assert len(index.vector_search.profiles) > 0
        profile = index.vector_search.profiles[0]
        assert profile.name == 'vector-profile-optimized'

        # Verify compression
        assert len(index.vector_search.compressions) > 0
        compression = index.vector_search.compressions[0]
        assert compression.compression_name == 'scalar-quantization'

    @patch('ingestor.index.SearchIndexClient')
    def test_create_index_suggesters(self, mock_client_class, basic_manager_params):
        """Test suggester configuration."""
        manager = IndexDeploymentManager(**basic_manager_params)
        index = manager.create_improved_index()

        assert index.suggesters is not None
        assert len(index.suggesters) > 0
        suggester = index.suggesters[0]
        assert suggester.name == 'document-suggester'
        assert 'title' in suggester.source_fields
        assert 'filename' in suggester.source_fields


class TestDeleteIndex:
    """Tests for delete_index method."""

    @patch('ingestor.index.SearchIndexClient')
    def test_delete_index_success(self, mock_client_class, basic_manager_params):
        """Test successful index deletion."""
        mock_client = Mock()
        mock_client.delete_index = Mock()
        mock_client_class.return_value = mock_client

        manager = IndexDeploymentManager(**basic_manager_params)
        result = manager.delete_index()

        assert result is True
        mock_client.delete_index.assert_called_once_with('test-index')

    @patch('ingestor.index.SearchIndexClient')
    def test_delete_index_not_found(self, mock_client_class, basic_manager_params):
        """Test deleting non-existent index (should return True)."""
        from azure.core.exceptions import ResourceNotFoundError

        mock_client = Mock()
        mock_client.delete_index = Mock(side_effect=ResourceNotFoundError('Not found'))
        mock_client_class.return_value = mock_client

        manager = IndexDeploymentManager(**basic_manager_params)
        result = manager.delete_index()

        assert result is True  # Not an error if index doesn't exist

    @patch('ingestor.index.SearchIndexClient')
    def test_delete_index_error(self, mock_client_class, basic_manager_params):
        """Test index deletion with error."""
        mock_client = Mock()
        mock_client.delete_index = Mock(side_effect=Exception('Test error'))
        mock_client_class.return_value = mock_client

        manager = IndexDeploymentManager(**basic_manager_params)
        result = manager.delete_index()

        assert result is False


class TestBackupIndex:
    """Tests for backup_current_index method."""

    @patch('ingestor.index.SearchIndexClient')
    @patch('builtins.open', create=True)
    @patch('json.dump')
    def test_backup_index_success(self, mock_json_dump, mock_open, mock_client_class, basic_manager_params):
        """Test successful index backup."""
        mock_index = Mock()
        mock_index.name = 'test-index'
        mock_index.fields = [Mock()] * 10
        mock_index.scoring_profiles = [Mock()] * 2

        mock_client = Mock()
        mock_client.get_index = Mock(return_value=mock_index)
        mock_client_class.return_value = mock_client

        manager = IndexDeploymentManager(**basic_manager_params)
        backup_path = manager.backup_current_index()

        assert backup_path is not None
        assert 'test-index_backup_' in backup_path
        mock_client.get_index.assert_called_once_with('test-index')

    @patch('ingestor.index.SearchIndexClient')
    def test_backup_index_not_found(self, mock_client_class, basic_manager_params):
        """Test backup of non-existent index."""
        from azure.core.exceptions import ResourceNotFoundError

        mock_client = Mock()
        mock_client.get_index = Mock(side_effect=ResourceNotFoundError('Not found'))
        mock_client_class.return_value = mock_client

        manager = IndexDeploymentManager(**basic_manager_params)
        backup_path = manager.backup_current_index()

        assert backup_path is None


class TestValidateIndex:
    """Tests for validate_index method."""

    @patch('ingestor.index.SearchIndexClient')
    def test_validate_index_success(self, mock_client_class, basic_manager_params):
        """Test successful index validation."""
        # Create a mock index with all required configurations
        mock_index = Mock()
        mock_index.name = 'test-index'

        # Mock scoring profiles
        mock_profile = Mock()
        mock_profile.name = 'contentRAGProfile'
        mock_index.scoring_profiles = [mock_profile]

        # Mock BM25 similarity
        mock_similarity = Mock()
        mock_similarity.__class__.__name__ = 'BM25SimilarityAlgorithm'
        mock_index.similarity = mock_similarity

        # Mock semantic search
        mock_semantic_field = Mock()
        mock_semantic_field.field_name = 'title'
        mock_prioritized_fields = Mock()
        mock_prioritized_fields.title_field = mock_semantic_field
        mock_semantic_config = Mock()
        mock_semantic_config.prioritized_fields = mock_prioritized_fields
        mock_semantic_search = Mock()
        mock_semantic_search.configurations = [mock_semantic_config]
        mock_index.semantic_search = mock_semantic_search

        # Mock suggesters
        mock_index.suggesters = [Mock()]

        # Mock vector search
        mock_vector_search = Mock()
        mock_vector_search.compressions = [Mock()]
        mock_vector_search.algorithms = [Mock()]
        mock_index.vector_search = mock_vector_search

        mock_client = Mock()
        mock_client.get_index = Mock(return_value=mock_index)
        mock_client_class.return_value = mock_client

        manager = IndexDeploymentManager(**basic_manager_params)
        result = manager.validate_index()

        assert result is True

    @patch('ingestor.index.SearchIndexClient')
    def test_validate_index_missing_scoring_profile(self, mock_client_class, basic_manager_params):
        """Test validation with missing scoring profile."""
        mock_index = Mock()
        mock_index.scoring_profiles = []
        mock_index.similarity = Mock()
        mock_index.semantic_search = Mock()
        mock_index.semantic_search.configurations = []
        mock_index.suggesters = []
        mock_index.vector_search = Mock()
        mock_index.vector_search.compressions = []
        mock_index.vector_search.algorithms = []

        mock_client = Mock()
        mock_client.get_index = Mock(return_value=mock_index)
        mock_client_class.return_value = mock_client

        manager = IndexDeploymentManager(**basic_manager_params)
        result = manager.validate_index()

        assert result is False

    @patch('ingestor.index.SearchIndexClient')
    def test_validate_index_exception(self, mock_client_class, basic_manager_params):
        """Test validation with exception."""
        mock_client = Mock()
        mock_client.get_index = Mock(side_effect=Exception('Test error'))
        mock_client_class.return_value = mock_client

        manager = IndexDeploymentManager(**basic_manager_params)
        result = manager.validate_index()

        assert result is False


class TestDeployIndex:
    """Tests for deploy_index method."""

    @patch('ingestor.index.SearchIndexClient')
    def test_deploy_index_new(self, mock_client_class, basic_manager_params):
        """Test deploying a new index."""
        mock_client = Mock()
        mock_client.get_index = Mock(side_effect=Exception('Not found'))
        mock_client.create_or_update_index = Mock(return_value=Mock(
            name='test-index',
            fields=[Mock()] * 10,
            scoring_profiles=[Mock()],
            suggesters=[Mock()]
        ))
        mock_client_class.return_value = mock_client

        manager = IndexDeploymentManager(**basic_manager_params)

        # Mock validate_index to return True
        with patch.object(manager, 'validate_index', return_value=True):
            result = manager.deploy_index(dry_run=False)

        assert result is True
        mock_client.create_or_update_index.assert_called_once()

    @patch('ingestor.index.SearchIndexClient')
    def test_deploy_index_dry_run(self, mock_client_class, basic_manager_params):
        """Test dry run mode."""
        mock_client = Mock()
        mock_client.get_index = Mock(side_effect=Exception('Not found'))
        mock_client_class.return_value = mock_client

        manager = IndexDeploymentManager(**basic_manager_params)
        result = manager.deploy_index(dry_run=True)

        assert result is True
        # Should not call create_or_update_index in dry run
        mock_client.create_or_update_index.assert_not_called()

    @patch('ingestor.index.SearchIndexClient')
    def test_deploy_index_exists_no_force(self, mock_client_class, basic_manager_params):
        """Test deploying when index exists without force flag."""
        mock_client = Mock()
        mock_client.get_index = Mock(return_value=Mock())
        mock_client_class.return_value = mock_client

        manager = IndexDeploymentManager(**basic_manager_params)
        result = manager.deploy_index(dry_run=False, force=False)

        assert result is False

    @patch('ingestor.index.SearchIndexClient')
    @patch('builtins.open', create=True)
    @patch('json.dump')
    def test_deploy_index_exists_with_force(self, mock_json_dump, mock_open, mock_client_class, basic_manager_params):
        """Test deploying when index exists with force flag."""
        mock_existing_index = Mock()
        mock_existing_index.name = 'test-index'
        mock_existing_index.fields = [Mock()] * 8
        mock_existing_index.scoring_profiles = []

        mock_new_index = Mock()
        mock_new_index.name = 'test-index'
        mock_new_index.fields = [Mock()] * 10
        mock_new_index.scoring_profiles = [Mock()]
        mock_new_index.suggesters = [Mock()]

        mock_client = Mock()
        mock_client.get_index = Mock(return_value=mock_existing_index)
        mock_client.delete_index = Mock()
        mock_client.create_or_update_index = Mock(return_value=mock_new_index)
        mock_client_class.return_value = mock_client

        manager = IndexDeploymentManager(**basic_manager_params)

        # Mock validate_index to return True
        with patch.object(manager, 'validate_index', return_value=True):
            result = manager.deploy_index(dry_run=False, force=True)

        assert result is True
        mock_client.delete_index.assert_called_once()
        mock_client.create_or_update_index.assert_called_once()


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    @patch('ingestor.index.SearchIndexClient')
    def test_index_name_with_special_chars(self, mock_client_class):
        """Test initialization with special characters in index name."""
        manager = IndexDeploymentManager(
            endpoint='https://test-service.search.windows.net',
            api_key='test-key',
            index_name='test-index-123_abc'
        )

        assert manager.index_name == 'test-index-123_abc'

    @patch('ingestor.index.SearchIndexClient')
    @patch('ingestor.index.HAVE_AZURE_OPENAI_VECTORIZER', False)
    def test_create_index_without_vectorizer_sdk_support(self, mock_client_class, manager_with_openai_params):
        """Test index creation when SDK doesn't support vectorizer."""
        manager = IndexDeploymentManager(**manager_with_openai_params)
        index = manager.create_improved_index()

        # Should create index without vectorizer
        assert index.vector_search.vectorizers == []

    @patch('ingestor.index.SearchIndexClient')
    def test_create_index_partial_openai_config(self, mock_client_class):
        """Test index creation with partial OpenAI configuration."""
        manager = IndexDeploymentManager(
            endpoint='https://test-service.search.windows.net',
            api_key='test-key',
            index_name='test-index',
            openai_endpoint='https://test.openai.azure.com/',
            # Missing openai_deployment and openai_key
        )
        index = manager.create_improved_index()

        # Should create index without vectorizer
        assert len(index.vector_search.vectorizers) == 0
