"""Test full document chunking with logging"""
import asyncio
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

# Enable logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

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

    pdf_path = Path(__file__).parent / "data" / "research_attention_paper.pdf"

    with pdf_path.open("rb") as f:
        pdf_bytes = f.read()

    print("Extracting...")
    pages = await extractor.extract_document(filename=pdf_path.name, pdf_bytes=pdf_bytes)
    print(f"Extracted {len(pages)} pages\n")

    chunker = create_chunker(
        max_chars=config.chunking.max_chars,
        max_tokens=config.chunking.max_tokens,
        max_section_tokens=750,
        overlap_percent=config.chunking.overlap_percent,
        cross_page_overlap=True
    )

    print("Chunking all pages with logging...\n")
    chunks = chunker.chunk_pages(pages)
    print(f"\nGenerated {len(chunks)} total chunks")

if __name__ == "__main__":
    asyncio.run(test())
