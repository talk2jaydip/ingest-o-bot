"""Custom configuration example without environment variables."""

import asyncio
from ingestor import Pipeline, create_config
from ingestor.config import InputMode, TableRenderMode


async def main():
    """Create and run pipeline with explicit configuration."""
    print("🚀 Creating pipeline with custom configuration...")
    print()

    # Option 1: Use create_config helper
    config = create_config(
        input_glob="documents/**/*.pdf",
        azure_search_index="my-custom-index",
    )

    # Option 2: Or create full config manually (shown commented below)
    # from ingestor import PipelineConfig
    # config = PipelineConfig(
    #     # Input configuration
    #     input_mode=InputMode.LOCAL,
    #     input_glob="documents/**/*.pdf",
    #
    #     # Azure Search
    #     azure_search_service="my-search-service",
    #     azure_search_key="your-search-key-here",
    #     azure_search_index="my-index",
    #
    #     # Document Intelligence
    #     documentintelligence_endpoint="https://your-di.cognitiveservices.azure.com",
    #     documentintelligence_key="your-di-key-here",
    #
    #     # Embeddings
    #     azure_openai_endpoint="https://your-openai.openai.azure.com",
    #     azure_openai_key="your-openai-key-here",
    #     azure_openai_embedding_deployment="text-embedding-3-large",
    #     embedding_dimensions=1536,
    #
    #     # Processing options
    #     split_pdf_by_page=True,
    #     chunker_target_token_count=4000,
    #     table_render_mode=TableRenderMode.MARKDOWN,
    # )

    # Create and run pipeline
    pipeline = Pipeline(config)
    try:
        print("▶️  Running pipeline...")
        status = await pipeline.run()

        # Print results
        print()
        print("=" * 60)
        print(f"✅ Success rate: {status.successful_documents}/{status.total_documents}")
        print(f"📦 Total chunks indexed: {status.total_chunks_indexed}")
        print("=" * 60)
    finally:
        await pipeline.close()


if __name__ == "__main__":
    asyncio.run(main())
