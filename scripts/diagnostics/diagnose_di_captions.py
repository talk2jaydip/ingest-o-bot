"""Diagnose if figure/table captions are in DI response or being lost"""
import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ingestor.config import PipelineConfig
from ingestor.di_extractor import DocumentIntelligenceExtractor
from ingestor.table_renderer import TableRenderer
from dotenv import load_dotenv

async def diagnose():
    load_dotenv()
    config = PipelineConfig.from_env()
    table_renderer = TableRenderer()
    extractor = DocumentIntelligenceExtractor(config.document_intelligence, table_renderer=table_renderer)

    pdf_path = Path(__file__).parent / "data" / "sample_tracemonkey_paper.pdf"

    print("="*80)
    print("DI CAPTION DIAGNOSIS")
    print("="*80)
    print()

    with pdf_path.open("rb") as f:
        pdf_bytes = f.read()

    # Extract with DI
    pages = await extractor.extract_document(filename=pdf_path.name, pdf_bytes=pdf_bytes)

    # Focus on Page 3 (index 2) which has Figure 3 and Figure 4
    page_3 = pages[2]

    print(f"📄 Page 3 Analysis")
    print(f"   Page number: {page_3.page_num}")
    print(f"   Text length: {len(page_3.text)} chars")
    print(f"   Tables: {len(page_3.tables)}")
    print(f"   Images: {len(page_3.images)}")
    print()

    # Check if figure captions are in the text
    target_captions = [
        "Figure 3. LIR snippet",
        "Figure 4. x86 snippet",
        "Figure 3.",
        "Figure 4.",
    ]

    print("🔍 Searching for figure captions in Page 3 text:")
    print("-"*80)
    for caption in target_captions:
        if caption in page_3.text:
            print(f"   ✅ FOUND: '{caption}'")
        else:
            print(f"   ❌ NOT FOUND: '{caption}'")
    print()

    # Show first 500 chars of Page 3 text
    print("📝 First 500 chars of Page 3 text:")
    print("-"*80)
    print(page_3.text[:500])
    print("-"*80)
    print()

    # Check tables
    if page_3.tables:
        print(f"📊 Page 3 Tables ({len(page_3.tables)}):")
        print("-"*80)
        for i, table in enumerate(page_3.tables, 1):
            print(f"   Table {i}:")
            print(f"      ID: {table.id}")
            print(f"      Rows: {table.row_count}")
            print(f"      Cols: {table.column_count}")
            # Check if table object has caption attribute
            if hasattr(table, 'caption'):
                print(f"      Caption: {table.caption}")
            if hasattr(table, 'title'):
                print(f"      Title: {table.title}")
            print()

    # Check figures
    if page_3.images:
        print(f"🖼️  Page 3 Figures ({len(page_3.images)}):")
        print("-"*80)
        for i, fig in enumerate(page_3.images, 1):
            print(f"   Figure {i}:")
            print(f"      ID: {fig.id}")
            if hasattr(fig, 'caption'):
                print(f"      Caption: {fig.caption}")
            if hasattr(fig, 'title'):
                print(f"      Title: {fig.title}")
            print()

    # Show what our Page object structure contains
    print("🔧 Page object attributes:")
    print("-"*80)
    print(f"   Available attributes: {dir(page_3)}")
    print()

    # Check raw DI response structure (if available)
    print("="*80)
    print("CONCLUSION")
    print("="*80)
    print()

    # Check Page 2 (which has Figure 1 and shows the caption correctly)
    page_2 = pages[1]
    print(f"📄 Page 2 (for comparison - has Figure 1):")
    print(f"   Text length: {len(page_2.text)} chars")
    print(f"   Figures: {len(page_2.images)}")

    if "Figure 1." in page_2.text:
        print(f"   ✅ Page 2 has 'Figure 1.' in text")
        # Find where it appears
        idx = page_2.text.find("Figure 1.")
        print(f"   Context: ...{page_2.text[max(0,idx-50):idx+150]}...")
    else:
        print(f"   ❌ Page 2 missing 'Figure 1.' in text")

    if page_2.images:
        fig1 = page_2.images[0]
        print(f"   Figure 1 ID: {fig1.id}")
        if hasattr(fig1, 'title'):
            print(f"   Figure 1 title: {fig1.title}")
        if hasattr(fig1, 'caption'):
            print(f"   Figure 1 caption: {fig1.caption}")

    print()
    print("="*80)
    print("DIAGNOSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(diagnose())
