"""ChromaDB collection browser component.

DEPRECATED: This component is superseded by the unified vector store browser
in index_browser.py, which handles both Azure AI Search and ChromaDB in a
single interface. This file is kept for backward compatibility but should
not be used in new code.
"""

import json
import gradio as gr

from ..helpers import (
    CHROMADB_AVAILABLE,
    list_chromadb_collections,
    get_collection_info,
    get_collection_chunks,
    get_chunk_details,
)


def create_chromadb_browser() -> tuple:
    """Create ChromaDB browser component.

    Returns:
        Tuple of UI components for ChromaDB collection browsing
    """
    with gr.Column():
        gr.Markdown("### 🗄️ ChromaDB Collection Browser")

        if not CHROMADB_AVAILABLE:
            gr.Warning("ChromaDB not installed. Run: pip install chromadb")
            return ()

        # Collection selector
        with gr.Row():
            collection_dropdown = gr.Dropdown(
                choices=list_chromadb_collections(),
                label="Collection",
                interactive=True
            )
            refresh_btn = gr.Button("🔄 Refresh Collections", size="sm")

        collection_info_text = gr.Textbox(
            label="Collection Info",
            value="",
            interactive=False
        )

        # Filters
        with gr.Accordion("🔍 Filter Chunks", open=False):
            with gr.Row():
                filter_sourcefile = gr.Textbox(
                    label="Source File Pattern",
                    placeholder="e.g., document.pdf or *.pdf"
                )
                filter_page = gr.Number(
                    label="Page Number",
                    value=None,
                    precision=0
                )
            with gr.Row():
                filter_limit = gr.Slider(
                    minimum=10,
                    maximum=500,
                    value=100,
                    step=10,
                    label="Max Results"
                )
                apply_filter_btn = gr.Button("Apply Filter", variant="primary")

        # Results
        chunks_dataframe = gr.Dataframe(
            headers=["ID", "Source", "Page", "Content Preview", "Tokens"],
            label="Chunks",
            interactive=False
        )

        # Details viewer
        with gr.Accordion("📄 Chunk Details", open=False):
            chunk_id_input = gr.Textbox(
                label="Chunk ID",
                placeholder="Enter chunk ID or select from table above"
            )
            view_btn = gr.Button("View Details")

            with gr.Tabs():
                with gr.Tab("Content"):
                    chunk_content = gr.Textbox(
                        label="Full Content",
                        lines=10,
                        interactive=False
                    )
                with gr.Tab("Metadata"):
                    chunk_metadata = gr.Code(
                        language="json",
                        label="Metadata",
                        interactive=False
                    )
                with gr.Tab("Embedding"):
                    embedding_preview = gr.Textbox(
                        label="Embedding (first 10 dimensions)",
                        lines=3,
                        interactive=False
                    )

    # Event handlers
    def refresh_collections():
        """Refresh the list of collections."""
        collections = list_chromadb_collections()
        if collections and not collections[0].startswith("⚠️"):
            return gr.Dropdown(choices=collections, value=collections[0] if collections else None)
        return gr.Dropdown(choices=collections, value=None)

    def load_collection(collection_name):
        """Load collection info and initial chunks."""
        if not collection_name or collection_name.startswith("⚠️"):
            return "No collection selected", []

        info = get_collection_info(collection_name)
        if "error" in info:
            return f"Error: {info['error']}", []

        chunks, status = get_collection_chunks(collection_name, limit=100)

        info_text = f"Count: {info['count']}, Dimensions: {info['dimensions']}"
        return info_text, chunks

    def apply_filters(collection, sourcefile, page, limit):
        """Apply filters and load chunks."""
        if not collection or collection.startswith("⚠️"):
            return []

        filters = {}
        if sourcefile and sourcefile.strip():
            filters['sourcefile'] = sourcefile.strip()
        if page is not None:
            filters['page_number'] = int(page)

        chunks, status = get_collection_chunks(
            collection,
            limit=int(limit),
            filters=filters if filters else None
        )

        return chunks

    def view_chunk_details(collection, chunk_id):
        """View detailed information for a specific chunk."""
        if not collection or not chunk_id:
            return "No chunk selected", "{}", ""

        if collection.startswith("⚠️"):
            return "Invalid collection", "{}", ""

        details = get_chunk_details(collection, chunk_id)

        if not details:
            return "Chunk not found", "{}", ""

        content = details.get("content", "")
        metadata = details.get("metadata", {})
        embedding = details.get("embedding", [])

        # Format metadata as JSON
        metadata_json = json.dumps(metadata, indent=2)

        # Show first 10 dimensions of embedding
        if embedding:
            embedding_preview_text = f"[{', '.join(f'{x:.4f}' for x in embedding[:10])}..."
            embedding_preview_text += f"\n\nTotal dimensions: {len(embedding)}"
        else:
            embedding_preview_text = "No embedding data"

        return content, metadata_json, embedding_preview_text

    # Wire events
    refresh_btn.click(
        fn=refresh_collections,
        outputs=[collection_dropdown]
    )

    collection_dropdown.change(
        fn=load_collection,
        inputs=[collection_dropdown],
        outputs=[collection_info_text, chunks_dataframe]
    )

    apply_filter_btn.click(
        fn=apply_filters,
        inputs=[collection_dropdown, filter_sourcefile, filter_page, filter_limit],
        outputs=[chunks_dataframe]
    )

    view_btn.click(
        fn=view_chunk_details,
        inputs=[collection_dropdown, chunk_id_input],
        outputs=[chunk_content, chunk_metadata, embedding_preview]
    )

    return (
        collection_dropdown,
        chunks_dataframe,
        refresh_btn,
        collection_info_text,
        chunk_id_input,
        view_btn,
        chunk_content,
        chunk_metadata,
        embedding_preview
    )
