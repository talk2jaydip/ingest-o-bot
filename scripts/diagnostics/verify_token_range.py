"""Verify that chunks are in 500-750 token range (except atomic tables)"""
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

    # Test with all 3 documents
    test_files = [
        "Tables.pdf",
        "medical_who_report.pdf",
        "research_attention_paper.pdf"
    ]

    print("="*80)
    print("VERIFICATION: 500-750 TOKEN RANGE")
    print("="*80)
    print()

    for pdf_name in test_files:
        pdf_path = Path(__file__).parent / "data" / pdf_name
        if not pdf_path.exists():
            print(f"⚠️  Skipping {pdf_name} (not found)")
            continue

        print(f"📄 Testing: {pdf_name}")
        print("-"*80)

        with pdf_path.open("rb") as f:
            pdf_bytes = f.read()

        pages = await extractor.extract_document(filename=pdf_path.name, pdf_bytes=pdf_bytes)

        chunker = create_chunker(
            max_chars=config.chunking.max_chars,
            max_tokens=500,  # Minimum
            max_section_tokens=750,  # Maximum
            overlap_percent=config.chunking.overlap_percent,
            cross_page_overlap=True
        )

        chunks = chunker.chunk_pages(pages)

        # Analyze token distribution
        under_500 = []
        in_range_500_750 = []
        over_750 = []

        for i, chunk in enumerate(chunks):
            tokens = chunk.token_count or 0
            if tokens < 500:
                under_500.append((i+1, tokens, '<table>' in chunk.text.lower()))
            elif tokens <= 750:
                in_range_500_750.append((i+1, tokens))
            else:
                over_750.append((i+1, tokens, '<table>' in chunk.text.lower() or '<figure' in chunk.text.lower()))

        # Report
        print(f"Total chunks: {len(chunks)}")
        print()

        if under_500:
            print(f"❌ UNDER 500 tokens: {len(under_500)} chunks")
            for cid, tokens, has_table in under_500:
                table_note = " (has table/figure)" if has_table else ""
                print(f"   Chunk {cid}: {tokens} tokens{table_note}")
        else:
            print(f"✅ No chunks under 500 tokens")

        print()

        print(f"✅ IN RANGE 500-750: {len(in_range_500_750)} chunks ({100*len(in_range_500_750)/len(chunks):.0f}%)")
        if len(in_range_500_750) <= 5:
            for cid, tokens in in_range_500_750:
                print(f"   Chunk {cid}: {tokens} tokens")

        print()

        if over_750:
            print(f"⚠️  OVER 750 tokens: {len(over_750)} chunks")
            for cid, tokens, has_table in over_750:
                if has_table:
                    print(f"   Chunk {cid}: {tokens} tokens ✅ (atomic table/figure - OK to exceed)")
                else:
                    print(f"   Chunk {cid}: {tokens} tokens ❌ (NOT a table - should not exceed!)")
        else:
            print(f"✅ No chunks over 750 tokens")

        print()

        # Calculate statistics
        avg_tokens = sum(c.token_count or 0 for c in chunks) / len(chunks)
        min_tokens = min((c.token_count or 0 for c in chunks), default=0)
        max_tokens = max((c.token_count or 0 for c in chunks), default=0)

        print(f"Statistics:")
        print(f"  Average: {avg_tokens:.0f} tokens")
        print(f"  Min: {min_tokens} tokens")
        print(f"  Max: {max_tokens} tokens")
        print()

        # Overall assessment
        non_table_under_500 = [c for c in under_500 if not c[2]]
        non_table_over_750 = [c for c in over_750 if not c[2]]

        if non_table_under_500:
            print(f"❌ FAIL: {len(non_table_under_500)} regular chunks under 500 tokens")
        elif non_table_over_750:
            print(f"❌ FAIL: {len(non_table_over_750)} regular chunks over 750 tokens")
        else:
            print(f"✅ PASS: All regular chunks in 500-750 range, atomic tables handled correctly")

        print()
        print("="*80)
        print()

if __name__ == "__main__":
    asyncio.run(verify())
