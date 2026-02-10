"""Diagnose span processing - trace every span through the chunking pipeline"""
import asyncio
import sys
import re
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ingestor.config import PipelineConfig
from ingestor.di_extractor import DocumentIntelligenceExtractor
from ingestor.table_renderer import TableRenderer
from ingestor.chunker import extract_page_header, bpe
from dotenv import load_dotenv

# Replicate the _split_into_spans logic
def split_into_spans(text: str) -> list[str]:
    """Split text into sentence-like spans (replicate chunker logic)."""
    sentence_endings = {'.', '!', '?', '\n'}
    spans = []
    current_chars = []

    for ch in text:
        current_chars.append(ch)
        if ch in sentence_endings:
            spans.append("".join(current_chars))
            current_chars = []

    if current_chars:  # Remaining tail
        spans.append("".join(current_chars))

    return spans

async def diagnose():
    """Trace span processing for Page 2"""

    load_dotenv()
    config = PipelineConfig.from_env()
    table_renderer = TableRenderer()
    extractor = DocumentIntelligenceExtractor(config.document_intelligence, table_renderer=table_renderer)

    pdf_path = Path(__file__).parent / "data" / "research_attention_paper.pdf"
    print("="*80)
    print(f"🔬 DIAGNOSING SPAN PROCESSING FOR PAGE 2")
    print("="*80)
    print()

    with pdf_path.open("rb") as f:
        pdf_bytes = f.read()

    # Extract with DI
    pages = await extractor.extract_document(filename=pdf_path.name, pdf_bytes=pdf_bytes)

    # Focus on Page 2 (index 1)
    page = pages[1]

    # Process like the chunker does
    text = page.text
    for image in page.images:
        if image.description:
            caption_parts = [image.figure_id]
            if image.title:
                caption_parts.append(image.title)
            caption = " ".join(caption_parts)
            figure_markup = f"<figure id=\"{image.figure_id}\">\nFigure: {caption}\nDescription: {image.description}\n</figure>"
            text = text.replace(image.placeholder, figure_markup)

    text, page_header = extract_page_header(text)

    # Create blocks (same as chunker)
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

    print(f"Page 2: {len(blocks)} block(s), {len(text)} total chars")
    print()

    # Process text blocks
    for block_idx, (btype, btext) in enumerate(blocks):
        if btype != "text":
            continue

        print("="*80)
        print(f"TEXT BLOCK {block_idx + 1}")
        print("="*80)
        print()
        print(f"Block length: {len(btext)} characters")
        print()

        # Split into spans
        spans = split_into_spans(btext)
        print(f"Split into {len(spans)} spans")
        print()

        # Analyze each span
        span_analysis = []
        total_span_chars = 0

        for i, span in enumerate(spans):
            span_tokens = len(bpe.encode(span))
            span_chars = len(span)
            total_span_chars += span_chars

            # Get first/last words for identification
            words = span.split()
            first_words = " ".join(words[:5]) if len(words) >= 5 else span[:50]
            last_words = " ".join(words[-5:]) if len(words) >= 5 else span[-50:]

            span_analysis.append({
                'idx': i+1,
                'chars': span_chars,
                'tokens': span_tokens,
                'first': first_words,
                'last': last_words,
                'full_text': span
            })

        print(f"Total chars in spans: {total_span_chars}")
        print(f"Original block chars: {len(btext)}")
        print(f"Difference: {len(btext) - total_span_chars} chars")
        print()

        if len(btext) != total_span_chars:
            print("❌ TEXT LOST IN SPAN SPLITTING!")
        else:
            print("✅ All text preserved in spans")
        print()

        # Show span details
        print("SPAN DETAILS:")
        print("-"*80)
        for s in span_analysis:
            print(f"Span {s['idx']:3d}: {s['chars']:5d} chars, {s['tokens']:4d} tokens")
            print(f"  First: {s['first'][:70]}")
            if len(s['last']) > 0:
                print(f"  Last:  {s['last'][-70:]}")
            print()

        # Check for key missing phrases
        print("="*80)
        print("CHECKING FOR KEY PHRASES IN SPANS:")
        print("="*80)
        print()

        key_phrases = [
            ("remains", "The fundamental constraint of sequential computation, however, remains"),
            ("Attention mechanisms", "Attention mechanisms have become an integral part"),
            ("In this work", "In this work we propose the Transformer"),
            ("## 2 Background", "## 2 Background"),
            ("reducing sequential", "The goal of reducing sequential computation"),
            ("Self-attention", "Self-attention, sometimes called intra-attention"),
            ("## 3 Model", "## 3 Model Architecture")
        ]

        for short_name, phrase in key_phrases:
            found = False
            found_in_span = -1
            for s in span_analysis:
                if phrase in s['full_text']:
                    found = True
                    found_in_span = s['idx']
                    break

            status = "✅" if found else "❌"
            location = f"Span {found_in_span}" if found else "NOT FOUND"
            print(f"{status} {short_name:25s} -> {location}")

        print()

if __name__ == "__main__":
    asyncio.run(diagnose())
