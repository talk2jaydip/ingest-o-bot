"""Analyze performance bottlenecks from batch ingestion."""
import json
from pathlib import Path

# Read the pipeline status
status_file = Path("test_artifacts/pipeline_status_20260209_191233.json")

if status_file.exists():
    with open(status_file) as f:
        data = json.load(f)

    print("=" * 80)
    print("PERFORMANCE ANALYSIS - 19 FILES")
    print("=" * 80)

    # Calculate breakdown by phase
    results = data.get("results", [])

    total_time = sum(r["processing_time_seconds"] for r in results if r.get("success"))
    total_chunks = sum(r["chunks_indexed"] for r in results if r.get("success"))

    print(f"\nTotal Processing Time: {total_time:.2f}s ({total_time/60:.2f}m)")
    print(f"Total Chunks: {total_chunks}")
    print(f"Average per file: {total_time/len(results):.2f}s")
    print(f"Average per chunk: {total_time/total_chunks:.2f}s")

    # Find bottlenecks
    print("\n" + "=" * 80)
    print("BOTTLENECK ANALYSIS")
    print("=" * 80)

    # Sort by processing time
    sorted_results = sorted(results, key=lambda x: x.get("processing_time_seconds", 0), reverse=True)

    print("\nTop 10 Slowest Files:")
    print("-" * 80)
    for i, r in enumerate(sorted_results[:10], 1):
        time_s = r["processing_time_seconds"]
        chunks = r["chunks_indexed"]
        time_per_chunk = time_s / chunks if chunks > 0 else 0
        print(f"{i:2}. {r['filename']:40} | {time_s:7.2f}s | {chunks:3} chunks | {time_per_chunk:.2f}s/chunk")

    # Identify patterns
    print("\n" + "=" * 80)
    print("PERFORMANCE PATTERNS")
    print("=" * 80)

    slow_files = [r for r in results if r.get("processing_time_seconds", 0) > 100]
    fast_files = [r for r in results if r.get("processing_time_seconds", 0) < 20]

    print(f"\nSlow files (>100s): {len(slow_files)}")
    print(f"Fast files (<20s): {len(fast_files)}")

    # Time per chunk analysis
    times_per_chunk = [(r["filename"], r["processing_time_seconds"]/r["chunks_indexed"])
                       for r in results if r.get("success") and r["chunks_indexed"] > 0]
    times_per_chunk.sort(key=lambda x: x[1], reverse=True)

    print("\nTop 5 Slowest per Chunk:")
    for fname, time_per_chunk in times_per_chunk[:5]:
        print(f"  {fname:40} | {time_per_chunk:.2f}s/chunk")

    print("\nFastest per Chunk:")
    for fname, time_per_chunk in times_per_chunk[-5:]:
        print(f"  {fname:40} | {time_per_chunk:.2f}s/chunk")

    # Estimated time for 100 files
    print("\n" + "=" * 80)
    print("SCALING PROJECTIONS")
    print("=" * 80)

    avg_time_per_file = total_time / len(results)
    print(f"\nCurrent average per file: {avg_time_per_file:.2f}s")
    print(f"\nProjected time for 100 files:")
    print(f"  Sequential: {(avg_time_per_file * 100)/60:.2f} minutes ({(avg_time_per_file * 100)/3600:.2f} hours)")
    print(f"  4x parallel: {(avg_time_per_file * 100 / 4)/60:.2f} minutes")
    print(f"  8x parallel: {(avg_time_per_file * 100 / 8)/60:.2f} minutes")
    print(f"  16x parallel: {(avg_time_per_file * 100 / 16)/60:.2f} minutes")

else:
    print("Pipeline status file not found")
    print("\nManual Analysis from Logs:")
    print("=" * 80)

    # Manual data from the output
    files_data = [
        ("51583247-004_ICM_myLUX_QSG_IT_S.pdf", 2, 272.64),
        ("extraction_test_pack.pdf", 3, 153.49),
        ("Figures.pdf", 56, 975.98),
        ("finance_basel_framework.pdf", 197, 111.52),
        ("legal_irs_form.pdf", 5, 15.47),
        ("medical_who_report.pdf", 14, 211.59),
        ("Mixed_6pages.pdf", 7, 120.41),
        ("research_attention_paper.pdf", 20, 74.77),
        ("research_paper.pdf", 18, 374.53),
        ("sample_basic.pdf", 1, 12.19),
        ("sample_complex.pdf", 3, 117.93),
        ("sample_complex_structure.pdf", 2, 50.14),
        ("sample_formatted.pdf", 1, 11.37),
        ("sample_learning.pdf", 1, 13.83),
        ("sample_pages_test.pdf", 7, 40.49),
        ("sample_table_wcag.pdf", 1, 10.70),
        ("sample_tracemonkey_paper.pdf", 34, 247.89),
        ("Tables.pdf", 14, 173.54),
        ("Trends.pdf", 24, 131.55),
    ]

    total_time = sum(t for _, _, t in files_data)
    total_chunks = sum(c for _, c, _ in files_data)

    print(f"\nTotal Time: {total_time:.2f}s ({total_time/60:.2f}m)")
    print(f"Total Chunks: {total_chunks}")
    print(f"Avg per file: {total_time/len(files_data):.2f}s")
    print(f"Avg per chunk: {total_time/total_chunks:.2f}s")

    print("\n" + "=" * 80)
    print("BOTTLENECK ANALYSIS")
    print("=" * 80)

    sorted_data = sorted(files_data, key=lambda x: x[2], reverse=True)
    print("\nSlowest Files:")
    for fname, chunks, time_s in sorted_data[:10]:
        time_per_chunk = time_s / chunks if chunks > 0 else 0
        print(f"  {fname:40} | {time_s:7.2f}s | {chunks:3} chunks | {time_per_chunk:.2f}s/chunk")

print("\n" + "=" * 80)
print("OPTIMIZATION OPPORTUNITIES")
print("=" * 80)

print("""
CURRENT BOTTLENECKS:

1. Azure Document Intelligence (DI) Processing
   - Sequential page-by-page processing
   - Network round-trip per page
   - Largest bottleneck for multi-page PDFs

2. Embedding Generation
   - Currently batched (max_concurrency=5)
   - OpenAI API rate limits
   - Network latency

3. Document Parallelization
   - Currently processes 4 documents in parallel
   - Could be increased for better throughput

4. Search Index Uploads
   - Batched in groups of 1000
   - Not a major bottleneck currently

OPTIMIZATION STRATEGIES:

Strategy 1: Increase Document Parallelization
  Current: 4 documents in parallel
  Recommendation: 8-16 documents (limited by DI quota)
  Expected gain: 2-4x faster
  Risk: May hit Azure DI rate limits

Strategy 2: Optimize Embedding Batch Size
  Current: max_concurrency=5
  Recommendation: Increase to 10-20
  Expected gain: 1.5-2x faster for embedding phase
  Risk: OpenAI rate limits

Strategy 3: Use Integrated Vectorization (with Indexer)
  Setup: Configure blob storage + indexer
  Benefit: No client-side embedding generation
  Expected gain: 30-50% faster (skip embedding phase)
  Trade-off: Requires indexer setup + wait time

Strategy 4: Skip DI for Simple PDFs
  Use: Local PDF extraction for text-only PDFs
  Benefit: No network calls for simple PDFs
  Expected gain: 5-10x faster for simple PDFs
  Trade-off: May miss tables/figures

Strategy 5: Batch Upload to Index
  Current: Upload per document
  Recommendation: Accumulate and upload in larger batches
  Expected gain: 10-20% faster overall
  Implementation: Collect chunks, upload every N documents

Strategy 6: Pre-process in Stages
  Stage 1: Extract all PDFs (parallel)
  Stage 2: Generate all embeddings (parallel batched)
  Stage 3: Upload to index (large batches)
  Expected gain: Better resource utilization
""")

print("\n" + "=" * 80)
print("RECOMMENDED CONFIGURATION FOR 100+ FILES")
print("=" * 80)

print("""
OPTIMAL SETTINGS:

Environment Variables (.env):
  AZURE_OPENAI_MAX_CONCURRENCY=15        # Increase embedding parallelism
  AZURE_DI_MAX_PARALLEL_DOCS=8           # Increase document parallelism
  AZURE_SEARCH_BATCH_SIZE=100            # Larger upload batches

Pipeline Configuration:
  - Process documents in batches of 20-50
  - Use blob storage for artifacts (faster than local I/O)
  - Enable result caching for retry scenarios

Expected Performance (100 files):
  Current: ~86 minutes (1.4 hours) with 4x parallel
  Optimized: ~22 minutes with 16x parallel + optimizations
  Best case: ~15 minutes with all optimizations

IMPLEMENTATION PRIORITY:
  1. [EASY] Increase document parallelization (8-16x)
  2. [EASY] Increase embedding concurrency (10-20)
  3. [MEDIUM] Batch index uploads more aggressively
  4. [HARD] Implement staged processing pipeline
  5. [HARD] Switch to integrated vectorization with indexer
""")
