"""Fully Offline Setup: ChromaDB + Hugging Face Embeddings

This example demonstrates a completely offline document processing pipeline
using ChromaDB for vector storage and Hugging Face sentence-transformers
for local embedding generation.

Features:
- ✅ No internet required (after initial model download)
- ✅ Zero API costs
- ✅ Complete data privacy
- ✅ Local vector storage with persistence
- ✅ Multilingual model support

Requirements:
    pip install -r requirements-chromadb.txt
    pip install -r requirements-embeddings.txt

Usage:
    python examples/offline_chromadb_huggingface.py
"""

import asyncio
import os
from pathlib import Path

# Set environment variables before importing ingestor
os.environ.update({
    # Vector Store: ChromaDB (persistent local storage)
    "VECTOR_STORE_MODE": "chromadb",
    "CHROMADB_COLLECTION_NAME": "offline-documents",
    "CHROMADB_PERSIST_DIR": "./chroma_db",
    "CHROMADB_BATCH_SIZE": "1000",

    # Embeddings: Hugging Face (local model)
    "EMBEDDINGS_MODE": "huggingface",
    "HUGGINGFACE_MODEL_NAME": "sentence-transformers/all-MiniLM-L6-v2",  # 384 dims, fast
    "HUGGINGFACE_DEVICE": "cpu",  # or cuda, mps for GPU acceleration
    "HUGGINGFACE_BATCH_SIZE": "32",
    "HUGGINGFACE_NORMALIZE": "true",

    # Input: Local files
    "INPUT_MODE": "local",
    "LOCAL_INPUT_GLOB": "./documents/**/*.pdf",

    # Artifacts: Local storage
    "ARTIFACTS_MODE": "local",
    "LOCAL_ARTIFACTS_DIR": "./artifacts",

    # Document Processing: Offline mode (no Azure services)
    "AZURE_OFFICE_EXTRACTOR_MODE": "markitdown",

    # Chunking settings
    "AZURE_CHUNKING_MAX_CHARS": "2000",
    "AZURE_CHUNKING_MAX_TOKENS": "500",
    "AZURE_CHUNKING_OVERLAP_PERCENT": "10",

    # Logging
    "LOG_LEVEL": "INFO",
})

from ingestor import Pipeline
from ingestor.config import PipelineConfig


async def main():
    """Run the offline document processing pipeline."""

    print("=" * 80)
    print("Offline Document Processing: ChromaDB + Hugging Face")
    print("=" * 80)
    print()

    # Load configuration from environment
    print("Loading configuration...")
    config = PipelineConfig.from_env()

    print(f"✅ Vector Store: {config.vector_store_mode.value if config.vector_store_mode else 'N/A'}")
    print(f"✅ Embeddings: {config.embeddings_mode.value if config.embeddings_mode else 'N/A'}")
    print(f"✅ ChromaDB Path: {config.vector_store_config.persist_directory if config.vector_store_config else 'N/A'}")
    print()

    # Initialize pipeline
    print("Initializing pipeline...")
    pipeline = Pipeline(config)

    # Validate configuration
    print("Validating configuration...")
    try:
        await pipeline.validate()
        print("✅ Configuration valid")
    except RuntimeError as e:
        print(f"❌ Validation failed: {e}")
        print()
        print("Common issues:")
        print("- sentence-transformers not installed: pip install sentence-transformers")
        print("- chromadb not installed: pip install chromadb")
        print("- No documents found in ./documents/")
        return

    print()

    # Run pipeline
    print("Processing documents...")
    print("Note: First run will download the Hugging Face model (~90MB)")
    print("      Subsequent runs will use cached model.")
    print()

    try:
        results = await pipeline.run()

        print()
        print("=" * 80)
        print("Processing Complete!")
        print("=" * 80)
        print(f"Documents processed: {len(results.results)}")
        print(f"Total chunks: {sum(r.num_chunks for r in results.results if r.status == 'success')}")
        print(f"Success: {sum(1 for r in results.results if r.status == 'success')}")
        print(f"Failed: {sum(1 for r in results.results if r.status == 'failed')}")
        print()
        print(f"Vector database: ./chroma_db/")
        print(f"Artifacts: ./artifacts/")
        print()
        print("Your data is now fully offline and searchable!")

    except Exception as e:
        print(f"❌ Error during processing: {e}")
        raise

    finally:
        # Cleanup
        await pipeline.close()


if __name__ == "__main__":
    # Create necessary directories
    Path("./documents").mkdir(exist_ok=True)
    Path("./chroma_db").mkdir(exist_ok=True)
    Path("./artifacts").mkdir(exist_ok=True)

    print()
    print("TIP: Place your PDF files in ./documents/ directory")
    print()

    # Run the pipeline
    asyncio.run(main())
