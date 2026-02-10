"""Test chunking fixes on Tables.pdf"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ingestor.config import PipelineConfig
from ingestor.chunker import create_chunker
from ingestor.di_extractor import DocumentIntelligenceExtractor
from ingestor.table_renderer import TableRenderer
from dotenv import load_dotenv

async def test_chunking():
    """Test chunking with all fixes applied"""

    # Load config
    load_dotenv()
    config = PipelineConfig.from_env()

    # Create table renderer
    table_renderer = TableRenderer()

    # Create extractor with table renderer
    extractor = DocumentIntelligenceExtractor(config.document_intelligence, table_renderer=table_renderer)

    # Extract Tables.pdf
    pdf_path = Path(__file__).parent / "data" / "Tables.pdf"
    print(f"📄 Loading {pdf_path.name}...")

    with pdf_path.open("rb") as f:
        pdf_bytes = f.read()

    print("🔍 Extracting with Document Intelligence...")
    pages = await extractor.extract_document(
        filename=pdf_path.name,
        pdf_bytes=pdf_bytes
    )

    print(f"✅ Extracted {len(pages)} pages")

    # Create chunker with new parameters
    chunker = create_chunker(
        max_chars=config.chunking.max_chars,
        max_tokens=config.chunking.max_tokens,
        max_section_tokens=750,  # New parameter!
        overlap_percent=config.chunking.overlap_percent,
        cross_page_overlap=True  # Now enabled by default
    )

    # Chunk document
    print("\n✂️  Chunking document...")
    chunks = chunker.chunk_pages(pages)

    print(f"\n📊 Results:")
    print(f"   Total chunks: {len(chunks)}")
    print(f"   Expected: ~16 (was 17 before fixes)")
    print()

    # Analyze chunks
    print("📈 Chunk Analysis:")
    print(f"{'Chunk':<10} {'Page':<6} {'Tokens':<8} {'Size':<10} {'Has Table?':<12} {'Has Caption?':<15}")
    print("=" * 85)

    for i, chunk in enumerate(chunks):
        has_table = '<table>' in chunk.text or '<figure id="table_' in chunk.text
        # Check for table references like "(Table 4-1 Episode Priority...)"
        has_caption = 'Table ' in chunk.text and 'page' in chunk.text

        print(f"{i+1:<10} {chunk.page_num+1:<6} {chunk.token_count:<8} "
              f"{len(chunk.text):<10} {str(has_table):<12} {str(has_caption):<15}")

    print()

    # Check specific issues
    print("🔍 Checking Fixes:")
    print()

    # Fix 1 & 2: Token limits (500-700)
    over_700 = [c for c in chunks if c.token_count and c.token_count > 700]
    under_450 = [c for c in chunks if c.token_count and c.token_count < 450 and c.token_count > 200]
    print(f"✅ Fix 1 & 2 (Token Limits 500-700):")
    print(f"   Chunks > 700 tokens: {len(over_700)} (should be 0)")
    if over_700:
        for c in over_700:
            print(f"      ❌ Chunk {chunks.index(c)+1}: {c.token_count} tokens")
    print(f"   Chunks 450-700 tokens: {len([c for c in chunks if c.token_count and 450 <= c.token_count <= 700])}")
    print()

    # Fix 3: Orphan merging
    orphans = [c for c in chunks if c.token_count and c.token_count < 200]
    print(f"✅ Fix 3 (Orphan Merging):")
    print(f"   Chunks < 200 tokens: {len(orphans)} (should be 0)")
    if orphans:
        for c in orphans:
            print(f"      ❌ Chunk {chunks.index(c)+1}: {c.token_count} tokens")
    print()

    # Fix 4: Table caption preservation
    # Look for chunk with "(Table 4-1 Episode Priority" reference
    print(f"✅ Fix 4 (Table Caption Preservation):")
    for i, chunk in enumerate(chunks):
        if "Table 4-1" in chunk.text and "Episode Priority" in chunk.text:
            # Check if this chunk also contains table_12
            has_table_12 = 'id="table_12"' in chunk.text or 'table_12' in chunk.text
            print(f"   Found 'Table 4-1 Episode Priority' in Chunk {i+1}")
            print(f"   Same chunk has table_12? {has_table_12}")
            if not has_table_12:
                # Check if table_12 is in next chunk
                if i+1 < len(chunks):
                    next_has_table = 'id="table_12"' in chunks[i+1].text
                    print(f"   ❌ Table 4-1 reference in Chunk {i+1}, but table in Chunk {i+2}: {next_has_table}")
            else:
                print(f"   ✅ Caption and table together!")
            break
    print()

    # Fix 5: Cross-page overlap (check if enabled)
    print(f"✅ Fix 5 (Cross-Page Overlap):")
    print(f"   Cross-page overlap enabled: {chunker.cross_page_overlap}")
    print()

    print("🎉 Testing complete!")

if __name__ == "__main__":
    asyncio.run(test_chunking())
