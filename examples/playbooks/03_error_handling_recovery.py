"""Error Handling and Recovery Playbook

This playbook demonstrates robust error handling, validation, retry logic,
and recovery strategies for production document processing workflows.

USE CASE:
- Process large document collections with reliability
- Handle failures gracefully without stopping entire pipeline
- Retry failed documents with exponential backoff
- Save progress and resume from failures
- Generate detailed error reports

SCENARIO:
You're processing a large collection of documents in production and need:
- Graceful handling of problematic documents
- Automatic retry with backoff for transient failures
- Checkpoint/resume capability for long-running jobs
- Detailed error tracking and reporting
- Separate processing of failed documents

REQUIREMENTS:
- .env file configured
- Documents in input directory (some may be problematic)
- Write access for checkpoint and error logs

OUTPUTS:
- Successfully processed documents in vector store
- Failed documents tracked in error report
- Checkpoint file for resuming interrupted processing
- Detailed failure analysis

ESTIMATED TIME:
- Varies by document count and failure rate
- Includes retry delays

Author: Ingestor Team
Date: 2024-02-11
Version: 1.0
"""

import asyncio
import logging
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'error_recovery_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

from ingestor import Pipeline
from ingestor.config import PipelineConfig


@dataclass
class ProcessingCheckpoint:
    """Checkpoint for resumable processing."""
    timestamp: str
    total_documents: int
    processed_documents: List[str]
    failed_documents: Dict[str, str]
    successful_documents: List[str]
    checkpoint_hash: str


@dataclass
class ErrorDetails:
    """Detailed error information for a failed document."""
    filename: str
    error_type: str
    error_message: str
    timestamp: str
    retry_count: int
    stack_trace: Optional[str] = None


class ResilientPipeline:
    """Wrapper around Pipeline with error handling and retry logic."""

    def __init__(self, config: PipelineConfig, max_retries: int = 3,
                 retry_delay_base: float = 2.0, checkpoint_file: str = "processing_checkpoint.json"):
        self.config = config
        self.max_retries = max_retries
        self.retry_delay_base = retry_delay_base
        self.checkpoint_file = checkpoint_file
        self.processed: Set[str] = set()
        self.successful: List[str] = []
        self.failed: Dict[str, ErrorDetails] = {}

    def _calculate_backoff_delay(self, retry_count: int) -> float:
        """Calculate exponential backoff delay."""
        return self.retry_delay_base ** retry_count

    def _get_file_hash(self, filepath: str) -> str:
        """Get hash of file for tracking."""
        path = Path(filepath)
        if not path.exists():
            return hashlib.md5(filepath.encode()).hexdigest()

        # Hash file path and modification time
        hash_input = f"{filepath}:{path.stat().st_mtime}"
        return hashlib.md5(hash_input.encode()).hexdigest()

    def save_checkpoint(self):
        """Save current processing state to checkpoint file."""
        checkpoint = ProcessingCheckpoint(
            timestamp=datetime.now().isoformat(),
            total_documents=len(self.processed),
            processed_documents=list(self.processed),
            failed_documents={f: asdict(e) for f, e in self.failed.items()},
            successful_documents=self.successful,
            checkpoint_hash=hashlib.md5(
                json.dumps(sorted(self.processed)).encode()
            ).hexdigest(),
        )

        with open(self.checkpoint_file, 'w') as f:
            json.dump(asdict(checkpoint), f, indent=2)

        logger.info(f"✓ Checkpoint saved: {self.checkpoint_file}")

    def load_checkpoint(self) -> bool:
        """Load checkpoint from file if exists."""
        if not Path(self.checkpoint_file).exists():
            logger.info("No checkpoint found, starting fresh")
            return False

        try:
            with open(self.checkpoint_file, 'r') as f:
                data = json.load(f)

            self.processed = set(data['processed_documents'])
            self.successful = data['successful_documents']
            self.failed = {
                f: ErrorDetails(**e) for f, e in data['failed_documents'].items()
            }

            logger.info(f"✓ Checkpoint loaded: {len(self.processed)} documents already processed")
            logger.info(f"  Successful: {len(self.successful)}")
            logger.info(f"  Failed: {len(self.failed)}")
            return True

        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            return False

    async def process_with_retry(self, document_path: str, retry_count: int = 0) -> bool:
        """Process a single document with retry logic."""

        if retry_count > 0:
            delay = self._calculate_backoff_delay(retry_count - 1)
            logger.info(f"  Retry {retry_count}/{self.max_retries} after {delay:.1f}s delay")
            await asyncio.sleep(delay)

        try:
            # Create single-document configuration
            import os
            os.environ['LOCAL_INPUT_GLOB'] = document_path

            config = PipelineConfig.from_env()
            pipeline = Pipeline(config)

            try:
                # Validate
                await pipeline.validate()

                # Process
                results = await pipeline.run()

                # Check results
                if results.results and results.results[0].status == 'success':
                    logger.info(f"  ✓ Success: {document_path}")
                    self.successful.append(document_path)
                    self.processed.add(document_path)
                    return True
                else:
                    error_msg = results.results[0].error_message if results.results else "Unknown error"
                    raise RuntimeError(error_msg)

            finally:
                await pipeline.close()

        except Exception as e:
            error_msg = str(e)
            logger.warning(f"  ✗ Failed: {document_path} - {error_msg}")

            # Retry logic
            if retry_count < self.max_retries:
                # Check if this is a retryable error
                retryable_errors = [
                    'timeout',
                    'connection',
                    'throttle',
                    'rate limit',
                    '429',
                    '503',
                ]

                if any(err in error_msg.lower() for err in retryable_errors):
                    logger.info(f"  Retryable error detected, will retry...")
                    return await self.process_with_retry(document_path, retry_count + 1)

            # Record failure
            import traceback
            self.failed[document_path] = ErrorDetails(
                filename=document_path,
                error_type=type(e).__name__,
                error_message=error_msg,
                timestamp=datetime.now().isoformat(),
                retry_count=retry_count,
                stack_trace=traceback.format_exc(),
            )
            self.processed.add(document_path)
            return False

    async def process_all(self, document_paths: List[str]) -> Dict:
        """Process all documents with error handling."""

        logger.info(f"Processing {len(document_paths)} documents")
        logger.info(f"Max retries: {self.max_retries}")
        logger.info(f"Retry delay base: {self.retry_delay_base}s")
        logger.info("")

        start_time = datetime.now()

        for i, doc_path in enumerate(document_paths, 1):
            # Skip if already processed (from checkpoint)
            if doc_path in self.processed:
                logger.info(f"[{i}/{len(document_paths)}] Skipping (already processed): {doc_path}")
                continue

            logger.info(f"[{i}/{len(document_paths)}] Processing: {doc_path}")

            try:
                await self.process_with_retry(doc_path)

            except KeyboardInterrupt:
                logger.warning("Processing interrupted by user")
                self.save_checkpoint()
                raise

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                logger.exception("Full traceback:")

            # Save checkpoint periodically (every 10 documents)
            if i % 10 == 0:
                self.save_checkpoint()

        # Final checkpoint
        self.save_checkpoint()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return {
            'total': len(document_paths),
            'successful': len(self.successful),
            'failed': len(self.failed),
            'duration_seconds': duration,
        }


async def main():
    """Execute the error handling and recovery workflow."""

    logger.info("=" * 80)
    logger.info("ERROR HANDLING AND RECOVERY PLAYBOOK")
    logger.info("=" * 80)
    logger.info("")

    # ========================================================================
    # STEP 1: CONFIGURATION
    # ========================================================================
    logger.info("STEP 1: Loading configuration")
    logger.info("-" * 80)

    try:
        base_config = PipelineConfig.from_env()
        logger.info(f"✓ Vector Store: {base_config.vector_store_mode.value if base_config.vector_store_mode else 'N/A'}")
        logger.info(f"✓ Embeddings: {base_config.embeddings_mode.value if base_config.embeddings_mode else 'N/A'}")
    except Exception as e:
        logger.error(f"✗ Configuration failed: {e}")
        return 1

    logger.info("")

    # ========================================================================
    # STEP 2: DISCOVER DOCUMENTS
    # ========================================================================
    logger.info("STEP 2: Discovering documents")
    logger.info("-" * 80)

    from glob import glob
    input_pattern = base_config.input.local_glob if base_config.input else "documents/**/*.pdf"
    document_paths = glob(input_pattern, recursive=True)

    if not document_paths:
        logger.error(f"✗ No documents found matching: {input_pattern}")
        return 1

    logger.info(f"✓ Found {len(document_paths)} documents")
    logger.info("")

    # ========================================================================
    # STEP 3: INITIALIZE RESILIENT PIPELINE
    # ========================================================================
    logger.info("STEP 3: Initializing resilient pipeline")
    logger.info("-" * 80)

    # Configuration
    MAX_RETRIES = 3
    RETRY_DELAY_BASE = 2.0  # seconds
    CHECKPOINT_FILE = "processing_checkpoint.json"

    resilient_pipeline = ResilientPipeline(
        config=base_config,
        max_retries=MAX_RETRIES,
        retry_delay_base=RETRY_DELAY_BASE,
        checkpoint_file=CHECKPOINT_FILE,
    )

    # Try to resume from checkpoint
    resumed = resilient_pipeline.load_checkpoint()
    if resumed:
        logger.info("✓ Resuming from previous checkpoint")
    else:
        logger.info("✓ Starting fresh processing")

    logger.info("")

    # ========================================================================
    # STEP 4: PROCESS DOCUMENTS
    # ========================================================================
    logger.info("STEP 4: Processing documents with error handling")
    logger.info("-" * 80)

    try:
        results = await resilient_pipeline.process_all(document_paths)

        # ====================================================================
        # STEP 5: RESULTS AND ERROR ANALYSIS
        # ====================================================================
        logger.info("")
        logger.info("=" * 80)
        logger.info("PROCESSING COMPLETE")
        logger.info("=" * 80)
        logger.info("")

        logger.info("OVERALL STATISTICS:")
        logger.info(f"  Total Documents: {results['total']}")
        logger.info(f"  ✓ Successful: {results['successful']}")
        logger.info(f"  ✗ Failed: {results['failed']}")
        logger.info(f"  Success Rate: {results['successful']/results['total']*100:.1f}%")
        logger.info(f"  Duration: {results['duration_seconds']:.2f}s")
        logger.info("")

        # Error analysis
        if resilient_pipeline.failed:
            logger.info("FAILED DOCUMENTS:")
            logger.info("-" * 80)

            # Group by error type
            error_types: Dict[str, List[str]] = {}
            for doc, error in resilient_pipeline.failed.items():
                error_type = error.error_type
                if error_type not in error_types:
                    error_types[error_type] = []
                error_types[error_type].append(doc)

            for error_type, docs in error_types.items():
                logger.info(f"{error_type}: {len(docs)} document(s)")
                for doc in docs[:5]:  # Show first 5
                    error = resilient_pipeline.failed[doc]
                    logger.info(f"  - {doc}")
                    logger.info(f"    Error: {error.error_message[:100]}...")
                    logger.info(f"    Retries: {error.retry_count}")
                if len(docs) > 5:
                    logger.info(f"  ... and {len(docs) - 5} more")
                logger.info("")

            # Save detailed error report
            error_report_file = f"error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            error_report = {
                'timestamp': datetime.now().isoformat(),
                'summary': results,
                'errors': {doc: asdict(error) for doc, error in resilient_pipeline.failed.items()},
            }

            with open(error_report_file, 'w') as f:
                json.dump(error_report, f, indent=2)

            logger.info(f"Detailed error report saved: {error_report_file}")
            logger.info("")

        # ====================================================================
        # STEP 6: RECOMMENDATIONS
        # ====================================================================
        logger.info("=" * 80)
        logger.info("RECOMMENDATIONS")
        logger.info("=" * 80)
        logger.info("")

        if resilient_pipeline.failed:
            logger.info("Actions to take for failed documents:")
            logger.info("1. Review error_report_*.json for detailed failure information")
            logger.info("2. Check if failures are due to:")
            logger.info("   - Corrupted or invalid files")
            logger.info("   - API rate limits (consider reducing concurrency)")
            logger.info("   - Insufficient permissions")
            logger.info("   - Unsupported file formats")
            logger.info("3. Fix issues and re-run (will skip successful documents)")
            logger.info("4. Consider increasing max_retries for transient errors")
            logger.info("")

        logger.info("To resume processing after fixing issues:")
        logger.info(f"  python {__file__}")
        logger.info("  (Will automatically resume from checkpoint)")
        logger.info("")

        logger.info("To start fresh:")
        logger.info(f"  rm {CHECKPOINT_FILE}")
        logger.info(f"  python {__file__}")
        logger.info("")

        return 0 if results['failed'] == 0 else 1

    except KeyboardInterrupt:
        logger.warning("Processing interrupted by user")
        logger.info("Checkpoint saved. Run again to resume.")
        return 130

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    Path("./documents").mkdir(exist_ok=True)
    Path("./artifacts").mkdir(exist_ok=True)

    print("")
    print("=" * 80)
    print("ERROR HANDLING AND RECOVERY PLAYBOOK")
    print("=" * 80)
    print("")
    print("This playbook demonstrates robust error handling with:")
    print("- Automatic retry with exponential backoff")
    print("- Checkpoint/resume for interrupted processing")
    print("- Detailed error tracking and reporting")
    print("- Graceful handling of problematic documents")
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

    exit_code = asyncio.run(main())
    sys.exit(exit_code)
