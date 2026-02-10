"""Verify cross-page overlap behavior for semantic context preservation"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ingestor.config import PipelineConfig
from ingestor.chunker import create_chunker
from ingestor.di_extractor import DocumentIntelligenceExtractor
from ingestor.table_renderer import TableRenderer
from dotenv import load_dotenv

async def verify():
    load_dotenv()
    config = PipelineConfig.from_env()
    table_renderer = TableRenderer()
    extractor = DocumentIntelligenceExtractor(config.document_intelligence, table_renderer=table_renderer)

    pdf_path = Path(__file__).parent / "data" / "research_attention_paper.pdf"

    with pdf_path.open("rb") as f:
        pdf_bytes = f.read()

    print("="*80)
    print("CROSS-PAGE OVERLAP VERIFICATION")
    print("="*80)
    print()

    # Extract with DI
    pages = await extractor.extract_document(filename=pdf_path.name, pdf_bytes=pdf_bytes)

    # Chunk with overlap enabled
    chunker = create_chunker(
        max_chars=config.chunking.max_chars,
        max_tokens=config.chunking.max_tokens,
        max_section_tokens=750,
        overlap_percent=10,  # 10% overlap
        cross_page_overlap=True
    )

    chunks = chunker.chunk_pages(pages)
    print(f"Generated {len(chunks)} chunks\n")

    # Check each page transition
    print("="*80)
    print("PAGE TRANSITION ANALYSIS")
    print("="*80)
    print()

    for i in range(len(chunks) - 1):
        current = chunks[i]
        next_chunk = chunks[i + 1]

        # Check if this is a page boundary
        if current.page_num != next_chunk.page_num:
            print(f"📄 Page {current.page_num+1} → Page {next_chunk.page_num+1} Transition:")
            print(f"   Current chunk ends on Page {current.page_num+1}")
            print(f"   Next chunk starts on Page {next_chunk.page_num+1}")
            print()

            # Get last 100 chars of current chunk
            current_end = current.text[-200:].strip()
            # Get first 200 chars of next chunk
            next_start = next_chunk.text[:200].strip()

            print(f"   Current chunk ending:")
            print(f"   ...{current_end[-150:]}")
            print()
            print(f"   Next chunk starting:")
            print(f"   {next_start[:150]}...")
            print()

            # Check for overlap - see if any words from end of current appear in start of next
            current_words = current_end.split()[-20:]  # Last 20 words
            next_words = next_start.split()[:50]  # First 50 words

            overlap_words = []
            for word in current_words:
                if len(word) > 3 and word in ' '.join(next_words):
                    overlap_words.append(word)

            if overlap_words:
                print(f"   ✅ OVERLAP DETECTED: {len(overlap_words)} words overlap")
                print(f"   Overlapping words: {', '.join(overlap_words[:10])}")
            else:
                print(f"   ❌ NO OVERLAP: Next chunk starts fresh (no context from previous page)")

            print()
            print("-"*80)
            print()

    # Summary
    print("="*80)
    print("OVERLAP BEHAVIOR SUMMARY")
    print("="*80)
    print()
    print("Expected behavior for RAG/retrieval:")
    print("✅ Next chunk should START with overlap from previous page")
    print("✅ This preserves semantic context at page boundaries")
    print("✅ Helps retrieval find relevant context even if query matches page boundary")
    print()
    print("Configuration:")
    print(f"  - Overlap percent: 10%")
    print(f"  - Cross-page overlap: Enabled")
    print(f"  - Token range: 500-750 tokens")

if __name__ == "__main__":
    asyncio.run(verify())
