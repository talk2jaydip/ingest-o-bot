"""Artifacts browser tab for the Gradio UI."""

import os
import json
import gradio as gr
from pathlib import Path
from typing import List, Tuple

from .components import (
    create_embedding_visualizer,
    create_chunk_locker,
)


def create_artifacts_tab() -> dict:
    """Create the artifacts browser tab.

    Returns:
        Dictionary of component references
    """
    components = {}

    with gr.Column():
        gr.Markdown("### 📦 Processing Artifacts & Vector Stores")
        gr.Markdown("View artifacts, browse vector stores, visualize embeddings, and manage chunk locks")

        # EXISTING: Local artifacts browser
        with gr.Accordion("📁 Local Artifacts Browser", open=True):
            # Artifacts location
            artifacts_mode = gr.Radio(
                choices=["Local", "Blob Storage"],
                label="Artifacts Location",
                value="Local"
            )

            with gr.Row():
                artifacts_path = gr.Textbox(
                    label="Local Artifacts Path",
                    value=os.getenv("AZURE_ARTIFACTS_LOCAL_PATH", "./artifacts"),
                    placeholder="./artifacts"
                )
                refresh_btn = gr.Button("🔄 Refresh", size="sm")

            # Artifact list
            artifact_list = gr.Dataframe(
                headers=["Filename", "Type", "Size"],
                label="Available Artifacts",
                interactive=False
            )

            # Artifact viewer
            with gr.Accordion("📄 View Artifact", open=False):
                selected_artifact = gr.Dropdown(
                    choices=[],
                    label="Select Artifact",
                    interactive=True
                )
                view_btn = gr.Button("View")

                artifact_content = gr.Code(
                    label="Content",
                    language="json",
                    interactive=False
                )

        # NEW: Embedding Visualization
        with gr.Accordion("📊 Embedding Visualization", open=False):
            viz_components = create_embedding_visualizer()
            components["visualizer"] = viz_components

        # NEW: Chunk Locking
        with gr.Accordion("🔒 Chunk Lock Management", open=False):
            lock_components = create_chunk_locker()
            components["locker"] = lock_components

    # Event handlers for local artifacts browser
    def list_artifacts(path: str) -> Tuple[List, List]:
        """List artifacts in the given path.

        Args:
            path: Path to the artifacts directory

        Returns:
            Tuple of (artifact_rows, artifact_file_paths)
        """
        try:
            artifact_path = Path(path)
            if not artifact_path.exists():
                return [], []

            artifacts = []
            artifact_files = []

            for file_path in artifact_path.rglob("*"):
                if file_path.is_file():
                    # Determine type
                    suffix = file_path.suffix
                    if suffix == ".json":
                        artifact_type = "Document Intelligence JSON"
                    elif suffix == ".md":
                        artifact_type = "Markdown"
                    elif "chunks" in file_path.name:
                        artifact_type = "Chunks"
                    else:
                        artifact_type = "Other"

                    size = file_path.stat().st_size
                    artifacts.append([
                        file_path.name,
                        artifact_type,
                        f"{size / 1024:.1f} KB"
                    ])
                    artifact_files.append(str(file_path))

            return artifacts, artifact_files

        except Exception as e:
            return [["Error", str(e), ""]], []

    def view_artifact(artifact_file: str) -> str:
        """View the content of an artifact.

        Args:
            artifact_file: Path to the artifact file

        Returns:
            Content of the artifact file, formatted if JSON
        """
        if not artifact_file:
            return "No artifact selected"

        try:
            path = Path(artifact_file)
            if not path.exists():
                return f"File not found: {artifact_file}"

            # Read content
            content = path.read_text(encoding="utf-8")

            # Pretty-print JSON
            if path.suffix == ".json":
                try:
                    data = json.loads(content)
                    content = json.dumps(data, indent=2)
                except Exception:
                    pass

            return content

        except Exception as e:
            return f"Error reading artifact: {str(e)}"

    # Wire up events
    def refresh_artifacts(path: str):
        """Refresh artifacts list and update dropdown.

        Args:
            path: Path to artifacts directory

        Returns:
            Tuple of (artifact_rows, updated_dropdown)
        """
        artifacts, files = list_artifacts(path)
        return artifacts, gr.Dropdown(choices=files)

    refresh_btn.click(
        fn=refresh_artifacts,
        inputs=[artifacts_path],
        outputs=[artifact_list, selected_artifact]
    )

    artifacts_path.change(
        fn=refresh_artifacts,
        inputs=[artifacts_path],
        outputs=[artifact_list, selected_artifact]
    )

    view_btn.click(
        fn=view_artifact,
        inputs=[selected_artifact],
        outputs=[artifact_content]
    )

    # Store components
    components["artifacts_mode"] = artifacts_mode
    components["artifacts_path"] = artifacts_path
    components["refresh_btn"] = refresh_btn
    components["artifact_list"] = artifact_list
    components["selected_artifact"] = selected_artifact
    components["view_btn"] = view_btn
    components["artifact_content"] = artifact_content

    return components
