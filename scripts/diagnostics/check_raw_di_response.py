"""Call Document Intelligence directly and save RAW JSON response"""
import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

async def check_raw_di():
    load_dotenv()

    endpoint = os.getenv("AZURE_DOC_INT_ENDPOINT")
    key = os.getenv("AZURE_DOC_INT_KEY")

    if not endpoint or not key:
        print("X Missing AZURE_DOC_INT_ENDPOINT or KEY in .env")
        return

    pdf_path = Path("data/sample_tracemonkey_paper.pdf")

    print("="*80)
    print("RAW DOCUMENT INTELLIGENCE RESPONSE CHECK")
    print("="*80)
    print()
    print(f"PDF: {pdf_path.name}")
    print(f"Endpoint: {endpoint}")
    print()

    # Read PDF
    with pdf_path.open("rb") as f:
        pdf_bytes = f.read()

    print(f"PDF size: {len(pdf_bytes):,} bytes")
    print()

    # Call DI
    print("... Calling Document Intelligence...")

    credential = AzureKeyCredential(key)
    client = DocumentIntelligenceClient(endpoint=endpoint, credential=credential)

    try:
        poller = await client.begin_analyze_document(
            model_id="prebuilt-layout",
            body=AnalyzeDocumentRequest(bytes_source=pdf_bytes),
            output=["figures"],
            features=["ocrHighResolution"],
            output_content_format="markdown"
        )

        result = await poller.result()

        print("OK DI analysis complete")
        print()

        # Convert result to dict
        result_dict = result.as_dict()

        # Save full JSON response
        output_file = Path("di_raw_response.json")
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)

        print(f"Saved Saved full response to: {output_file}")
        print(f"   File size: {output_file.stat().st_size:,} bytes")
        print()

        # Analyze Page 3 specifically
        if result.pages and len(result.pages) >= 3:
            page_3 = result.pages[2]  # 0-indexed

            print("="*80)
            print("PAGE 3 ANALYSIS")
            print("="*80)
            print()

            # Check for paragraphs/lines
            if hasattr(result, 'paragraphs'):
                page_3_paras = [p for p in result.paragraphs if any(span.get('page_number') == 3 for span in (p.get('spans') or []))]
                print(f"Text: Paragraphs on Page 3: {len(page_3_paras)}")

                if page_3_paras:
                    print()
                    print("First 3 paragraphs:")
                    for i, para in enumerate(page_3_paras[:3], 1):
                        content = para.get('content', '')[:150]
                        print(f"   {i}. {content}...")
                    print()

            # Check for tables
            if hasattr(result, 'tables'):
                page_3_tables = [t for t in result.tables if t.bounding_regions and any(br.page_number == 3 for br in t.bounding_regions)]
                print(f"Tables: Tables on Page 3: {len(page_3_tables)}")

                for i, table in enumerate(page_3_tables, 1):
                    print(f"\n   Table {i}:")
                    print(f"      Row count: {table.row_count}")
                    print(f"      Column count: {table.column_count}")

                    # Check for caption
                    if hasattr(table, 'caption'):
                        print(f"      Caption: {table.caption}")
                    else:
                        print(f"      Caption: None")

                    # Check cells for figure references
                    if hasattr(table, 'cells'):
                        first_cell = table.cells[0] if table.cells else None
                        if first_cell and hasattr(first_cell, 'content'):
                            print(f"      First cell: {first_cell.content[:100]}")

            # Check for figures
            if hasattr(result, 'figures'):
                page_3_figures = [f for f in result.figures if any(br.page_number == 3 for br in (f.bounding_regions or []))]
                print(f"\nFigures:  Figures on Page 3: {len(page_3_figures)}")

                for i, fig in enumerate(page_3_figures, 1):
                    print(f"\n   Figure {i}:")
                    if hasattr(fig, 'caption'):
                        print(f"      Caption: {fig.caption}")
                    if hasattr(fig, 'elements'):
                        print(f"      Elements: {len(fig.elements or [])}")

            # Search for "Figure 3" and "Figure 4" in all content
            print()
            print("="*80)
            print("SEARCHING FOR 'Figure 3' and 'Figure 4' in DI response")
            print("="*80)

            result_json_str = json.dumps(result_dict, ensure_ascii=False)

            for term in ["Figure 3", "Figure 4", "LIR snippet", "x86 snippet"]:
                if term in result_json_str:
                    print(f"   OK FOUND: '{term}' in DI response")
                    # Find context
                    idx = result_json_str.find(term)
                    context = result_json_str[max(0,idx-100):idx+200]
                    print(f"      Context: ...{context}...")
                else:
                    print(f"   X NOT FOUND: '{term}' in DI response")

        print()
        print("="*80)
        print(f"OK COMPLETE - Check {output_file} for full details")
        print("="*80)

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(check_raw_di())
