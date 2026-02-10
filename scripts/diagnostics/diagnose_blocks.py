"""Diagnose block creation to find where text is lost"""
import asyncio
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ingestor.config import PipelineConfig
from ingestor.di_extractor import DocumentIntelligenceExtractor
from ingestor.table_renderer import TableRenderer
from ingestor.chunker import extract_page_header
from dotenv import load_dotenv

async def diagnose():
    """Check block creation for Page 2"""

    load_dotenv()
    config = PipelineConfig.from_env()
    table_renderer = TableRenderer()
    extractor = DocumentIntelligenceExtractor(config.document_intelligence, table_renderer=table_renderer)

    pdf_path = Path(__file__).parent / "data" / "research_attention_paper.pdf"
    print("="*80)
    print(f"🔬 DIAGNOSING BLOCK CREATION")
    print("="*80)
    print()

    with pdf_path.open("rb") as f:
        pdf_bytes = f.read()

    # Extract with DI
    print("📄 Extracting with Document Intelligence...")
    pages = await extractor.extract_document(filename=pdf_path.name, pdf_bytes=pdf_bytes)
    print(f"✅ Extracted {len(pages)} pages")
    print()

    # Focus on Page 2 (index 1)
    page = pages[1]
    print("="*80)
    print(f"PAGE 2 RAW TEXT FROM DI (page_num={page.page_num})")
    print("="*80)
    print()

    print(f"Length: {len(page.text)} characters")
    print()
    print("Full text:")
    print("-"*80)
    print(page.text)
    print("-"*80)
    print()

    # Now process like the chunker does
    print("="*80)
    print("PROCESSING PAGE TEXT (like chunker)")
    print("="*80)
    print()

    # Step 1: Replace figure placeholders (from _prepare_page_text)
    text = page.text
    for image in page.images:
        if image.description:
            caption_parts = [image.figure_id]
            if image.title:
                caption_parts.append(image.title)
            caption = " ".join(caption_parts)
            figure_markup = f"<figure id=\"{image.figure_id}\">\nFigure: {caption}\nDescription: {image.description}\n</figure>"
            text = text.replace(image.placeholder, figure_markup)
            print(f"Replaced placeholder: {image.placeholder} -> <figure id=\"{image.figure_id}\">...")

    print()
    print(f"Text after figure replacement: {len(text)} characters")
    print()

    # Step 2: Extract page header
    text, page_header = extract_page_header(text)
    print(f"Page header: '{page_header}'")
    print(f"Text after header extraction: {len(text)} characters")
    print()

    # Step 3: Split into blocks
    figure_regex = re.compile(r'<figure.*?</figure>', re.IGNORECASE | re.DOTALL)
    blocks = []
    last = 0
    for m in figure_regex.finditer(text):
        if m.start() > last:
            blocks.append(("text", text[last:m.start()]))
        blocks.append(("figure", m.group()))
        last = m.end()
    if last < len(text):
        blocks.append(("text", text[last:]))

    print(f"Created {len(blocks)} blocks")
    print()

    # Show all blocks
    print("="*80)
    print("BLOCKS CREATED:")
    print("="*80)
    print()

    total_block_chars = 0
    for i, (btype, btext) in enumerate(blocks):
        print(f"Block {i+1}: type={btype}, length={len(btext)} chars")
        total_block_chars += len(btext)
        print("Content preview (first 200 chars):")
        print(btext[:200])
        print()
        if len(btext) > 200:
            print("... middle ...")
            print()
            print("Last 200 chars:")
            print(btext[-200:])
            print()
        print("-"*80)
        print()

    print(f"Total characters in blocks: {total_block_chars}")
    print(f"Original text length: {len(text)}")
    print(f"Difference: {len(text) - total_block_chars} chars")
    print()

    if len(text) > total_block_chars:
        print("❌ TEXT LOST DURING BLOCK SPLITTING!")
    else:
        print("✅ No text lost during block splitting")

if __name__ == "__main__":
    asyncio.run(diagnose())
