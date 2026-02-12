"""Test script for vector store and embeddings provider detection."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ingestor.gradio_app import (
    detect_vector_stores,
    detect_embeddings_providers,
    generate_provider_detection_html,
)


def print_detection_results():
    """Print detection results for debugging."""
    print("=" * 80)
    print("VECTOR STORE DETECTION")
    print("=" * 80)

    vector_stores = detect_vector_stores()
    for result in vector_stores:
        print(f"\n{result.display_name} ({result.provider_name})")
        print(f"  Status: {result.status}")
        print(f"  Active: {result.is_active}")
        print(f"  Config: {result.config_summary}")
        if result.missing_required:
            print(f"  Missing Required: {', '.join(result.missing_required)}")
        if result.missing_optional:
            print(f"  Missing Optional: {', '.join(result.missing_optional)}")

    print("\n" + "=" * 80)
    print("EMBEDDINGS PROVIDER DETECTION")
    print("=" * 80)

    embeddings_providers = detect_embeddings_providers()
    for result in embeddings_providers:
        print(f"\n{result.display_name} ({result.provider_name})")
        print(f"  Status: {result.status}")
        print(f"  Active: {result.is_active}")
        print(f"  Config: {result.config_summary}")
        if result.missing_required:
            print(f"  Missing Required: {', '.join(result.missing_required)}")
        if result.missing_optional:
            print(f"  Missing Optional: {', '.join(result.missing_optional)}")

    print("\n" + "=" * 80)
    print("ACTIVE PROVIDERS SUMMARY")
    print("=" * 80)

    active_vector_store = next((r for r in vector_stores if r.is_active), None)
    active_embeddings = next((r for r in embeddings_providers if r.is_active), None)

    if active_vector_store:
        print(f"Active Vector Store: {active_vector_store.display_name} ({active_vector_store.status})")
    else:
        print("Active Vector Store: None detected")

    if active_embeddings:
        print(f"Active Embeddings Provider: {active_embeddings.display_name} ({active_embeddings.status})")
    else:
        print("Active Embeddings Provider: None detected")

    print("\n" + "=" * 80)
    print("ENVIRONMENT VARIABLES (for debugging)")
    print("=" * 80)
    print(f"VECTOR_STORE_MODE: {os.getenv('VECTOR_STORE_MODE', 'not set')}")
    print(f"EMBEDDINGS_MODE: {os.getenv('EMBEDDINGS_MODE', 'not set')}")
    print(f"AZURE_SEARCH_INDEX: {os.getenv('AZURE_SEARCH_INDEX', 'not set')}")
    print(f"AZURE_OPENAI_ENDPOINT: {'set' if os.getenv('AZURE_OPENAI_ENDPOINT') else 'not set'}")
    print(f"CHROMADB_COLLECTION_NAME: {os.getenv('CHROMADB_COLLECTION_NAME', 'not set')}")
    print(f"HUGGINGFACE_MODEL_NAME: {os.getenv('HUGGINGFACE_MODEL_NAME', 'not set')}")


if __name__ == "__main__":
    print_detection_results()
