"""Diagnose text loss in chunking - compare DI extraction vs chunks"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ingestor.config import PipelineConfig
from ingestor.chunker import create_chunker
from ingestor.di_extractor import DocumentIntelligenceExtractor
from ingestor.table_renderer import TableRenderer
from dotenv import load_dotenv

async def diagnose():
    """Compare DI extraction with chunked output to find text loss"""

    load_dotenv()
    config = PipelineConfig.from_env()
    table_renderer = TableRenderer()
    extractor = DocumentIntelligenceExtractor(config.document_intelligence, table_renderer=table_renderer)

    pdf_path = Path(__file__).parent / "data" / "research_attention_paper.pdf"
    print("="*80)
    print(f"🔬 DIAGNOSING TEXT LOSS: {pdf_path.name}")
    print("="*80)
    print()

    with pdf_path.open("rb") as f:
        pdf_bytes = f.read()

    # Extract with DI
    print("📄 Step 1: Extract with Document Intelligence...")
    pages = await extractor.extract_document(filename=pdf_path.name, pdf_bytes=pdf_bytes)
    print(f"✅ Extracted {len(pages)} pages")
    print()

    # Focus on Page 2 (index 1)
    page_2 = pages[1]
    print("="*80)
    print(f"PAGE 2 ANALYSIS (page_num={page_2.page_num})")
    print("="*80)
    print()

    print(f"Page 2 text length: {len(page_2.text)} characters")
    print(f"Page 2 tables: {len(page_2.tables)}")
    print(f"Page 2 images: {len(page_2.images)}")
    print()

    # Show the text from DI extraction
    print("--- DI EXTRACTED TEXT FOR PAGE 2 ---")
    print("First 2000 characters:")
    print(page_2.text[:2000])
    print("\n... middle section ...\n")
    print("Last 1000 characters:")
    print(page_2.text[-1000:])
    print()

    # Now chunk it
    print("="*80)
    print("CHUNKING PAGE 2")
    print("="*80)
    print()

    chunker = create_chunker(
        max_chars=config.chunking.max_chars,
        max_tokens=config.chunking.max_tokens,
        max_section_tokens=750,
        overlap_percent=config.chunking.overlap_percent,
        cross_page_overlap=True
    )

    chunks = chunker.chunk_pages(pages)
    print(f"✅ Generated {len(chunks)} total chunks")
    print()

    # Find chunks from Page 2
    page_2_chunks = [c for c in chunks if c.page_num == 1]  # page_num is 0-indexed
    print(f"Page 2 has {len(page_2_chunks)} chunk(s)")
    print()

    for i, chunk in enumerate(page_2_chunks, 1):
        print(f"--- Page 2 Chunk {i} ---")
        print(f"Token count: {chunk.token_count}")
        print(f"Text length: {len(chunk.text)} characters")
        print()
        print("First 500 characters:")
        print(chunk.text[:500])
        print("\n... middle ...\n")
        print("Last 500 characters:")
        print(chunk.text[-500:])
        print()
        print("-"*80)
        print()

    # Now compare text content
    print("="*80)
    print("TEXT COMPARISON")
    print("="*80)
    print()

    # Concatenate all chunks from page 2
    all_chunk_text = "\n\n".join(c.text for c in page_2_chunks)

    # Clean up text for comparison (remove extra whitespace)
    def normalize_text(text):
        import re
        # Remove multiple spaces/newlines
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    di_text_clean = normalize_text(page_2.text)
    chunk_text_clean = normalize_text(all_chunk_text)

    print(f"DI extracted text length: {len(di_text_clean)} chars")
    print(f"Chunked text length: {len(chunk_text_clean)} chars")
    print(f"Difference: {len(di_text_clean) - len(chunk_text_clean)} chars")
    print()

    if len(di_text_clean) > len(chunk_text_clean):
        print("❌ TEXT IS MISSING FROM CHUNKS!")
        print()

        # Find what's missing
        # Look for key phrases that should be present
        key_phrases = [
            "The fundamental constraint of sequential computation, however, remains",
            "Attention mechanisms have become an integral part",
            "In this work we propose the Transformer",
            "The goal of reducing sequential computation",
            "Self-attention, sometimes called intra-attention"
        ]

        print("Checking key phrases:")
        for phrase in key_phrases:
            in_di = phrase in page_2.text
            in_chunks = phrase in all_chunk_text
            status = "✅" if (in_di and in_chunks) else "❌"
            print(f"{status} '{phrase[:50]}...' - DI: {in_di}, Chunks: {in_chunks}")
        print()

        # Show missing section
        print("="*80)
        print("IDENTIFYING MISSING TEXT")
        print("="*80)

        # Find where "however," appears
        if "however, remains" in page_2.text:
            idx = page_2.text.index("however, remains")
            print("\nText around 'however, remains' in DI extraction:")
            print(page_2.text[max(0, idx-100):idx+500])
            print()

        if "however," in all_chunk_text:
            idx = all_chunk_text.index("however,")
            print("\nText around 'however,' in chunks:")
            print(all_chunk_text[max(0, idx-100):idx+500])
            print()
    else:
        print("✅ No text missing!")

if __name__ == "__main__":
    asyncio.run(diagnose())
