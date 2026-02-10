"""Test Tables.pdf with fixes"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ingestor.config import PipelineConfig
from ingestor.chunker import create_chunker
from ingestor.di_extractor import DocumentIntelligenceExtractor
from ingestor.table_renderer import TableRenderer
from dotenv import load_dotenv

async def test():
    load_dotenv()
    config = PipelineConfig.from_env()
    table_renderer = TableRenderer()
    extractor = DocumentIntelligenceExtractor(config.document_intelligence, table_renderer=table_renderer)

    pdf_path = Path(__file__).parent / "data" / "Tables.pdf"

    with pdf_path.open("rb") as f:
        pdf_bytes = f.read()

    print("Extracting Tables.pdf...")
    pages = await extractor.extract_document(filename=pdf_path.name, pdf_bytes=pdf_bytes)
    print(f"Extracted {len(pages)} pages\n")

    chunker = create_chunker(
        max_chars=config.chunking.max_chars,
        max_tokens=config.chunking.max_tokens,
        max_section_tokens=750,
        overlap_percent=config.chunking.overlap_percent,
        cross_page_overlap=True
    )

    print("Chunking...")
    chunks = chunker.chunk_pages(pages)
    print(f"Generated {len(chunks)} chunks\n")

    # Analyze token distribution
    print("="*80)
    print("CHUNK ANALYSIS")
    print("="*80)

    below_500 = 0
    for i, chunk in enumerate(chunks, 1):
        status = "OK " if chunk.token_count >= 500 or '<table>' in chunk.text.lower() or '<figure' in chunk.text.lower() else "LOW"
        has_table = " [TABLE]" if '<table>' in chunk.text.lower() else ""
        has_figure = " [FIGURE]" if '<figure' in chunk.text.lower() and '<table>' not in chunk.text.lower() else ""

        print(f"{status} Chunk {i:2d}: Page {chunk.page_num+1}, {chunk.token_count:4d} tokens{has_table}{has_figure}")

        if chunk.token_count < 500 and '<table>' not in chunk.text.lower() and '<figure' not in chunk.text.lower():
            below_500 += 1

    print()
    print("="*80)
    print(f"Total chunks: {len(chunks)}")
    print(f"Text chunks below 500 tokens: {below_500}")
    print(f"Success rate: {100 * (len(chunks) - below_500) // len(chunks)}%")

if __name__ == "__main__":
    asyncio.run(test())
