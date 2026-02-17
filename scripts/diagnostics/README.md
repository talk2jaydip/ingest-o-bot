# Diagnostic Scripts

This folder contains diagnostic and testing scripts used for development and debugging.

## Script Categories

### Test Scripts (test_*.py)
Scripts that test specific functionality:
- `test_both_documents.py` - Test processing of multiple documents
- `test_caption_fix.py` - Test caption handling fixes
- `test_chunking_fixes.py` - Test chunking behavior
- `test_full_document.py` - Test full document processing
- `test_overlap_fix.py` - Test overlap calculation
- `test_span_logging.py` - Test span processing logging
- `test_tables_fix.py` - Test table handling fixes

### Diagnostic Scripts (diagnose_*.py)
Scripts that diagnose issues:
- `diagnose_blocks.py` - Diagnose block extraction issues
- `diagnose_di_captions.py` - Diagnose Document Intelligence caption issues
- `diagnose_span_processing.py` - Diagnose span processing issues
- `diagnose_text_loss.py` - Diagnose text loss during processing

### Verification Scripts (verify_*.py)
Scripts that verify correct behavior:
- `verify_crosspage_overlap.py` - Verify cross-page overlap behavior
- `verify_research_paper_hard.py` - Verify complex document processing
- `verify_token_range.py` - Verify token count calculations

### Check Scripts (check_*.py)
Scripts that check specific aspects:
- `check_raw_di_response.py` - Check raw Document Intelligence responses
- `check_text_preservation.py` - Check text preservation through pipeline

### Analysis Scripts (analyze_*.py)
Scripts that analyze documents, logs, or behavior:
- `analyze_medical_who.py` - Analyze medical WHO documents
- `analyze_performance.py` - Analyze pipeline performance metrics

### Performance & Monitoring Scripts
- `analyze_performance.py` - Analyze pipeline performance metrics
- `apply_performance_optimizations.py` - Apply performance optimizations
- `check_embeddings.py` - Check embedding generation
- `check_indexer_status.py` - Check indexer status
- `verify_index_config.py` - Verify index configuration
- `wait_for_embeddings.py` - Wait for embeddings to be generated
- `run_batch_ingestion.py` - Run batch ingestion tests


### Other Scripts
- `final_verification.py` - Final verification of pipeline behavior
- `show_page2_chunk_text.py` - Display chunk text for debugging
- `test_colorful_logging.py` - Test colorful logging output
- `test_artifact_config.py` - Test artifact configuration

## Usage

Most scripts can be run directly from the project root:

```bash
# Example: Run a test script
python scripts/diagnostics/test_chunking_fixes.py

# Example: Run a diagnostic script
python scripts/diagnostics/diagnose_blocks.py
```

Some scripts may require:
- Environment variables to be set (`.env` file)
- Test documents in the `data/` folder
- Artifacts from previous pipeline runs

## Notes

These scripts are for development and debugging purposes. They:
- May produce verbose output
- May require specific test files
- Are not part of the production pipeline
- Help identify and fix issues during development

For production use, use the main CLI:
```bash
python -m ingestor.cli --help
```
