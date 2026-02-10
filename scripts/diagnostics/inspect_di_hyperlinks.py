"""Diagnostic script to inspect Document Intelligence API response for hyperlinks."""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential

from ingestor.config import load_config


async def inspect_di_response():
    """Inspect DI response for hyperlink information."""
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

    # Create DI client
    credential = AzureKeyCredential(di_config.key) if di_config.key else None
    client = DocumentIntelligenceClient(
        endpoint=di_config.endpoint,
        credential=credential
    )

    try:
        print("Calling Document Intelligence API...")
        poller = await client.begin_analyze_document(
            model_id="prebuilt-layout",
            body=AnalyzeDocumentRequest(bytes_source=pdf_bytes),
            output=["figures"],
            features=["ocrHighResolution"],
            output_content_format="markdown"
        )

        result = await poller.result()

        print(f"\n{'='*60}")
        print("DOCUMENT INTELLIGENCE RESPONSE ANALYSIS")
        print(f"{'='*60}\n")

        print(f"Total pages: {len(result.pages)}")
        print(f"Total paragraphs: {len(result.paragraphs) if result.paragraphs else 0}")
        print(f"Total tables: {len(result.tables) if result.tables else 0}")
        print(f"Total figures: {len(result.figures) if result.figures else 0}")

        # Check for hyperlinks in content
        print(f"\n{'='*60}")
        print("SEARCHING FOR HYPERLINKS IN CONTENT")
        print(f"{'='*60}\n")

        content = result.content

        # Search for "here" links
        search_terms = ["can be found here", "available here", "here.", "here)", "https://", "http://"]
        for term in search_terms:
            if term in content:
                # Find context around the term
                idx = content.find(term)
                start = max(0, idx - 100)
                end = min(len(content), idx + len(term) + 100)
                context = content[start:end]
                print(f"Found '{term}' at position {idx}:")
                print(f"Context: ...{context}...")
                print()

        # Check paragraphs for hyperlink information
        if result.paragraphs:
            print(f"\n{'='*60}")
            print("INSPECTING PARAGRAPHS")
            print(f"{'='*60}\n")

            for i, para in enumerate(result.paragraphs[:20]):  # First 20 paragraphs
                para_dict = para.as_dict()
                if any(term in para.content.lower() for term in ["here", "http", "www", "available"]):
                    print(f"Paragraph {i}:")
                    print(f"  Content: {para.content[:200]}...")
                    print(f"  Spans: {para.spans}")
                    print(f"  Role: {para.role}")
                    print(f"  Keys in dict: {para_dict.keys()}")
                    print()

        # Check if content format has markdown links
        print(f"\n{'='*60}")
        print("CHECKING MARKDOWN LINK FORMAT")
        print(f"{'='*60}\n")

        # Look for markdown link patterns [text](url)
        import re
        markdown_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        if markdown_links:
            print(f"Found {len(markdown_links)} markdown links:")
            for text, url in markdown_links[:10]:
                print(f"  [{text}]({url})")
        else:
            print("No markdown links found in content")

        # Check page footer
        print(f"\n{'='*60}")
        print("CHECKING PAGE FOOTERS")
        print(f"{'='*60}\n")

        # Look for PageFooter or footer content
        if "PageFooter" in content:
            idx = content.find("PageFooter")
            start = max(0, idx - 50)
            end = min(len(content), idx + 500)
            footer_context = content[start:end]
            print(f"Found PageFooter at position {idx}:")
            print(footer_context)
        else:
            # Check last page for footer
            last_page_content = content[-2000:]  # Last 2000 chars
            if "https://" in last_page_content or "http://" in last_page_content:
                print("Found URLs in last page:")
                urls = re.findall(r'https?://[^\s<>"]+', last_page_content)
                for url in urls:
                    print(f"  {url}")

        # Save full response for inspection
        output_file = Path("C:/Work/ingest-o-bot/src/logs/di_hyperlink_inspection.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict for JSON serialization
        result_dict = result.as_dict()
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)

        print(f"\n{'='*60}")
        print(f"Full response saved to: {output_file}")
        print(f"{'='*60}\n")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(inspect_di_response())
