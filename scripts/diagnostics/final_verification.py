"""Final verification of chunking for both documents"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ingestor.config import PipelineConfig
from ingestor.chunker import create_chunker
from ingestor.di_extractor import DocumentIntelligenceExtractor
from ingestor.table_renderer import TableRenderer
from dotenv import load_dotenv

async def verify_document(pdf_name: str):
    """Verify a single document"""
    load_dotenv()
    config = PipelineConfig.from_env()
    table_renderer = TableRenderer()
    extractor = DocumentIntelligenceExtractor(config.document_intelligence, table_renderer=table_renderer)

    pdf_path = Path(__file__).parent / "data" / pdf_name

    print("="*80)
    print(f"VERIFYING: {pdf_name}")
    print("="*80)
    print()

    with pdf_path.open("rb") as f:
        pdf_bytes = f.read()

    # Extract
    pages = await extractor.extract_document(filename=pdf_path, pdf_bytes=pdf_bytes)
    print(f"✅ Extracted {len(pages)} pages")

    # Chunk
    chunker = create_chunker(
        max_chars=config.chunking.max_chars,
        max_tokens=500,
        max_section_tokens=750,
        overlap_percent=10,
        cross_page_overlap=True
    )

    chunks = chunker.chunk_pages(pages)
    print(f"✅ Generated {len(chunks)} chunks")
    print()

    # Analyze
    print(f"{'Chunk':<6} {'Page':<5} {'Tokens':<8} {'Chars':<8} {'Type':<20}")
    print("-"*80)

    text_below_500 = 0
    text_above_500 = 0
    atomic_chunks = 0

    for i, chunk in enumerate(chunks, 1):
        has_table = '<table>' in chunk.text.lower()
        has_figure = '<figure' in chunk.text.lower()

        if has_table:
            chunk_type = "TABLE (atomic)"
            atomic_chunks += 1
        elif has_figure:
            chunk_type = "FIGURE (atomic)"
            atomic_chunks += 1
        elif chunk.token_count >= 500:
            chunk_type = "TEXT ✅"
            text_above_500 += 1
        else:
            chunk_type = "TEXT ⚠️  (<500tok)"
            text_below_500 += 1

        print(f"#{i:<5} {chunk.page_num+1:<5} {chunk.token_count:<8} {len(chunk.text):<8} {chunk_type:<20}")

    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total chunks:                 {len(chunks)}")
    print(f"Text chunks ≥500 tokens:      {text_above_500}")
    print(f"Text chunks <500 tokens:      {text_below_500}")
    print(f"Atomic tables/figures:        {atomic_chunks}")
    print()

    # Cross-page overlap
    transitions = 0
    overlaps = 0

    for i in range(len(chunks) - 1):
        if chunks[i].page_num != chunks[i+1].page_num:
            transitions += 1
            # Simple overlap check
            end_words = set(chunks[i].text.split()[-20:])
            start_words = set(chunks[i+1].text.split()[:40])
            if len(end_words & start_words) > 0:
                overlaps += 1

    print(f"Page transitions:             {transitions}")
    print(f"Transitions with overlap:     {overlaps} ({100*overlaps//max(1,transitions)}%)")
    print()

    # Text preservation
    di_text = ''.join(p.text for p in pages)
    chunk_text = '\n\n'.join(c.text for c in chunks)

    # Check for key content preservation (sample check)
    issues = []

    # Check if any page's text is completely missing
    for i, page in enumerate(pages):
        if len(page.text.strip()) > 100:  # Only check pages with substantial text
            sample = page.text[:200].strip()
            if sample and sample not in chunk_text:
                issues.append(f"Page {i+1} text might be missing")

    if issues:
        print("⚠️  POTENTIAL ISSUES:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ Text preservation: GOOD")

    print()

    # Overall verdict
    text_quality = text_above_500 / max(1, text_above_500 + text_below_500)
    overlap_quality = overlaps / max(1, transitions)

    print("="*80)
    if text_quality >= 0.7 and overlap_quality >= 0.6:
        print("✅ READY FOR RAG")
    elif text_quality >= 0.5 and overlap_quality >= 0.5:
        print("⚠️  ACCEPTABLE FOR RAG (with minor issues)")
    else:
        print("❌ NEEDS IMPROVEMENT")
    print("="*80)
    print()
    print()


async def main():
    print()
    print("="*80)
    print("FINAL VERIFICATION - BOTH DOCUMENTS")
    print("="*80)
    print()

    await verify_document("Tables.pdf")
    await verify_document("medical_who_report.pdf")

    print()
    print("="*80)
    print("VERIFICATION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
