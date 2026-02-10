"""Test overlap fix"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ingestor.config import PipelineConfig
from ingestor.chunker import create_chunker
from ingestor.di_extractor import DocumentIntelligenceExtractor
from ingestor.table_renderer import TableRenderer
from dotenv import load_dotenv

async def test_overlap():
    """Test overlap with new fix"""

    load_dotenv()
    config = PipelineConfig.from_env()
    table_renderer = TableRenderer()
    extractor = DocumentIntelligenceExtractor(config.document_intelligence, table_renderer=table_renderer)

    pdf_path = Path(__file__).parent / "data" / "Tables.pdf"
    print(f"📄 Loading {pdf_path.name}...")

    with pdf_path.open("rb") as f:
        pdf_bytes = f.read()

    print("🔍 Extracting...")
    pages = await extractor.extract_document(filename=pdf_path.name, pdf_bytes=pdf_bytes)
    print(f"✅ Extracted {len(pages)} pages")

    # Create chunker
    chunker = create_chunker(
        max_chars=config.chunking.max_chars,
        max_tokens=config.chunking.max_tokens,
        max_section_tokens=750,  # New parameter!
        overlap_percent=config.chunking.overlap_percent,
        cross_page_overlap=True
    )

    print("\n✂️  Chunking...")
    chunks = chunker.chunk_pages(pages)

    print(f"\n📊 Results:")
    print(f"   Total chunks: {len(chunks)} (was 16 before overlap fix)")
    print()

    # Count chunks by page
    from collections import Counter
    page_counts = Counter(c.page_num for c in chunks)
    print("Chunks per page:")
    for page_num in sorted(page_counts.keys()):
        print(f"   Page {page_num+1}: {page_counts[page_num]} chunk(s)")

    print()
    print("Token distribution:")
    print(f"   Chunks > 700 tokens: {len([c for c in chunks if c.token_count > 700])}")
    print(f"   Chunks 500-700 tokens: {len([c for c in chunks if 500 <= c.token_count <= 700])}")
    print(f"   Chunks 200-500 tokens: {len([c for c in chunks if 200 <= c.token_count < 500])}")
    print(f"   Orphans < 200 tokens: {len([c for c in chunks if c.token_count < 200])}")

if __name__ == "__main__":
    asyncio.run(test_overlap())
