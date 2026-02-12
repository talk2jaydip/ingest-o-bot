"""Multi-Stage Pipeline Playbook

This playbook demonstrates a sophisticated multi-stage document processing
workflow with different processing strategies for different document types.

USE CASE:
- Process multiple document collections with different requirements
- Apply different chunking strategies based on content type
- Route documents through different processing paths
- Aggregate results from multiple stages

SCENARIO:
You have documents of different types (e.g., technical manuals, legal contracts,
research papers) that need different processing approaches:
- Technical docs: Larger chunks to preserve code context
- Legal docs: Smaller chunks with more overlap for precision
- Research papers: Medium chunks optimized for academic content

REQUIREMENTS:
- .env file configured
- Multiple document folders organized by type
- Azure credentials OR offline setup

OUTPUTS:
- All document types indexed in the same vector store
- Separate artifact folders per document type
- Comprehensive processing report
- Per-stage statistics

ESTIMATED TIME:
- Varies by document count and type

Author: Ingestor Team
Date: 2024-02-11
Version: 1.0
"""

import asyncio
import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'multi_stage_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

from ingestor import Pipeline
from ingestor.config import PipelineConfig


@dataclass
class ProcessingStage:
    """Configuration for a single processing stage."""
    name: str
    description: str
    input_glob: str
    artifacts_suffix: str
    chunking_max_chars: int
    chunking_max_tokens: int
    overlap_percent: int


# Define processing stages with optimized settings for each document type
PROCESSING_STAGES = [
    ProcessingStage(
        name="Technical Documentation",
        description="Large chunks to preserve code context and technical continuity",
        input_glob="documents/technical/**/*.pdf",
        artifacts_suffix="technical",
        chunking_max_chars=3000,
        chunking_max_tokens=800,
        overlap_percent=15,
    ),
    ProcessingStage(
        name="Legal Documents",
        description="Small chunks with high overlap for precise legal search",
        input_glob="documents/legal/**/*.pdf",
        artifacts_suffix="legal",
        chunking_max_chars=1200,
        chunking_max_tokens=300,
        overlap_percent=20,
    ),
    ProcessingStage(
        name="Research Papers",
        description="Medium chunks optimized for academic content",
        input_glob="documents/research/**/*.pdf",
        artifacts_suffix="research",
        chunking_max_chars=2000,
        chunking_max_tokens=500,
        overlap_percent=12,
    ),
    ProcessingStage(
        name="General Documents",
        description="Balanced settings for mixed content types",
        input_glob="documents/general/**/*.pdf",
        artifacts_suffix="general",
        chunking_max_chars=2000,
        chunking_max_tokens=500,
        overlap_percent=10,
    ),
]


async def process_stage(stage: ProcessingStage, base_config: PipelineConfig) -> Dict[str, Any]:
    """Process a single stage with custom configuration."""

    logger.info("")
    logger.info("=" * 80)
    logger.info(f"PROCESSING STAGE: {stage.name}")
    logger.info("=" * 80)
    logger.info(f"Description: {stage.description}")
    logger.info(f"Input: {stage.input_glob}")
    logger.info(f"Chunking: {stage.chunking_max_chars} chars, {stage.chunking_max_tokens} tokens")
    logger.info(f"Overlap: {stage.overlap_percent}%")
    logger.info("")

    # Create stage-specific configuration
    import os
    os.environ.update({
        'LOCAL_INPUT_GLOB': stage.input_glob,
        'LOCAL_ARTIFACTS_DIR': f"./artifacts/{stage.artifacts_suffix}",
        'CHUNKING_MAX_CHARS': str(stage.chunking_max_chars),
        'CHUNKING_MAX_TOKENS': str(stage.chunking_max_tokens),
        'CHUNKING_OVERLAP_PERCENT': str(stage.overlap_percent),
    })

    # Reload configuration with stage-specific settings
    config = PipelineConfig.from_env()

    # Initialize pipeline for this stage
    pipeline = Pipeline(config)

    try:
        # Validate
        logger.info("Validating stage configuration...")
        await pipeline.validate()
        logger.info("✓ Configuration valid")
        logger.info("")

        # Process documents
        logger.info("Processing documents...")
        start_time = datetime.now()
        results = await pipeline.run()
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Collect statistics
        total = len(results.results)
        successful = sum(1 for r in results.results if r.status == 'success')
        failed = sum(1 for r in results.results if r.status == 'failed')
        total_chunks = sum(r.num_chunks for r in results.results if r.status == 'success')

        logger.info("")
        logger.info(f"Stage Complete: {stage.name}")
        logger.info(f"  Documents: {successful}/{total} successful")
        logger.info(f"  Chunks: {total_chunks}")
        logger.info(f"  Duration: {duration:.2f}s")
        logger.info("")

        return {
            'stage_name': stage.name,
            'description': stage.description,
            'total_documents': total,
            'successful_documents': successful,
            'failed_documents': failed,
            'total_chunks': total_chunks,
            'duration_seconds': duration,
            'documents': [
                {
                    'filename': r.filename,
                    'status': r.status,
                    'chunks': r.num_chunks,
                    'error': r.error_message if r.status == 'failed' else None,
                }
                for r in results.results
            ]
        }

    except Exception as e:
        logger.error(f"✗ Stage failed: {e}")
        logger.exception("Full traceback:")
        return {
            'stage_name': stage.name,
            'description': stage.description,
            'error': str(e),
            'total_documents': 0,
            'successful_documents': 0,
            'failed_documents': 0,
            'total_chunks': 0,
            'duration_seconds': 0,
        }

    finally:
        await pipeline.close()


async def main():
    """Execute the multi-stage pipeline workflow."""

    logger.info("=" * 80)
    logger.info("MULTI-STAGE PIPELINE PLAYBOOK")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Stages to process: {len(PROCESSING_STAGES)}")
    for stage in PROCESSING_STAGES:
        logger.info(f"  - {stage.name}: {stage.input_glob}")
    logger.info("")

    # Load base configuration
    logger.info("Loading base configuration...")
    try:
        base_config = PipelineConfig.from_env()
        logger.info(f"✓ Vector Store: {base_config.vector_store_mode.value if base_config.vector_store_mode else 'N/A'}")
        logger.info(f"✓ Embeddings: {base_config.embeddings_mode.value if base_config.embeddings_mode else 'N/A'}")
    except Exception as e:
        logger.error(f"✗ Configuration failed: {e}")
        return 1

    # Process each stage
    stage_results: List[Dict[str, Any]] = []
    overall_start = datetime.now()

    for i, stage in enumerate(PROCESSING_STAGES, 1):
        logger.info("")
        logger.info(f"Starting Stage {i}/{len(PROCESSING_STAGES)}")
        logger.info("-" * 80)

        result = await process_stage(stage, base_config)
        stage_results.append(result)

        # Brief pause between stages
        if i < len(PROCESSING_STAGES):
            await asyncio.sleep(1)

    overall_end = datetime.now()
    overall_duration = (overall_end - overall_start).total_seconds()

    # ========================================================================
    # AGGREGATE RESULTS
    # ========================================================================
    logger.info("")
    logger.info("=" * 80)
    logger.info("MULTI-STAGE PIPELINE COMPLETE")
    logger.info("=" * 80)
    logger.info("")

    # Calculate totals
    total_documents = sum(r['total_documents'] for r in stage_results)
    total_successful = sum(r['successful_documents'] for r in stage_results)
    total_failed = sum(r['failed_documents'] for r in stage_results)
    total_chunks = sum(r['total_chunks'] for r in stage_results)

    logger.info("OVERALL STATISTICS:")
    logger.info(f"  Total Stages: {len(PROCESSING_STAGES)}")
    logger.info(f"  Total Documents: {total_documents}")
    logger.info(f"  ✓ Successful: {total_successful}")
    logger.info(f"  ✗ Failed: {total_failed}")
    logger.info(f"  Total Chunks: {total_chunks}")
    logger.info(f"  Total Duration: {overall_duration:.2f}s")
    logger.info("")

    # Per-stage summary
    logger.info("PER-STAGE SUMMARY:")
    logger.info("-" * 80)
    for result in stage_results:
        logger.info(f"{result['stage_name']}:")
        logger.info(f"  Documents: {result['successful_documents']}/{result['total_documents']}")
        logger.info(f"  Chunks: {result['total_chunks']}")
        logger.info(f"  Duration: {result['duration_seconds']:.2f}s")
        if result.get('error'):
            logger.info(f"  Error: {result['error']}")
        logger.info("")

    # Save detailed report
    report_file = f"multi_stage_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'overall': {
            'total_stages': len(PROCESSING_STAGES),
            'total_documents': total_documents,
            'successful_documents': total_successful,
            'failed_documents': total_failed,
            'total_chunks': total_chunks,
            'duration_seconds': overall_duration,
        },
        'stages': stage_results,
    }

    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)

    logger.info(f"Detailed report saved: {report_file}")
    logger.info("")

    # ========================================================================
    # NEXT STEPS
    # ========================================================================
    logger.info("=" * 80)
    logger.info("NEXT STEPS")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Your multi-stage processing is complete!")
    logger.info("")
    logger.info("What you can do next:")
    logger.info("1. Review the detailed report: " + report_file)
    logger.info("2. Check artifacts in: ./artifacts/<stage-name>/")
    logger.info("3. Query your vector store for semantic search")
    logger.info("4. Compare chunk quality across different stages")
    logger.info("5. Adjust stage configurations based on results")
    logger.info("")

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    # Create directory structure for each stage
    for stage in PROCESSING_STAGES:
        # Extract document type folder from glob pattern
        # e.g., "documents/technical/**/*.pdf" -> "documents/technical"
        doc_folder = Path(stage.input_glob.split('/**')[0])
        doc_folder.mkdir(parents=True, exist_ok=True)

        # Create artifacts folder
        artifacts_folder = Path(f"./artifacts/{stage.artifacts_suffix}")
        artifacts_folder.mkdir(parents=True, exist_ok=True)

    print("")
    print("=" * 80)
    print("MULTI-STAGE PIPELINE PLAYBOOK")
    print("=" * 80)
    print("")
    print("This playbook processes documents in multiple stages with")
    print("optimized settings for each document type.")
    print("")
    print("DOCUMENT STRUCTURE:")
    print("  documents/")
    print("    technical/  - Technical manuals, code docs")
    print("    legal/      - Contracts, legal documents")
    print("    research/   - Academic papers, research")
    print("    general/    - Mixed content")
    print("")
    print("PREREQUISITES:")
    print("1. .env file configured")
    print("2. Documents organized in type-specific folders")
    print("3. Dependencies installed")
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
