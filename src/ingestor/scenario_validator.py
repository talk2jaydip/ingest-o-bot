"""Scenario-based environment validation.

This module validates environment configurations based on specific usage scenarios,
providing clear, actionable error messages for missing or invalid configurations.
"""

import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Scenario(str, Enum):
    """Configuration scenarios with different requirements."""
    LOCAL_DEV = "local_dev"  # Local files, local artifacts
    AZURE_FULL = "azure_full"  # Azure Search + Azure OpenAI + Azure DI
    OFFLINE = "offline"  # ChromaDB + HuggingFace, no Azure
    HYBRID_CLOUD_LOCAL = "hybrid"  # Azure Search + local embeddings
    AZURE_COHERE = "azure_cohere"  # Azure Search + Cohere embeddings


@dataclass
class ValidationResult:
    """Result of environment validation."""
    valid: bool
    errors: List[str]
    warnings: List[str]
    scenario: Optional[Scenario] = None
    missing_required: List[str] = None
    invalid_values: Dict[str, str] = None

    def __post_init__(self):
        if self.missing_required is None:
            self.missing_required = []
        if self.invalid_values is None:
            self.invalid_values = {}


class ScenarioValidator:
    """Validates environment configuration for specific scenarios."""

    # Required environment variables by scenario
    SCENARIO_REQUIREMENTS = {
        Scenario.LOCAL_DEV: {
            "required": [
                "INPUT_MODE",  # Must be "local"
                "LOCAL_INPUT_GLOB",
            ],
            "optional": [
                "ARTIFACTS_DIR",
                "OFFICE_EXTRACTOR_MODE",
                "LOG_LEVEL",
            ],
            "forbidden": [],  # No Azure services required
            "context": "Local development mode - no Azure services needed"
        },
        Scenario.AZURE_FULL: {
            "required": [
                "AZURE_SEARCH_SERVICE",
                "AZURE_SEARCH_INDEX",
                "AZURE_DOC_INT_ENDPOINT",
                "AZURE_OPENAI_ENDPOINT",
                "AZURE_OPENAI_KEY",
                "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
            ],
            "optional": [
                "AZURE_SEARCH_KEY",  # Optional with managed identity
                "AZURE_DOC_INT_KEY",  # Optional with managed identity
                "AZURE_STORAGE_ACCOUNT",  # For blob mode
                "AZURE_STORAGE_ACCOUNT_KEY",  # For blob mode
            ],
            "forbidden": [],
            "context": "Full Azure setup - Azure Search, Document Intelligence, and OpenAI"
        },
        Scenario.OFFLINE: {
            "required": [
                "VECTOR_STORE_MODE",  # Must be "chromadb"
                "EMBEDDINGS_MODE",  # Must be "huggingface"
                "INPUT_MODE",  # Must be "local"
                "LOCAL_INPUT_GLOB",
            ],
            "optional": [
                "CHROMADB_PERSIST_DIR",
                "CHROMADB_COLLECTION_NAME",
                "HUGGINGFACE_MODEL_NAME",
                "HUGGINGFACE_DEVICE",
                "OFFICE_EXTRACTOR_MODE",  # Should be "markitdown"
            ],
            "forbidden": [
                "AZURE_SEARCH_SERVICE",
                "AZURE_OPENAI_ENDPOINT",
            ],
            "context": "Fully offline mode - ChromaDB + HuggingFace, no Azure services"
        },
        Scenario.HYBRID_CLOUD_LOCAL: {
            "required": [
                "VECTOR_STORE_MODE",  # Must be "azure_search"
                "AZURE_SEARCH_SERVICE",
                "AZURE_SEARCH_INDEX",
                "EMBEDDINGS_MODE",  # Must be "huggingface"
                "HUGGINGFACE_MODEL_NAME",
                "AZURE_USE_INTEGRATED_VECTORIZATION",  # Must be "false"
            ],
            "optional": [
                "AZURE_SEARCH_KEY",
                "HUGGINGFACE_DEVICE",
                "AZURE_DOC_INT_ENDPOINT",  # Optional for document processing
                "AZURE_OPENAI_ENDPOINT",  # Optional for media descriptions
            ],
            "forbidden": [],
            "context": "Hybrid mode - Azure Search storage + local HuggingFace embeddings"
        },
        Scenario.AZURE_COHERE: {
            "required": [
                "VECTOR_STORE_MODE",  # Must be "azure_search"
                "AZURE_SEARCH_SERVICE",
                "AZURE_SEARCH_INDEX",
                "EMBEDDINGS_MODE",  # Must be "cohere"
                "COHERE_API_KEY",
                "AZURE_USE_INTEGRATED_VECTORIZATION",  # Must be "false"
            ],
            "optional": [
                "AZURE_SEARCH_KEY",
                "COHERE_MODEL_NAME",
                "AZURE_DOC_INT_ENDPOINT",
                "AZURE_OPENAI_ENDPOINT",  # Optional for media descriptions
            ],
            "forbidden": [],
            "context": "Azure Search + Cohere embeddings"
        },
    }

    @staticmethod
    def detect_scenario() -> Optional[Scenario]:
        """Auto-detect the intended scenario from environment variables.

        Returns:
            Detected scenario or None if cannot determine
        """
        # Check explicit mode settings
        vector_mode = os.getenv("VECTOR_STORE_MODE", "").lower()
        embeddings_mode = os.getenv("EMBEDDINGS_MODE", "").lower()
        input_mode = os.getenv("INPUT_MODE", "local").lower()

        # Offline scenario: ChromaDB + HuggingFace + local input
        if vector_mode == "chromadb" and embeddings_mode == "huggingface" and input_mode == "local":
            return Scenario.OFFLINE

        # Hybrid scenario: Azure Search + HuggingFace
        if vector_mode == "azure_search" and embeddings_mode == "huggingface":
            return Scenario.HYBRID_CLOUD_LOCAL

        # Azure + Cohere
        if vector_mode == "azure_search" and embeddings_mode == "cohere":
            return Scenario.AZURE_COHERE

        # Azure full stack (default)
        if os.getenv("AZURE_SEARCH_SERVICE") and os.getenv("AZURE_OPENAI_ENDPOINT"):
            return Scenario.AZURE_FULL

        # Local dev (no cloud services)
        if input_mode == "local" and not os.getenv("AZURE_SEARCH_SERVICE"):
            return Scenario.LOCAL_DEV

        return None

    @staticmethod
    def validate_scenario(scenario: Scenario, verbose: bool = False) -> ValidationResult:
        """Validate environment for a specific scenario.

        Args:
            scenario: The scenario to validate
            verbose: Include detailed validation info

        Returns:
            ValidationResult with errors, warnings, and missing variables
        """
        errors = []
        warnings = []
        missing_required = []
        invalid_values = {}

        requirements = ScenarioValidator.SCENARIO_REQUIREMENTS.get(scenario)
        if not requirements:
            return ValidationResult(
                valid=False,
                errors=[f"Unknown scenario: {scenario}"],
                warnings=[],
                scenario=scenario
            )

        # Check required variables
        for var in requirements["required"]:
            value = os.getenv(var)
            if not value:
                missing_required.append(var)
                errors.append(f"Missing required variable: {var}")

        # Check forbidden variables (should not be set in this scenario)
        for var in requirements["forbidden"]:
            value = os.getenv(var)
            if value:
                warnings.append(
                    f"Variable {var} is set but not used in {scenario.value} scenario. "
                    f"This may indicate a configuration mismatch."
                )

        # Scenario-specific validation
        if scenario == Scenario.OFFLINE:
            # Verify offline-compatible settings
            vector_mode = os.getenv("VECTOR_STORE_MODE", "").lower()
            if vector_mode and vector_mode != "chromadb":
                errors.append(
                    f"VECTOR_STORE_MODE must be 'chromadb' for offline scenario, "
                    f"got: {vector_mode}"
                )

            embeddings_mode = os.getenv("EMBEDDINGS_MODE", "").lower()
            if embeddings_mode and embeddings_mode not in ["huggingface"]:
                errors.append(
                    f"EMBEDDINGS_MODE must be 'huggingface' for offline scenario, "
                    f"got: {embeddings_mode}"
                )

            office_mode = os.getenv("AZURE_OFFICE_EXTRACTOR_MODE", "hybrid").lower()
            if office_mode not in ["markitdown"]:
                warnings.append(
                    f"AZURE_OFFICE_EXTRACTOR_MODE should be 'markitdown' for offline scenario, "
                    f"got: {office_mode}. You may encounter errors if Azure DI is not available."
                )

        elif scenario == Scenario.HYBRID_CLOUD_LOCAL:
            # Verify integrated vectorization is disabled
            integrated_vec = os.getenv("AZURE_USE_INTEGRATED_VECTORIZATION", "false").lower()
            if integrated_vec == "true":
                errors.append(
                    "AZURE_USE_INTEGRATED_VECTORIZATION must be 'false' when using local embeddings. "
                    "Azure Search cannot use integrated vectorization with HuggingFace embeddings."
                )

        elif scenario == Scenario.AZURE_COHERE:
            # Verify integrated vectorization is disabled
            integrated_vec = os.getenv("AZURE_USE_INTEGRATED_VECTORIZATION", "false").lower()
            if integrated_vec == "true":
                errors.append(
                    "AZURE_USE_INTEGRATED_VECTORIZATION must be 'false' when using Cohere embeddings. "
                    "Azure Search cannot use integrated vectorization with Cohere."
                )

        valid = len(errors) == 0

        return ValidationResult(
            valid=valid,
            errors=errors,
            warnings=warnings,
            scenario=scenario,
            missing_required=missing_required,
            invalid_values=invalid_values
        )

    @staticmethod
    def get_scenario_help(scenario: Scenario) -> str:
        """Get helpful documentation for a scenario.

        Args:
            scenario: The scenario to document

        Returns:
            Formatted help text with setup instructions
        """
        requirements = ScenarioValidator.SCENARIO_REQUIREMENTS.get(scenario)
        if not requirements:
            return f"No documentation available for scenario: {scenario}"

        help_text = []
        help_text.append(f"\n{'='*70}")
        help_text.append(f"Scenario: {scenario.value.upper()}")
        help_text.append(f"{'='*70}")
        help_text.append(f"\n{requirements['context']}\n")

        help_text.append("Required Environment Variables:")
        for var in requirements["required"]:
            help_text.append(f"  - {var}")

        if requirements["optional"]:
            help_text.append("\nOptional Variables:")
            for var in requirements["optional"]:
                help_text.append(f"  - {var}")

        if requirements["forbidden"]:
            help_text.append("\nNOT Used (can be omitted):")
            for var in requirements["forbidden"]:
                help_text.append(f"  - {var}")

        # Add scenario-specific setup instructions
        help_text.append("\nSetup Instructions:")

        if scenario == Scenario.LOCAL_DEV:
            help_text.append("  1. Set AZURE_INPUT_MODE=local")
            help_text.append("  2. Set AZURE_LOCAL_GLOB=path/to/files/*.pdf")
            help_text.append("  3. Optionally set AZURE_ARTIFACTS_DIR=./artifacts")
            help_text.append("  4. No Azure services needed!")
            help_text.append("\nExample .env:")
            help_text.append("  AZURE_INPUT_MODE=local")
            help_text.append("  AZURE_LOCAL_GLOB=documents/**/*.pdf")
            help_text.append("  AZURE_ARTIFACTS_DIR=./artifacts")
            help_text.append("  VECTOR_STORE_MODE=chromadb")
            help_text.append("  EMBEDDINGS_MODE=huggingface")

        elif scenario == Scenario.AZURE_FULL:
            help_text.append("  1. Create Azure AI Search service")
            help_text.append("  2. Create Azure Document Intelligence service")
            help_text.append("  3. Create Azure OpenAI service with embedding deployment")
            help_text.append("  4. Set all required environment variables")
            help_text.append("\nSee: envs/.env.example for full template")

        elif scenario == Scenario.OFFLINE:
            help_text.append("  1. Install: pip install chromadb sentence-transformers")
            help_text.append("  2. Set VECTOR_STORE_MODE=chromadb")
            help_text.append("  3. Set EMBEDDINGS_MODE=huggingface")
            help_text.append("  4. Set AZURE_INPUT_MODE=local")
            help_text.append("  5. Set AZURE_OFFICE_EXTRACTOR_MODE=markitdown")
            help_text.append("\nSee: envs/.env.chromadb.example for full template")

        elif scenario == Scenario.HYBRID_CLOUD_LOCAL:
            help_text.append("  1. Create Azure AI Search service")
            help_text.append("  2. Install: pip install sentence-transformers")
            help_text.append("  3. Set VECTOR_STORE_MODE=azure_search")
            help_text.append("  4. Set EMBEDDINGS_MODE=huggingface")
            help_text.append("  5. Set AZURE_USE_INTEGRATED_VECTORIZATION=false")
            help_text.append("\nSee: envs/.env.hybrid.example for full template")

        elif scenario == Scenario.AZURE_COHERE:
            help_text.append("  1. Create Azure AI Search service")
            help_text.append("  2. Get Cohere API key from https://dashboard.cohere.com/")
            help_text.append("  3. Install: pip install cohere")
            help_text.append("  4. Set VECTOR_STORE_MODE=azure_search")
            help_text.append("  5. Set EMBEDDINGS_MODE=cohere")
            help_text.append("  6. Set AZURE_USE_INTEGRATED_VECTORIZATION=false")
            help_text.append("\nSee: envs/.env.cohere.example for full template")

        help_text.append(f"\n{'='*70}\n")

        return "\n".join(help_text)

    @staticmethod
    def print_validation_report(result: ValidationResult, include_help: bool = True) -> None:
        """Print a formatted validation report.

        Args:
            result: The validation result to report
            include_help: Whether to include setup help
        """
        if result.valid:
            print("\n✅ Environment configuration is VALID")
            if result.scenario:
                print(f"   Detected scenario: {result.scenario.value}")
            if result.warnings:
                print(f"\n⚠️  {len(result.warnings)} warnings:")
                for warning in result.warnings:
                    print(f"   - {warning}")
        else:
            print("\n❌ Environment configuration is INVALID")
            if result.scenario:
                print(f"   Scenario: {result.scenario.value}")

            if result.errors:
                print(f"\n🚫 {len(result.errors)} errors found:")
                for error in result.errors:
                    print(f"   - {error}")

            if result.missing_required:
                print(f"\n📋 Missing required variables:")
                for var in result.missing_required:
                    print(f"   - {var}")

            if result.warnings:
                print(f"\n⚠️  {len(result.warnings)} warnings:")
                for warning in result.warnings:
                    print(f"   - {warning}")

            if include_help and result.scenario:
                print(ScenarioValidator.get_scenario_help(result.scenario))


def validate_current_environment(verbose: bool = False) -> ValidationResult:
    """Validate the current environment configuration.

    Args:
        verbose: Include detailed validation info

    Returns:
        ValidationResult with detected scenario and validation status
    """
    # Auto-detect scenario
    scenario = ScenarioValidator.detect_scenario()

    if not scenario:
        # Cannot detect scenario - provide generic validation
        return ValidationResult(
            valid=False,
            errors=[
                "Cannot detect configuration scenario from environment variables.",
                "Please set VECTOR_STORE_MODE and EMBEDDINGS_MODE explicitly, or",
                "ensure AZURE_SEARCH_SERVICE and AZURE_OPENAI_ENDPOINT are set for Azure mode."
            ],
            warnings=[
                "Consider using one of the scenario templates from envs/ directory.",
                "Run: cp envs/.env.example .env (for Azure full stack)",
                "Run: cp envs/.env.chromadb.example .env (for offline mode)"
            ]
        )

    # Validate detected scenario
    result = ScenarioValidator.validate_scenario(scenario, verbose=verbose)
    return result


if __name__ == "__main__":
    """Command-line interface for scenario validation."""
    import sys
    import argparse

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Validate environment configuration for ingest-o-bot scenarios',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect scenario and validate current .env
  python -m ingestor.scenario_validator

  # Validate specific scenario with current .env
  python -m ingestor.scenario_validator azure_full

  # Validate specific .env file (no copying needed!)
  python -m ingestor.scenario_validator --env-file envs/.env.azure-local-input.example

  # Validate specific scenario with specific .env file
  python -m ingestor.scenario_validator azure_full --env-file envs/.env.azure-local-input.example

Available scenarios:
  local_dev   - Local development (no Azure)
  azure_full  - Full Azure stack (DI + OpenAI + Search)
  offline     - Fully offline (ChromaDB + Hugging Face)
  hybrid      - Hybrid (Azure Search + local embeddings)
  azure_cohere - Azure Search + Cohere embeddings
        """
    )
    parser.add_argument(
        'scenario',
        nargs='?',
        help='Scenario to validate (auto-detect if not specified)'
    )
    parser.add_argument(
        '--env-file',
        '-e',
        type=str,
        default='.env',
        help='Path to .env file (default: .env in current directory)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Show verbose validation details'
    )

    args = parser.parse_args()

    # Load specified .env file
    try:
        from dotenv import load_dotenv
        env_file = Path(args.env_file).resolve()

        if env_file.exists():
            load_dotenv(dotenv_path=env_file, override=True)
            print(f"✓ Loaded environment from: {env_file}\n")
        else:
            print(f"⚠️  Environment file not found: {env_file}")
            print(f"⚠️  (Searched at: {env_file})")
            print(f"⚠️  Using system environment variables\n")
    except ImportError:
        print(f"⚠️  python-dotenv not installed, using system environment variables\n")

    # Validate scenario
    if args.scenario:
        scenario_name = args.scenario.lower()
        try:
            scenario = Scenario(scenario_name)
            result = ScenarioValidator.validate_scenario(scenario, verbose=args.verbose or True)
            ScenarioValidator.print_validation_report(result, include_help=True)
            sys.exit(0 if result.valid else 1)
        except ValueError:
            print(f"❌ Unknown scenario: {scenario_name}")
            print(f"\nAvailable scenarios: {', '.join([s.value for s in Scenario])}")
            sys.exit(1)
    else:
        # Auto-detect and validate
        result = validate_current_environment(verbose=args.verbose or True)
        ScenarioValidator.print_validation_report(result, include_help=True)
        sys.exit(0 if result.valid else 1)
