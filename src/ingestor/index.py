"""
Azure AI Search Index Improvement Deployment Script

This script deploys the improved index configuration to Azure AI Search.
It includes safety checks, backup, and rollback capabilities.

Usage:
    python deploy_index_improvements.py --mode [backup|deploy|validate]
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Any, Optional

# Fix Windows console encoding for emoji support
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Simple config management - all config passed via constructor parameters
# No config_helper needed - cli.py uses PipelineConfig to load from environment

from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    ScoringProfile,
    TextWeights,
    FreshnessScoringFunction,
    FreshnessScoringParameters,
    MagnitudeScoringFunction,
    MagnitudeScoringParameters,
    ScoringFunctionAggregation,
    ScoringFunctionInterpolation,
    SearchSuggester,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    HnswParameters,
    VectorSearchAlgorithmMetric,
    VectorSearchCompression,
    ScalarQuantizationCompression,
    ScalarQuantizationParameters,
    RescoringOptions,
    VectorSearchCompressionRescoreStorageMethod,
    SemanticSearch,
    PatternAnalyzer,
    BM25SimilarityAlgorithm
)
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError

# Try to import vectorizer support (added in newer SDK versions)
HAVE_AZURE_OPENAI_VECTORIZER = True
try:
    from azure.search.documents.indexes.models import (
        AzureOpenAIVectorizer,
        AzureOpenAIVectorizerParameters,
    )
except Exception:
    HAVE_AZURE_OPENAI_VECTORIZER = False


class IndexDeploymentManager:
    """Manages the deployment of index improvements"""

    def __init__(self, endpoint: str, api_key: str, index_name: str,
                 openai_endpoint: str = None, openai_deployment: str = None, openai_key: str = None,
                 verbose: bool = False):
        self.endpoint = endpoint
        self.api_key = api_key
        self.index_name = index_name
        self.openai_endpoint = openai_endpoint
        self.openai_deployment = openai_deployment
        self.openai_key = openai_key
        self.verbose = verbose
        self.client = SearchIndexClient(endpoint, AzureKeyCredential(api_key))
        self.backup_dir = "backups"
        os.makedirs(self.backup_dir, exist_ok=True)

    def backup_current_index(self) -> str:
        """Backup the current index configuration"""
        print(f"📦 Backing up current index: {self.index_name}")

        try:
            current_index = self.client.get_index(self.index_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{self.backup_dir}/{self.index_name}_backup_{timestamp}.json"

            # Convert index to dict
            index_dict = {
                "name": current_index.name,
                "fields": [self._field_to_dict(f) for f in current_index.fields],
                "scoring_profiles": [self._scoring_profile_to_dict(sp) for sp in (current_index.scoring_profiles or [])],
                "suggesters": [self._suggester_to_dict(s) for s in (current_index.suggesters or [])],
                "analyzers": [self._analyzer_to_dict(a) for a in (current_index.analyzers or [])],
                "semantic_search": self._semantic_to_dict(current_index.semantic_search) if current_index.semantic_search else None,
                "vector_search": self._vector_search_to_dict(current_index.vector_search) if current_index.vector_search else None
            }

            with open(backup_filename, 'w', encoding='utf-8') as f:
                json.dump(index_dict, f, indent=2, ensure_ascii=False)

            print(f"✅ Backup saved to: {backup_filename}")
            return backup_filename

        except ResourceNotFoundError:
            print(f"ℹ️  Index '{self.index_name}' does not exist - skipping backup")
            return None
        except Exception as e:
            print(f"❌ Backup failed: {str(e)}")
            raise

    def _field_to_dict(self, field) -> Dict:
        """Convert SearchField to dictionary"""
        return {
            "name": getattr(field, 'name', None),
            "type": str(getattr(field, 'type', None)),
            "searchable": getattr(field, 'searchable', None),
            "filterable": getattr(field, 'filterable', None),
            "sortable": getattr(field, 'sortable', None),
            "facetable": getattr(field, 'facetable', None),
            "key": getattr(field, 'key', None),
            "retrievable": getattr(field, 'retrievable', None),
            "analyzer": getattr(field, 'analyzer_name', None),
            "vector_search_profile": getattr(field, 'vector_search_profile_name', None),
            "dimensions": getattr(field, 'vector_search_dimensions', None)
        }

    def _scoring_profile_to_dict(self, sp) -> Dict:
        """Convert ScoringProfile to dictionary"""
        return {"name": sp.name}

    def _suggester_to_dict(self, s) -> Dict:
        """Convert SearchSuggester to dictionary"""
        return {"name": s.name, "source_fields": s.source_fields}

    def _analyzer_to_dict(self, a) -> Dict:
        """Convert Analyzer to dictionary"""
        return {"name": a.name}

    def _semantic_to_dict(self, semantic) -> Optional[Dict]:
        """Convert SemanticSearch to dictionary"""
        if not semantic or not semantic.configurations:
            return None
        return {
            "configurations": [
                {
                    "name": config.name,
                    "prioritized_fields": {
                        "title_field": config.prioritized_fields.title_field.field_name if config.prioritized_fields.title_field else None,
                        "content_fields": [f.field_name for f in (config.prioritized_fields.content_fields or [])],
                        "keyword_fields": [f.field_name for f in (config.prioritized_fields.keywords_fields or [])]
                    }
                }
                for config in semantic.configurations
            ]
        }

    def _vector_search_to_dict(self, vector_search) -> Optional[Dict]:
        """Convert VectorSearch to dictionary"""
        if not vector_search:
            return None
        return {"profiles": [p.name for p in (vector_search.profiles or [])]}

    def create_improved_index(self) -> SearchIndex:
        """Create the improved index configuration"""
        print(f"🔧 Creating improved index configuration")

        # Define fields
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
            SearchableField(
                name="content",
                type=SearchFieldDataType.String,
                analyzer_name="en.microsoft",
                searchable=True
            ),
            SearchField(
                name="embeddings",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                hidden=False,  # Make embeddings retrievable for debugging/inspection
                vector_search_dimensions=1536,
                vector_search_profile_name="vector-profile-optimized"
            ),
            SearchableField(
                name="filename",
                type=SearchFieldDataType.String,
                filterable=True,
                sortable=True,
                facetable=True,
                analyzer_name="keyword"
            ),
            SimpleField(
                name="url",
                type=SearchFieldDataType.String,
                filterable=True,
                sortable=True
            ),
            SearchableField(
                name="country",
                type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                filterable=True,
                facetable=True,
                analyzer_name="keyword"
            ),
            SearchableField(
                name="language",
                type=SearchFieldDataType.String,
                filterable=True,
                sortable=True,
                facetable=True,
                analyzer_name="keyword"
            ),
            SearchableField(
                name="product_family",
                type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                filterable=True,
                facetable=True,
                analyzer_name="en.microsoft"
            ),
            SearchableField(
                name="productTradeNames",
                type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                filterable=True,
                facetable=True,
                analyzer_name="standard.lucene"  # Allow partial matching (e.g., "pacemaker" matches without hyphens)
            ),
            SearchableField(
                name="prod_from_url",
                type=SearchFieldDataType.String,
                filterable=True,
                sortable=True,
                facetable=True,
                analyzer_name="keyword"
            ),
            SearchableField(
                name="title",
                type=SearchFieldDataType.String,
                filterable=True,
                sortable=True,
                analyzer_name="standard.lucene"  # Tokenized without stemming for page headers
            ),
            SearchableField(
                name="literatureType",
                type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                filterable=True,
                facetable=True,
                analyzer_name="keyword"
            ),
            SearchableField(
                name="partNumber",
                type=SearchFieldDataType.String,
                filterable=True,
                sortable=True,
                analyzer_name="keyword"
            ),
            SearchableField(
                name="applicableTo",
                type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                filterable=True,
                facetable=True,
                analyzer_name="en.microsoft"
            ),
            SearchableField(
                name="model",
                type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                filterable=True,
                facetable=True,
                analyzer_name="keyword"
            ),
            SimpleField(
                name="publishedDate",
                type=SearchFieldDataType.DateTimeOffset,
                filterable=True,
                sortable=True,
                facetable=True
            ),
            SimpleField(
                name="pageNumber",
                type=SearchFieldDataType.Int32,
                filterable=True,
                sortable=True
            ),
            # Additional document metadata fields
            SearchableField(
                name="category",
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=True,
                sortable=True,
                facetable=True,
                analyzer_name="en.microsoft"
            ),
            SearchableField(
                name="sourcepage",
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=True,
                sortable=True,
                facetable=False,
                analyzer_name="keyword"
            ),
            SearchableField(
                name="sourcefile",
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=True,
                sortable=True,
                facetable=False,
                analyzer_name="keyword"
            ),
            SimpleField(
                name="storageUrl",
                type=SearchFieldDataType.String,
                searchable=False,
                filterable=False,
                sortable=False,
                facetable=False
            ),
            # Visual content indicators (MINIMAL - essential for UI only)
            # Figure images: Need blob URLs for <img> display
            # Tables: Content already in chunk text, just flag for filtering
            SimpleField(
                name="has_figures",
                type=SearchFieldDataType.Boolean,
                filterable=True,
                facetable=True,
                retrievable=True
            ),
            SearchField(
                name="figure_urls",
                type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                searchable=False,
                retrievable=True
            ),
            SimpleField(
                name="has_tables",
                type=SearchFieldDataType.Boolean,
                filterable=True,
                facetable=True,
                retrievable=True
            )
        ]

        # Create scoring profiles
        scoring_profiles = [
            # Profile 1: Product-focused scoring (existing)
            ScoringProfile(
                name="productBoostingProfile",
                text_weights=TextWeights(
                    weights={
                        "title": 3.0,
                        "productTradeNames": 2.5,
                        "product_family": 2.0,
                        "partNumber": 2.5,
                        "model": 2.0,
                        "content": 1.0,
                        "filename": 1.5,
                        "applicableTo": 1.8
                    }
                ),
                functions=[
                    FreshnessScoringFunction(
                        field_name="publishedDate",
                        boost=2.0,
                        parameters=FreshnessScoringParameters(boosting_duration="P365D"),
                        interpolation=ScoringFunctionInterpolation.LINEAR
                    )
                ],
                function_aggregation=ScoringFunctionAggregation.SUM
            ),
            # Profile 2: Content-focused for general RAG queries
            ScoringProfile(
                name="contentRAGProfile",
                text_weights=TextWeights(
                    weights={
                        "content": 3.0,         # Primary focus on content
                        "title": 2.5,           # Page headers important
                        "applicableTo": 2.0,    # Context matters
                        "productTradeNames": 1.5,
                        "product_family": 1.5,
                        "category": 1.2,
                        "filename": 1.0
                    }
                ),
                functions=[
                    FreshnessScoringFunction(
                        field_name="publishedDate",
                        boost=1.5,  # Slightly lower boost than product profile
                        parameters=FreshnessScoringParameters(boosting_duration="P365D"),
                        interpolation=ScoringFunctionInterpolation.LINEAR
                    )
                ],
                function_aggregation=ScoringFunctionAggregation.SUM
            )
        ]

        # Create suggester for autocomplete functionality
        # Note: Suggesters only support default analyzer and language analyzers
        # Removed fields with keyword analyzer (productTradeNames, partNumber)
        suggesters = [
            SearchSuggester(
                name="product-suggester",
                source_fields=["title", "product_family"]
            )
        ]

        # Create semantic configuration with enhanced content fields
        semantic_config = SemanticConfiguration(
            name="default-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="title"),
                content_fields=[
                    SemanticField(field_name="content"),
                    SemanticField(field_name="applicableTo"),  # Additional context for semantic ranking
                ],
                keywords_fields=[
                    SemanticField(field_name="productTradeNames"),
                    SemanticField(field_name="product_family"),
                    SemanticField(field_name="partNumber"),
                    SemanticField(field_name="model"),
                    SemanticField(field_name="category")  # Added for better semantic understanding
                ]
            )
        )

        semantic_search = SemanticSearch(configurations=[semantic_config])

        # Create vectorizer if OpenAI credentials provided and SDK supports it
        vectorizer = None
        profile_vectorizer = None

        if self.openai_endpoint and self.openai_deployment and HAVE_AZURE_OPENAI_VECTORIZER:
            vectorizer_name = f"vectorizer-{self.index_name}"

            vectorizer = AzureOpenAIVectorizer(
                vectorizer_name=vectorizer_name,
                parameters=AzureOpenAIVectorizerParameters(
                    resource_url=self.openai_endpoint,
                    deployment_name=self.openai_deployment,
                    api_key=self.openai_key,
                    model_name="text-embedding-ada-002"
                )
            )

            profile_vectorizer = vectorizer_name
            print(f"   ✅ Integrated vectorizer configured: {vectorizer_name}")
        else:
            # SDK doesn't support the integrated AzureOpenAIVectorizer or
            # the OpenAI settings are missing — proceed without an
            # integrated vectorizer. The index will still be created but
            # without the integrated vectorizer profile.
            if self.openai_endpoint and self.openai_deployment and not HAVE_AZURE_OPENAI_VECTORIZER:
                print(f"   ⚠️  SDK does not provide AzureOpenAIVectorizer; skipping integrated vectorizer")
            else:
                print(f"   ℹ️  No OpenAI credentials provided; skipping integrated vectorizer")

        # Create vector search configuration
        algorithm_name = "vector-config-optimized"

        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name=algorithm_name,
                    parameters=HnswParameters(
                        metric=VectorSearchAlgorithmMetric.COSINE,
                        m=16,              # Increased from 8 for better recall
                        ef_construction=400,  # Reduced from 600 for faster indexing
                        ef_search=500      # Balanced from 800 for speed/accuracy
                    )
                )
            ],
            profiles=[
                VectorSearchProfile(
                    name="vector-profile-optimized",
                    algorithm_configuration_name=algorithm_name,
                    vectorizer_name=profile_vectorizer,
                    compression_name="scalar-quantization"
                )
            ],
            vectorizers=[vectorizer] if vectorizer else [],
            compressions=[
                ScalarQuantizationCompression(
                    compression_name="scalar-quantization",
                    rescoring_options=RescoringOptions(
                        enable_rescoring=True,
                        default_oversampling=20.0,  # Increased from 10.0 for better recall with int8
                        rescore_storage_method=VectorSearchCompressionRescoreStorageMethod.PRESERVE_ORIGINALS
                    ),
                    parameters=ScalarQuantizationParameters(
                        quantized_data_type="int8"
                    )
                )
            ]
        )

        # Configure BM25 similarity for better technical/medical document ranking
        # k1=1.5: Boost term frequency importance for repeated technical terms
        # b=0.5: Reduce document length penalty (long manuals shouldn't be penalized)
        similarity = BM25SimilarityAlgorithm(k1=1.5, b=0.5)
        print(f"   ✅ BM25 similarity configured (k1=1.5, b=0.5)")

        # Create the index
        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            scoring_profiles=scoring_profiles,
            suggesters=suggesters,
            semantic_search=semantic_search,
            vector_search=vector_search,
            similarity=similarity
        )

        print(f"✅ Improved index configuration created")
        return index

    def index_exists(self) -> bool:
        """Check if index exists"""
        try:
            self.client.get_index(self.index_name)
            return True
        except Exception:
            return False

    def delete_index(self) -> bool:
        """Delete the index"""
        try:
            if self.verbose:
                print(f"\n[WARNING] Deleting existing index '{self.index_name}'...")

            self.client.delete_index(self.index_name)

            if self.verbose:
                print(f"[OK] Index deleted")

            return True
        except ResourceNotFoundError:
            print(f"ℹ️  Index '{self.index_name}' does not exist")
            return True  # Not an error if index doesn't exist
        except Exception as e:
            print(f"❌ Failed to delete index: {str(e)}")
            return False

    def deploy_index(self, dry_run: bool = False, force: bool = False, skip_if_exists: bool = True) -> bool:
        """Deploy the improved index

        Args:
            dry_run: If True, only show what would be done
            force: If True, delete and recreate existing index
            skip_if_exists: If True, treat existing index as success (default for --setup-index)
                           If False, treat existing index as failure (old behavior)
        """
        print(f"\n{'🔍 DRY RUN MODE' if dry_run else '🚀 DEPLOYMENT MODE'}")
        print(f"{'='*60}")

        try:
            # Check if index exists
            exists = self.index_exists()

            if exists:
                if self.verbose:
                    print(f"[INFO] Index '{self.index_name}' already exists")

                if not force:
                    if skip_if_exists:
                        # Graceful: Index exists, just acknowledge it
                        print(f"\n✓ Index '{self.index_name}' already exists.")
                        print(f"   No changes needed. Index is ready for ingestion.")
                        print(f"   Use --force-index to delete and recreate (WARNING: destroys all data)")
                        return True
                    else:
                        # Old behavior: Treat as failure
                        print(f"\n⚠️  Index '{self.index_name}' already exists.")
                        print(f"    Use --force to delete and recreate with improvements.")
                        print(f"    WARNING: --force will destroy all data in the index!")
                        return False

                # Step 1: Backup before deleting
                backup_file = self.backup_current_index()

                # Step 2: Delete existing index
                if not dry_run:
                    if not self.delete_index():
                        return False
                else:
                    print(f"[DRY RUN] Would delete existing index")
            else:
                if self.verbose:
                    print(f"[INFO] Index '{self.index_name}' does not exist")
                backup_file = None

            # Step 3: Create improved index
            improved_index = self.create_improved_index()

            if dry_run:
                print("\n✅ Dry run completed successfully!")
                print(f"📋 Changes that would be applied:")
                if exists and force:
                    print(f"   - Delete existing index '{self.index_name}'")
                print(f"   - Scoring profiles: 2 (productBoostingProfile, semanticBoostingProfile)")
                print(f"   - Suggester: 1 (product-suggester)")
                print(f"   - Semantic config: Fixed title field")
                print(f"   - Vector search: Optimized HNSW + compression")
                print(f"   - Analyzers: Updated for better matching")
                print(f"   - Faceting: Enabled on key fields")
                print(f"\n⚠️  Run without --dry-run to apply changes")
                return True

            # Step 4: Apply changes
            if self.verbose:
                print(f"\n[INFO] Applying index improvements...")
            else:
                print(f"\n🔄 Applying index improvements...")

            result = self.client.create_or_update_index(improved_index)

            print(f"\n✅ Index updated successfully!")
            print(f"📊 Index: {result.name}")
            print(f"📝 Fields: {len(result.fields)}")
            print(f"⭐ Scoring profiles: {len(result.scoring_profiles or [])}")
            print(f"🔍 Suggesters: {len(result.suggesters or [])}")

            # Step 5: Validation
            if self.verbose:
                print(f"\n[INFO] Validating deployment...")
            else:
                print(f"\n🔍 Validating deployment...")

            validated = self.validate_index()

            if validated:
                print(f"\n✅ Deployment completed successfully!")
                if backup_file:
                    print(f"📦 Backup saved: {backup_file}")
                return True
            else:
                print(f"\n⚠️  Deployment completed but validation found issues")
                return False

        except Exception as e:
            print(f"\n❌ Deployment failed: {str(e)}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            if 'backup_file' in locals() and backup_file:
                print(f"💡 Use backup to restore: {backup_file}")
            raise

    def validate_index(self) -> bool:
        """Validate the deployed index"""
        print(f"   Checking index configuration...")

        try:
            index = self.client.get_index(self.index_name)

            issues = []
            warnings = []

            # Check scoring profiles
            if not index.scoring_profiles or len(index.scoring_profiles) < 1:
                issues.append("Missing scoring profiles")
            else:
                profile_names = [p.name for p in index.scoring_profiles]
                if "productBoostingProfile" in profile_names:
                    print(f"   ✓ Product boosting profile found")
                if "contentRAGProfile" in profile_names:
                    print(f"   ✓ Content RAG profile found")
                if len(profile_names) >= 2:
                    print(f"   ✓ {len(profile_names)} scoring profiles configured")

            # Check BM25 similarity settings
            if index.similarity:
                similarity_type = str(type(index.similarity).__name__)
                if "BM25" in similarity_type:
                    print(f"   ✓ BM25 similarity configured")
                    # Note: Cannot directly access k1/b values from the SDK model
                else:
                    warnings.append(f"Similarity is not BM25: {similarity_type}")
            else:
                warnings.append("No similarity configuration (using defaults)")

            # Check semantic configuration
            if index.semantic_search and index.semantic_search.configurations:
                config = index.semantic_search.configurations[0]
                if config.prioritized_fields.title_field:
                    title_field = config.prioritized_fields.title_field.field_name
                    if title_field == "id":
                        issues.append("Semantic title field still set to 'id' instead of 'title'")
                    elif title_field == "title":
                        print(f"   ✓ Semantic title field correctly set to 'title'")
                else:
                    issues.append("No title field in semantic configuration")
                
                # Check content fields
                content_fields_count = len(config.prioritized_fields.content_fields) if config.prioritized_fields.content_fields else 0
                if content_fields_count >= 2:
                    print(f"   ✓ {content_fields_count} content fields in semantic config")
                elif content_fields_count == 1:
                    warnings.append("Only 1 content field in semantic config (recommend 2+)")
                
                # Check keywords fields
                keywords_count = len(config.prioritized_fields.keywords_fields) if config.prioritized_fields.keywords_fields else 0
                if keywords_count >= 4:
                    print(f"   ✓ {keywords_count} keyword fields in semantic config")
            else:
                issues.append("Missing semantic configuration")
            
            # Check suggester
            if index.suggesters and len(index.suggesters) > 0:
                print(f"   ✓ Suggester configured for autocomplete")
            else:
                warnings.append("No suggester configured (autocomplete disabled)")

            # Check analyzers on key fields
            title_field = next((f for f in index.fields if f.name == "title"), None)
            if title_field and hasattr(title_field, 'analyzer_name'):
                if title_field.analyzer_name == "standard.lucene":
                    print(f"   ✓ Title field uses standard.lucene analyzer")
                else:
                    warnings.append(f"Title analyzer is '{title_field.analyzer_name}', expected 'standard.lucene'")

            # Check embeddings field retrievability
            embeddings_field = next((f for f in index.fields if f.name == "embeddings"), None)
            if embeddings_field:
                if hasattr(embeddings_field, 'retrievable') and embeddings_field.retrievable:
                    print(f"   ✓ Embeddings field is retrievable")
                elif hasattr(embeddings_field, 'hidden') and not embeddings_field.hidden:
                    print(f"   ✓ Embeddings field is not hidden")
                else:
                    warnings.append("Embeddings field may not be retrievable")

            # Check vector search
            if index.vector_search:
                if not index.vector_search.compressions:
                    issues.append("Vector compression not configured")
                else:
                    print(f"   ✓ Vector compression configured")
                
                if index.vector_search.algorithms:
                    print(f"   ✓ Vector search algorithms configured ({len(index.vector_search.algorithms)})")

            if issues:
                print(f"   ⚠️  Validation issues found:")
                for issue in issues:
                    print(f"      - {issue}")
            
            if warnings:
                print(f"   ⚠️  Validation warnings:")
                for warning in warnings:
                    print(f"      - {warning}")
            
            if not issues:
                print(f"   ✅ All critical validations passed")
                return True
            else:
                return False

        except Exception as e:
            print(f"   ❌ Validation error: {str(e)}")
            return False

    def rollback(self, backup_file: str) -> bool:
        """Rollback to a previous backup"""
        print(f"🔄 Rolling back to: {backup_file}")

        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            # Note: This is a simplified rollback
            # Full rollback would require recreating the index from backup
            print(f"⚠️  Manual rollback required")
            print(f"📋 Backup file: {backup_file}")
            print(f"💡 Use Azure Portal or REST API to restore from backup")

            return False

        except Exception as e:
            print(f"❌ Rollback failed: {str(e)}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Deploy Azure AI Search index improvements")
    parser.add_argument("--mode", choices=["backup", "deploy", "validate", "rollback"],
                       default="deploy", help="Operation mode")
    parser.add_argument("--dry-run", action="store_true",
                       help="Perform a dry run without making changes")
    parser.add_argument("--force", action="store_true",
                       help="Delete and recreate index (WARNING: destroys all data)")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")
    parser.add_argument("--backup-file", type=str,
                       help="Backup file for rollback")
    parser.add_argument("--searchservice", type=str,
                       help="Azure Search service name (fallback: AZURE_SEARCH_SERVICE env var)")
    parser.add_argument("--searchkey", type=str,
                       help="Azure Search API key (fallback: AZURE_SEARCH_KEY env var)")
    parser.add_argument("--index-name", type=str,
                       help="Index name (fallback: AZURE_SEARCH_INDEX env var, default: myproject-index)")

    # Optional OpenAI settings for integrated vectorizer
    parser.add_argument("--openai-endpoint", type=str,
                       help="Azure OpenAI endpoint (fallback: AZURE_OPENAI_ENDPOINT env var)")
    parser.add_argument("--openai-deployment", type=str,
                       help="Azure OpenAI embedding deployment (fallback: AZURE_OPENAI_EMBEDDING_DEPLOYMENT env var)")
    parser.add_argument("--openai-key", type=str,
                       help="Azure OpenAI API key (fallback: AZURE_OPENAI_KEY env var)")

    args = parser.parse_args()

    # Get credentials from args or environment variables (simple approach)
    search_service = args.searchservice or os.getenv("AZURE_SEARCH_SERVICE")
    search_key = args.searchkey or os.getenv("AZURE_SEARCH_KEY")
    index_name = args.index_name or os.getenv("AZURE_SEARCH_INDEX", "myproject-index")

    # Optional OpenAI credentials for integrated vectorizer
    openai_endpoint = args.openai_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
    openai_deployment = args.openai_deployment or os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    openai_key = args.openai_key or os.getenv("AZURE_OPENAI_KEY")

    if not search_service:
        print(f"❌ Error: AZURE_SEARCH_SERVICE is required", file=sys.stderr)
        return 1

    if not search_key:
        print(f"❌ Error: AZURE_SEARCH_KEY is required", file=sys.stderr)
        return 1

    # Build search endpoint
    search_endpoint = f"https://{search_service}.search.windows.net"

    # Create manager
    manager = IndexDeploymentManager(
        search_endpoint,
        search_key,
        index_name,
        openai_endpoint=openai_endpoint,
        openai_deployment=openai_deployment,
        openai_key=openai_key,
        verbose=args.verbose
    )

    # Execute mode
    try:
        if args.mode == "backup":
            backup_file = manager.backup_current_index()
            print(f"\n✅ Backup completed: {backup_file}")
            return 0

        elif args.mode == "deploy":
            success = manager.deploy_index(dry_run=args.dry_run, force=args.force)
            return 0 if success else 1

        elif args.mode == "validate":
            success = manager.validate_index()
            return 0 if success else 1

        elif args.mode == "rollback":
            if not args.backup_file:
                print("❌ Error: --backup-file required for rollback")
                return 1
            success = manager.rollback(args.backup_file)
            return 0 if success else 1

    except Exception as e:
        print(f"\n❌ Operation failed: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())