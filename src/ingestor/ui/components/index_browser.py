"""Azure AI Search index browser component."""

import gradio as gr
from typing import Tuple

from ..helpers import (
    AZURE_SEARCH_AVAILABLE,
    get_search_client,
    search_documents_by_filename,
    get_document_chunks,
)


def create_index_browser() -> Tuple:
    """Create Azure AI Search index browser UI components.

    Returns:
        Tuple of UI components
    """
    with gr.Column():
        gr.Markdown("### 🔍 Azure AI Search Index Browser")

        if not AZURE_SEARCH_AVAILABLE:
            gr.Warning("Azure Search SDK not installed. Run: pip install azure-search-documents")

        # Search interface
        with gr.Row():
            search_pattern = gr.Textbox(
                label="Search Pattern",
                placeholder="filename* or * for all",
                value="*"
            )
            search_btn = gr.Button("🔍 Search", variant="primary")

        # Document list
        document_list = gr.Dataframe(
            headers=["Filename", "Category", "Chunks"],
            label="Documents in Index",
            interactive=False
        )

        doc_count_text = gr.Textbox(
            label="Statistics",
            value="",
            interactive=False
        )

        # Document viewer
        with gr.Accordion("📄 View Document Chunks", open=False):
            selected_doc = gr.Textbox(
                label="Document ID",
                placeholder="Enter document filename to view chunks"
            )
            view_doc_btn = gr.Button("View Chunks")

            chunks_display = gr.Dataframe(
                headers=["Chunk ID", "Page", "Content Preview"],
                label="Document Chunks",
                interactive=False
            )

    # Event handlers
    def search_index(pattern: str):
        """Search documents in index."""
        if not AZURE_SEARCH_AVAILABLE:
            return [], "Azure Search SDK not available"

        client = get_search_client()
        if not client:
            return [], "Search client not configured. Check environment variables."

        try:
            documents = search_documents_by_filename(pattern or "*")

            if not documents:
                return [], "No documents found"

            # Format for dataframe
            rows = []
            total_chunks = 0
            for doc in documents:
                rows.append([
                    doc["filename"],
                    doc.get("category", ""),
                    doc.get("chunk_count", 0)
                ])
                total_chunks += doc.get("chunk_count", 0)

            stats = f"Found {len(documents)} documents with {total_chunks} total chunks"
            return rows, stats

        except Exception as e:
            return [], f"Error: {str(e)}"

    def view_document_chunks(doc_id: str):
        """View chunks for a specific document."""
        if not doc_id:
            return []

        try:
            chunks = get_document_chunks(doc_id)

            if not chunks:
                return []

            # Format for dataframe
            rows = []
            for chunk in chunks:
                content_preview = chunk["content"][:100] + "..." if len(chunk["content"]) > 100 else chunk["content"]
                rows.append([
                    chunk["id"],
                    chunk["page"],
                    content_preview
                ])

            return rows

        except Exception as e:
            return []

    # Wire up events
    search_btn.click(
        fn=search_index,
        inputs=[search_pattern],
        outputs=[document_list, doc_count_text]
    )

    view_doc_btn.click(
        fn=view_document_chunks,
        inputs=[selected_doc],
        outputs=[chunks_display]
    )

    # Auto-search on load
    search_pattern.submit(
        fn=search_index,
        inputs=[search_pattern],
        outputs=[document_list, doc_count_text]
    )

    return (
        search_pattern,
        search_btn,
        document_list,
        doc_count_text,
        selected_doc,
        view_doc_btn,
        chunks_display
    )
