"""Basic PDF Ingestion Playbook

This playbook demonstrates the simplest end-to-end workflow for ingesting
PDF documents into a vector store.

USE CASE:
- Process a collection of PDF documents
- Extract text and tables
- Chunk intelligently
- Generate embeddings
- Store in vector database

SCENARIO:
You have a folder of PDF documents (reports, papers, manuals) that you want
to make searchable using semantic search.

REQUIREMENTS:
- .env file configured (see .env.example companion file)
- PDF documents in input directory
- Azure credentials OR offline setup (ChromaDB + Hugging Face)

OUTPUTS:
- Vectorized chunks in your configured vector store
- Artifacts (pages, chunks, images) in artifacts directory
- Processing statistics and logs

ESTIMATED TIME:
- ~10-30 seconds per PDF (depends on size and configuration)

COST ESTIMATE (Azure):
- Document Intelligence: ~$0.001-0.01 per page
- Azure OpenAI Embeddings: ~$0.0001 per 1K tokens
- Azure Search: Included in service tier

Author: Ingestor Team
Date: 2024-02-11
Version: 1.0
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Configure logging for detailed progress tracking
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'ingestion_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

from ingestor import Pipeline
from ingestor.config import PipelineConfig


async def main():
    """Execute the basic PDF ingestion workflow."""

    logger.info("=" * 80)
    logger.info("BASIC PDF INGESTION PLAYBOOK")
    logger.info("=" * 80)
    logger.info("")

    # ========================================================================
    # STEP 1: CONFIGURATION
    # ========================================================================
    logger.info("STEP 1: Loading configuration from environment")
    logger.info("-" * 80)

    try:
        # Load configuration from .env file
        # This automatically reads all environment variables and validates them
        config = PipelineConfig.from_env()

        logger.info(f"✓ Vector Store: {config.vector_store_mode.value if config.vector_store_mode else 'N/A'}")
        logger.info(f"✓ Embeddings: {config.embeddings_mode.value if config.embeddings_mode else 'N/A'}")
        logger.info(f"✓ Input Mode: {config.input.mode.value if config.input else 'N/A'}")
        logger.info(f"✓ Input Pattern: {config.input.local_glob if config.input else 'N/A'}")
        logger.info(f"✓ Artifacts: {config.artifacts.mode.value if config.artifacts else 'N/A'}")
        logger.info("")

    except Exception as e:
        logger.error(f"✗ Configuration failed: {e}")
        logger.error("")
        logger.error("TROUBLESHOOTING:")
        logger.error("1. Ensure .env file exists in project root")
        logger.error("2. Copy from: cp envs/.env.example .env")
        logger.error("3. Fill in your credentials in .env")
        logger.error("4. See examples/playbooks/.env.basic-pdf.example for this playbook")
        return 1

    # ========================================================================
    # STEP 2: PIPELINE INITIALIZATION
    # ========================================================================
    logger.info("STEP 2: Initializing pipeline")
    logger.info("-" * 80)

    try:
        pipeline = Pipeline(config)
        logger.info("✓ Pipeline initialized successfully")
        logger.info("")
    except Exception as e:
        logger.error(f"✗ Pipeline initialization failed: {e}")
        return 1

    # ========================================================================
    # STEP 3: VALIDATION
    # ========================================================================
    logger.info("STEP 3: Validating configuration and connectivity")
    logger.info("-" * 80)

    try:
        await pipeline.validate()
        logger.info("✓ Configuration validated")
        logger.info("✓ Vector store accessible")
        logger.info("✓ Embeddings provider ready")
        logger.info("✓ Input documents found")
        logger.info("")
    except Exception as e:
        logger.error(f"✗ Validation failed: {e}")
        logger.error("")
        logger.error("COMMON ISSUES:")
        logger.error("- No documents found: Check INPUT_MODE and LOCAL_INPUT_GLOB in .env")
        logger.error("- Authentication failed: Check your API keys in .env")
        logger.error("- Index not found: Run with --setup-index first")
        logger.error("- Missing dependencies: pip install -r requirements.txt")
        await pipeline.close()
        return 1

    # ========================================================================
    # STEP 4: DOCUMENT PROCESSING
    # ========================================================================
    logger.info("STEP 4: Processing documents")
    logger.info("-" * 80)
    logger.info("This will:")
    logger.info("  1. Parse PDFs and extract text, tables, figures")
    logger.info("  2. Chunk text intelligently (layout-aware)")
    logger.info("  3. Generate embeddings for each chunk")
    logger.info("  4. Upload to vector store")
    logger.info("")

    try:
        # Run the full pipeline
        # This processes all documents matching the input pattern
        results = await pipeline.run()

        # ====================================================================
        # STEP 5: RESULTS ANALYSIS
        # ====================================================================
        logger.info("")
        logger.info("=" * 80)
        logger.info("STEP 5: Processing Results")
        logger.info("=" * 80)
        logger.info("")

        # Overall statistics
        total = len(results.results)
        successful = sum(1 for r in results.results if r.status == 'success')
        failed = sum(1 for r in results.results if r.status == 'failed')
        total_chunks = sum(r.num_chunks for r in results.results if r.status == 'success')

        logger.info(f"Total Documents: {total}")
        logger.info(f"✓ Successful: {successful}")
        logger.info(f"✗ Failed: {failed}")
        logger.info(f"Total Chunks: {total_chunks}")
        logger.info("")

        # Per-document details
        if results.results:
            logger.info("Document Details:")
            logger.info("-" * 80)
            for result in results.results:
                status_icon = "✓" if result.status == 'success' else "✗"
                logger.info(f"{status_icon} {result.filename}")
                logger.info(f"   Chunks: {result.num_chunks}")
                logger.info(f"   Status: {result.status}")
                if result.error_message:
                    logger.info(f"   Error: {result.error_message}")
                logger.info("")

        # ====================================================================
        # STEP 6: NEXT STEPS
        # ====================================================================
        logger.info("=" * 80)
        logger.info("NEXT STEPS")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Your documents are now indexed and ready for semantic search!")
        logger.info("")
        logger.info("What you can do next:")
        logger.info("1. Query your vector store using semantic search")
        logger.info("2. Inspect artifacts in the artifacts directory")
        logger.info("3. Review logs for detailed processing information")
        logger.info("4. Process more documents by adding them to input directory")
        logger.info("")

        if config.vector_store_mode and config.vector_store_mode.value == 'azure_search':
            logger.info("Azure Search specific:")
            logger.info(f"- Portal: https://portal.azure.com")
            logger.info(f"- Index: {config.search.index_name if config.search else 'N/A'}")
            logger.info(f"- Endpoint: {config.search.endpoint if config.search else 'N/A'}")
            logger.info("")
        elif config.vector_store_mode and config.vector_store_mode.value == 'chromadb':
            logger.info("ChromaDB specific:")
            logger.info(f"- Database: {config.vector_store_config.persist_directory if config.vector_store_config else 'N/A'}")
            logger.info(f"- Collection: {config.vector_store_config.collection_name if config.vector_store_config else 'N/A'}")
            logger.info("")

        return 0

    except KeyboardInterrupt:
        logger.warning("")
        logger.warning("Processing interrupted by user")
        return 130

    except Exception as e:
        logger.error("")
        logger.error("=" * 80)
        logger.error("PROCESSING ERROR")
        logger.error("=" * 80)
        logger.error(f"Error: {e}")
        logger.exception("Full traceback:")
        return 1

    finally:
        # ====================================================================
        # CLEANUP
        # ====================================================================
        logger.info("Cleaning up resources...")
        await pipeline.close()
        logger.info("✓ Cleanup complete")


if __name__ == "__main__":
    # Ensure necessary directories exist
    Path("./documents").mkdir(exist_ok=True)
    Path("./artifacts").mkdir(exist_ok=True)

    print("")
    print("=" * 80)
    print("BASIC PDF INGESTION PLAYBOOK")
    print("=" * 80)
    print("")
    print("PREREQUISITES:")
    print("1. .env file configured (see examples/playbooks/.env.basic-pdf.example)")
    print("2. PDF documents in ./documents/ directory")
    print("3. Dependencies installed: pip install -r requirements.txt")
    print("")
    print("STARTING IN 3 SECONDS...")
    print("(Press Ctrl+C to cancel)")
    print("")

    import time
    try:
        time.sleep(3)
    except KeyboardInterrupt:
        print("\nCancelled by user")
        sys.exit(130)

    # Run the playbook
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
