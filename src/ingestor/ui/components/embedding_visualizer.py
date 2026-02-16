"""Embedding visualization component with dimensionality reduction."""

import os
import json
import gradio as gr

from ..helpers import (
    VISUALIZATION_AVAILABLE,
    UMAP_AVAILABLE,
    CHROMADB_AVAILABLE,
    AZURE_SEARCH_AVAILABLE,
    list_chromadb_collections,
    get_embeddings_from_chromadb,
    get_embeddings_from_azure_search,
    reduce_embeddings_pca,
    reduce_embeddings_tsne,
    reduce_embeddings_umap,
    create_embedding_plot,
)


def create_embedding_visualizer() -> tuple:
    """Create embedding visualization component.

    Returns:
        Tuple of UI components for embedding visualization
    """
    with gr.Column():
        gr.Markdown("### 📊 Embedding Visualization")
        gr.Markdown("Visualize embeddings with dimensionality reduction (PCA, t-SNE, UMAP)")

        if not VISUALIZATION_AVAILABLE:
            gr.Warning("Visualization libraries not installed. Run: pip install -r requirements-visualization.txt")
            gr.Markdown("""
            **Required libraries:**
            - plotly>=5.17.0
            - scikit-learn>=1.3.0
            - umap-learn>=0.5.5 (optional)
            - pandas>=2.0.0
            """)
            return ()

        # Source selection
        with gr.Row():
            source_options = []
            if CHROMADB_AVAILABLE:
                source_options.append("ChromaDB")
            if AZURE_SEARCH_AVAILABLE:
                source_options.append("Azure Search")

            if not source_options:
                gr.Warning("No vector store available. Install ChromaDB or configure Azure Search.")
                return ()

            source_radio = gr.Radio(
                choices=source_options,
                label="Source",
                value=source_options[0] if source_options else None
            )

            collection_dropdown = gr.Dropdown(
                label="Collection/Index",
                interactive=True
            )

        # Visualization settings
        with gr.Row():
            method_choices = ["PCA", "t-SNE"]
            if UMAP_AVAILABLE:
                method_choices.append("UMAP")

            method_dropdown = gr.Dropdown(
                choices=method_choices,
                value="PCA",
                label="Dimensionality Reduction"
            )

            dimensions_radio = gr.Radio(
                choices=["2D", "3D"],
                value="2D",
                label="Dimensions"
            )

        with gr.Row():
            max_points_slider = gr.Slider(
                minimum=100,
                maximum=5000,
                value=1000,
                step=100,
                label="Max Points"
            )

            color_by_dropdown = gr.Dropdown(
                choices=["sourcefile", "page_number", "title", "token_count"],
                value="sourcefile",
                label="Color By"
            )

        generate_btn = gr.Button("🎨 Generate Visualization", variant="primary", size="lg")

        status_text = gr.Textbox(
            label="Status",
            value="",
            interactive=False
        )

        # Plot output
        plot_output = gr.Plot(label="Embedding Visualization")

        # Details viewer
        with gr.Accordion("📄 Selected Point Details", open=False):
            selected_info = gr.JSON(
                label="Chunk Details",
                value={}
            )

        # Export buttons
        with gr.Row():
            export_data_btn = gr.Button("💾 Export Data (CSV)")
            export_plot_btn = gr.Button("🖼️ Export Plot (HTML)")

    # Store data for export
    current_data = {"coords": None, "metadata": None}

    # Event handlers
    def source_changed(source):
        """Update collection dropdown when source changes.

        Args:
            source: The selected vector store source ("ChromaDB" or "Azure Search")

        Returns:
            Updated Dropdown component with available collections/indices
        """
        try:
            if source == "ChromaDB":
                collections = list_chromadb_collections()
                if collections and not collections[0].startswith("⚠️"):
                    return gr.Dropdown(choices=collections, value=collections[0] if collections else None)
                return gr.Dropdown(choices=collections, value=None)
            elif source == "Azure Search":
                index_name = os.getenv("AZURE_SEARCH_INDEX", "documents-index")
                return gr.Dropdown(choices=[index_name], value=index_name)
            return gr.Dropdown(choices=[], value=None)
        except Exception as e:
            return gr.Dropdown(choices=[f"⚠️ Error: {str(e)}"], value=None)

    def generate_visualization(source, collection, method, dims, max_points, color_by):
        """Generate embedding visualization."""
        try:
            if not collection:
                return None, "Please select a collection/index"

            # 1. Fetch embeddings
            status_text_val = f"Fetching embeddings from {source}..."

            if source == "ChromaDB":
                embeddings, metadata = get_embeddings_from_chromadb(collection, int(max_points))
            else:  # Azure Search
                embeddings, metadata = get_embeddings_from_azure_search(collection, int(max_points))

            if embeddings is None or len(embeddings) == 0:
                return None, "No embeddings found. Make sure embeddings are stored in the vector store."

            if len(embeddings) < 3:
                return None, f"Too few embeddings ({len(embeddings)}). Need at least 3 points."

            # 2. Apply dimensionality reduction
            n_components = 3 if dims == "3D" else 2
            status_text_val = f"Applying {method} reduction..."

            if method == "PCA":
                coords = reduce_embeddings_pca(embeddings, n_components)
            elif method == "t-SNE":
                coords = reduce_embeddings_tsne(embeddings, n_components)
            else:  # UMAP
                if not UMAP_AVAILABLE:
                    return None, "UMAP not installed. Run: pip install umap-learn"
                coords = reduce_embeddings_umap(embeddings, n_components)

            if coords is None or len(coords) == 0:
                return None, f"{method} reduction failed. Try a different method."

            # Store for export
            current_data["coords"] = coords
            current_data["metadata"] = metadata

            # 3. Create plot
            fig = create_embedding_plot(coords, metadata, color_by, is_3d=(dims == "3D"))

            if fig is None:
                return None, "Failed to create plot"

            final_status = f"✅ Plotted {len(coords)} points using {method} ({dims})"
            return fig, final_status

        except Exception as e:
            return None, f"Error: {str(e)}"

    def export_data_as_csv():
        """Export visualization data as CSV."""
        try:
            if current_data["coords"] is None or current_data["metadata"] is None:
                return "No data to export. Generate visualization first."

            import pandas as pd
            from datetime import datetime

            coords = current_data["coords"]
            metadata = current_data["metadata"]

            # Build dataframe
            data = []
            for i, meta in enumerate(metadata):
                row = {
                    "x": coords[i, 0],
                    "y": coords[i, 1],
                }
                if coords.shape[1] == 3:
                    row["z"] = coords[i, 2]

                row.update(meta)
                data.append(row)

            df = pd.DataFrame(data)

            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"embeddings_export_{timestamp}.csv"
            df.to_csv(filename, index=False)

            return f"✅ Exported {len(data)} points to {filename}"

        except Exception as e:
            return f"Export failed: {str(e)}"

    def export_plot_as_html(plot_fig):
        """Export plot as interactive HTML."""
        try:
            if plot_fig is None:
                return "No plot to export. Generate visualization first."

            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"embeddings_plot_{timestamp}.html"

            plot_fig.write_html(filename)

            return f"✅ Exported plot to {filename}"

        except Exception as e:
            return f"Export failed: {str(e)}"

    # Wire events
    source_radio.change(
        fn=source_changed,
        inputs=[source_radio],
        outputs=[collection_dropdown]
    )

    generate_btn.click(
        fn=generate_visualization,
        inputs=[source_radio, collection_dropdown, method_dropdown, dimensions_radio,
                max_points_slider, color_by_dropdown],
        outputs=[plot_output, status_text]
    )

    export_data_btn.click(
        fn=export_data_as_csv,
        outputs=[status_text]
    )

    export_plot_btn.click(
        fn=export_plot_as_html,
        inputs=[plot_output],
        outputs=[status_text]
    )

    # Auto-populate collection on load
    source_radio.change(source_changed, inputs=[source_radio], outputs=[collection_dropdown])

    return (
        plot_output,
        generate_btn,
        status_text,
        source_radio,
        collection_dropdown
    )
