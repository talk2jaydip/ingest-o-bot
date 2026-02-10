"""Comprehensive verification of Tables.pdf and WHO medical report"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ingestor.config import PipelineConfig
from ingestor.chunker import create_chunker
from ingestor.di_extractor import DocumentIntelligenceExtractor
from ingestor.table_renderer import TableRenderer
from dotenv import load_dotenv

async def test_document(pdf_path: Path, config: PipelineConfig, extractor: DocumentIntelligenceExtractor):
    """Test a single document"""
    print("="*80)
    print(f"TESTING: {pdf_path.name}")
    print("="*80)
    print()

    with pdf_path.open("rb") as f:
        pdf_bytes = f.read()

    # Extract with DI
    print(f"📄 Extracting {pdf_path.name}...")
    pages = await extractor.extract_document(filename=pdf_path.name, pdf_bytes=pdf_bytes)
    print(f"✅ Extracted {len(pages)} pages")
    print()

    # Chunk
    chunker = create_chunker(
        max_chars=config.chunking.max_chars,
        max_tokens=config.chunking.max_tokens,
        max_section_tokens=750,
        overlap_percent=config.chunking.overlap_percent,
        cross_page_overlap=True
    )

    print("✂️  Chunking...")
    chunks = chunker.chunk_pages(pages)
    print(f"✅ Generated {len(chunks)} chunks")
    print()

    # Analyze chunks
    print("-"*80)
    print("CHUNK ANALYSIS")
    print("-"*80)
    print()

    below_500_count = 0
    atomic_count = 0
    good_count = 0
    overlap_count = 0

    print(f"{'#':<4} {'Page':<5} {'Tokens':<7} {'Type':<15} {'Status':<10}")
    print("-"*80)

    for i, chunk in enumerate(chunks, 1):
        has_table = '<table>' in chunk.text.lower()
        has_figure = '<figure' in chunk.text.lower()

        # Determine type
        if has_table or (has_figure and chunk.token_count < 50):
            chunk_type = "TABLE/FIGURE"
            atomic_count += 1
            status = "ATOMIC"
        elif chunk.token_count >= 500:
            chunk_type = "TEXT"
            good_count += 1
            status = "✅ GOOD"
        else:
            chunk_type = "TEXT"
            below_500_count += 1
            status = "⚠️  SMALL"

        print(f"{i:<4} {chunk.page_num+1:<5} {chunk.token_count:<7} {chunk_type:<15} {status:<10}")

    print()
    print("-"*80)
    print("SUMMARY")
    print("-"*80)
    print(f"Total chunks:              {len(chunks)}")
    print(f"Text chunks ≥500 tokens:   {good_count} ({100*good_count//len(chunks)}%)")
    print(f"Text chunks <500 tokens:   {below_500_count} ({100*below_500_count//len(chunks)}%)")
    print(f"Atomic tables/figures:     {atomic_count} ({100*atomic_count//len(chunks)}%)")
    print()

    # Check cross-page overlap
    print("-"*80)
    print("CROSS-PAGE OVERLAP ANALYSIS")
    print("-"*80)
    print()

    page_transitions = 0
    overlaps_detected = 0

    for i in range(len(chunks) - 1):
        current = chunks[i]
        next_chunk = chunks[i + 1]

        if current.page_num != next_chunk.page_num:
            page_transitions += 1

            # Check for overlap
            current_end_words = current.text.split()[-30:]
            next_start_words = next_chunk.text.split()[:50]

            overlap_words = []
            for word in current_end_words:
                if len(word) > 3 and word in ' '.join(next_start_words):
                    overlap_words.append(word)

            has_overlap = len(overlap_words) > 0
            if has_overlap:
                overlaps_detected += 1

            status = "✅" if has_overlap else "❌"
            print(f"{status} Page {current.page_num+1} → {next_chunk.page_num+1}: {len(overlap_words)} overlapping words")

    print()
    print(f"Page transitions:          {page_transitions}")
    print(f"Overlaps detected:         {overlaps_detected} ({100*overlaps_detected//max(1,page_transitions)}%)")
    print()

    # Verify text preservation (check that chunks have meaningful content)
    print("-"*80)
    print("TEXT PRESERVATION CHECK")
    print("-"*80)
    print()

    # Get all text from DI
    di_total_chars = sum(len(page.text) for page in pages)

    # Get all text from chunks
    chunk_total_chars = sum(len(chunk.text) for chunk in chunks)

    # Account for overlap (approximate)
    overlap_chars_estimate = overlaps_detected * 200  # ~200 chars per overlap
    adjusted_chunk_chars = chunk_total_chars - overlap_chars_estimate

    print(f"DI extraction text:        {di_total_chars:,} chars")
    print(f"Chunk text (with overlap): {chunk_total_chars:,} chars")
    print(f"Chunk text (adjusted):     {adjusted_chunk_chars:,} chars")

    # Allow some variance due to figure tags and formatting
    if adjusted_chunk_chars >= di_total_chars * 0.95:
        print("✅ Text preservation: GOOD (≥95%)")
    elif adjusted_chunk_chars >= di_total_chars * 0.90:
        print("⚠️  Text preservation: ACCEPTABLE (≥90%)")
    else:
        print("❌ Text preservation: POOR (<90%)")

    print()

    # Overall score
    print("-"*80)
    print("OVERALL QUALITY SCORE")
    print("-"*80)
    print()

    # Calculate score
    good_chunks_score = 40 * good_count // len(chunks)
    overlap_score = 30 * overlaps_detected // max(1, page_transitions)
    preservation_score = 30 if adjusted_chunk_chars >= di_total_chars * 0.95 else 15

    total_score = good_chunks_score + overlap_score + preservation_score

    print(f"Good chunks (≥500 tok):    {good_chunks_score}/40")
    print(f"Cross-page overlap:        {overlap_score}/30")
    print(f"Text preservation:         {preservation_score}/30")
    print()
    print(f"TOTAL SCORE:               {total_score}/100")
    print()

    if total_score >= 80:
        print("✅ EXCELLENT - Ready for RAG")
    elif total_score >= 60:
        print("⚠️  GOOD - Minor improvements possible")
    else:
        print("❌ NEEDS IMPROVEMENT")

    print()
    print()

    return {
        'name': pdf_path.name,
        'chunks': len(chunks),
        'good_chunks': good_count,
        'below_500': below_500_count,
        'atomic': atomic_count,
        'overlaps': overlaps_detected,
        'transitions': page_transitions,
        'score': total_score
    }


async def main():
    load_dotenv()
    config = PipelineConfig.from_env()
    table_renderer = TableRenderer()
    extractor = DocumentIntelligenceExtractor(config.document_intelligence, table_renderer=table_renderer)

    print()
    print("="*80)
    print("COMPREHENSIVE DOCUMENT CHUNKING VERIFICATION")
    print("="*80)
    print()
    print("Testing Configuration:")
    print(f"  - Min tokens: 500")
    print(f"  - Max tokens: 750")
    print(f"  - Overlap: 10%")
    print(f"  - Cross-page overlap: Enabled")
    print()

    results = []

    # Test Tables.pdf
    tables_path = Path(__file__).parent / "data" / "Tables.pdf"
    if tables_path.exists():
        result = await test_document(tables_path, config, extractor)
        results.append(result)

    # Test WHO medical report
    who_path = Path(__file__).parent / "data" / "medical_who_report.pdf"
    if who_path.exists():
        result = await test_document(who_path, config, extractor)
        results.append(result)

    # Final summary
    print("="*80)
    print("FINAL SUMMARY - BOTH DOCUMENTS")
    print("="*80)
    print()

    print(f"{'Document':<30} {'Chunks':<8} {'≥500tok':<10} {'Overlap':<10} {'Score':<8}")
    print("-"*80)

    for r in results:
        overlap_pct = f"{100*r['overlaps']//max(1,r['transitions'])}%" if r['transitions'] > 0 else "N/A"
        print(f"{r['name']:<30} {r['chunks']:<8} {r['good_chunks']:<10} {overlap_pct:<10} {r['score']}/100")

    print()
    print("="*80)
    print()

    avg_score = sum(r['score'] for r in results) // len(results)
    if avg_score >= 80:
        print("✅ OVERALL: EXCELLENT - All documents ready for RAG")
    elif avg_score >= 60:
        print("⚠️  OVERALL: GOOD - Documents usable with minor issues")
    else:
        print("❌ OVERALL: NEEDS WORK - Improvements required")

    print()


if __name__ == "__main__":
    asyncio.run(main())
