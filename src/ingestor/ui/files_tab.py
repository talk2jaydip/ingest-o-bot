"""File management tab for the Gradio UI."""

import os
import gradio as gr
from pathlib import Path
from typing import List, Tuple

from .components import create_blob_browser, create_index_browser


def create_files_tab() -> dict:
    """Create the file management tab.

    Returns:
        Dictionary of component references
    """
    components = {}

    with gr.Column():
        gr.Markdown("### 📁 File Management")

        # Input mode selection
        input_mode = gr.Radio(
            choices=["Local Files", "Azure Blob Storage"],
            label="Input Source",
            value="Local Files"
        )

        # Local files section
        with gr.Group(visible=True) as local_group:
            gr.Markdown("#### Local Files")

            local_glob = gr.Textbox(
                label="File Pattern (glob)",
                placeholder="documents/*.pdf",
                value=os.getenv("AZURE_LOCAL_GLOB", "documents/*.pdf")
            )

            with gr.Row():
                browse_btn = gr.Button("📂 Browse Files")
                file_count_text = gr.Textbox(
                    label="Files Found",
                    value="0 files",
                    interactive=False,
                    scale=1
                )

            file_list = gr.Dataframe(
                headers=["Filename", "Size", "Type"],
                label="Matched Files",
                interactive=False
            )

        # Blob storage section
        with gr.Group(visible=False) as blob_group:
            gr.Markdown("#### Azure Blob Storage")
            blob_components = create_blob_browser()

        # Index browser section - OPEN BY DEFAULT for visibility
        with gr.Accordion("🔍 Browse Vector Store (Azure Search / ChromaDB)", open=True):
            gr.Markdown("*Browse and inspect indexed documents from your vector store*")
            index_components = create_index_browser()

    # Event handlers
    def browse_local_files(pattern: str) -> Tuple[List, str]:
        """Browse local files matching the pattern.

        Args:
            pattern: Glob pattern to match files (e.g., "documents/*.pdf")

        Returns:
            Tuple of (file_rows, status_message)
        """
        try:
            # Expand pattern
            files = list(Path().glob(pattern))

            if not files:
                return [], "0 files found"

            # Format for dataframe
            rows = []
            for file_path in files:
                if file_path.is_file():
                    size = file_path.stat().st_size
                    suffix = file_path.suffix
                    rows.append([
                        str(file_path),
                        f"{size / 1024:.1f} KB",
                        suffix
                    ])

            return rows, f"{len(rows)} files found"

        except Exception as e:
            return [], f"Error: {str(e)}"

    def toggle_input_mode(mode: str):
        """Toggle between local files and blob storage.

        Args:
            mode: Selected input mode ("Local Files" or "Azure Blob Storage")

        Returns:
            Tuple of (local_group_visibility, blob_group_visibility)
        """
        if mode == "Local Files":
            return gr.Group(visible=True), gr.Group(visible=False)
        else:
            return gr.Group(visible=False), gr.Group(visible=True)

    # Wire up events
    browse_btn.click(
        fn=browse_local_files,
        inputs=[local_glob],
        outputs=[file_list, file_count_text]
    )

    input_mode.change(
        fn=toggle_input_mode,
        inputs=[input_mode],
        outputs=[local_group, blob_group]
    )

    # Auto-browse on glob change
    local_glob.change(
        fn=browse_local_files,
        inputs=[local_glob],
        outputs=[file_list, file_count_text]
    )

    # Store components
    components["input_mode"] = input_mode
    components["local_glob"] = local_glob
    components["browse_btn"] = browse_btn
    components["file_count_text"] = file_count_text
    components["file_list"] = file_list
    components["local_group"] = local_group
    components["blob_group"] = blob_group
    components["blob_components"] = blob_components
    components["index_components"] = index_components

    return components
