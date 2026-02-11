"""Environment configuration parameter validation.

This module provides validation for environment variables to catch typos,
missing parameters, and deprecated configurations.
"""

import os
import difflib
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class ParamType(Enum):
    """Parameter value types."""
    STRING = "str"
    INTEGER = "int"
    FLOAT = "float"
    BOOLEAN = "bool"
    PATH = "path"
    URL = "url"


@dataclass
class ParamDefinition:
    """Definition of an environment parameter."""
    name: str
    category: str
    type: ParamType
    default: Any
    description: str
    aliases: List[str] = None
    deprecated: bool = False
    required: bool = False

    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []


# Parameter registry organized by category
PARAMETER_REGISTRY: Dict[str, ParamDefinition] = {
    # Vector Store Mode
    "VECTOR_STORE_MODE": ParamDefinition(
        name="VECTOR_STORE_MODE",
        category="Vector Store",
        type=ParamType.STRING,
        default=None,
        description="Vector store implementation (azure_search, chromadb, pinecone, qdrant)",
    ),

    # ChromaDB Parameters
    "CHROMADB_COLLECTION_NAME": ParamDefinition(
        name="CHROMADB_COLLECTION_NAME",
        category="ChromaDB",
        type=ParamType.STRING,
        default="documents",
        description="ChromaDB collection name",
    ),
    "CHROMADB_PERSIST_DIR": ParamDefinition(
        name="CHROMADB_PERSIST_DIR",
        category="ChromaDB",
        type=ParamType.PATH,
        default=None,
        description="ChromaDB persistent storage directory (None = in-memory)",
    ),
    "CHROMADB_HOST": ParamDefinition(
        name="CHROMADB_HOST",
        category="ChromaDB",
        type=ParamType.STRING,
        default=None,
        description="ChromaDB server host (for client/server mode)",
    ),
    "CHROMADB_PORT": ParamDefinition(
        name="CHROMADB_PORT",
        category="ChromaDB",
        type=ParamType.INTEGER,
        default=None,
        description="ChromaDB server port (for client/server mode)",
    ),
    "CHROMADB_BATCH_SIZE": ParamDefinition(
        name="CHROMADB_BATCH_SIZE",
        category="ChromaDB",
        type=ParamType.INTEGER,
        default=1000,
        description="ChromaDB upload batch size",
    ),

    # Embeddings Mode
    "EMBEDDINGS_MODE": ParamDefinition(
        name="EMBEDDINGS_MODE",
        category="Embeddings",
        type=ParamType.STRING,
        default=None,
        description="Embeddings provider (azure_openai, huggingface, cohere, openai)",
    ),
    "EMBEDDINGS_MAX_SEQ_LENGTH": ParamDefinition(
        name="EMBEDDINGS_MAX_SEQ_LENGTH",
        category="Embeddings",
        type=ParamType.INTEGER,
        default=None,
        description="Manual override for embedding model's max sequence length",
    ),

    # Hugging Face Parameters
    "HUGGINGFACE_MODEL_NAME": ParamDefinition(
        name="HUGGINGFACE_MODEL_NAME",
        category="HuggingFace",
        type=ParamType.STRING,
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="HuggingFace model identifier from Hub",
    ),
    "HUGGINGFACE_DEVICE": ParamDefinition(
        name="HUGGINGFACE_DEVICE",
        category="HuggingFace",
        type=ParamType.STRING,
        default="cpu",
        description="Device to run model on (cpu, cuda, mps)",
    ),
    "HUGGINGFACE_BATCH_SIZE": ParamDefinition(
        name="HUGGINGFACE_BATCH_SIZE",
        category="HuggingFace",
        type=ParamType.INTEGER,
        default=32,
        description="Batch size for encoding",
    ),
    "HUGGINGFACE_NORMALIZE_EMBEDDINGS": ParamDefinition(
        name="HUGGINGFACE_NORMALIZE_EMBEDDINGS",
        category="HuggingFace",
        type=ParamType.BOOLEAN,
        default=True,
        description="Whether to normalize embeddings",
    ),

    # Cohere Parameters
    "COHERE_API_KEY": ParamDefinition(
        name="COHERE_API_KEY",
        category="Cohere",
        type=ParamType.STRING,
        default=None,
        description="Cohere API key",
        required=True,  # Required when using Cohere
    ),
    "COHERE_MODEL_NAME": ParamDefinition(
        name="COHERE_MODEL_NAME",
        category="Cohere",
        type=ParamType.STRING,
        default="embed-multilingual-v3.0",
        description="Cohere model name",
    ),

    # OpenAI Parameters
    "OPENAI_API_KEY": ParamDefinition(
        name="OPENAI_API_KEY",
        category="OpenAI",
        type=ParamType.STRING,
        default=None,
        description="OpenAI API key (non-Azure)",
    ),
    "OPENAI_EMBEDDING_MODEL": ParamDefinition(
        name="OPENAI_EMBEDDING_MODEL",
        category="OpenAI",
        type=ParamType.STRING,
        default="text-embedding-3-small",
        description="OpenAI embedding model name",
    ),

    # Chunking Parameters (Generic names)
    "CHUNKING_MAX_CHARS": ParamDefinition(
        name="CHUNKING_MAX_CHARS",
        category="Chunking",
        type=ParamType.INTEGER,
        default=1000,
        description="Soft character limit per chunk",
        aliases=["AZURE_CHUNKING_MAX_CHARS"],
    ),
    "CHUNKING_MAX_TOKENS": ParamDefinition(
        name="CHUNKING_MAX_TOKENS",
        category="Chunking",
        type=ParamType.INTEGER,
        default=500,
        description="Target minimum tokens per chunk",
        aliases=["AZURE_CHUNKING_MAX_TOKENS"],
    ),
    "CHUNKING_MAX_SECTION_TOKENS": ParamDefinition(
        name="CHUNKING_MAX_SECTION_TOKENS",
        category="Chunking",
        type=ParamType.INTEGER,
        default=750,
        description="Hard maximum tokens per chunk",
        aliases=["AZURE_CHUNKING_MAX_SECTION_TOKENS"],
    ),
    "CHUNKING_OVERLAP_PERCENT": ParamDefinition(
        name="CHUNKING_OVERLAP_PERCENT",
        category="Chunking",
        type=ParamType.INTEGER,
        default=10,
        description="Percentage overlap between chunks",
        aliases=["AZURE_CHUNKING_OVERLAP_PERCENT"],
    ),
    "CHUNKING_CROSS_PAGE_OVERLAP": ParamDefinition(
        name="CHUNKING_CROSS_PAGE_OVERLAP",
        category="Chunking",
        type=ParamType.BOOLEAN,
        default=True,
        description="Enable overlap across page boundaries",
        aliases=["AZURE_CHUNKING_CROSS_PAGE_OVERLAP"],
    ),

    # Azure-prefixed Chunking Parameters (for backward compatibility)
    "AZURE_CHUNKING_MAX_CHARS": ParamDefinition(
        name="AZURE_CHUNKING_MAX_CHARS",
        category="Chunking",
        type=ParamType.INTEGER,
        default=1000,
        description="Soft character limit per chunk (Azure-prefixed)",
        aliases=["CHUNKING_MAX_CHARS"],
    ),
    "AZURE_CHUNKING_MAX_TOKENS": ParamDefinition(
        name="AZURE_CHUNKING_MAX_TOKENS",
        category="Chunking",
        type=ParamType.INTEGER,
        default=500,
        description="Target minimum tokens per chunk (Azure-prefixed)",
        aliases=["CHUNKING_MAX_TOKENS"],
    ),

    # Performance Parameters
    "MAX_WORKERS": ParamDefinition(
        name="MAX_WORKERS",
        category="Performance",
        type=ParamType.INTEGER,
        default=4,
        description="Maximum worker threads",
        aliases=["AZURE_MAX_WORKERS"],
    ),
    "EMBED_BATCH_SIZE": ParamDefinition(
        name="EMBED_BATCH_SIZE",
        category="Performance",
        type=ParamType.INTEGER,
        default=128,
        description="Embedding batch size",
        aliases=["AZURE_EMBED_BATCH_SIZE"],
    ),

    # Azure Search Parameters
    "AZURE_SEARCH_SERVICE": ParamDefinition(
        name="AZURE_SEARCH_SERVICE",
        category="Azure Search",
        type=ParamType.STRING,
        default=None,
        description="Azure Search service name",
    ),
    "AZURE_SEARCH_INDEX": ParamDefinition(
        name="AZURE_SEARCH_INDEX",
        category="Azure Search",
        type=ParamType.STRING,
        default=None,
        description="Azure Search index name",
    ),
    "AZURE_SEARCH_KEY": ParamDefinition(
        name="AZURE_SEARCH_KEY",
        category="Azure Search",
        type=ParamType.STRING,
        default=None,
        description="Azure Search API key",
    ),

    # Azure OpenAI Parameters
    "AZURE_OPENAI_ENDPOINT": ParamDefinition(
        name="AZURE_OPENAI_ENDPOINT",
        category="Azure OpenAI",
        type=ParamType.URL,
        default=None,
        description="Azure OpenAI endpoint URL",
    ),
    "AZURE_OPENAI_KEY": ParamDefinition(
        name="AZURE_OPENAI_KEY",
        category="Azure OpenAI",
        type=ParamType.STRING,
        default=None,
        description="Azure OpenAI API key",
    ),
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": ParamDefinition(
        name="AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
        category="Azure OpenAI",
        type=ParamType.STRING,
        default=None,
        description="Azure OpenAI embedding deployment name",
    ),

    # Input/Output Parameters
    "AZURE_INPUT_MODE": ParamDefinition(
        name="AZURE_INPUT_MODE",
        category="Input",
        type=ParamType.STRING,
        default="blob",
        description="Input mode (blob, local)",
    ),
    "AZURE_LOCAL_GLOB": ParamDefinition(
        name="AZURE_LOCAL_GLOB",
        category="Input",
        type=ParamType.STRING,
        default=None,
        description="Local file glob pattern",
    ),
    "AZURE_ARTIFACTS_DIR": ParamDefinition(
        name="AZURE_ARTIFACTS_DIR",
        category="Artifacts",
        type=ParamType.PATH,
        default=None,
        description="Local artifacts directory",
    ),
}


def get_logger(name: str):
    """Get logger instance."""
    import logging
    return logging.getLogger(name)


def find_similar_parameters(typo: str, max_results: int = 3) -> List[Tuple[str, float]]:
    """Find similar parameter names using fuzzy matching.

    Args:
        typo: The potentially misspelled parameter name
        max_results: Maximum number of suggestions to return

    Returns:
        List of (parameter_name, similarity_score) tuples
    """
    all_params = list(PARAMETER_REGISTRY.keys())
    matches = difflib.get_close_matches(typo, all_params, n=max_results, cutoff=0.6)

    # Calculate similarity scores
    results = []
    for match in matches:
        ratio = difflib.SequenceMatcher(None, typo.lower(), match.lower()).ratio()
        results.append((match, ratio))

    return sorted(results, key=lambda x: x[1], reverse=True)


def validate_environment(warn_only: bool = True) -> Tuple[List[str], List[str]]:
    """Validate environment variables for typos and issues.

    Args:
        warn_only: If True, only log warnings. If False, raise exceptions.

    Returns:
        Tuple of (warnings, errors) lists
    """
    logger = get_logger(__name__)
    warnings = []
    errors = []

    # Known prefixes to scan
    known_prefixes = [
        "VECTOR_STORE_",
        "CHROMADB_",
        "EMBEDDINGS_",
        "HUGGINGFACE_",
        "COHERE_",
        "OPENAI_",
        "CHUNKING_",
        "AZURE_CHUNKING_",
        "AZURE_SEARCH_",
        "AZURE_OPENAI_",
        "AZURE_STORAGE_",
        "AZURE_DOC_INT_",
        "AZURE_INPUT_",
        "AZURE_ARTIFACTS_",
        "AZURE_OFFICE_",
        "MAX_WORKERS",
        "EMBED_BATCH_",
        "UPLOAD_BATCH_",
    ]

    # Scan environment for parameters
    for env_var in os.environ.keys():
        # Check if it matches known prefixes
        if not any(env_var.startswith(prefix) for prefix in known_prefixes):
            continue

        # Check if parameter exists in registry
        if env_var not in PARAMETER_REGISTRY:
            # Check if it's an alias
            is_alias = False
            for param_def in PARAMETER_REGISTRY.values():
                if env_var in param_def.aliases:
                    is_alias = True
                    break

            if not is_alias:
                # Find similar parameters
                suggestions = find_similar_parameters(env_var, max_results=2)

                if suggestions:
                    best_match, score = suggestions[0]
                    if score > 0.8:
                        warning = (
                            f"⚠️  Unknown parameter: {env_var}\n"
                            f"    Did you mean: {best_match}?"
                        )
                    else:
                        warning = f"⚠️  Unknown parameter: {env_var}"
                        if len(suggestions) > 0:
                            warning += "\n    Similar parameters: " + ", ".join(s[0] for s in suggestions)
                else:
                    warning = f"⚠️  Unknown parameter: {env_var}"

                warnings.append(warning)
                logger.warning(warning)

    return warnings, errors


def print_parameter_help(category: Optional[str] = None):
    """Print help for available parameters.

    Args:
        category: If specified, only print parameters from this category
    """
    if category:
        params = {k: v for k, v in PARAMETER_REGISTRY.items() if v.category == category}
        print(f"\n{category} Parameters:")
    else:
        params = PARAMETER_REGISTRY
        print("\nAll Available Parameters:")

    print("=" * 80)

    # Group by category
    by_category = {}
    for param_name, param_def in params.items():
        if param_def.category not in by_category:
            by_category[param_def.category] = []
        by_category[param_def.category].append((param_name, param_def))

    for cat_name in sorted(by_category.keys()):
        print(f"\n{cat_name}:")
        for param_name, param_def in sorted(by_category[cat_name]):
            print(f"  {param_name}")
            print(f"    Type: {param_def.type.value}")
            print(f"    Default: {param_def.default}")
            print(f"    {param_def.description}")
            if param_def.aliases:
                print(f"    Aliases: {', '.join(param_def.aliases)}")
            print()
