"""Test caption fix for table/figure captions"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ingestor.config import PipelineConfig
from ingestor.chunker import create_chunker
from ingestor.di_extractor import DocumentIntelligenceExtractor
from ingestor.table_renderer import TableRenderer
from dotenv import load_dotenv

async def test_caption():
    load_dotenv()
    config = PipelineConfig.from_env()
    table_renderer = TableRenderer()
    extractor = DocumentIntelligenceExtractor(config.document_intelligence, table_renderer=table_renderer)

    pdf_path = Path(__file__).parent / "data" / "sample_tracemonkey_paper.pdf"

    print("="*80)
    print("TESTING CAPTION FIX - TracMonkey Paper")
    print("="*80)
    print()

    with pdf_path.open("rb") as f:
        pdf_bytes = f.read()

    # Extract with DI
    print("Extracting with DI...")
    pages = await extractor.extract_document(filename=pdf_path.name, pdf_bytes=pdf_bytes)
    print(f"OK Extracted {len(pages)} pages")
    print()

    # Check Page 3 (index 2) which has the tables with Figure 3 and Figure 4 captions
    page_3 = pages[2]

    print("="*80)
    print("PAGE 3 TABLE CAPTIONS")
    print("="*80)
    print()

    for i, table in enumerate(page_3.tables, 1):
        print(f"Table {i}:")
        print(f"   Row count: {table.row_count}")
        print(f"   Column count: {table.column_count}")
        print(f"   Caption: {table.caption if table.caption else 'None'}")
        print()

    # Chunk and check if captions appear in chunks
    print("="*80)
    print("CHUNKING AND CHECKING FOR CAPTIONS")
    print("="*80)
    print()

    chunker = create_chunker(
        max_chars=config.chunking.max_chars,
        max_tokens=500,
        max_section_tokens=750,
        overlap_percent=10,
        cross_page_overlap=True
    )

    chunks = chunker.chunk_pages(pages)
    print(f"Generated {len(chunks)} chunks")
    print()

    # Find chunks on Page 3
    page_3_chunks = [c for c in chunks if c.page_num == 2]  # 0-indexed

    print(f"Page 3 has {len(page_3_chunks)} chunk(s)")
    print()

    # Check if Figure 3 and Figure 4 captions appear
    target_captions = [
        "Figure 3. LIR snippet",
        "Figure 4. x86 snippet",
        "Figure 3.",
        "Figure 4."
    ]

    all_page_3_text = "\n".join(c.text for c in page_3_chunks)

    print("="*80)
    print("CAPTION SEARCH RESULTS")
    print("="*80)
    print()

    for caption in target_captions:
        if caption in all_page_3_text:
            print(f"OK FOUND: '{caption}' in Page 3 chunks")
        else:
            print(f"X MISSING: '{caption}' in Page 3 chunks")

    print()

    # Show first chunk with Figure 3 or Figure 4
    print("="*80)
    print("SAMPLE CHUNK WITH CAPTION")
    print("="*80)
    print()

    for i, chunk in enumerate(page_3_chunks, 1):
        if "Figure 3" in chunk.text or "Figure 4" in chunk.text:
            print(f"Chunk {i} (Page {chunk.page_num + 1}):")
            print(f"Tokens: {chunk.token_count}")
            print()
            print("First 500 chars:")
            print("-"*80)
            print(chunk.text[:500])
            print("-"*80)
            break

    print()
    print("="*80)
    print("TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_caption())
