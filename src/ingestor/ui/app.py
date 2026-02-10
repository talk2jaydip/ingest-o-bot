"""Main Gradio application for ingestor."""

import gradio as gr
from .config_tab import create_config_tab
from .files_tab import create_files_tab
from .artifacts_tab import create_artifacts_tab
from .logs_tab import create_logs_tab


def create_ui() -> gr.Blocks:
    """Create the main Gradio UI.

    Returns:
        Gradio Blocks application
    """
    with gr.Blocks(
        title="Ingestor - Document Processing Pipeline",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 1400px !important;
        }
        """
    ) as app:
        # Header
        gr.Markdown("""
        # 📚 Ingestor - Document Processing Pipeline

        Process documents and index them into Azure AI Search with Document Intelligence and OpenAI embeddings.
        """)

        # Version and status
        with gr.Row():
            gr.Markdown("**Version:** 0.3.0 | **Status:** ✅ Ready")

        # Main tabs
        with gr.Tabs() as tabs:
            # Configuration Tab
            with gr.Tab("⚙️ Configuration", id="config"):
                config_components = create_config_tab()

            # Files Tab
            with gr.Tab("📁 Files", id="files"):
                files_components = create_files_tab()

            # Artifacts Tab
            with gr.Tab("📦 Artifacts", id="artifacts"):
                artifacts_components = create_artifacts_tab()

            # Logs Tab
            with gr.Tab("📝 Logs", id="logs"):
                logs_components = create_logs_tab()

        # Footer
        gr.Markdown("""
        ---
        **Documentation:** [GitHub](https://github.com/yourusername/ingestor) |
        **Issues:** [Report](https://github.com/yourusername/ingestor/issues)
        """)

        # Setup log auto-refresh (every 1 second)
        # This updates logs in real-time while pipeline is running
        app.load(
            fn=logs_components["get_logs_fn"],
            inputs=[
                logs_components["log_level"],
                logs_components["log_output"]
            ],
            outputs=[
                logs_components["log_output"],
                logs_components["log_stats"]
            ],
            every=1.0  # Refresh every second
        )

    return app


def launch(share: bool = False, server_port: int = 7860, **kwargs):
    """Launch the Gradio UI.

    Args:
        share: Whether to create a public share link
        server_port: Port to run the server on
        **kwargs: Additional arguments passed to gr.Blocks.launch()
    """
    app = create_ui()
    app.launch(
        share=share,
        server_port=server_port,
        server_name="0.0.0.0",  # Allow external access
        **kwargs
    )


# Allow running as script
if __name__ == "__main__":
    launch()


__all__ = ["create_ui", "launch"]
