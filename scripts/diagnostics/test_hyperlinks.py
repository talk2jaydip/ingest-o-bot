"""Test hyperlink extraction with the updated di_extractor."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ingestor.config import load_config
from ingestor.di_extractor import DocumentIntelligenceExtractor


async def test_hyperlink_extraction():
    """Test hyperlink extraction on medical_who_report.pdf."""
    # Load config
    config = load_config()
    di_config = config.document_intelligence

    # Load PDF
    pdf_path = Path("C:/Work/ingest-o-bot/data/medical_who_report.pdf")
    if not pdf_path.exists():
        print(f"Error: PDF not found at {pdf_path}")
        return

    print(f"Loading PDF: {pdf_path}")
    pdf_bytes = pdf_path.read_bytes()

    # Create DI extractor
    extractor = DocumentIntelligenceExtractor(di_config)

    try:
        print("Extracting content with hyperlinks...")
        pages = await extractor.extract_document(pdf_bytes, pdf_path.name, process_figures=True)

        print(f"\n{'='*60}")
        print(f"EXTRACTION RESULTS")
        print(f"{'='*60}\n")
        print(f"Total pages: {len(pages)}")

        # Check for hyperlinks
        total_hyperlinks = sum(len(page.hyperlinks) for page in pages)
        print(f"Total hyperlinks extracted: {total_hyperlinks}")

        if total_hyperlinks > 0:
            print(f"\n{'='*60}")
            print("HYPERLINKS FOUND")
            print(f"{'='*60}\n")

            for page in pages:
                if page.hyperlinks:
                    print(f"\nPage {page.page_num + 1}:")
                    for link in page.hyperlinks:
                        print(f"  - Text: '{link.link_text}'")
                        print(f"    URL: {link.url}")
                        print(f"    BBox: {link.bbox}")
                        print()

        # Check first page for "here" text
        print(f"\n{'='*60}")
        print("CHECKING PAGE 1 TEXT FOR HYPERLINKS")
        print(f"{'='*60}\n")

        if pages:
            page1_text = pages[0].text
            # Look for "here" references
            import re
            here_matches = list(re.finditer(r'\bhere\b', page1_text, re.IGNORECASE))
            print(f"Found {len(here_matches)} instances of 'here' on page 1")

            for match in here_matches[:5]:  # Show first 5
                start = max(0, match.start() - 50)
                end = min(len(page1_text), match.end() + 100)
                context = page1_text[start:end]
                print(f"\nContext: ...{context}...")

        # Check last page for PageFooter URLs
        print(f"\n{'='*60}")
        print("CHECKING LAST PAGE FOR PAGEFOOTER URLS")
        print(f"{'='*60}\n")

        if pages:
            last_page_text = pages[-1].text
            if "PageFooter" in last_page_text or "https://" in last_page_text:
                # Show last 1000 characters
                print(last_page_text[-1000:])

        # Save output
        output_file = Path("C:/Work/ingest-o-bot/src/logs/hyperlink_test_results.txt")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("HYPERLINK EXTRACTION TEST RESULTS\n")
            f.write("="*60 + "\n\n")
            f.write(f"Total pages: {len(pages)}\n")
            f.write(f"Total hyperlinks: {total_hyperlinks}\n\n")

            for page in pages:
                f.write(f"\n{'='*60}\n")
                f.write(f"Page {page.page_num + 1}\n")
                f.write(f"{'='*60}\n\n")

                if page.hyperlinks:
                    f.write(f"Hyperlinks ({len(page.hyperlinks)}):\n")
                    for link in page.hyperlinks:
                        f.write(f"  - Text: '{link.link_text}'\n")
                        f.write(f"    URL: {link.url}\n")
                        f.write(f"    BBox: {link.bbox}\n\n")

                f.write("\nPage Text:\n")
                f.write("-"*60 + "\n")
                f.write(page.text)
                f.write("\n\n")

        print(f"\n{'='*60}")
        print(f"Full results saved to: {output_file}")
        print(f"{'='*60}\n")

    finally:
        await extractor.close()


if __name__ == "__main__":
    asyncio.run(test_hyperlink_extraction())
