"""Production Deployment Playbook

This playbook demonstrates best practices for production deployment of
document ingestion pipelines with enterprise Azure services.

USE CASE:
- Production document processing at scale
- Enterprise-grade reliability and performance
- Cloud-native architecture with Azure services
- Scheduled batch processing or event-driven workflows

SCENARIO:
You're deploying a production document processing system that:
- Processes documents from Azure Blob Storage
- Uses Azure AI Search for vector storage
- Leverages Azure Document Intelligence for extraction
- Stores artifacts in blob storage
- Handles failures gracefully
- Provides comprehensive monitoring

REQUIREMENTS:
- Azure subscription with required resources
- .env file with production credentials
- Azure Storage containers created
- Azure Search index configured
- Monitoring and alerting setup

OUTPUTS:
- Documents indexed in Azure AI Search
- Artifacts stored in Azure Blob Storage
- Processing metrics and logs
- Error reports for failed documents

ESTIMATED TIME:
- ~10-30 seconds per PDF (depends on size and configuration)

COST ESTIMATE:
- Document Intelligence: ~$0.001-0.01 per page
- Azure OpenAI Embeddings: ~$0.0001 per 1K tokens
- Azure Search: Included in service tier
- Azure Storage: ~$0.02 per GB/month

Author: Ingestor Team
Date: 2024-02-11
Version: 1.0
"""

import asyncio
import logging
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Production-grade logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'production_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

from ingestor import Pipeline
from ingestor.config import PipelineConfig


def validate_environment() -> bool:
    """Validate that all required environment variables are set for production."""
    required_vars = [
        # Azure Search
        ('AZURE_SEARCH_SERVICE', 'Azure AI Search service name'),
        ('AZURE_SEARCH_INDEX', 'Azure AI Search index name'),
        ('AZURE_SEARCH_KEY', 'Azure AI Search admin key'),

        # Azure OpenAI
        ('AZURE_OPENAI_ENDPOINT', 'Azure OpenAI endpoint'),
        ('AZURE_OPENAI_KEY', 'Azure OpenAI API key'),
        ('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', 'Azure OpenAI embedding deployment'),

        # Azure Document Intelligence
        ('AZURE_DOC_INT_ENDPOINT', 'Azure Document Intelligence endpoint'),
        ('AZURE_DOC_INT_KEY', 'Azure Document Intelligence key'),

        # Azure Storage
        ('AZURE_STORAGE_ACCOUNT', 'Azure Storage account name'),
        ('AZURE_STORAGE_CONTAINER', 'Azure Storage input container'),
    ]

    missing = []
    for var, description in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(f"{var} ({description})")
        elif value.startswith('your-') or value == 'documents':
            # Check for placeholder values
            logger.warning(f"⚠️  {var} appears to be a placeholder: {value}")

    if missing:
        logger.error("=" * 80)
        logger.error("MISSING REQUIRED ENVIRONMENT VARIABLES")
        logger.error("=" * 80)
        for item in missing:
            logger.error(f"  ✗ {item}")
        logger.error("")
        logger.error("Please configure these in your .env file")
        logger.error("See: examples/playbooks/.env.production.example")
        return False

    return True


def check_production_readiness() -> Dict[str, Any]:
    """Perform production readiness checks."""
    checks = {
        'environment': True,
        'dependencies': True,
        'configuration': True,
        'connectivity': True,
    }
    issues = []

    # Check 1: Environment variables
    logger.info("Checking environment configuration...")
    if not validate_environment():
        checks['environment'] = False
        issues.append("Missing required environment variables")

    # Check 2: Dependencies
    logger.info("Checking dependencies...")
    try:
        import azure.search.documents
        import azure.ai.formrecognizer
        import azure.storage.blob
    except ImportError as e:
        checks['dependencies'] = False
        issues.append(f"Missing dependency: {e}")

    # Check 3: Configuration values
    logger.info("Checking configuration...")

    # Ensure production-appropriate settings
    input_mode = os.getenv('INPUT_MODE', 'local')
    if input_mode == 'local':
        logger.warning("⚠️  INPUT_MODE=local is not recommended for production")
        logger.warning("   Consider using INPUT_MODE=blob for production")

    artifacts_mode = os.getenv('ARTIFACTS_MODE', 'local')
    if artifacts_mode == 'local':
        logger.warning("⚠️  ARTIFACTS_MODE=local is not recommended for production")
        logger.warning("   Consider using ARTIFACTS_MODE=blob for production")

    # Check performance settings
    max_workers = int(os.getenv('AZURE_CHUNKING_MAX_WORKERS', '4'))
    if max_workers > 16:
        logger.warning(f"⚠️  MAX_WORKERS={max_workers} may cause rate limiting")

    # Log production settings
    logger.info("")
    logger.info("Production Configuration:")
    logger.info(f"  Input Mode: {input_mode}")
    logger.info(f"  Artifacts Mode: {artifacts_mode}")
    logger.info(f"  Max Workers: {max_workers}")
    logger.info(f"  Office Extractor: {os.getenv('AZURE_OFFICE_EXTRACTOR_MODE', 'hybrid')}")
    logger.info(f"  Media Describer: {os.getenv('AZURE_MEDIA_DESCRIBER', 'disabled')}")
    logger.info("")

    return {
        'passed': all(checks.values()),
        'checks': checks,
        'issues': issues,
    }


async def main():
    """Execute the production deployment workflow."""

    logger.info("=" * 80)
    logger.info("PRODUCTION DEPLOYMENT PLAYBOOK")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Started at: {datetime.now().isoformat()}")
    logger.info("")

    # ========================================================================
    # STEP 1: PRODUCTION READINESS CHECKS
    # ========================================================================
    logger.info("STEP 1: Production Readiness Checks")
    logger.info("-" * 80)

    readiness = check_production_readiness()

    if not readiness['passed']:
        logger.error("=" * 80)
        logger.error("PRODUCTION READINESS FAILED")
        logger.error("=" * 80)
        logger.error("")
        logger.error("Issues found:")
        for issue in readiness['issues']:
            logger.error(f"  ✗ {issue}")
        logger.error("")
        logger.error("Please resolve these issues before running in production")
        return 1

    logger.info("✓ Production readiness checks passed")
    logger.info("")

    # ========================================================================
    # STEP 2: CONFIGURATION
    # ========================================================================
    logger.info("STEP 2: Loading production configuration")
    logger.info("-" * 80)

    try:
        config = PipelineConfig.from_env()

        logger.info("Production Configuration Loaded:")
        logger.info(f"  Vector Store: {config.vector_store_mode.value if config.vector_store_mode else 'N/A'}")
        logger.info(f"  Embeddings: {config.embeddings_mode.value if config.embeddings_mode else 'N/A'}")
        logger.info(f"  Search Index: {config.search.index_name if config.search else 'N/A'}")
        logger.info(f"  Input: {config.input.mode.value if config.input else 'N/A'}")
        logger.info("")

    except Exception as e:
        logger.error(f"✗ Configuration failed: {e}")
        logger.exception("Full traceback:")
        return 1

    # ========================================================================
    # STEP 3: PIPELINE INITIALIZATION
    # ========================================================================
    logger.info("STEP 3: Initializing production pipeline")
    logger.info("-" * 80)

    try:
        pipeline = Pipeline(config)
        logger.info("✓ Pipeline initialized")
        logger.info("")
    except Exception as e:
        logger.error(f"✗ Pipeline initialization failed: {e}")
        logger.exception("Full traceback:")
        return 1

    # ========================================================================
    # STEP 4: VALIDATION
    # ========================================================================
    logger.info("STEP 4: Validating connectivity and resources")
    logger.info("-" * 80)

    try:
        await pipeline.validate()
        logger.info("✓ Azure Search accessible")
        logger.info("✓ Document Intelligence accessible")
        logger.info("✓ Azure OpenAI accessible")
        logger.info("✓ Azure Storage accessible")
        logger.info("✓ Input documents found")
        logger.info("")
    except Exception as e:
        logger.error(f"✗ Validation failed: {e}")
        logger.exception("Full traceback:")
        await pipeline.close()
        return 1

    # ========================================================================
    # STEP 5: PROCESSING
    # ========================================================================
    logger.info("STEP 5: Processing documents")
    logger.info("-" * 80)
    logger.info("Starting production document processing...")
    logger.info("")

    try:
        start_time = datetime.now()
        results = await pipeline.run()
        end_time = datetime.now()

        processing_duration = (end_time - start_time).total_seconds()

        # ====================================================================
        # STEP 6: RESULTS ANALYSIS
        # ====================================================================
        logger.info("")
        logger.info("=" * 80)
        logger.info("PRODUCTION PROCESSING COMPLETE")
        logger.info("=" * 80)
        logger.info("")

        total = len(results.results)
        successful = sum(1 for r in results.results if r.status == 'success')
        failed = sum(1 for r in results.results if r.status == 'failed')
        total_chunks = sum(r.num_chunks for r in results.results if r.status == 'success')

        logger.info("PRODUCTION METRICS:")
        logger.info(f"  Start Time: {start_time.isoformat()}")
        logger.info(f"  End Time: {end_time.isoformat()}")
        logger.info(f"  Duration: {processing_duration:.2f}s ({processing_duration/60:.2f}m)")
        logger.info(f"  Total Documents: {total}")
        logger.info(f"  Successful: {successful}")
        logger.info(f"  Failed: {failed}")
        logger.info(f"  Success Rate: {(successful/total*100) if total > 0 else 0:.2f}%")
        logger.info(f"  Total Chunks: {total_chunks}")
        logger.info(f"  Avg Chunks/Doc: {(total_chunks/successful) if successful > 0 else 0:.1f}")
        logger.info(f"  Avg Time/Doc: {(processing_duration/total) if total > 0 else 0:.2f}s")
        logger.info("")

        # Document details
        if results.results:
            logger.info("Document Processing Details:")
            logger.info("-" * 80)
            for result in results.results:
                status = "✓" if result.status == 'success' else "✗"
                logger.info(f"{status} {result.filename}")
                logger.info(f"   Chunks: {result.num_chunks}")
                if result.error_message:
                    logger.error(f"   Error: {result.error_message}")
            logger.info("")

        # ====================================================================
        # STEP 7: SAVE PRODUCTION METRICS
        # ====================================================================
        logger.info("STEP 7: Saving production metrics")
        logger.info("-" * 80)

        metrics = {
            'timestamp': datetime.now().isoformat(),
            'environment': 'production',
            'configuration': {
                'vector_store': config.vector_store_mode.value if config.vector_store_mode else None,
                'embeddings': config.embeddings_mode.value if config.embeddings_mode else None,
                'search_index': config.search.index_name if config.search else None,
                'input_mode': config.input.mode.value if config.input else None,
            },
            'metrics': {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': processing_duration,
                'total_documents': total,
                'successful_documents': successful,
                'failed_documents': failed,
                'success_rate_percent': (successful/total*100) if total > 0 else 0,
                'total_chunks': total_chunks,
                'avg_chunks_per_document': (total_chunks/successful) if successful > 0 else 0,
                'avg_time_per_document': (processing_duration/total) if total > 0 else 0,
            },
            'results': [
                {
                    'filename': r.filename,
                    'status': r.status,
                    'chunks': r.num_chunks,
                    'error': r.error_message if r.status == 'failed' else None,
                }
                for r in results.results
            ]
        }

        metrics_file = f"production_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)

        logger.info(f"✓ Metrics saved: {metrics_file}")
        logger.info("")

        # ====================================================================
        # STEP 8: ALERTING (if failures)
        # ====================================================================
        if failed > 0:
            logger.warning("=" * 80)
            logger.warning("FAILURES DETECTED")
            logger.warning("=" * 80)
            logger.warning(f"{failed} document(s) failed processing")
            logger.warning("Please review logs and metrics for details")
            logger.warning("")
            logger.warning("Failed documents:")
            for result in results.results:
                if result.status == 'failed':
                    logger.warning(f"  ✗ {result.filename}: {result.error_message}")
            logger.warning("")

        # ====================================================================
        # STEP 9: PRODUCTION RECOMMENDATIONS
        # ====================================================================
        logger.info("=" * 80)
        logger.info("PRODUCTION RECOMMENDATIONS")
        logger.info("=" * 80)
        logger.info("")

        logger.info("Monitoring:")
        logger.info("- Review production_metrics_*.json for processing statistics")
        logger.info("- Set up Azure Monitor alerts for failures")
        logger.info("- Monitor Azure Search index size and query performance")
        logger.info("- Track Azure OpenAI token usage for cost optimization")
        logger.info("")

        logger.info("Optimization:")
        logger.info("- Adjust AZURE_CHUNKING_MAX_WORKERS based on throughput needs")
        logger.info("- Consider batch processing during off-peak hours")
        logger.info("- Implement document deduplication if needed")
        logger.info("- Review chunk sizes for your query patterns")
        logger.info("")

        logger.info("Reliability:")
        logger.info("- Implement retry logic for transient failures")
        logger.info("- Set up backup/archival for processed documents")
        logger.info("- Monitor API rate limits and quotas")
        logger.info("- Implement health checks and heartbeats")
        logger.info("")

        return 0 if failed == 0 else 1

    except KeyboardInterrupt:
        logger.warning("Processing interrupted by user")
        return 130

    except Exception as e:
        logger.error("=" * 80)
        logger.error("PRODUCTION ERROR")
        logger.error("=" * 80)
        logger.error(f"Error: {e}")
        logger.exception("Full traceback:")

        # Save error report
        error_report = {
            'timestamp': datetime.now().isoformat(),
            'environment': 'production',
            'error_type': type(e).__name__,
            'error_message': str(e),
        }

        error_file = f"production_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(error_file, 'w') as f:
            json.dump(error_report, f, indent=2)

        logger.error(f"Error report saved: {error_file}")
        return 1

    finally:
        logger.info("Cleaning up resources...")
        await pipeline.close()
        logger.info("✓ Cleanup complete")


if __name__ == "__main__":
    print("")
    print("=" * 80)
    print("PRODUCTION DEPLOYMENT PLAYBOOK")
    print("=" * 80)
    print("")
    print("⚠️  WARNING: This is a PRODUCTION playbook")
    print("")
    print("Before running:")
    print("1. Verify .env has production credentials")
    print("2. Ensure Azure resources are created and accessible")
    print("3. Confirm INPUT_MODE=blob and ARTIFACTS_MODE=blob for production")
    print("4. Review and adjust performance settings")
    print("5. Set up monitoring and alerting")
    print("")
    print("This playbook will:")
    print("- Process documents from Azure Blob Storage")
    print("- Index into Azure AI Search")
    print("- Store artifacts in Azure Blob Storage")
    print("- Generate production metrics")
    print("")
    print("STARTING IN 5 SECONDS...")
    print("(Press Ctrl+C to cancel)")
    print("")

    import time
    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("\nCancelled by user")
        sys.exit(130)

    exit_code = asyncio.run(main())
    sys.exit(exit_code)
