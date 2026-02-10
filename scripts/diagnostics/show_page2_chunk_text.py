"""Show the actual text in Page 2 chunks"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ingestor.config import PipelineConfig
from ingestor.chunker import create_chunker
from ingestor.di_extractor import DocumentIntelligenceExtractor
from ingestor.table_renderer import TableRenderer
from dotenv import load_dotenv

async def show():
    load_dotenv()
    config = PipelineConfig.from_env()
    table_renderer = TableRenderer()
    extractor = DocumentIntelligenceExtractor(config.document_intelligence, table_renderer=table_renderer)

    pdf_path = Path(__file__).parent / "data" / "research_attention_paper.pdf"

    with pdf_path.open("rb") as f:
        pdf_bytes = f.read()

    # Extract and chunk
    pages = await extractor.extract_document(filename=pdf_path.name, pdf_bytes=pdf_bytes)
    chunker = create_chunker(
        max_chars=config.chunking.max_chars,
        max_tokens=config.chunking.max_tokens,
        max_section_tokens=750,
        overlap_percent=config.chunking.overlap_percent,
        cross_page_overlap=True
    )
    chunks = chunker.chunk_pages(pages)

    # Find Page 2 chunks
    page_2_chunks = [c for c in chunks if c.page_num == 1]  # 0-indexed

    print(f"Page 2 has {len(page_2_chunks)} chunk(s)")
    print()

    for i, chunk in enumerate(page_2_chunks, 1):
        print(f"===== CHUNK {i} =====")
        print(f"Tokens: {chunk.token_count}")
        print(f"Chars: {len(chunk.text)}")
        print()
        print("FULL TEXT:")
        print("-"*80)
        print(chunk.text)
        print("-"*80)
        print()

if __name__ == "__main__":
    asyncio.run(show())
