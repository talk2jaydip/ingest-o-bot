"""Check if all text from DI extraction appears in chunks"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ingestor.config import PipelineConfig
from ingestor.chunker import create_chunker
from ingestor.di_extractor import DocumentIntelligenceExtractor
from ingestor.table_renderer import TableRenderer
from dotenv import load_dotenv

async def check():
    load_dotenv()
    config = PipelineConfig.from_env()
    table_renderer = TableRenderer()
    extractor = DocumentIntelligenceExtractor(config.document_intelligence, table_renderer=table_renderer)

    pdf_path = Path(__file__).parent / "data" / "research_attention_paper.pdf"

    with pdf_path.open("rb") as f:
        pdf_bytes = f.read()

    # Extract with DI
    pages = await extractor.extract_document(filename=pdf_path.name, pdf_bytes=pdf_bytes)

    # Get Page 2 text
    page_2 = pages[1]
    di_text = page_2.text

    print(f"DI extraction Page 2: {len(di_text)} chars")
    print()

    # Chunk the document
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

    print(f"Page 2 chunks: {len(page_2_chunks)}")
    print()

    for i, chunk in enumerate(page_2_chunks, 1):
        print(f"Chunk {i}: {chunk.token_count} tokens, {len(chunk.text)} chars")
        print(f"  First 100 chars: {chunk.text[:100]}")
        print()

    # Combine all Page 2 chunk text
    all_chunk_text = "\n\n".join(c.text for c in page_2_chunks)

    print(f"Total chunk text: {len(all_chunk_text)} chars")
    print()

    # Check for key phrases
    phrases = [
        ("however, remains", "The word 'remains' after 'however,'"),
        ("Attention mechanisms have become", "Start of paragraph about attention mechanisms"),
        ("In this work we propose", "Paragraph about proposing Transformer"),
        ("## 2 Background", "Section 2 heading"),
        ("The goal of reducing sequential", "Start of Section 2 content")
    ]

    missing_count = 0
    print("Checking key phrases:")
    print("="*80)
    for phrase, description in phrases:
        in_di = phrase in di_text
        in_chunks = phrase in all_chunk_text

        if in_di and not in_chunks:
            print(f"❌ MISSING: {description}")
            print(f"   Phrase: '{phrase}'")
            print(f"   In DI: {in_di}, In chunks: {in_chunks}")
            print()
            missing_count += 1
        elif in_di and in_chunks:
            print(f"✅ Found: {description}")
        else:
            print(f"⚠️  Not in DI: {description}")

    print()
    print("="*80)
    if missing_count > 0:
        print(f"❌ {missing_count} phrase(s) MISSING from chunks!")
        print()
        print("This indicates text loss during chunking.")
    else:
        print("✅ All key phrases preserved!")

if __name__ == "__main__":
    asyncio.run(check())
