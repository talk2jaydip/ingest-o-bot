"""Monitor pipeline progress with streaming logs."""

import asyncio
import logging
from ingestor import Pipeline, PipelineConfig


# Set up logging to see progress
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def main():
    """Run pipeline with detailed logging."""
    print("🚀 Starting pipeline with detailed logging...")
    print("📊 Watch the logs below for real-time progress")
    print("=" * 60)
    print()

    # Load configuration from environment
    config = PipelineConfig.from_env()

    # Create and run pipeline
    pipeline = Pipeline(config)
    try:
        status = await pipeline.run()

        # Show detailed results
        print()
        print("=" * 60)
        print("📋 Final Results:")
        print("=" * 60)
        for result in status.results:
            if result.success:
                print(f"✅ {result.filename}: {result.chunks_indexed} chunks")
            else:
                print(f"❌ {result.filename}: {result.error_message}")
        print("=" * 60)
    finally:
        await pipeline.close()


if __name__ == "__main__":
    asyncio.run(main())
