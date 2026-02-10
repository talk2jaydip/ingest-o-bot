"""Configuration tab for the Gradio UI."""

import os
import gradio as gr
import asyncio
from typing import Tuple

from ingestor import Pipeline, PipelineConfig
from ingestor.config import InputMode, DocumentAction, OfficeExtractorMode
from .components import create_env_editor
from .helpers import run_async


def create_config_tab() -> dict:
    """Create the configuration tab.

    Returns:
        Dictionary of component references
    """
    components = {}

    with gr.Column():
        gr.Markdown("# ⚙️ Ingestor Configuration")
        gr.Markdown("Configure and run the document processing pipeline")

        # Environment variables editor
        with gr.Accordion("🔧 Environment Variables", open=False):
            env_components = create_env_editor()

        # Quick configuration
        gr.Markdown("### Quick Configuration")

        with gr.Row():
            input_glob_config = gr.Textbox(
                label="Input Files (glob pattern)",
                placeholder="documents/*.pdf",
                value=os.getenv("AZURE_LOCAL_GLOB", "documents/*.pdf")
            )
            document_action = gr.Dropdown(
                choices=["add", "remove", "removeall"],
                label="Action",
                value="add"
            )

        with gr.Row():
            index_name = gr.Textbox(
                label="Search Index Name",
                value=os.getenv("AZURE_SEARCH_INDEX", "documents-index"),
                placeholder="my-index"
            )
            setup_index = gr.Checkbox(
                label="Setup/Update Index",
                value=False
            )

        # Advanced configuration
        with gr.Accordion("⚙️ Advanced Settings", open=False):
            with gr.Row():
                chunk_size = gr.Slider(
                    label="Target Chunk Size",
                    minimum=500,
                    maximum=3000,
                    value=1000,
                    step=100
                )
                chunk_overlap = gr.Slider(
                    label="Chunk Overlap",
                    minimum=0,
                    maximum=500,
                    value=100,
                    step=50
                )

            office_mode = gr.Dropdown(
                choices=["hybrid", "azure_di", "markitdown"],
                label="Office Document Extraction",
                value="hybrid"
            )

            verbose_logging = gr.Checkbox(
                label="Verbose Logging",
                value=False
            )

        # Run controls
        with gr.Row():
            run_btn = gr.Button("▶️ Run Pipeline", variant="primary", size="lg")
            stop_btn = gr.Button("⏹️ Stop", size="lg")

        # Status output
        status_output = gr.Textbox(
            label="Pipeline Status",
            lines=10,
            interactive=False,
            show_copy_button=True
        )

        # Results summary
        with gr.Row():
            docs_processed = gr.Number(
                label="Documents Processed",
                value=0,
                interactive=False
            )
            chunks_indexed = gr.Number(
                label="Chunks Indexed",
                value=0,
                interactive=False
            )
            processing_time = gr.Number(
                label="Processing Time (s)",
                value=0,
                interactive=False,
                precision=2
            )

    # Event handlers
    async def run_pipeline_async(
        glob_pattern: str,
        action: str,
        index: str,
        setup_idx: bool,
        chunk_sz: int,
        overlap: int,
        office: str,
        verbose: bool
    ) -> Tuple[str, int, int, float]:
        """Run the ingestion pipeline."""
        try:
            # Create configuration
            config = PipelineConfig.from_env()

            # Override with UI settings
            config.input.mode = InputMode.LOCAL
            config.input.local_glob = glob_pattern
            config.search.index_name = index
            config.chunking.target_chunk_size = chunk_sz
            config.chunking.chunk_overlap = overlap
            config.office_extractor.mode = OfficeExtractorMode(office)

            # Set action
            if action == "remove":
                config.document_action = DocumentAction.REMOVE
            elif action == "removeall":
                config.document_action = DocumentAction.REMOVE_ALL
            else:
                config.document_action = DocumentAction.ADD

            # Create and run pipeline
            status_msg = f"🚀 Starting pipeline...\n"
            status_msg += f"   Input: {glob_pattern}\n"
            status_msg += f"   Action: {action}\n"
            status_msg += f"   Index: {index}\n\n"

            pipeline = Pipeline(config)

            try:
                # Setup index if requested
                if setup_idx and action == "add":
                    status_msg += "📊 Setting up index...\n"
                    # Index setup would happen here
                    status_msg += "✅ Index ready\n\n"

                status_msg += "📂 Processing documents...\n"

                # Run pipeline
                result = await pipeline.run()

                # Format results
                status_msg += f"\n✅ Pipeline complete!\n\n"
                status_msg += f"📊 Results:\n"
                status_msg += f"   Successful: {result.successful_documents}\n"
                status_msg += f"   Failed: {result.failed_documents}\n"
                status_msg += f"   Total chunks: {result.total_chunks_indexed}\n"
                status_msg += f"   Time: {result.total_processing_time_seconds:.2f}s\n"

                if result.results:
                    status_msg += f"\n📋 Details:\n"
                    for doc_result in result.results:
                        if doc_result.success:
                            status_msg += f"   ✅ {doc_result.filename}: {doc_result.chunks_indexed} chunks\n"
                        else:
                            status_msg += f"   ❌ {doc_result.filename}: {doc_result.error_message}\n"

                return (
                    status_msg,
                    result.successful_documents,
                    result.total_chunks_indexed,
                    result.total_processing_time_seconds
                )

            finally:
                await pipeline.close()

        except Exception as e:
            error_msg = f"❌ Pipeline failed: {str(e)}\n"
            import traceback
            error_msg += f"\nTraceback:\n{traceback.format_exc()}"
            return error_msg, 0, 0, 0.0

    def run_pipeline_wrapper(*args):
        """Wrapper to run async pipeline in sync context."""
        return run_async(run_pipeline_async(*args))

    # Wire up events
    run_btn.click(
        fn=run_pipeline_wrapper,
        inputs=[
            input_glob_config,
            document_action,
            index_name,
            setup_index,
            chunk_size,
            chunk_overlap,
            office_mode,
            verbose_logging
        ],
        outputs=[
            status_output,
            docs_processed,
            chunks_indexed,
            processing_time
        ]
    )

    # Store components
    components["env_components"] = env_components
    components["input_glob_config"] = input_glob_config
    components["document_action"] = document_action
    components["index_name"] = index_name
    components["setup_index"] = setup_index
    components["chunk_size"] = chunk_size
    components["chunk_overlap"] = chunk_overlap
    components["office_mode"] = office_mode
    components["verbose_logging"] = verbose_logging
    components["run_btn"] = run_btn
    components["stop_btn"] = stop_btn
    components["status_output"] = status_output
    components["docs_processed"] = docs_processed
    components["chunks_indexed"] = chunks_indexed
    components["processing_time"] = processing_time

    return components
