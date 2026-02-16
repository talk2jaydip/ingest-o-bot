"""Unified vector store browser component (Azure Search + ChromaDB)."""

import os
import json
import gradio as gr

from ..helpers import (
    AZURE_SEARCH_AVAILABLE,
    CHROMADB_AVAILABLE,
    get_search_client,
    search_documents_by_filename,
    get_document_chunks,
    list_chromadb_collections,
    get_collection_info,
    get_collection_chunks,
    get_chunk_details,
)


def create_index_browser() -> tuple:
    """Create unified vector store browser UI components.

    Supports both Azure AI Search and ChromaDB with environment configuration.

    Returns:
        Tuple of UI component dictionaries for Azure Search and ChromaDB
    """
    with gr.Column():
        # Check available vector stores
        if not AZURE_SEARCH_AVAILABLE and not CHROMADB_AVAILABLE:
            gr.Warning("⚠️ No vector stores available. Install azure-search-documents or chromadb")
            gr.Markdown("```bash\npip install azure-search-documents  # For Azure AI Search\npip install chromadb                # For ChromaDB\n```")
            return tuple()

        # Header with status badges
        with gr.Row():
            gr.Markdown("### 🔍 Vector Store Browser")
            status_badges = []
            if AZURE_SEARCH_AVAILABLE:
                status_badges.append("🔵 **Azure Search**: Available")
            if CHROMADB_AVAILABLE:
                status_badges.append("🟢 **ChromaDB**: Available")
            gr.Markdown(" | ".join(status_badges))

        # Quick guide
        with gr.Accordion("ℹ️ Quick Guide", open=False):
            gr.Markdown("""
**How to use the Vector Store Browser:**

1. **Select a Vector Store Tab** - Choose between Azure AI Search or ChromaDB
2. **Configure Connection** - Click the configuration accordion to set environment variables (session only)
3. **Browse Content** - Search for documents/chunks using patterns (e.g., `*.pdf` or `document*`)
4. **View Details** - Click on items to view full content, metadata, and embeddings

**Tips:**
- Configuration values are loaded from your active .env file (selected in Configuration tab)
- Use `*` to list all items
- Connection status indicators show if your configuration is working
- All changes are session-only unless you update the .env file directly
            """)

        gr.Markdown("---")  # Visual separator
        gr.Markdown("**👇 Select your Vector Store below:**")

        # Modular tabs for each vector store - PROMINENT TABS
        with gr.Tabs() as vector_store_tabs:

            # ===== AZURE AI SEARCH TAB =====
            if AZURE_SEARCH_AVAILABLE:
                with gr.Tab("🔵 Azure AI Search") as azure_tab:
                    with gr.Column():
                        # Connection status indicator
                        with gr.Row():
                            gr.Markdown("**Azure AI Search Vector Store**")
                            azure_connection_status = gr.Markdown(
                                "🔴 Not Connected" if not os.getenv("AZURE_SEARCH_SERVICE") else "🟢 Connected",
                                elem_classes=["status-badge"]
                            )

                        # Environment configuration
                        with gr.Accordion("⚙️ Azure Search Configuration", open=False):
                            gr.Markdown("*Configure Azure AI Search connection. Values loaded from active .env file.*")

                            with gr.Row():
                                azure_refresh_btn = gr.Button("🔄 Refresh from Environment", size="sm")

                            azure_service = gr.Textbox(
                                label="AZURE_SEARCH_SERVICE",
                                value=os.getenv("AZURE_SEARCH_SERVICE", ""),
                                placeholder="your-search-service"
                            )
                            azure_index = gr.Textbox(
                                label="AZURE_SEARCH_INDEX",
                                value=os.getenv("AZURE_SEARCH_INDEX", ""),
                                placeholder="documents-index"
                            )
                            azure_key = gr.Textbox(
                                label="AZURE_SEARCH_KEY",
                                value=os.getenv("AZURE_SEARCH_KEY", "")[:4] + "..." if os.getenv("AZURE_SEARCH_KEY") else "",
                                placeholder="your-api-key",
                                type="password"
                            )
                            azure_save_btn = gr.Button("💾 Save Config (Session)", size="sm")
                            azure_config_status = gr.Textbox(label="Status", value="", interactive=False)

                        # Index selector
                        with gr.Row():
                            azure_index_selector = gr.Dropdown(
                                label="Index Name",
                                choices=[os.getenv("AZURE_SEARCH_INDEX", "documents-index")],
                                value=os.getenv("AZURE_SEARCH_INDEX", "documents-index"),
                                interactive=True
                            )
                            azure_refresh_index_btn = gr.Button("🔄 Refresh", size="sm")

                        azure_index_info = gr.Textbox(label="Index Info", value="", interactive=False)

                        # Search interface
                        with gr.Row():
                            azure_search_pattern = gr.Textbox(
                                label="Search Pattern",
                                placeholder="filename* or * for all",
                                value="*"
                            )
                            azure_search_btn = gr.Button("🔍 Search", variant="primary")

                        # Results
                        azure_results = gr.Dataframe(
                            headers=["Filename", "Category", "Chunks"],
                            label="Documents",
                            interactive=False
                        )
                        azure_stats = gr.Textbox(label="Statistics", value="", interactive=False)

                        # Details viewer
                        with gr.Accordion("📄 View Document Details", open=False):
                            azure_doc_id = gr.Textbox(
                                label="Document ID",
                                placeholder="Enter document ID"
                            )
                            azure_view_btn = gr.Button("View Details")

                            with gr.Tabs():
                                with gr.Tab("Content"):
                                    azure_content = gr.Textbox(label="Content", lines=10, interactive=False)
                                with gr.Tab("Metadata"):
                                    azure_metadata = gr.Code(language="json", label="Metadata", interactive=False)

            # ===== CHROMADB TAB =====
            if CHROMADB_AVAILABLE:
                with gr.Tab("🟢 ChromaDB") as chromadb_tab:
                    with gr.Column():
                        # Connection status indicator
                        with gr.Row():
                            gr.Markdown("**ChromaDB Vector Store (Local/Remote)**")
                            chromadb_connection_status = gr.Markdown(
                                "🟢 Ready" if os.getenv("CHROMADB_PERSIST_DIR") or os.getenv("CHROMADB_HOST") else "🔴 Not Configured",
                                elem_classes=["status-badge"]
                            )

                        # Environment configuration
                        with gr.Accordion("⚙️ ChromaDB Configuration", open=False):
                            gr.Markdown("*Configure ChromaDB connection. Values loaded from active .env file.*")

                            with gr.Row():
                                chromadb_refresh_btn = gr.Button("🔄 Refresh from Environment", size="sm")

                            chromadb_mode = gr.Radio(
                                choices=["Persistent (Local)", "In-Memory", "Client/Server"],
                                value="Persistent (Local)",
                                label="ChromaDB Mode"
                            )
                            chromadb_persist_dir = gr.Textbox(
                                label="CHROMADB_PERSIST_DIR",
                                value=os.getenv("CHROMADB_PERSIST_DIR", "./chroma_db"),
                                placeholder="./chroma_db"
                            )
                            with gr.Row():
                                chromadb_host = gr.Textbox(
                                    label="CHROMADB_HOST",
                                    value=os.getenv("CHROMADB_HOST", ""),
                                    placeholder="localhost"
                                )
                                chromadb_port = gr.Textbox(
                                    label="CHROMADB_PORT",
                                    value=os.getenv("CHROMADB_PORT", ""),
                                    placeholder="8000"
                                )
                            chromadb_save_btn = gr.Button("💾 Save Config (Session)", size="sm")
                            chromadb_config_status = gr.Textbox(label="Status", value="", interactive=False)

                        # Collection selector
                        with gr.Row():
                            chromadb_collection_selector = gr.Dropdown(
                                label="Collection",
                                choices=list_chromadb_collections(),
                                interactive=True
                            )
                            chromadb_refresh_collection_btn = gr.Button("🔄 Refresh", size="sm")

                        chromadb_collection_info = gr.Textbox(label="Collection Info", value="", interactive=False)

                        # Search interface
                        with gr.Row():
                            chromadb_search_pattern = gr.Textbox(
                                label="Search Pattern (Source File)",
                                placeholder="filename* or * for all",
                                value="*"
                            )
                            chromadb_search_btn = gr.Button("🔍 Search", variant="primary")

                        # Results
                        chromadb_results = gr.Dataframe(
                            headers=["Chunk ID", "Source", "Page", "Content Preview"],
                            label="Chunks",
                            interactive=False
                        )
                        chromadb_stats = gr.Textbox(label="Statistics", value="", interactive=False)

                        # Details viewer
                        with gr.Accordion("📄 View Chunk Details", open=False):
                            chromadb_chunk_id = gr.Textbox(
                                label="Chunk ID",
                                placeholder="Enter chunk ID"
                            )
                            chromadb_view_btn = gr.Button("View Details")

                            with gr.Tabs():
                                with gr.Tab("Content"):
                                    chromadb_content = gr.Textbox(label="Content", lines=10, interactive=False)
                                with gr.Tab("Metadata"):
                                    chromadb_metadata = gr.Code(language="json", label="Metadata", interactive=False)

    # ===== AZURE AI SEARCH EVENT HANDLERS =====
    def refresh_azure_config():
        """Refresh Azure Search config from environment."""
        try:
            service = os.getenv("AZURE_SEARCH_SERVICE", "")
            index = os.getenv("AZURE_SEARCH_INDEX", "")
            key = os.getenv("AZURE_SEARCH_KEY", "")
            key_display = key[:4] + "..." if key else ""
            status = "🟢 Connected" if service else "🔴 Not Connected"
            return service, index, key_display, "✅ Refreshed from environment", status
        except Exception as e:
            return "", "", "", f"❌ Error: {str(e)}", "🔴 Not Connected"

    def save_azure_config(service, index, key):
        """Save Azure Search configuration to environment."""
        try:
            os.environ["AZURE_SEARCH_SERVICE"] = service
            os.environ["AZURE_SEARCH_INDEX"] = index
            if key and not key.endswith("..."):
                os.environ["AZURE_SEARCH_KEY"] = key
            status = "🟢 Connected" if service else "🔴 Not Connected"
            return "✅ Azure Search config saved (session only)", status
        except Exception as e:
            return f"❌ Error: {str(e)}", "🔴 Error"

    def refresh_azure_index():
        """Refresh Azure Search index dropdown."""
        index_name = os.getenv("AZURE_SEARCH_INDEX", "documents-index")
        return gr.Dropdown(choices=[index_name], value=index_name)

    def load_azure_index_info(index_name):
        """Load Azure Search index info."""
        if not index_name:
            return "No index selected"
        client = get_search_client()
        if client:
            return f"Index: {index_name} (Azure AI Search)"
        return "❌ Azure Search not configured"

    def search_azure_documents(index_name, pattern):
        """Search documents in Azure Search."""
        if not index_name:
            return [], "No index selected"

        try:
            documents = search_documents_by_filename(pattern or "*")
            if not documents:
                return [], "No documents found"

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

    def view_azure_document(doc_id):
        """View Azure Search document details."""
        if not doc_id:
            return "No document selected", "{}"

        try:
            chunks = get_document_chunks(doc_id)
            if not chunks:
                return "No chunks found", "{}"

            content = "\n\n---\n\n".join([
                f"Chunk {i+1} (Page {chunk['page']}):\n{chunk['content']}"
                for i, chunk in enumerate(chunks)
            ])

            metadata = {"document_id": doc_id, "total_chunks": len(chunks)}
            return content, json.dumps(metadata, indent=2)
        except Exception as e:
            return f"Error: {str(e)}", "{}"

    # ===== CHROMADB EVENT HANDLERS =====
    def refresh_chromadb_config():
        """Refresh ChromaDB config from environment."""
        try:
            persist_dir = os.getenv("CHROMADB_PERSIST_DIR", "./chroma_db")
            host = os.getenv("CHROMADB_HOST", "")
            port = os.getenv("CHROMADB_PORT", "")

            # Determine mode
            if host and port:
                mode = "Client/Server"
                status = "🟢 Ready (Client/Server)"
            elif persist_dir:
                mode = "Persistent (Local)"
                status = "🟢 Ready (Local)"
            else:
                mode = "In-Memory"
                status = "🟡 In-Memory Mode"

            return mode, persist_dir, host, port, "✅ Refreshed from environment", status
        except Exception as e:
            return "Persistent (Local)", "./chroma_db", "", "", f"❌ Error: {str(e)}", "🔴 Error"

    def save_chromadb_config(mode, persist_dir, host, port):
        """Save ChromaDB configuration to environment."""
        try:
            if mode == "Persistent (Local)":
                os.environ["CHROMADB_PERSIST_DIR"] = persist_dir
                os.environ.pop("CHROMADB_HOST", None)
                os.environ.pop("CHROMADB_PORT", None)
                status = "🟢 Ready (Local)"
            elif mode == "Client/Server":
                os.environ["CHROMADB_HOST"] = host
                os.environ["CHROMADB_PORT"] = port
                os.environ.pop("CHROMADB_PERSIST_DIR", None)
                status = "🟢 Ready (Client/Server)"
            else:  # In-Memory
                os.environ.pop("CHROMADB_PERSIST_DIR", None)
                os.environ.pop("CHROMADB_HOST", None)
                os.environ.pop("CHROMADB_PORT", None)
                status = "🟡 In-Memory Mode"
            return "✅ ChromaDB config saved (session only)", status
        except Exception as e:
            return f"❌ Error: {str(e)}", "🔴 Error"

    def refresh_chromadb_collections():
        """Refresh ChromaDB collections dropdown."""
        collections = list_chromadb_collections()
        if collections and not collections[0].startswith("⚠️"):
            return gr.Dropdown(choices=collections, value=collections[0] if collections else None)
        return gr.Dropdown(choices=collections, value=None)

    def load_chromadb_collection_info(collection_name):
        """Load ChromaDB collection info."""
        if not collection_name:
            return "No collection selected"

        info = get_collection_info(collection_name)
        if "error" in info:
            return f"Error: {info['error']}"
        return f"Count: {info['count']}, Dimensions: {info['dimensions']}"

    def search_chromadb_chunks(collection_name, pattern):
        """Search chunks in ChromaDB."""
        if not collection_name:
            return [], "No collection selected"

        try:
            filters = {}
            if pattern and pattern.strip() and pattern != "*":
                filters["sourcefile"] = pattern.strip()

            chunks, status = get_collection_chunks(
                collection_name,
                limit=100,
                filters=filters if filters else None
            )
            return chunks, status
        except Exception as e:
            return [], f"Error: {str(e)}"

    def view_chromadb_chunk(collection_name, chunk_id):
        """View ChromaDB chunk details."""
        if not chunk_id or not collection_name:
            return "No chunk selected", "{}"

        try:
            details = get_chunk_details(collection_name, chunk_id)
            if not details:
                return "Chunk not found", "{}"

            content = details.get("content", "")
            metadata = details.get("metadata", {})
            return content, json.dumps(metadata, indent=2)
        except Exception as e:
            return f"Error: {str(e)}", "{}"

    # ===== WIRE UP AZURE AI SEARCH EVENTS =====
    if AZURE_SEARCH_AVAILABLE:
        azure_refresh_btn.click(
            fn=refresh_azure_config,
            inputs=[],
            outputs=[azure_service, azure_index, azure_key, azure_config_status, azure_connection_status]
        )

        azure_save_btn.click(
            fn=save_azure_config,
            inputs=[azure_service, azure_index, azure_key],
            outputs=[azure_config_status, azure_connection_status]
        )

        azure_refresh_index_btn.click(
            fn=refresh_azure_index,
            inputs=[],
            outputs=[azure_index_selector]
        )

        azure_index_selector.change(
            fn=load_azure_index_info,
            inputs=[azure_index_selector],
            outputs=[azure_index_info]
        )

        azure_search_btn.click(
            fn=search_azure_documents,
            inputs=[azure_index_selector, azure_search_pattern],
            outputs=[azure_results, azure_stats]
        )

        azure_search_pattern.submit(
            fn=search_azure_documents,
            inputs=[azure_index_selector, azure_search_pattern],
            outputs=[azure_results, azure_stats]
        )

        azure_view_btn.click(
            fn=view_azure_document,
            inputs=[azure_doc_id],
            outputs=[azure_content, azure_metadata]
        )

    # ===== WIRE UP CHROMADB EVENTS =====
    if CHROMADB_AVAILABLE:
        chromadb_refresh_btn.click(
            fn=refresh_chromadb_config,
            inputs=[],
            outputs=[chromadb_mode, chromadb_persist_dir, chromadb_host, chromadb_port, chromadb_config_status, chromadb_connection_status]
        )

        chromadb_save_btn.click(
            fn=save_chromadb_config,
            inputs=[chromadb_mode, chromadb_persist_dir, chromadb_host, chromadb_port],
            outputs=[chromadb_config_status, chromadb_connection_status]
        )

        chromadb_refresh_collection_btn.click(
            fn=refresh_chromadb_collections,
            inputs=[],
            outputs=[chromadb_collection_selector]
        )

        chromadb_collection_selector.change(
            fn=load_chromadb_collection_info,
            inputs=[chromadb_collection_selector],
            outputs=[chromadb_collection_info]
        )

        chromadb_search_btn.click(
            fn=search_chromadb_chunks,
            inputs=[chromadb_collection_selector, chromadb_search_pattern],
            outputs=[chromadb_results, chromadb_stats]
        )

        chromadb_search_pattern.submit(
            fn=search_chromadb_chunks,
            inputs=[chromadb_collection_selector, chromadb_search_pattern],
            outputs=[chromadb_results, chromadb_stats]
        )

        chromadb_view_btn.click(
            fn=view_chromadb_chunk,
            inputs=[chromadb_collection_selector, chromadb_chunk_id],
            outputs=[chromadb_content, chromadb_metadata]
        )

    # Return tuple of key components for external access
    components = {}
    if AZURE_SEARCH_AVAILABLE:
        components["azure"] = {
            "index_selector": azure_index_selector,
            "search_pattern": azure_search_pattern,
            "results": azure_results,
        }
    if CHROMADB_AVAILABLE:
        components["chromadb"] = {
            "collection_selector": chromadb_collection_selector,
            "search_pattern": chromadb_search_pattern,
            "results": chromadb_results,
        }

    return tuple(components.values()) if components else tuple()
