"""Local Development Playbook

This playbook demonstrates a complete local development setup for testing
and iterating on document processing workflows.

USE CASE:
- Rapid development and testing without cloud costs
- Inspect artifacts locally for debugging
- Test different configurations quickly
- Validate changes before production deployment

SCENARIO:
You're developing a new document processing feature or testing the pipeline
with sample documents. You want:
- Fast iteration cycle
- Local artifact inspection
- No cloud API costs
- Full control over processing parameters

REQUIREMENTS:
- Python 3.10+
- pip install -r requirements-chromadb.txt requirements-embeddings.txt
- Optional: LibreOffice for Office document processing
- Sample documents in ./documents/

OUTPUTS:
- ChromaDB database in ./chroma_db/
- Artifacts (pages, chunks, images) in ./artifacts/
- Processing logs for debugging
- Performance metrics

ESTIMATED TIME:
- Setup: ~5 minutes (includes model download)
- Processing: ~5-15 seconds per PDF

COST:
- FREE (no cloud services)

Author: Ingestor Team
Date: 2024-02-11
Version: 1.0
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
import time

# Configure development-friendly logging
logging.basicConfig(
    level=logging.DEBUG,  # Detailed logging for development
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'dev_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

# Set environment for local development BEFORE importing ingestor
os.environ.update({
    # ========================================================================
    # VECTOR STORE: ChromaDB (Local, Persistent)
    # ========================================================================
    "VECTOR_STORE_MODE": "chromadb",
    "CHROMADB_COLLECTION_NAME": "dev-documents",
    "CHROMADB_PERSIST_DIR": "./chroma_db",
    "CHROMADB_BATCH_SIZE": "1000",

    # ========================================================================
    # EMBEDDINGS: Hugging Face (Local, Free)
    # ========================================================================
    "EMBEDDINGS_MODE": "huggingface",
    # Fast model for development (good balance of speed and quality)
    "HUGGINGFACE_MODEL_NAME": "sentence-transformers/all-MiniLM-L6-v2",  # 384 dims, fast
    # For better quality in dev, use: "sentence-transformers/all-mpnet-base-v2"  # 768 dims
    "HUGGINGFACE_DEVICE": "cpu",  # Use "cuda" or "mps" if GPU available
    "HUGGINGFACE_BATCH_SIZE": "32",
    "HUGGINGFACE_NORMALIZE": "true",

    # ========================================================================
    # INPUT: Local Files
    # ========================================================================
    "INPUT_MODE": "local",
    "LOCAL_INPUT_GLOB": "./documents/**/*.{pdf,txt,md}",

    # ========================================================================
    # ARTIFACTS: Local Directory
    # ========================================================================
    "ARTIFACTS_MODE": "local",
    "LOCAL_ARTIFACTS_DIR": "./artifacts",
    "LOG_ARTIFACTS": "true",

    # ========================================================================
    # DOCUMENT PROCESSING: Offline Mode
    # ========================================================================
    # No Azure Document Intelligence - use MarkItDown instead
    "AZURE_OFFICE_EXTRACTOR_MODE": "markitdown",
    # No media descriptions for faster processing
    "AZURE_MEDIA_DESCRIBER": "disabled",

    # ========================================================================
    # CHUNKING: Development Settings
    # ========================================================================
    "CHUNKING_MAX_CHARS": "1500",  # Smaller for faster processing
    "CHUNKING_MAX_TOKENS": "400",
    "CHUNKING_OVERLAP_PERCENT": "10",
    "CHUNKING_CROSS_PAGE_OVERLAP": "false",

    # ========================================================================
    # PERFORMANCE: Development Settings
    # ========================================================================
    "AZURE_CHUNKING_MAX_WORKERS": "2",  # Lower for easier debugging
    "AZURE_CHUNKING_MAX_IMAGE_CONCURRENCY": "4",
    "AZURE_CHUNKING_MAX_BATCH_UPLOAD_CONCURRENCY": "2",

    # ========================================================================
    # LOGGING: Verbose for Development
    # ========================================================================
    "LOG_LEVEL": "DEBUG",
    "LOG_FILE_LEVEL": "DEBUG",
    "LOG_USE_COLORS": "true",
})

from ingestor import Pipeline
from ingestor.config import PipelineConfig


def check_dependencies():
    """Check if required dependencies are installed."""
    missing_deps = []

    try:
        import chromadb
    except ImportError:
        missing_deps.append("chromadb")

    try:
        import sentence_transformers
    except ImportError:
        missing_deps.append("sentence-transformers")

    try:
        import torch
    except ImportError:
        missing_deps.append("torch")

    if missing_deps:
        logger.error("Missing required dependencies:")
        for dep in missing_deps:
            logger.error(f"  - {dep}")
        logger.error("")
        logger.error("Install with:")
        logger.error("  pip install -r requirements-chromadb.txt")
        logger.error("  pip install -r requirements-embeddings.txt")
        return False

    return True


def inspect_artifacts(artifacts_dir: str):
    """Inspect and display artifacts for development debugging."""
    logger.info("")
    logger.info("=" * 80)
    logger.info("ARTIFACT INSPECTION")
    logger.info("=" * 80)
    logger.info("")

    artifacts_path = Path(artifacts_dir)
    if not artifacts_path.exists():
        logger.warning("No artifacts directory found")
        return

    # Count artifacts by type
    pages = list(artifacts_path.glob("*_pages/**/*"))
    chunks = list(artifacts_path.glob("*_chunks/**/*"))
    images = list(artifacts_path.glob("*_images/**/*"))

    logger.info(f"Artifacts saved to: {artifacts_path.absolute()}")
    logger.info(f"  Pages: {len(pages)} files")
    logger.info(f"  Chunks: {len(chunks)} files")
    logger.info(f"  Images: {len(images)} files")
    logger.info("")

    # Show example chunk
    if chunks:
        example_chunk = chunks[0]
        logger.info(f"Example chunk: {example_chunk.name}")
        try:
            content = example_chunk.read_text(encoding='utf-8')
            logger.info("Content preview:")
            logger.info("-" * 80)
            logger.info(content[:500] + ("..." if len(content) > 500 else ""))
            logger.info("-" * 80)
        except Exception as e:
            logger.warning(f"Could not read chunk: {e}")

    logger.info("")


def inspect_chromadb(persist_dir: str, collection_name: str):
    """Inspect ChromaDB contents for development debugging."""
    logger.info("")
    logger.info("=" * 80)
    logger.info("CHROMADB INSPECTION")
    logger.info("=" * 80)
    logger.info("")

    try:
        import chromadb

        client = chromadb.PersistentClient(path=persist_dir)
        collection = client.get_collection(name=collection_name)

        count = collection.count()
        logger.info(f"Collection: {collection_name}")
        logger.info(f"Total vectors: {count}")
        logger.info("")

        # Get sample entries
        if count > 0:
            results = collection.get(limit=3, include=['documents', 'metadatas'])

            logger.info("Sample entries:")
            logger.info("-" * 80)
            for i, (doc_id, doc, meta) in enumerate(zip(
                results['ids'],
                results['documents'],
                results['metadatas']
            ), 1):
                logger.info(f"{i}. ID: {doc_id}")
                logger.info(f"   Document: {doc[:150]}...")
                logger.info(f"   Metadata: {meta}")
                logger.info("")

    except Exception as e:
        logger.warning(f"Could not inspect ChromaDB: {e}")

    logger.info("")


async def main():
    """Execute the local development workflow."""

    logger.info("=" * 80)
    logger.info("LOCAL DEVELOPMENT PLAYBOOK")
    logger.info("=" * 80)
    logger.info("")

    # ========================================================================
    # STEP 0: DEPENDENCY CHECK
    # ========================================================================
    logger.info("STEP 0: Checking dependencies")
    logger.info("-" * 80)

    if not check_dependencies():
        return 1

    logger.info("✓ All dependencies installed")
    logger.info("")

    # ========================================================================
    # STEP 1: CONFIGURATION
    # ========================================================================
    logger.info("STEP 1: Loading development configuration")
    logger.info("-" * 80)

    try:
        config = PipelineConfig.from_env()

        logger.info("Development Configuration:")
        logger.info(f"  Vector Store: {config.vector_store_mode.value if config.vector_store_mode else 'N/A'}")
        logger.info(f"  Embeddings: {config.embeddings_mode.value if config.embeddings_mode else 'N/A'}")
        logger.info(f"  Model: {os.getenv('HUGGINGFACE_MODEL_NAME')}")
        logger.info(f"  Device: {os.getenv('HUGGINGFACE_DEVICE')}")
        logger.info(f"  Input: {config.input.local_glob if config.input else 'N/A'}")
        logger.info(f"  Artifacts: {os.getenv('LOCAL_ARTIFACTS_DIR')}")
        logger.info(f"  ChromaDB: {os.getenv('CHROMADB_PERSIST_DIR')}")
        logger.info("")

    except Exception as e:
        logger.error(f"✗ Configuration failed: {e}")
        return 1

    # ========================================================================
    # STEP 2: PIPELINE INITIALIZATION
    # ========================================================================
    logger.info("STEP 2: Initializing pipeline")
    logger.info("-" * 80)

    pipeline = Pipeline(config)

    # ========================================================================
    # STEP 3: VALIDATION
    # ========================================================================
    logger.info("STEP 3: Validating configuration")
    logger.info("-" * 80)

    try:
        await pipeline.validate()
        logger.info("✓ Configuration valid")
        logger.info("✓ ChromaDB accessible")
        logger.info("✓ Embedding model ready (will download if first run)")
        logger.info("✓ Input documents found")
        logger.info("")
    except Exception as e:
        logger.error(f"✗ Validation failed: {e}")
        await pipeline.close()
        return 1

    # ========================================================================
    # STEP 4: PROCESSING
    # ========================================================================
    logger.info("STEP 4: Processing documents")
    logger.info("-" * 80)
    logger.info("Note: First run will download embedding model (~80-400MB)")
    logger.info("      Subsequent runs will use cached model")
    logger.info("")

    try:
        start_time = time.time()
        results = await pipeline.run()
        end_time = time.time()

        processing_time = end_time - start_time

        # ====================================================================
        # STEP 5: RESULTS
        # ====================================================================
        logger.info("")
        logger.info("=" * 80)
        logger.info("PROCESSING RESULTS")
        logger.info("=" * 80)
        logger.info("")

        total = len(results.results)
        successful = sum(1 for r in results.results if r.status == 'success')
        failed = sum(1 for r in results.results if r.status == 'failed')
        total_chunks = sum(r.num_chunks for r in results.results if r.status == 'success')

        logger.info(f"Documents: {successful}/{total} successful")
        logger.info(f"Chunks: {total_chunks}")
        logger.info(f"Processing Time: {processing_time:.2f}s")
        logger.info(f"Avg Time/Doc: {processing_time/total:.2f}s")
        logger.info("")

        # Per-document details
        if results.results:
            logger.info("Document Details:")
            logger.info("-" * 80)
            for result in results.results:
                status = "✓" if result.status == 'success' else "✗"
                logger.info(f"{status} {result.filename}: {result.num_chunks} chunks")
                if result.error_message:
                    logger.info(f"   Error: {result.error_message}")

        # ====================================================================
        # STEP 6: INSPECTION
        # ====================================================================
        # Inspect artifacts for development debugging
        inspect_artifacts(os.getenv('LOCAL_ARTIFACTS_DIR', './artifacts'))

        # Inspect ChromaDB
        inspect_chromadb(
            os.getenv('CHROMADB_PERSIST_DIR', './chroma_db'),
            os.getenv('CHROMADB_COLLECTION_NAME', 'dev-documents')
        )

        # ====================================================================
        # STEP 7: DEVELOPMENT TIPS
        # ====================================================================
        logger.info("=" * 80)
        logger.info("DEVELOPMENT TIPS")
        logger.info("=" * 80)
        logger.info("")
        logger.info("✓ Your documents are now indexed in ChromaDB")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Inspect artifacts in ./artifacts/ for debugging")
        logger.info("2. Query ChromaDB directly:")
        logger.info("   >>> import chromadb")
        logger.info("   >>> client = chromadb.PersistentClient('./chroma_db')")
        logger.info("   >>> collection = client.get_collection('dev-documents')")
        logger.info("   >>> results = collection.query(query_texts=['your query'], n_results=5)")
        logger.info("")
        logger.info("3. Modify settings in this script and re-run")
        logger.info("4. Try different embedding models (edit HUGGINGFACE_MODEL_NAME)")
        logger.info("5. Adjust chunking parameters for your use case")
        logger.info("")
        logger.info("Performance optimization:")
        logger.info("- Use GPU if available (HUGGINGFACE_DEVICE=cuda or mps)")
        logger.info("- Increase batch sizes for faster processing")
        logger.info("- Use smaller model for faster embedding (all-MiniLM-L6-v2)")
        logger.info("- Use larger model for better quality (all-mpnet-base-v2)")
        logger.info("")

        return 0

    except Exception as e:
        logger.error(f"✗ Processing failed: {e}")
        logger.exception("Full traceback:")
        return 1

    finally:
        await pipeline.close()


if __name__ == "__main__":
    # Create directories
    Path("./documents").mkdir(exist_ok=True)
    Path("./artifacts").mkdir(exist_ok=True)
    Path("./chroma_db").mkdir(exist_ok=True)

    print("")
    print("=" * 80)
    print("LOCAL DEVELOPMENT PLAYBOOK")
    print("=" * 80)
    print("")
    print("This playbook demonstrates a complete local development setup:")
    print("- ChromaDB for vector storage (persistent, local)")
    print("- Hugging Face for embeddings (free, offline)")
    print("- Local artifacts for debugging")
    print("- Detailed logging for development")
    print("")
    print("REQUIREMENTS:")
    print("  pip install -r requirements-chromadb.txt")
    print("  pip install -r requirements-embeddings.txt")
    print("")
    print("COST: FREE (no cloud services)")
    print("")
    print("Place PDF files in ./documents/ directory")
    print("")
    print("STARTING IN 3 SECONDS...")
    print("")

    import time
    try:
        time.sleep(3)
    except KeyboardInterrupt:
        print("\nCancelled by user")
        sys.exit(130)

    exit_code = asyncio.run(main())
    sys.exit(exit_code)
