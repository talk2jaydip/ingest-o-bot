"""Comprehensive analysis of medical_who_report.pdf chunking"""
import asyncio
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ingestor.config import PipelineConfig
from ingestor.chunker import create_chunker
from ingestor.di_extractor import DocumentIntelligenceExtractor
from ingestor.table_renderer import TableRenderer
from dotenv import load_dotenv

async def analyze():
    """Analyze medical WHO report chunking"""

    load_dotenv()
    config = PipelineConfig.from_env()
    table_renderer = TableRenderer()
    extractor = DocumentIntelligenceExtractor(config.document_intelligence, table_renderer=table_renderer)

    pdf_path = Path(__file__).parent / "data" / "medical_who_report.pdf"
    print(f"📄 Analyzing {pdf_path.name}")
    print("=" * 80)

    with pdf_path.open("rb") as f:
        pdf_bytes = f.read()

    print("\n🔍 Extracting with Document Intelligence...")
    pages = await extractor.extract_document(filename=pdf_path.name, pdf_bytes=pdf_bytes)
    print(f"✅ Extracted {len(pages)} pages")

    # Count content across pages
    page_stats = []
    for page in pages:
        stats = {
            'page': page.page_num + 1,
            'tables': len(page.tables),
            'images': len(page.images),
            'text_len': len(page.text),
            'has_figures': '<figure' in page.text.lower()
        }
        page_stats.append(stats)

    print("\n📊 Document Structure:")
    print(f"{'Page':<6} {'Tables':<8} {'Images':<8} {'Text Len':<10} {'Figures':<10}")
    print("-" * 50)
    for s in page_stats:
        print(f"{s['page']:<6} {s['tables']:<8} {s['images']:<8} {s['text_len']:<10} {s['has_figures']:<10}")

    # Create chunker with all fixes
    chunker = create_chunker(
        max_chars=config.chunking.max_chars,
        max_tokens=config.chunking.max_tokens,
        max_section_tokens=750,  # Hard maximum
        overlap_percent=config.chunking.overlap_percent,
        cross_page_overlap=True
    )

    print("\n✂️  Chunking document...")
    chunks = chunker.chunk_pages(pages)

    print(f"\n✅ Generated {len(chunks)} chunks")
    print()

    # Comprehensive chunk analysis
    print("=" * 80)
    print("CHUNK ANALYSIS")
    print("=" * 80)
    print()

    # Token distribution
    token_ranges = {
        'Atomic tables (>700)': [],
        '500-700 (target)': [],
        '300-500 (acceptable)': [],
        '200-300 (borderline)': [],
        '<200 (orphans)': []
    }

    for i, chunk in enumerate(chunks):
        tokens = chunk.token_count
        if tokens > 700:
            token_ranges['Atomic tables (>700)'].append((i+1, tokens))
        elif 500 <= tokens <= 700:
            token_ranges['500-700 (target)'].append((i+1, tokens))
        elif 300 <= tokens < 500:
            token_ranges['300-500 (acceptable)'].append((i+1, tokens))
        elif 200 <= tokens < 300:
            token_ranges['200-300 (borderline)'].append((i+1, tokens))
        else:
            token_ranges['<200 (orphans)'].append((i+1, tokens))

    print("Token Distribution:")
    for range_name, chunk_list in token_ranges.items():
        if chunk_list:
            print(f"\n{range_name}: {len(chunk_list)} chunks")
            for chunk_id, tokens in chunk_list:
                has_table = '<table>' in chunks[chunk_id-1].text or 'table_' in chunks[chunk_id-1].text.lower()
                has_figure = '<figure' in chunks[chunk_id-1].text.lower()
                print(f"  Chunk {chunk_id}: {tokens} tokens (table={has_table}, figure={has_figure})")

    print()
    print("=" * 80)
    print("EDGE CASES CHECK")
    print("=" * 80)
    print()

    # Check for specific edge cases
    print("1. Cross-page overlap verification:")
    overlap_found = 0
    for i in range(len(chunks)-1):
        curr = chunks[i]
        nxt = chunks[i+1]
        if curr.page_num != nxt.page_num:
            # Check if there's overlapping text
            curr_end = curr.text[-200:].strip() if len(curr.text) > 200 else curr.text.strip()
            nxt_start = nxt.text[:200].strip() if len(nxt.text) > 200 else nxt.text.strip()

            # Simple overlap detection - check if any sentence from end of curr appears in start of nxt
            sentences_curr = [s.strip() for s in curr_end.split('.') if len(s.strip()) > 20]
            sentences_nxt = [s.strip() for s in nxt_start.split('.') if len(s.strip()) > 20]

            for sent in sentences_curr[-2:]:  # Check last 2 sentences
                if sent and any(sent in nxt_sent for nxt_sent in sentences_nxt[:3]):
                    overlap_found += 1
                    print(f"  ✅ Overlap found: Page {curr.page_num+1} → {nxt.page_num+1}")
                    print(f"     Sentence: '{sent[:80]}...'")
                    break

    print(f"\n  Total overlaps detected: {overlap_found}")

    print("\n2. Table caption preservation:")
    table_chunks = [i for i, c in enumerate(chunks) if '<table>' in c.text or 'table_' in c.text.lower()]
    print(f"  Chunks with tables: {len(table_chunks)}")

    # Check for table references
    import re
    table_ref_pattern = re.compile(r'Table\s+\d+[:\.]', re.IGNORECASE)
    for idx in table_chunks:
        chunk = chunks[idx]
        refs = table_ref_pattern.findall(chunk.text)
        if refs:
            print(f"  ✅ Chunk {idx+1} has table reference(s): {refs[:2]}")

    print("\n3. PageHeader boundary respect:")
    page_transitions = []
    for i in range(len(chunks)-1):
        curr = chunks[i]
        nxt = chunks[i+1]
        if curr.page_num != nxt.page_num:
            same_header = curr.page_header == nxt.page_header if curr.page_header and nxt.page_header else False
            page_transitions.append({
                'from': curr.page_num + 1,
                'to': nxt.page_num + 1,
                'same_header': same_header,
                'prev_header': curr.page_header,
                'next_header': nxt.page_header
            })

    print(f"  Total page transitions: {len(page_transitions)}")
    for t in page_transitions[:5]:  # Show first 5
        print(f"  Page {t['from']} → {t['to']}: Same header={t['same_header']}")

    print("\n4. Orphan chunks analysis:")
    orphans = [i+1 for i, c in enumerate(chunks) if c.token_count < 200]
    print(f"  Total orphans (<200 tokens): {len(orphans)}")
    for oid in orphans:
        chunk = chunks[oid-1]
        prev_chunk = chunks[oid-2] if oid > 1 else None
        next_chunk = chunks[oid] if oid < len(chunks) else None

        print(f"\n  Orphan Chunk {oid}: {chunk.token_count} tokens (Page {chunk.page_num+1})")
        if prev_chunk:
            print(f"    Previous chunk: {prev_chunk.token_count} tokens")
            print(f"    Could merge? {prev_chunk.token_count + chunk.token_count} tokens total")
            would_exceed = (prev_chunk.token_count + chunk.token_count) > 700
            print(f"    Exceeds 700? {would_exceed}")

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total chunks: {len(chunks)}")
    print(f"Avg tokens/chunk: {sum(c.token_count for c in chunks) / len(chunks):.0f}")
    print(f"Chunks >700 tokens: {len(token_ranges['Atomic tables (>700)'])}")
    print(f"Chunks 500-700 tokens: {len(token_ranges['500-700 (target)'])}")
    print(f"Chunks <200 tokens: {len(token_ranges['<200 (orphans)'])}")
    print(f"Cross-page overlaps: {overlap_found}")
    print()

if __name__ == "__main__":
    asyncio.run(analyze())
