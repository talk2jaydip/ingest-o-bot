"""Debug chunking issues"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import from prepdocslib_minimal
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PipelineConfig
from chunker import create_chunker
from di_extractor import DocumentIntelligenceExtractor

async def debug_chunking():
    """Debug chunking for sample_pages_test.pdf"""
    
    # Load config (relative to parent directory)
    env_path = Path(__file__).parent.parent / "envs" / ".env"
    config = PipelineConfig.from_env_file(str(env_path))
    
    # Create extractor
    extractor = DocumentIntelligenceExtractor(config.document_intelligence)
    
    # Extract document (relative to parent directory)
    pdf_path = Path(__file__).parent.parent / "test_file" / "sample_pages_test.pdf"
    with pdf_path.open("rb") as f:
        pdf_bytes = f.read()
    
    print("Extracting document...")
    pages = await extractor.extract_document(
        filename=pdf_path.name,
        pdf_bytes=pdf_bytes,
        source_url=str(pdf_path)
    )
    
    print(f"Extracted {len(pages)} pages")
    
    # Create chunker
    chunker = create_chunker(
        max_chars=config.chunking.max_chars,
        max_tokens=config.chunking.max_tokens,
        overlap_percent=config.chunking.overlap_percent
    )
    
    # Chunk document
    print("\nChunking document...")
    chunks = chunker.chunk_pages(pages)
    
    print(f"\nTotal chunks: {len(chunks)}")
    
    # Analyze first page chunks
    page1_chunks = [c for c in chunks if c.page_num == 0]
    
    print(f"\n{'='*60}")
    print(f"Page 1 - {len(page1_chunks)} chunk(s)")
    print(f"{'='*60}\n")
    
    for i, chunk in enumerate(page1_chunks):
        print(f"\n--- Chunk {i + 1} ---")
        print(f"Index on Page: {chunk.chunk_index_on_page}")
        print(f"Page: {chunk.page_num + 1}")
        print(f"Token Count: {chunk.token_count}")
        print(f"Content Length: {len(chunk.text)} characters")
        
        # Show first 200 and last 200 characters
        text = chunk.text
        if len(text) > 400:
            print(f"\nStart:\n{'-'*60}")
            print(text[:200])
            print(f"{'-'*60}")
            print(f"\nEnd:\n{'-'*60}")
            print(text[-200:])
            print(f"{'-'*60}")
        else:
            print(f"\nContent:\n{'-'*60}")
            print(text)
            print(f"{'-'*60}")
    
    # Check for duplication between chunks
    print(f"\n{'='*60}")
    print("Checking for duplications...")
    print(f"{'='*60}\n")
    
    for i in range(len(page1_chunks) - 1):
        chunk1 = page1_chunks[i]
        chunk2 = page1_chunks[i + 1]
        
        # Check last 100 chars of chunk1 vs first 100 chars of chunk2
        chunk1_end = chunk1.text[-100:]
        chunk2_start = chunk2.text[:100]
        
        # Find common substring
        common_len = 0
        for j in range(1, min(len(chunk1_end), len(chunk2_start)) + 1):
            if chunk1.text[-j:] == chunk2.text[:j]:
                common_len = j
        
        if common_len > 10:
            print(f"Chunk {i + 1} to Chunk {i + 2}: {common_len} characters overlap")
            print(f"Overlapping text: '{chunk1.text[-common_len:]}'")
            print()

if __name__ == "__main__":
    asyncio.run(debug_chunking())
