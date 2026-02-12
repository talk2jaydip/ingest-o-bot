"""Command-line interface for ingestor."""

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to allow running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from ingestor.config import DocumentAction, InputMode, PipelineConfig
from ingestor.pipeline import Pipeline
from ingestor.logging_utils import setup_logging


async def main():
    """Main CLI entry point."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Document ingestion pipeline for Azure AI Search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate configuration and environment (pre-check)
  python -m ingestor.cli --validate

  # Use a specific environment file (e.g., offline mode with ChromaDB + Hugging Face)
  python -m ingestor.cli --env .env.offline --glob "data/*.pdf"

  # Deploy/update index ONLY (no ingestion)
  python -m ingestor.cli --index-only

  # Delete index ONLY (no ingestion)
  python -m ingestor.cli --delete-index

  # Force recreate index ONLY (delete + create, no ingestion)
  python -m ingestor.cli --force-index

  # Deploy index and then ingest documents
  python -m ingestor.cli --setup-index --glob "documents/*.pdf"

  # Ingest documents ONLY (no index operations)
  python -m ingestor.cli --glob "documents/*.pdf"

  # Process a single PDF file
  python -m ingestor.cli --pdf "my_document.pdf"

  # Process all supported file types
  python -m ingestor.cli --glob "documents/**/*"

  # Remove specific documents from index
  python -m ingestor.cli --action remove --glob "my_document.pdf"

  # Remove ALL documents from index (WARNING!)
  python -m ingestor.cli --action removeall

  # Verbose logging
  python -m ingestor.cli --verbose --glob "documents/*.pdf"
        """
    )
    parser.add_argument(
        "--env",
        "--env-file",
        dest="env_file",
        type=str,
        metavar="PATH",
        default=".env",
        help="Path to environment file (default: .env). Use this to test different configurations, e.g., --env .env.offline"
    )
    parser.add_argument(
        "--pdf",
        "--file",
        dest="pdf_path",
        type=str,
        metavar="PATH",
        help="Path to file to process (overrides AZURE_LOCAL_GLOB)"
    )
    parser.add_argument(
        "--glob",
        type=str,
        metavar="PATTERN",
        help="Glob pattern for local files (overrides AZURE_LOCAL_GLOB), e.g., 'documents/*.pdf'"
    )
    parser.add_argument(
        "--action",
        type=str,
        choices=["add", "remove", "removeall"],
        default=None,
        help="Document action: add (default), remove (by filename), removeall (WARNING: removes ALL documents)"
    )
    parser.add_argument(
        "--setup-index",
        action="store_true",
        help="Deploy/update the Azure AI Search index before ingestion"
    )
    parser.add_argument(
        "--force-index",
        action="store_true",
        help="Force delete and recreate index, then EXIT (WARNING: destroys all data in index)"
    )
    parser.add_argument(
        "--index-only",
        action="store_true",
        help="Only deploy/update index, skip document ingestion pipeline"
    )
    parser.add_argument(
        "--delete-index",
        action="store_true",
        help="Delete the index only (WARNING: destroys all data in index)"
    )
    parser.add_argument(
        "--skip-ingestion",
        action="store_true",
        help="Skip document ingestion pipeline (useful with --setup-index or --delete-index)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose/debug logging"
    )
    parser.add_argument(
        "--no-colors",
        action="store_true",
        help="Disable colorful console output (useful for CI/CD or log files)"
    )
    parser.add_argument(
        "--check-index",
        action="store_true",
        help="Check if index exists, then exit (no ingestion)"
    )
    parser.add_argument(
        "--clean-artifacts",
        action="store_true",
        help="Clean blob artifacts for specified files (use with --glob or --action remove)"
    )
    parser.add_argument(
        "--clean-all-artifacts",
        action="store_true",
        help="Clean ALL blob artifacts (WARNING: destructive!)"
    )
    parser.add_argument(
        "--validate",
        "--pre-check",
        dest="validate_only",
        action="store_true",
        help="Run pre-check validation on configuration and environment, then exit (no document processing)"
    )
    args = parser.parse_args()

    # Load environment variables from specified .env file
    env_file_path = Path(args.env_file)
    if env_file_path.exists():
        load_dotenv(dotenv_path=env_file_path, override=True)
        print(f"✓ Loaded environment from: {env_file_path}")
    else:
        print(f"⚠️  Environment file not found: {env_file_path}")
        print(f"⚠️  Continuing with system environment variables...")

    # Validate environment parameters for typos and issues
    from ingestor.config_validator import validate_environment
    warnings, errors = validate_environment(warn_only=True)
    if warnings:
        print(f"\n⚠️  Found {len(warnings)} environment parameter warnings:")
        for warning in warnings[:5]:  # Show first 5 warnings
            print(f"  {warning}")
        if len(warnings) > 5:
            print(f"  ... and {len(warnings) - 5} more warnings")
        print()

    # Validate scenario configuration
    from ingestor.scenario_validator import validate_current_environment
    scenario_result = validate_current_environment(verbose=False)
    if scenario_result.scenario:
        if scenario_result.valid:
            print(f"✓ Detected scenario: {scenario_result.scenario.value}")
        else:
            print(f"\n⚠️  Configuration issues detected for scenario: {scenario_result.scenario.value}")
            if scenario_result.errors:
                print(f"   Errors: {len(scenario_result.errors)}")
                for error in scenario_result.errors[:3]:
                    print(f"     - {error}")
            print(f"   Run 'python -m ingestor.scenario_validator' for detailed help")
            print()

    # Load logging configuration from environment
    from ingestor.config import LoggingConfig
    logging_config = LoggingConfig.from_env()

    # Override with verbose flag if provided
    if args.verbose:
        logging_config.console_level = "DEBUG"
        logging_config.file_level = "DEBUG"

    # Override with no-colors flag if provided
    if args.no_colors:
        logging_config.use_colors = False

    # Setup comprehensive logging with configured levels and colors
    logger, log_dir = setup_logging(
        console_level=logging_config.console_level,
        file_level=logging_config.file_level,
        use_colors=logging_config.use_colors
    )

    logger.info("="*70)
    logger.info("ingestor - Document Ingestion Pipeline")
    logger.info("="*70)
    logger.info(f"Console log level: {logging_config.console_level}")
    logger.info(f"File log level: {logging_config.file_level}")
    logger.info(f"Write artifact logs: {logging_config.write_artifacts}")
    logger.info(f"Colorful console output: {logging_config.use_colors}")

    try:
        # Handle validation operation
        if args.validate_only:
            logger.info("")
            logger.info("=" * 70)
            logger.info("Running Pre-Check Validation")
            logger.info("=" * 70)
            logger.info("")

            try:
                # Load configuration
                config = PipelineConfig.from_env()

                # Create pipeline with validate_only flag
                pipeline = Pipeline(config, log_dir=log_dir, validate_only=True)

                # Run validation (this will exit after validation)
                await pipeline.run()

                logger.info("")
                logger.info("=" * 70)
                logger.info("✅ Validation Complete - Pipeline is Ready!")
                logger.info("=" * 70)
                logger.info("")
                logger.info("Your pipeline configuration is valid and all dependencies are available.")
                logger.info("You can now run the pipeline normally without the --validate flag.")
                logger.info("")
                sys.exit(0)

            except RuntimeError as e:
                logger.error("")
                logger.error("=" * 70)
                logger.error("❌ Validation Failed")
                logger.error("=" * 70)
                logger.error(str(e))
                logger.error("")
                sys.exit(1)
            except Exception as e:
                logger.error(f"ERROR: Validation failed with unexpected error: {e}", exc_info=args.verbose)
                sys.exit(1)

        # Handle check index operation
        if args.check_index:
            logger.info("")
            logger.info("=" * 70)
            logger.info("Checking Azure AI Search Index")
            logger.info("=" * 70)

            try:
                temp_config = PipelineConfig.from_env()
                from ingestor.index import IndexDeploymentManager

                search_endpoint = temp_config.search.endpoint
                search_key = temp_config.search.api_key
                index_name = temp_config.search.index_name

                logger.info(f"Checking index: {index_name}")

                manager = IndexDeploymentManager(
                    endpoint=search_endpoint,
                    api_key=search_key,
                    index_name=index_name,
                    verbose=args.verbose
                )

                # Check if index exists
                exists = manager.index_exists()

                if exists:
                    logger.info(f"✓ Index '{index_name}' exists")
                    sys.exit(0)
                else:
                    logger.warning(f"✗ Index '{index_name}' does not exist")
                    logger.info("Run with --setup-index to create it")
                    sys.exit(1)

            except Exception as e:
                logger.error(f"ERROR: Failed to check index: {e}", exc_info=args.verbose)
                sys.exit(1)

        # Handle clean all artifacts operation
        if args.clean_all_artifacts:
            logger.info("")
            logger.info("=" * 70)
            logger.info("Clean ALL Blob Artifacts (WARNING: DESTRUCTIVE!)")
            logger.info("=" * 70)

            try:
                temp_config = PipelineConfig.from_env()
                from ingestor.artifact_storage import create_artifact_storage

                # Create artifact storage
                artifact_storage = create_artifact_storage(temp_config.artifacts)

                logger.warning("WARNING: This will delete ALL artifacts from blob storage!")
                logger.warning(f"Artifacts mode: {temp_config.artifacts.mode}")

                if temp_config.artifacts.mode.value != "blob":
                    logger.error("ERROR: --clean-all-artifacts only works with blob artifacts mode")
                    sys.exit(1)

                # Delete all artifacts
                deleted_count = await artifact_storage.delete_all_artifacts()

                logger.info(f"✓ Deleted {deleted_count} blobs from all containers")
                sys.exit(0)

            except Exception as e:
                logger.error(f"ERROR: Failed to clean artifacts: {e}", exc_info=args.verbose)
                sys.exit(1)

        # Handle clean specific artifacts operation
        if args.clean_artifacts and not args.action:
            logger.info("")
            logger.info("=" * 70)
            logger.info("Clean Blob Artifacts for Specific Files")
            logger.info("=" * 70)

            if not (args.pdf_path or args.glob):
                logger.error("ERROR: --clean-artifacts requires --pdf or --glob to specify files")
                sys.exit(1)

            try:
                temp_config = PipelineConfig.from_env()
                from ingestor.artifact_storage import create_artifact_storage
                from ingestor.input_source import create_input_source

                # Override input config if PDF path or glob provided
                if args.pdf_path:
                    temp_config.input.mode = InputMode.LOCAL
                    temp_config.input.local_glob = args.pdf_path
                elif args.glob:
                    temp_config.input.mode = InputMode.LOCAL
                    temp_config.input.local_glob = args.glob

                if temp_config.artifacts.mode.value != "blob":
                    logger.error("ERROR: --clean-artifacts only works with blob artifacts mode")
                    sys.exit(1)

                # Create storage
                artifact_storage = create_artifact_storage(temp_config.artifacts)
                input_source = create_input_source(temp_config.input)

                # Process each file
                total_deleted = 0
                async for filename, _, _ in input_source.list_files():
                    logger.info(f"Cleaning artifacts for: {filename}")
                    deleted_count = await artifact_storage.delete_document_artifacts(filename)
                    total_deleted += deleted_count
                    logger.info(f"  Deleted {deleted_count} blobs")

                logger.info(f"✓ Total deleted: {total_deleted} blobs")
                sys.exit(0)

            except Exception as e:
                logger.error(f"ERROR: Failed to clean artifacts: {e}", exc_info=args.verbose)
                sys.exit(1)

        # Handle delete index operation
        if args.delete_index:
            logger.info("")
            logger.info("=" * 70)
            logger.info("Azure AI Search Index Deletion")
            logger.info("=" * 70)

            try:
                temp_config = PipelineConfig.from_env()
                from ingestor.index import IndexDeploymentManager
                from azure.core.exceptions import ResourceNotFoundError

                search_endpoint = temp_config.search.endpoint
                search_key = temp_config.search.api_key
                index_name = temp_config.search.index_name

                logger.warning(f"WARNING: Deleting index: {index_name}")
                logger.warning(f"WARNING: This will destroy all data in the index!")
                logger.info("")

                manager = IndexDeploymentManager(
                    endpoint=search_endpoint,
                    api_key=search_key,
                    index_name=index_name,
                    verbose=args.verbose
                )

                # Delete the index
                success = manager.delete_index()

                if not success:
                    logger.error("ERROR: Index deletion failed")
                    sys.exit(1)

                logger.info("")
                logger.info("SUCCESS: Index deleted successfully")
                logger.info("")

                # Exit after deletion (delete-index is standalone operation)
                logger.info("Delete operation completed. Exiting.")
                sys.exit(0)

            except ResourceNotFoundError:
                logger.warning(f"WARNING: Index '{temp_config.search.index_name}' does not exist")
                logger.info("Nothing to delete.")
                sys.exit(0)
            except Exception as e:
                logger.error(f"ERROR: Index deletion failed: {e}", exc_info=args.verbose)
                sys.exit(1)

        # Handle force-index operation (standalone: delete + recreate, then exit)
        if args.force_index and not args.setup_index:
            logger.info("")
            logger.info("=" * 70)
            logger.info("Force Recreate Index (Delete + Create)")
            logger.info("=" * 70)

            try:
                temp_config = PipelineConfig.from_env()
                from ingestor.index import IndexDeploymentManager
                from azure.core.exceptions import ResourceNotFoundError

                search_endpoint = temp_config.search.endpoint
                search_key = temp_config.search.api_key
                index_name = temp_config.search.index_name

                # Optional: OpenAI for integrated vectorizer
                openai_endpoint = temp_config.azure_openai.endpoint
                openai_deployment = temp_config.azure_openai.emb_deployment
                openai_key = temp_config.azure_openai.api_key

                logger.warning(f"WARNING: Force recreating index: {index_name}")
                logger.warning(f"WARNING: This will destroy all existing data!")
                logger.info("")

                manager = IndexDeploymentManager(
                    endpoint=search_endpoint,
                    api_key=search_key,
                    index_name=index_name,
                    openai_endpoint=openai_endpoint,
                    openai_deployment=openai_deployment,
                    openai_key=openai_key,
                    verbose=args.verbose
                )

                # Step 1: Delete existing index (gracefully handle if not exists)
                logger.info("Step 1: Deleting existing index...")
                try:
                    success = manager.delete_index()
                    if success:
                        logger.info("SUCCESS: Index deleted")
                except ResourceNotFoundError:
                    logger.info("INFO: Index did not exist (will create new)")

                logger.info("")

                # Step 2: Create new index
                logger.info("Step 2: Creating new index...")
                # skip_if_exists=False: We just deleted, so expect fresh creation
                success = manager.deploy_index(dry_run=False, force=False, skip_if_exists=False)

                if not success:
                    logger.error("ERROR: Index creation failed")
                    sys.exit(1)

                logger.info("")
                logger.info("SUCCESS: Index recreated successfully")
                logger.info("")

                # Exit after force recreation (force-index is standalone operation)
                logger.info("Force recreate operation completed. Exiting.")
                sys.exit(0)

            except Exception as e:
                logger.error(f"ERROR: Force recreate failed: {e}", exc_info=args.verbose)
                sys.exit(1)

        # Step 1: Deploy/update index if requested
        if args.setup_index or args.index_only:
            logger.info("")
            logger.info("=" * 70)
            logger.info("STEP 1: Azure AI Search Index Deployment")
            logger.info("=" * 70)
            
            try:
                # Import index deployment module here to avoid dependency if not using it

                # Temporarily load config to get search settings
                temp_config = PipelineConfig.from_env()
                
                # Import index deployment
                from ingestor.index import IndexDeploymentManager
                
                # Extract search service name from endpoint
                search_endpoint = temp_config.search.endpoint
                search_key = temp_config.search.api_key
                index_name = temp_config.search.index_name
                
                # Optional: OpenAI for integrated vectorizer
                openai_endpoint = temp_config.azure_openai.endpoint
                openai_deployment = temp_config.azure_openai.emb_deployment
                openai_key = temp_config.azure_openai.api_key
                
                logger.info(f"Search endpoint: {search_endpoint}")
                logger.info(f"Index name: {index_name}")
                logger.info(f"Force recreate: {args.force_index}")
                logger.info("")
                
                # Create deployment manager
                manager = IndexDeploymentManager(
                    endpoint=search_endpoint,
                    api_key=search_key,
                    index_name=index_name,
                    openai_endpoint=openai_endpoint,
                    openai_deployment=openai_deployment,
                    openai_key=openai_key,
                    verbose=args.verbose
                )
                
                # Deploy index
                # skip_if_exists=True means: if index exists, just acknowledge it (don't fail)
                success = manager.deploy_index(dry_run=False, force=args.force_index, skip_if_exists=True)

                if not success:
                    logger.error("ERROR: Index deployment failed")
                    sys.exit(1)
                
                logger.info("")
                logger.info("SUCCESS: Index deployment completed successfully")
                logger.info("")

                # Exit if index-only flag is set
                if args.index_only:
                    logger.info("Index-only mode: skipping document ingestion")
                    sys.exit(0)

            except ImportError as e:
                logger.error(f"ERROR: Failed to import index deployment module: {e}")
                logger.error("Make sure all required packages are installed")
                sys.exit(1)
            except Exception as e:
                logger.error(f"ERROR: Index deployment failed: {e}", exc_info=args.verbose)
                sys.exit(1)

        # Exit if skip-ingestion is set (and index operations are done)
        if args.skip_ingestion:
            logger.info("Skipping document ingestion pipeline (--skip-ingestion)")
            sys.exit(0)

        # Check if input files are provided before proceeding to ingestion
        # Load temp config to check if input source is configured
        temp_config = PipelineConfig.from_env()
        has_cli_input = bool(args.pdf_path or args.glob)
        has_env_input = bool(
            (temp_config.input.mode == InputMode.LOCAL and temp_config.input.local_glob) or
            (temp_config.input.mode == InputMode.BLOB and temp_config.input.blob_container_in)
        )

        # If --setup-index was used alone without input files, exit gracefully
        if args.setup_index and not has_cli_input and not has_env_input and not args.action:
            logger.info("")
            logger.info("=" * 70)
            logger.info("Index setup completed successfully!")
            logger.info("=" * 70)
            logger.info("")
            logger.info("No input files specified for ingestion.")
            logger.info("To ingest documents, use:")
            logger.info("  --glob 'path/to/files/*.pdf'")
            logger.info("  --pdf 'path/to/file.pdf'")
            logger.info("  Or set AZURE_LOCAL_GLOB or AZURE_BLOB_CONTAINER_IN in .env")
            logger.info("")
            sys.exit(0)

        # Step 2 or 3: Load configuration for ingestion
        step_num = 1
        if args.delete_index:
            step_num += 1
        if args.setup_index or args.index_only:
            step_num += 1

        logger.info("=" * 70)
        logger.info(f"STEP {step_num}: Document Ingestion Pipeline")
        logger.info("=" * 70)
        logger.info("Loading configuration from environment variables...")
        config = PipelineConfig.from_env()
        
        # Override input config if PDF path or glob provided via CLI
        if args.pdf_path:
            logger.info(f"Overriding input with file path: {args.pdf_path}")
            config.input.mode = InputMode.LOCAL
            config.input.local_glob = args.pdf_path
        elif args.glob:
            logger.info(f"Overriding input with glob pattern: {args.glob}")
            config.input.mode = InputMode.LOCAL
            config.input.local_glob = args.glob
        
        # Override document action if specified
        if args.action:
            config.document_action = DocumentAction(args.action)
            logger.info(f"Overriding document action: {config.document_action.value}")

        logger.info(f"Configuration loaded:")
        logger.info(f"  Document action: {config.document_action.value}")
        logger.info(f"  Input mode: {config.input.mode}")
        logger.info(f"  Input source: {config.input.local_glob if config.input.mode == InputMode.LOCAL else config.input.blob_container_in}")
        logger.info(f"  Artifacts mode: {config.artifacts.mode}")
        logger.info(f"  Search index: {config.search.index_name}")
        logger.info(f"  Media describer: {config.media_describer_mode}")
        logger.info(f"  Table rendering: {config.table_render_mode}")
        logger.info(f"  Embedding mode: {'Integrated Vectorization' if config.use_integrated_vectorization else 'Client-Side'}")
        if config.azure_openai.emb_dimensions:
            logger.info(f"  Embedding dimensions: {config.azure_openai.emb_dimensions}")
        logger.info(f"  Max retries: {config.azure_openai.max_retries}")
        logger.info(f"  Log directory: {log_dir}")
        logger.info("="*70)

        # Create and run pipeline
        pipeline = Pipeline(config, log_dir=log_dir, clean_artifacts=args.clean_artifacts)

        try:
            await pipeline.run()
        except ValueError as e:
            if "No files found to process" in str(e):
                logger.error("="*70)
                logger.error("ERROR: No files found to process")
                logger.error("="*70)
                logger.error("")
                logger.error("Please specify input files using one of these methods:")
                logger.error("")
                logger.error("1. Command line options:")
                logger.error("   --glob 'path/to/files/*.pdf'  (process multiple files)")
                logger.error("   --pdf 'path/to/file.pdf'      (process single file)")
                logger.error("")
                logger.error("2. Environment variables in .env:")
                logger.error("   AZURE_LOCAL_GLOB=path/to/files/*.pdf")
                logger.error("   OR")
                logger.error("   AZURE_BLOB_CONTAINER_IN=your-container-name")
                logger.error("")
                logger.error("3. Index operations only (without ingestion):")
                logger.error("   --setup-index   (create/update index, then ingest)")
                logger.error("   --index-only    (create/update index, skip ingestion)")
                logger.error("   --delete-index  (delete index)")
                logger.error("")
                logger.error(f"Current configuration:")
                logger.error(f"  Input mode: {config.input.mode.value}")
                if config.input.mode == InputMode.LOCAL:
                    logger.error(f"  Local glob: {config.input.local_glob or '(not set)'}")
                else:
                    logger.error(f"  Blob container: {config.input.blob_container_in or '(not set)'}")
                logger.error("")
                sys.exit(1)
            else:
                raise
        
        logger.info("="*70)
        logger.info("Pipeline completed successfully!")
        logger.info(f"All logs saved to: {log_dir}")
        logger.info("="*70)
    
    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error("="*70)
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        logger.error("="*70)
        sys.exit(1)


def cli_main():
    """Synchronous entry point for console script."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
