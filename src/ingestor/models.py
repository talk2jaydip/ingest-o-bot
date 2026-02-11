"""Data models for document processing."""

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse


@dataclass
class DocumentMetadata:
    """Metadata about a source document."""
    sourcefile: str
    storage_url: str
    content_type: str = "application/pdf"
    md5_hash: Optional[str] = None
    file_size: Optional[int] = None
    ingested_at: Optional[str] = None
    
    def __post_init__(self):
        if self.ingested_at is None:
            self.ingested_at = datetime.utcnow().isoformat() + "Z"


@dataclass
class PageMetadata:
    """Metadata about a page within a document."""
    page_num: int  # 1-indexed page number
    sourcepage: str  # e.g., "docname/page-0001.pdf#page=1" or "file.pdf#page=1"
    page_blob_url: Optional[str] = None
    
    @classmethod
    def create(
        cls,
        page_num_0indexed: int,
        sourcefile: str,
        page_blob_url: Optional[str] = None,
        is_presentation: bool = False
    ) -> "PageMetadata":
        """Create page metadata from page number and source file.

        Args:
            page_num_0indexed: 0-indexed page number (will be converted to 1-based)
            sourcefile: Original filename (e.g., "sample_pages_test.pdf", "presentation.pptx")
            page_blob_url: URL to per-page PDF blob (optional, not used for presentations)
            is_presentation: True for PPTX files (uses slide numbers instead of pages)

        The sourcepage format follows prepdocs pattern:
        - PPTX: "presentation.pptx#slide=3" (whole presentation as unit)
        - PDF with blob: "sample_pages_test/page-0001.pdf#page=1"
        - PDF/DOCX without blob: "filename.pdf#page=N" or "document.docx#page=N"
        """
        page_num_1based = page_num_0indexed + 1

        if is_presentation:
            # PPTX: Reference slide numbers, no per-slide PDFs
            sourcepage = f"{os.path.basename(sourcefile)}#slide={page_num_1based}"
        elif page_blob_url:
            # PDF: Extract path from URL for sourcepage (more compact for LLM context)
            # e.g., "sample_pages_test/page-0001.pdf#page=1"
            try:
                # Parse blob URL to get path part
                parsed = urlparse(page_blob_url)
                # Get path after container name (last parts of path)
                path_parts = parsed.path.strip('/').split('/')
                if len(path_parts) >= 2:
                    # Take: docname/page-XXXX.pdf
                    sourcepage = '/'.join(path_parts[-2:]) + f"#page={page_num_1based}"
                else:
                    sourcepage = '/'.join(path_parts) + f"#page={page_num_1based}"
            except Exception:
                # Fallback to simple format
                sourcepage = f"{os.path.basename(sourcefile)}#page={page_num_1based}"
        else:
            # Default format: "filename.ext#page=N" (PDF, DOCX)
            sourcepage = f"{os.path.basename(sourcefile)}#page={page_num_1based}"

        return cls(
            page_num=page_num_1based,
            sourcepage=sourcepage,
            page_blob_url=page_blob_url
        )


@dataclass
class ChunkMetadata:
    """Metadata about a text chunk."""
    chunk_id: str
    chunk_index_on_page: int
    text: str
    embedding: Optional[list[float]] = None
    char_span: Optional[tuple[int, int]] = None
    token_count: Optional[int] = None
    title: Optional[str] = None  # Page header keyword for search (e.g., "Pacing Therapies")


@dataclass
class ChunkArtifact:
    """Information about the chunk artifact location."""
    url: Optional[str] = None
    local_path: Optional[str] = None


@dataclass
class TableReference:
    """Reference to a table in the document."""
    table_id: str
    pages: list[int]
    rendered_text: Optional[str] = None
    summary: Optional[str] = None
    bbox: Optional[tuple[float, float, float, float]] = None


@dataclass
class FigureReference:
    """Reference to a figure in the document.

    Phase 3: Supports equations with LaTeX and confidence scores.
    """
    figure_id: str
    page_num: int
    bbox: tuple[float, float, float, float]
    url: str
    description: Optional[str] = None
    filename: str = ""
    title: str = ""
    figure_type: str = "image"  # Phase 3: "image", "equation", "chart"
    latex: Optional[str] = None  # Phase 3: LaTeX representation for equations
    equation_confidence: Optional[float] = None  # Phase 3: Detection confidence (0.0-1.0)


@dataclass
class IngestionResult:
    """Result of document ingestion."""
    filename: str
    success: bool
    chunks_indexed: int = 0
    error_message: Optional[str] = None
    processing_time_seconds: Optional[float] = None


@dataclass
class PipelineStatus:
    """Overall pipeline execution status."""
    total_documents: int = 0
    successful_documents: int = 0
    failed_documents: int = 0
    total_chunks_indexed: int = 0
    results: list[IngestionResult] = field(default_factory=list)

    def add_result(self, result: IngestionResult):
        """Add an ingestion result and update counters."""
        self.results.append(result)
        self.total_documents += 1
        if result.success:
            self.successful_documents += 1
            self.total_chunks_indexed += result.chunks_indexed
        else:
            self.failed_documents += 1

    def get_summary(self) -> dict:
        """Get summary statistics."""
        return {
            "total_documents": self.total_documents,
            "successful_documents": self.successful_documents,
            "failed_documents": self.failed_documents,
            "total_chunks_indexed": self.total_chunks_indexed,
            "success_rate": f"{(self.successful_documents / self.total_documents * 100):.1f}%" if self.total_documents > 0 else "0%"
        }


@dataclass
class ChunkDocument:
    """Complete chunk document for storage and indexing."""
    document: DocumentMetadata
    page: PageMetadata
    chunk: ChunkMetadata
    chunk_artifact: ChunkArtifact
    tables: list[TableReference] = field(default_factory=list)
    figures: list[FigureReference] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "document": {
                "sourcefile": self.document.sourcefile,
                "storageUrl": self.document.storage_url,
                "content_type": self.document.content_type,
                "md5": self.document.md5_hash,
                "file_size": self.document.file_size,
                "ingested_at": self.document.ingested_at
            },
            "page": {
                "page_num": self.page.page_num,  # 1-indexed
                "sourcepage": self.page.sourcepage,
                "page_blob_url": self.page.page_blob_url
            },
            "chunk": {
                "chunk_id": self.chunk.chunk_id,
                "chunk_index_on_page": self.chunk.chunk_index_on_page,
                "text": self.chunk.text,
                "embedding": self.chunk.embedding,
                "char_span": self.chunk.char_span,
                "token_count": self.chunk.token_count,
                "title": self.chunk.title
            },
            "chunk_artifact": {
                "url": self.chunk_artifact.url,
                "local_path": self.chunk_artifact.local_path
            },
            "tables": [
                {
                    "table_id": t.table_id,
                    "pages": t.pages,
                    "rendered_text": t.rendered_text,
                    "summary": t.summary,
                    "bbox": t.bbox
                }
                for t in self.tables
            ],
            "figures": [
                {
                    "figure_id": f.figure_id,
                    "page_num": f.page_num,
                    "bbox": f.bbox,
                    "url": f.url,
                    "description": f.description,
                    "filename": f.filename,
                    "title": f.title
                }
                for f in self.figures
            ]
        }
    
    def to_search_document(self, include_embeddings: bool = True) -> dict:
        """Convert to Azure AI Search document format matching my_index.json schema.

        Args:
            include_embeddings: If True, include the embeddings field (client-side embeddings).
                               If False, omit embeddings field entirely (for integrated vectorization).
        """
        doc = {
            "id": self.chunk.chunk_id,
            "content": self.chunk.text,
            "filename": self.document.sourcefile,
            "sourcefile": self.document.sourcefile,
            "sourcepage": self.page.sourcepage,
            "pageNumber": self.page.page_num,  # 1-indexed
            # storageUrl: Per-page PDF URL (page-specific, clicking opens that specific page)
            # This is the page-oriented storage URL for citations
            "storageUrl": self.page.page_blob_url or self.document.storage_url,
            # url: Full document URL (original PDF file - the complete document)
            "url": self.document.storage_url,
            "category": None,  # Can be populated from external metadata later
            # Page header as title - used for keyword search (cleaned, no page numbers)
            # e.g., "Pacing Therapies" extracted from "<!-- PageHeader="2-2 Pacing Therapies" -->"
            "title": self.chunk.title,

            # Visual content indicators (MINIMAL - just flags and figure URLs)
            # Table content already in chunk text, just need flag
            # Figure images need blob URLs for display

            # Figure indicators - need URLs from blob storage for <img> display
            "has_figures": len(self.figures) > 0,
            "figure_urls": [f.url for f in self.figures if f.url],

            # Table indicators - content already in chunk text, just flag for filtering
            "has_tables": len(self.tables) > 0,
            # Other fields in my_index.json left empty for now:
            # country, language, product_family, productTradeNames, prod_from_url,
            # literatureType, partNumber, applicableTo, model, publishedDate
        }

        # Only include embeddings field when using client-side embeddings
        # For integrated vectorization, the field must be completely omitted
        if include_embeddings:
            doc["embeddings"] = self.chunk.embedding

        return doc

    def to_vector_document(self, include_embeddings: bool = True) -> dict:
        """Convert to generic vector document format.

        This provides a standardized format that can be adapted by each
        vector store implementation. Azure Search uses to_search_document(),
        while other stores (ChromaDB, Pinecone, etc.) should use this method.

        Args:
            include_embeddings: If True, include the embeddings vector.
                               If False, omit embeddings (for server-side vectorization).

        Returns:
            Dictionary with standardized vector document format containing:
            - id: Unique chunk identifier
            - text: Chunk text content
            - embedding: Embedding vector (if include_embeddings=True)
            - metadata: Dictionary with all chunk metadata
        """
        return {
            "id": self.chunk.chunk_id,
            "text": self.chunk.text,
            "embedding": self.chunk.embedding if include_embeddings else None,
            "metadata": {
                "sourcefile": self.document.sourcefile,
                "sourcepage": self.page.sourcepage,
                "page_number": self.page.page_num,
                "storage_url": self.page.page_blob_url or self.document.storage_url,
                "document_url": self.document.storage_url,
                "chunk_index": self.chunk.chunk_index_on_page,
                "title": self.chunk.title,
                "token_count": self.chunk.token_count,
                "has_figures": len(self.figures) > 0,
                "has_tables": len(self.tables) > 0,
                "figure_urls": [f.url for f in self.figures if f.url],
            }
        }

