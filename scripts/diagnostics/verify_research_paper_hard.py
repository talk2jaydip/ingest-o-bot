"""HARD WAY verification of research paper chunking - all edge cases"""
import asyncio
import sys
import re
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ingestor.config import PipelineConfig
from ingestor.chunker import create_chunker
from ingestor.di_extractor import DocumentIntelligenceExtractor
from ingestor.table_renderer import TableRenderer
from dotenv import load_dotenv

def check_has_equation(text):
    """Check if text likely contains equations"""
    equation_indicators = [
        r'\$',  # LaTeX
        r'\\[a-z]+\{',  # LaTeX commands
        r'[=≈≠<>≤≥±].*[xyz]',  # Math symbols with variables
        r'[∑∏∫∂∇]',  # Math operators
        r'\^[0-9]',  # Superscripts
        r'_[0-9]',  # Subscripts
    ]
    return any(re.search(pattern, text) for pattern in equation_indicators)

def check_has_code(text):
    """Check if text contains code blocks"""
    code_indicators = [
        'def ', 'class ', 'import ', 'return ',
        'function ', 'var ', 'const ', 'let ',
        '```', 'for(', 'while(',
    ]
    return any(indicator in text for indicator in code_indicators)

async def verify_hard():
    """Comprehensive hard verification of research paper chunking"""

    load_dotenv()
    config = PipelineConfig.from_env()
    table_renderer = TableRenderer()
    extractor = DocumentIntelligenceExtractor(config.document_intelligence, table_renderer=table_renderer)

    pdf_path = Path(__file__).parent / "data" / "research_attention_paper.pdf"
    print("="*80)
    print(f"🔬 HARD VERIFICATION: {pdf_path.name}")
    print("="*80)
    print()

    with pdf_path.open("rb") as f:
        pdf_bytes = f.read()

    print("🔍 Step 1: Extract with Document Intelligence...")
    pages = await extractor.extract_document(filename=pdf_path.name, pdf_bytes=pdf_bytes)
    print(f"✅ Extracted {len(pages)} pages")
    print()

    # Detailed page analysis
    print("📄 DOCUMENT STRUCTURE ANALYSIS")
    print("-" * 80)
    total_tables = 0
    total_images = 0
    for page in pages:
        total_tables += len(page.tables)
        total_images += len(page.images)
        has_figure = '<figure' in page.text

        if len(page.tables) > 0 or len(page.images) > 0 or has_figure:
            print(f"Page {page.page_num+1:2d}: "
                  f"Tables={len(page.tables)}, "
                  f"Images={len(page.images)}, "
                  f"Figures={has_figure}, "
                  f"Text={len(page.text):,} chars")

    print()
    print(f"Total Tables: {total_tables}")
    print(f"Total Images: {total_images}")
    print()

    # Create chunker with all fixes
    chunker = create_chunker(
        max_chars=config.chunking.max_chars,
        max_tokens=config.chunking.max_tokens,
        max_section_tokens=750,
        overlap_percent=config.chunking.overlap_percent,
        cross_page_overlap=True
    )

    print("✂️  Step 2: Chunk document...")
    chunks = chunker.chunk_pages(pages)
    print(f"✅ Generated {len(chunks)} chunks")
    print()

    print("="*80)
    print("COMPREHENSIVE VERIFICATION")
    print("="*80)
    print()

    # 1. TOKEN DISTRIBUTION ANALYSIS
    print("1️⃣  TOKEN DISTRIBUTION")
    print("-" * 80)

    token_buckets = {
        '>1000 (very large)': [],
        '700-1000 (large table)': [],
        '500-700 (target)': [],
        '300-500 (acceptable)': [],
        '200-300 (borderline)': [],
        '<200 (orphan)': []
    }

    for i, chunk in enumerate(chunks):
        tokens = chunk.token_count
        if tokens > 1000:
            token_buckets['>1000 (very large)'].append((i+1, tokens))
        elif tokens > 700:
            token_buckets['700-1000 (large table)'].append((i+1, tokens))
        elif tokens >= 500:
            token_buckets['500-700 (target)'].append((i+1, tokens))
        elif tokens >= 300:
            token_buckets['300-500 (acceptable)'].append((i+1, tokens))
        elif tokens >= 200:
            token_buckets['200-300 (borderline)'].append((i+1, tokens))
        else:
            token_buckets['<200 (orphan)'].append((i+1, tokens))

    for bucket, chunk_list in token_buckets.items():
        if chunk_list:
            print(f"{bucket:25s}: {len(chunk_list):2d} chunks", end='')
            if len(chunk_list) <= 3:
                print(f" → {[f'#{c[0]}:{c[1]}tok' for c in chunk_list]}")
            else:
                print(f" → {[f'#{c[0]}:{c[1]}tok' for c in chunk_list[:3]]}...")
        else:
            print(f"{bucket:25s}:  0 chunks")

    avg_tokens = sum(c.token_count for c in chunks) / len(chunks)
    print(f"\nAverage: {avg_tokens:.0f} tokens/chunk")
    print()

    # 2. CONTENT TYPE ANALYSIS
    print("2️⃣  CONTENT TYPE ANALYSIS")
    print("-" * 80)

    chunks_with_tables = 0
    chunks_with_figures = 0
    chunks_with_equations = 0
    chunks_with_code = 0

    for chunk in chunks:
        if '<table>' in chunk.text or 'table_' in chunk.text.lower():
            chunks_with_tables += 1
        if '<figure' in chunk.text.lower():
            chunks_with_figures += 1
        if check_has_equation(chunk.text):
            chunks_with_equations += 1
        if check_has_code(chunk.text):
            chunks_with_code += 1

    print(f"Chunks with tables:    {chunks_with_tables:2d} / {len(chunks)} ({100*chunks_with_tables/len(chunks):.0f}%)")
    print(f"Chunks with figures:   {chunks_with_figures:2d} / {len(chunks)} ({100*chunks_with_figures/len(chunks):.0f}%)")
    print(f"Chunks with equations: {chunks_with_equations:2d} / {len(chunks)} ({100*chunks_with_equations/len(chunks):.0f}%)")
    print(f"Chunks with code:      {chunks_with_code:2d} / {len(chunks)} ({100*chunks_with_code/len(chunks):.0f}%)")
    print()

    # 3. CROSS-PAGE TRANSITIONS
    print("3️⃣  CROSS-PAGE TRANSITIONS")
    print("-" * 80)

    transitions = []
    overlaps_detected = 0

    for i in range(len(chunks)-1):
        curr = chunks[i]
        nxt = chunks[i+1]

        if curr.page_num != nxt.page_num:
            same_header = (curr.page_header == nxt.page_header) if (curr.page_header and nxt.page_header) else False

            # Check for actual overlap
            curr_tail = ' '.join(curr.text.split()[-50:])  # Last 50 words
            nxt_head = ' '.join(nxt.text.split()[:50])  # First 50 words

            overlap_words = []
            for word in curr_tail.split():
                if len(word) > 5 and word in nxt_head:
                    overlap_words.append(word)

            has_overlap = len(overlap_words) > 3
            if has_overlap:
                overlaps_detected += 1

            transitions.append({
                'from': curr.page_num + 1,
                'to': nxt.page_num + 1,
                'same_header': same_header,
                'has_overlap': has_overlap,
                'overlap_words': len(overlap_words)
            })

    print(f"Total page transitions: {len(transitions)}")
    print(f"Overlaps detected:      {overlaps_detected}")
    print()

    # Show transitions with details
    print("Transition details:")
    for t in transitions[:8]:  # Show first 8
        status = "✅" if t['has_overlap'] else "  "
        print(f"  {status} Page {t['from']:2d} → {t['to']:2d}: "
              f"Same header={t['same_header']:<5} "
              f"Overlap words={t['overlap_words']}")

    if len(transitions) > 8:
        print(f"  ... and {len(transitions)-8} more transitions")
    print()

    # 4. ORPHAN ANALYSIS
    print("4️⃣  ORPHAN CHUNKS ANALYSIS")
    print("-" * 80)

    orphans = [(i+1, chunks[i]) for i in range(len(chunks)) if chunks[i].token_count < 200]

    if orphans:
        print(f"Found {len(orphans)} orphan(s):")
        print()
        for oid, chunk in orphans:
            prev_chunk = chunks[oid-2] if oid > 1 else None
            next_chunk = chunks[oid] if oid < len(chunks) else None

            print(f"  Chunk {oid}: {chunk.token_count} tokens (Page {chunk.page_num+1})")

            if prev_chunk:
                combined = prev_chunk.token_count + chunk.token_count
                exceeds = combined > 700
                same_page = prev_chunk.page_num == chunk.page_num

                print(f"    Previous: {prev_chunk.token_count} tokens")
                print(f"    Combined: {combined} tokens (exceeds 700? {exceeds})")
                print(f"    Same page: {same_page}")

                # Check why not merged
                if not exceeds and same_page:
                    print(f"    ❌ ISSUE: Should have merged but didn't!")
                elif not same_page:
                    same_header = (prev_chunk.page_header == chunk.page_header) if (prev_chunk.page_header and chunk.page_header) else False
                    print(f"    Cross-page, same header: {same_header}")
            print()
    else:
        print("✅ No orphans found!")
        print()

    # 5. TABLE CAPTION VERIFICATION
    print("5️⃣  TABLE CAPTION VERIFICATION")
    print("-" * 80)

    table_ref_pattern = re.compile(r'Table\s+\d+', re.IGNORECASE)
    figure_ref_pattern = re.compile(r'Figure\s+\d+', re.IGNORECASE)

    chunks_with_table_refs = []
    chunks_with_figure_refs = []

    for i, chunk in enumerate(chunks):
        table_refs = table_ref_pattern.findall(chunk.text)
        figure_refs = figure_ref_pattern.findall(chunk.text)

        has_actual_table = '<table>' in chunk.text or 'table_' in chunk.text.lower()
        has_actual_figure = '<figure' in chunk.text.lower()

        if table_refs:
            chunks_with_table_refs.append((i+1, table_refs, has_actual_table))
        if figure_refs:
            chunks_with_figure_refs.append((i+1, figure_refs, has_actual_figure))

    print(f"Chunks with table references: {len(chunks_with_table_refs)}")
    for cid, refs, has_table in chunks_with_table_refs[:5]:
        status = "✅" if has_table else "⚠️"
        print(f"  {status} Chunk {cid}: {refs[0]} (has table: {has_table})")

    print()
    print(f"Chunks with figure references: {len(chunks_with_figure_refs)}")
    for cid, refs, has_figure in chunks_with_figure_refs[:5]:
        status = "✅" if has_figure else "⚠️"
        print(f"  {status} Chunk {cid}: {refs[0]} (has figure: {has_figure})")
    print()

    # 6. EQUATION HANDLING
    print("6️⃣  EQUATION HANDLING VERIFICATION")
    print("-" * 80)

    equation_chunks = [(i+1, chunks[i].token_count) for i in range(len(chunks)) if check_has_equation(chunks[i].text)]

    if equation_chunks:
        print(f"Chunks with equations: {len(equation_chunks)}")
        print(f"Token distribution:")
        eq_tokens = [t for _, t in equation_chunks]
        print(f"  Min: {min(eq_tokens)} tokens")
        print(f"  Max: {max(eq_tokens)} tokens")
        print(f"  Avg: {sum(eq_tokens)/len(eq_tokens):.0f} tokens")
        print()
    else:
        print("No equations detected (or all in figures)")
        print()

    # 7. PAGEHEADER BOUNDARY VERIFICATION
    print("7️⃣  PAGEHEADER BOUNDARY VERIFICATION")
    print("-" * 80)

    unique_headers = set()
    header_changes = 0

    for chunk in chunks:
        if chunk.page_header:
            unique_headers.add(chunk.page_header)

    for i in range(len(chunks)-1):
        curr = chunks[i]
        nxt = chunks[i+1]

        if curr.page_header and nxt.page_header:
            if curr.page_header != nxt.page_header:
                header_changes += 1

    print(f"Unique PageHeaders: {len(unique_headers)}")
    print(f"PageHeader changes: {header_changes}")

    if unique_headers:
        print(f"\nHeaders found:")
        for header in sorted(unique_headers)[:10]:
            print(f"  - {header}")
    print()

    # FINAL SUMMARY
    print("="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    print()

    issues = []

    # Check for issues
    if token_buckets['<200 (orphan)']:
        issues.append(f"❌ {len(token_buckets['<200 (orphan)'])} orphan chunk(s) < 200 tokens")
    else:
        print("✅ No orphans (<200 tokens)")

    if overlaps_detected > 0:
        print(f"✅ Cross-page overlap working ({overlaps_detected} overlaps detected)")
    else:
        print(f"⚠️  No cross-page overlaps detected (check if expected)")

    if chunks_with_tables > 0:
        print(f"✅ Tables preserved ({chunks_with_tables} chunks with tables)")

    if chunks_with_figures > 0:
        print(f"✅ Figures preserved ({chunks_with_figures} chunks with figures)")

    if header_changes > 0:
        print(f"✅ PageHeader boundaries detected ({header_changes} section changes)")

    print()
    print(f"Total chunks: {len(chunks)}")
    print(f"Average tokens: {avg_tokens:.0f}")
    print(f"Quality score: {100 - len(token_buckets['<200 (orphan)'])*5:.0f}%")

    if issues:
        print()
        print("Issues found:")
        for issue in issues:
            print(f"  {issue}")

    print()
    print("="*80)

if __name__ == "__main__":
    asyncio.run(verify_hard())
