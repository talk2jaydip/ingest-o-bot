#!/usr/bin/env python3
"""
Extract and analyze test results from BGE-M3 test runs.

This script analyzes pipeline logs to extract:
- Chunk counts and sizes
- Processing times
- Dynamic adjustment warnings
- Truncation warnings
- Embedding dimensions
- ChromaDB storage info

Usage:
    python extract_test_results.py logs/run_20260211_HHMMSS/
    python extract_test_results.py logs/run_20260211_HHMMSS/ logs/run_20260211_HHMMSS2/
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TestResults:
    """Container for test results from a single run."""
    config_name: str
    log_path: Path

    # Document processing
    document_name: Optional[str] = None
    pages_processed: Optional[int] = None
    extraction_method: Optional[str] = None

    # Chunking
    total_chunks: Optional[int] = None
    chunk_sizes: List[int] = None
    max_chunk_size: Optional[int] = None
    min_chunk_size: Optional[int] = None
    avg_chunk_size: Optional[float] = None

    # Model behavior
    dynamic_adjustment: bool = False
    adjustment_details: Optional[str] = None
    truncation_warnings: int = 0
    model_max_tokens: Optional[int] = None

    # Embeddings
    embedding_dims: Optional[int] = None
    embeddings_generated: Optional[int] = None
    embedding_time: Optional[float] = None

    # Performance
    total_time: Optional[float] = None
    success_rate: Optional[float] = None

    # Storage
    chromadb_count: Optional[int] = None

    # Issues
    errors: List[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.chunk_sizes is None:
            self.chunk_sizes = []
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


def find_pipeline_log(log_dir: Path) -> Optional[Path]:
    """Find the pipeline.log file in the log directory."""
    if log_dir.is_file() and log_dir.suffix == '.log':
        return log_dir

    pipeline_log = log_dir / 'pipeline.log'
    if pipeline_log.exists():
        return pipeline_log

    # Search for any .log file
    log_files = list(log_dir.glob('*.log'))
    if log_files:
        return log_files[0]

    return None


def extract_results(log_path: Path, config_name: str = "Unknown") -> TestResults:
    """Extract test results from a pipeline log file."""
    results = TestResults(config_name=config_name, log_path=log_path)

    if not log_path.exists():
        results.errors.append(f"Log file not found: {log_path}")
        return results

    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract document name
    doc_match = re.search(r'Processing document: (.+?)(?:\n|\s|$)', content)
    if doc_match:
        results.document_name = doc_match.group(1).strip()

    # Extract extraction method
    if 'markitdown' in content.lower():
        results.extraction_method = "MarkItDown"
    elif 'azure.*di' in content.lower() or 'document.*intelligence' in content.lower():
        results.extraction_method = "Azure DI"

    # Extract pages processed
    pages_match = re.search(r'Pages processed: (\d+)', content)
    if pages_match:
        results.pages_processed = int(pages_match.group(1))

    # Extract chunk information
    chunks_match = re.search(r'Chunks created: (\d+)', content)
    if chunks_match:
        results.total_chunks = int(chunks_match.group(1))
        results.embeddings_generated = results.total_chunks

    # Extract chunk sizes (look for "chunk X has Y tokens" patterns)
    chunk_size_pattern = r'chunk.*?(\d+)\s+tokens'
    chunk_sizes = [int(m) for m in re.findall(chunk_size_pattern, content, re.IGNORECASE)]
    if chunk_sizes:
        results.chunk_sizes = chunk_sizes
        results.max_chunk_size = max(chunk_sizes)
        results.min_chunk_size = min(chunk_sizes)
        results.avg_chunk_size = sum(chunk_sizes) / len(chunk_sizes)

    # Extract embedding dimensions
    dims_match = re.search(r'(?:Dimensions|embedding.*?dimensions?):\s*(\d+)', content, re.IGNORECASE)
    if dims_match:
        results.embedding_dims = int(dims_match.group(1))
    else:
        # Try to find in embeddings generated message
        dims_match2 = re.search(r'(\d+)\s+embeddings\s+\((\d+)\s+dimensions?\)', content, re.IGNORECASE)
        if dims_match2:
            results.embeddings_generated = int(dims_match2.group(1))
            results.embedding_dims = int(dims_match2.group(2))

    # Check for dynamic adjustment
    if 'automatically reducing' in content.lower() or 'adjusting chunking limit' in content.lower():
        results.dynamic_adjustment = True
        adjustment_match = re.search(r'(Automatically reducing.*?)(?:\n|$)', content, re.IGNORECASE)
        if adjustment_match:
            results.adjustment_details = adjustment_match.group(1).strip()

    # Check for model max tokens
    max_tokens_match = re.search(r'max_seq_length[:\s]+(\d+)', content, re.IGNORECASE)
    if max_tokens_match:
        results.model_max_tokens = int(max_tokens_match.group(1))

    # Count truncation warnings
    truncation_count = len(re.findall(r'truncat', content, re.IGNORECASE))
    results.truncation_warnings = truncation_count

    # Extract processing time
    time_match = re.search(r'Processing time:\s*([\d.]+)\s*seconds?', content, re.IGNORECASE)
    if time_match:
        results.total_time = float(time_match.group(1))

    # Extract success rate
    success_match = re.search(r'Success rate:\s*([\d.]+)%', content, re.IGNORECASE)
    if success_match:
        results.success_rate = float(success_match.group(1))

    # Extract ChromaDB count
    chromadb_match = re.search(r'Chunks indexed:\s*(\d+)', content, re.IGNORECASE)
    if chromadb_match:
        results.chromadb_count = int(chromadb_match.group(1))

    # Extract errors
    error_pattern = r'ERROR.*?:(.*?)(?:\n|$)'
    errors = re.findall(error_pattern, content, re.IGNORECASE)
    results.errors = [e.strip() for e in errors if e.strip()]

    # Extract warnings (excluding dynamic adjustment warnings)
    warning_pattern = r'WARNING.*?:(.*?)(?:\n|$)'
    warnings = re.findall(warning_pattern, content, re.IGNORECASE)
    results.warnings = [w.strip() for w in warnings if w.strip() and 'blob storage' not in w.lower()]

    return results


def format_comparison_table(test_4a: TestResults, test_4b: TestResults) -> str:
    """Format results as a comparison table."""

    def fmt(value, suffix=""):
        if value is None:
            return "?"
        if isinstance(value, float):
            return f"{value:.2f}{suffix}"
        return f"{value}{suffix}"

    table = f"""
## Test 4: BGE-M3 Comparison Results

| Metric | Test 4a (Offline/MarkItDown) | Test 4b (Azure DI) | Notes |
|--------|------------------------------|--------------------| ------|
| **Document Processing** |
| Extraction Method | {test_4a.extraction_method or '?'} | {test_4b.extraction_method or '?'} | |
| Processing Time | {fmt(test_4a.total_time, ' sec')} | {fmt(test_4b.total_time, ' sec')} | |
| **Chunking Results** |
| Total Chunks | {fmt(test_4a.total_chunks)} | {fmt(test_4b.total_chunks)} | |
| Max Chunk Size | {fmt(test_4a.max_chunk_size, ' tokens')} | {fmt(test_4b.max_chunk_size, ' tokens')} | |
| Min Chunk Size | {fmt(test_4a.min_chunk_size, ' tokens')} | {fmt(test_4b.min_chunk_size, ' tokens')} | |
| Avg Chunk Size | {fmt(test_4a.avg_chunk_size, ' tokens')} | {fmt(test_4b.avg_chunk_size, ' tokens')} | |
| **Model Behavior** |
| Dynamic Adjustment | {'YES' if test_4a.dynamic_adjustment else 'NO'} | {'YES' if test_4b.dynamic_adjustment else 'NO'} | Expected: NO |
| Truncation Warnings | {test_4a.truncation_warnings} | {test_4b.truncation_warnings} | Expected: 0 |
| Model Max Tokens | {fmt(test_4a.model_max_tokens)} | {fmt(test_4b.model_max_tokens)} | |
| **Embeddings** |
| Embedding Dims | {fmt(test_4a.embedding_dims)} | {fmt(test_4b.embedding_dims)} | Expected: 1024 |
| Embeddings Generated | {fmt(test_4a.embeddings_generated)} | {fmt(test_4b.embeddings_generated)} | |
| **Storage** |
| Vector Store | ChromaDB | ChromaDB | |
| Chunks Indexed | {fmt(test_4a.chromadb_count)} | {fmt(test_4b.chromadb_count)} | |
| **Status** |
| Success Rate | {fmt(test_4a.success_rate, '%')} | {fmt(test_4b.success_rate, '%')} | |
| Errors | {len(test_4a.errors)} | {len(test_4b.errors)} | |
"""

    return table


def format_detailed_report(results: TestResults) -> str:
    """Format detailed results for a single test."""

    report = f"""
### {results.config_name}

**Configuration:**
- Log: {results.log_path}
- Document: {results.document_name or 'Unknown'}
- Pages: {results.pages_processed or '?'}
- Extraction: {results.extraction_method or 'Unknown'}

**Chunking:**
- Total Chunks: {results.total_chunks or '?'}
- Max Size: {results.max_chunk_size or '?'} tokens
- Min Size: {results.min_chunk_size or '?'} tokens
- Avg Size: {f"{results.avg_chunk_size:.2f}" if results.avg_chunk_size else '?'} tokens

**Model Behavior:**
- Dynamic Adjustment: {'YES - ' + results.adjustment_details if results.dynamic_adjustment else 'NO'}
- Truncation Warnings: {results.truncation_warnings}
- Model Max Tokens: {results.model_max_tokens or '?'}

**Embeddings:**
- Dimensions: {results.embedding_dims or '?'}
- Generated: {results.embeddings_generated or '?'}

**Performance:**
- Processing Time: {f"{results.total_time:.2f}" if results.total_time else '?'} seconds
- Success Rate: {f"{results.success_rate:.1f}%" if results.success_rate else '?'}

**Storage:**
- ChromaDB Indexed: {results.chromadb_count or '?'}
"""

    if results.errors:
        report += f"\n**Errors ({len(results.errors)}):**\n"
        for error in results.errors[:5]:  # Show first 5
            report += f"- {error}\n"

    if results.warnings:
        report += f"\n**Warnings ({len(results.warnings)}):**\n"
        for warning in results.warnings[:5]:  # Show first 5
            report += f"- {warning}\n"

    return report


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nSearching for recent log directories...")

        logs_dir = Path('logs')
        if logs_dir.exists():
            recent_logs = sorted(logs_dir.glob('run_*'), reverse=True)[:5]
            if recent_logs:
                print("\nRecent log directories found:")
                for i, log_dir in enumerate(recent_logs, 1):
                    print(f"  {i}. {log_dir}")
                print(f"\nUsage: python {sys.argv[0]} {recent_logs[0]}/")

        sys.exit(1)

    # Process all provided log paths
    results_list = []
    for i, log_path_str in enumerate(sys.argv[1:], 1):
        log_path = Path(log_path_str)
        config_name = f"Test 4{'a' if i == 1 else 'b'}"

        # Find the pipeline log
        pipeline_log = find_pipeline_log(log_path)
        if pipeline_log is None:
            print(f"Error: No log file found in {log_path}")
            continue

        print(f"Analyzing {config_name}: {pipeline_log}")
        results = extract_results(pipeline_log, config_name)
        results_list.append(results)

    if not results_list:
        print("No results to analyze.")
        sys.exit(1)

    # Generate reports
    print("\n" + "="*80)
    print("DETAILED RESULTS")
    print("="*80)

    for results in results_list:
        print(format_detailed_report(results))

    # Generate comparison table if we have 2 results
    if len(results_list) >= 2:
        print("\n" + "="*80)
        print("COMPARISON TABLE")
        print("="*80)
        print(format_comparison_table(results_list[0], results_list[1]))

    # Verification checklist
    print("\n" + "="*80)
    print("VERIFICATION CHECKLIST")
    print("="*80)

    for results in results_list:
        print(f"\n{results.config_name}:")

        # Check chunks <= 8192
        if results.max_chunk_size:
            status = "✓" if results.max_chunk_size <= 8192 else "✗"
            print(f"  {status} Max chunk size ({results.max_chunk_size}) <= 8192 tokens")

        # Check no dynamic adjustment
        status = "✓" if not results.dynamic_adjustment else "⚠"
        print(f"  {status} No dynamic adjustment (expected for BGE-M3)")

        # Check no truncation
        status = "✓" if results.truncation_warnings == 0 else "✗"
        print(f"  {status} No truncation warnings ({results.truncation_warnings} found)")

        # Check embedding dims
        if results.embedding_dims:
            status = "✓" if results.embedding_dims == 1024 else "✗"
            print(f"  {status} Embedding dims = 1024 (actual: {results.embedding_dims})")

        # Check chunk count matches embeddings
        if results.total_chunks and results.embeddings_generated:
            status = "✓" if results.total_chunks == results.embeddings_generated else "✗"
            print(f"  {status} Chunks ({results.total_chunks}) = Embeddings ({results.embeddings_generated})")

        # Check no errors
        status = "✓" if len(results.errors) == 0 else "✗"
        print(f"  {status} No errors ({len(results.errors)} found)")


if __name__ == '__main__':
    main()
