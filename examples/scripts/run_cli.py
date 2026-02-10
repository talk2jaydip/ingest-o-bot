"""
CLI wrapper script with examples for running the ingestor from command line.

This script demonstrates all CLI options and provides a convenience wrapper.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ingestor import run_pipeline, PipelineConfig
from ingestor.config import DocumentAction
from dotenv import load_dotenv


async def run_cli(args):
    """Run the ingestor pipeline with CLI arguments."""

    # Load environment file if specified
    if args.env_path:
        env_path = Path(args.env_path)
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
            print(f"✅ Loaded environment from: {env_path.absolute()}")
        else:
            print(f"⚠️  Environment file not found: {env_path}")
    else:
        load_dotenv()
        print("✅ Loaded environment from default .env")

    # Determine document action
    action_map = {
        "add": DocumentAction.ADD,
        "remove": DocumentAction.REMOVE,
        "remove-all": DocumentAction.REMOVE_ALL
    }
    document_action = action_map.get(args.action, DocumentAction.ADD)

    # Build kwargs for run_pipeline
    kwargs = {
        "input_glob": args.input,
        "document_action": document_action
    }

    # Add optional arguments if provided
    if args.search_index:
        kwargs["azure_search_index"] = args.search_index

    if args.max_workers:
        kwargs["performance_max_workers"] = args.max_workers

    if args.openai_concurrency:
        kwargs["azure_openai_max_concurrency"] = args.openai_concurrency

    if args.di_concurrency:
        kwargs["azure_di_max_concurrency"] = args.di_concurrency

    if args.integrated_vectorization:
        kwargs["use_integrated_vectorization"] = True

    if args.chunking_max_tokens:
        kwargs["chunking_max_tokens"] = args.chunking_max_tokens

    if args.chunking_overlap:
        kwargs["chunking_overlap_percent"] = args.chunking_overlap

    # Run pipeline
    print(f"\n🔄 Starting pipeline...")
    print(f"   Input: {args.input}")
    print(f"   Action: {args.action}")
    if args.max_workers:
        print(f"   Max workers: {args.max_workers}")
    if args.integrated_vectorization:
        print(f"   Integrated vectorization: enabled")

    try:
        status = await run_pipeline(**kwargs)

        print(f"\n✅ Pipeline complete!")
        print(f"   Documents processed: {status.successful_documents}")
        print(f"   Documents failed: {status.failed_documents}")
        print(f"   Total chunks indexed: {status.total_chunks_indexed}")

        # Show per-document results
        if len(status.results) > 0:
            print(f"\n📄 Per-document results:")
            for result in status.results:
                icon = "✅" if result.success else "❌"
                print(f"   {icon} {result.filename}: {result.processing_time_seconds:.2f}s ({result.chunks_indexed} chunks)")
                if not result.success:
                    print(f"      Error: {result.error_message}")

        return 0

    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ingestor CLI - Process documents and index them into Azure AI Search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

  # Process single document
  python run_cli.py --input "document.pdf"

  # Process all PDFs in directory
  python run_cli.py --input "documents/*.pdf"

  # Process recursively
  python run_cli.py --input "documents/**/*.pdf"

  # With performance optimizations
  python run_cli.py --input "docs/*.pdf" --max-workers 4 --integrated-vectorization

  # Custom environment file
  python run_cli.py --input "docs/*.pdf" --env-path ".env.production"

  # Remove documents
  python run_cli.py --input "document.pdf" --action remove

  # Remove all documents
  python run_cli.py --action remove-all

Full documentation: https://github.com/your-org/ingestor
        """
    )

    # Required arguments
    parser.add_argument(
        "--input",
        type=str,
        help="Input glob pattern (e.g., 'documents/*.pdf', 'docs/**/*.pdf')"
    )

    # Environment
    parser.add_argument(
        "--env-path",
        type=str,
        help="Path to .env file (default: .env)"
    )

    # Azure services
    parser.add_argument(
        "--search-index",
        type=str,
        help="Azure Search index name (overrides env)"
    )

    # Performance
    parser.add_argument(
        "--max-workers",
        type=int,
        help="Maximum parallel workers for document processing (default: 4)"
    )

    parser.add_argument(
        "--openai-concurrency",
        type=int,
        help="Maximum concurrent OpenAI requests (default: 10)"
    )

    parser.add_argument(
        "--di-concurrency",
        type=int,
        help="Maximum concurrent Document Intelligence requests (default: 5)"
    )

    parser.add_argument(
        "--integrated-vectorization",
        action="store_true",
        help="Use integrated vectorization (server-side embeddings)"
    )

    # Chunking
    parser.add_argument(
        "--chunking-max-tokens",
        type=int,
        help="Maximum tokens per chunk (default: 1000)"
    )

    parser.add_argument(
        "--chunking-overlap",
        type=int,
        help="Chunk overlap percentage (default: 15)"
    )

    # Actions
    parser.add_argument(
        "--action",
        type=str,
        choices=["add", "remove", "remove-all"],
        default="add",
        help="Document action: add, remove, or remove-all (default: add)"
    )

    args = parser.parse_args()

    # Validate required arguments
    if not args.input and args.action != "remove-all":
        parser.error("--input is required unless using --action remove-all")

    # Run async pipeline
    exit_code = asyncio.run(run_cli(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
