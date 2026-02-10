"""Azure Blob Storage browser component."""

import gradio as gr
from typing import List, Tuple

from ..helpers import (
    AZURE_STORAGE_AVAILABLE,
    list_blob_containers,
    list_blobs_in_container,
)


def create_blob_browser() -> Tuple:
    """Create Azure Blob Storage browser UI components.

    Returns:
        Tuple of (container_dropdown, blob_list, refresh_btn, status_text)
    """
    with gr.Column():
        gr.Markdown("### 📦 Azure Blob Storage Browser")

        if not AZURE_STORAGE_AVAILABLE:
            gr.Warning("Azure Storage SDK not installed. Run: pip install azure-storage-blob")

        with gr.Row():
            container_dropdown = gr.Dropdown(
                choices=list_blob_containers(),
                label="Container",
                interactive=True,
                value=None
            )
            refresh_containers_btn = gr.Button("🔄 Refresh", size="sm")

        blob_prefix = gr.Textbox(
            label="Prefix Filter (optional)",
            placeholder="folder/subfolder/",
            value=""
        )

        blob_list = gr.Dataframe(
            headers=["Name", "Size (bytes)", "Last Modified"],
            label="Blobs",
            interactive=False
        )

        status_text = gr.Textbox(
            label="Status",
            value="Select a container to view blobs",
            interactive=False
        )

    # Event handlers
    def refresh_containers():
        """Refresh container list."""
        containers = list_blob_containers()
        return gr.Dropdown(choices=containers)

    def load_blobs(container: str, prefix: str):
        """Load blobs from container."""
        if not container or container.startswith("⚠️"):
            return [], "Select a valid container"

        blobs = list_blobs_in_container(container, prefix or "")

        if not blobs:
            return [], f"No blobs found in container '{container}'"

        # Format for dataframe
        rows = []
        for blob in blobs:
            rows.append([
                blob["name"],
                blob["size"],
                str(blob["last_modified"])
            ])

        return rows, f"Found {len(blobs)} blobs in '{container}'"

    refresh_containers_btn.click(
        fn=refresh_containers,
        outputs=[container_dropdown]
    )

    container_dropdown.change(
        fn=load_blobs,
        inputs=[container_dropdown, blob_prefix],
        outputs=[blob_list, status_text]
    )

    blob_prefix.change(
        fn=load_blobs,
        inputs=[container_dropdown, blob_prefix],
        outputs=[blob_list, status_text]
    )

    return container_dropdown, blob_list, refresh_containers_btn, status_text
