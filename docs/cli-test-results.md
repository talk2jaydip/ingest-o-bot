# CLI Test Results - Comprehensive Testing Log

**Test Date**: 2026-02-11
**Application**: ingest-o-bot
**CLI Entry Point**: `src\ingestor\cli.py`
**Test Status**: In Progress

---

## Table of Contents

1. [CLI Options Overview](#cli-options-overview)
2. [Test Scenarios Matrix](#test-scenarios-matrix)
3. [Validation & Pre-Check Tests](#validation--pre-check-tests)
4. [Index Management Tests](#index-management-tests)
5. [Input Source Tests](#input-source-tests)
6. [Document Action Tests](#document-action-tests)
7. [Artifact Management Tests](#artifact-management-tests)
8. [Logging & Output Tests](#logging--output-tests)
9. [Error Handling Tests](#error-handling-tests)
10. [Edge Cases & Combinations](#edge-cases--combinations)
11. [Summary](#summary)

---

## CLI Options Overview

### Required Arguments
- None (all arguments are optional with defaults from .env)

### Optional Arguments

#### Environment & Configuration
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--env`, `--env-file` | PATH | `.env` | Path to environment file |

#### Input Sources (Mutually Exclusive)
| Option | Type | Description |
|--------|------|-------------|
| `--pdf`, `--file` | PATH | Single file to process (overrides AZURE_LOCAL_GLOB) |
| `--glob` | PATTERN | Glob pattern for local files (e.g., 'documents/*.pdf') |

#### Document Actions
| Option | Type | Choices | Default | Description |
|--------|------|---------|---------|-------------|
| `--action` | STRING | add, remove, removeall | None (defaults to 'add') | Document operation mode |

#### Index Management Operations
| Option | Type | Description |
|--------|------|-------------|
| `--setup-index` | FLAG | Deploy/update the Azure AI Search index before ingestion |
| `--force-index` | FLAG | Force delete and recreate index, then EXIT (destructive) |
| `--index-only` | FLAG | Only deploy/update index, skip document ingestion |
| `--delete-index` | FLAG | Delete the index only (destructive) |
| `--check-index` | FLAG | Check if index exists, then exit |
| `--skip-ingestion` | FLAG | Skip document ingestion pipeline |

#### Artifact Management
| Option | Type | Description |
|--------|------|-------------|
| `--clean-artifacts` | FLAG | Clean blob artifacts for specified files (use with --glob) |
| `--clean-all-artifacts` | FLAG | Clean ALL blob artifacts (destructive) |

#### Validation & Diagnostics
| Option | Type | Description |
|--------|------|-------------|
| `--validate`, `--pre-check` | FLAG | Run pre-check validation, then exit |

#### Logging & Output
| Option | Type | Description |
|--------|------|-------------|
| `--verbose` | FLAG | Enable verbose/debug logging |
| `--no-colors` | FLAG | Disable colorful console output |

---

## Test Scenarios Matrix

### Category 1: Validation Operations
| ID | Command | Expected Result | Status | Notes |
|----|---------|----------------|--------|-------|
| V01 | `--validate` | Validate config and exit with code 0 | ⏳ PENDING | |
| V02 | `--validate --verbose` | Validate with debug logging | ⏳ PENDING | |
| V03 | `--validate --env missing.env` | Warn about missing env file, continue | ⏳ PENDING | |
| V04 | `--pre-check` | Same as --validate (alias) | ⏳ PENDING | |

### Category 2: Index Management
| ID | Command | Expected Result | Status | Notes |
|----|---------|----------------|--------|-------|
| I01 | `--check-index` | Check if index exists, exit 0 or 1 | ⏳ PENDING | |
| I02 | `--setup-index` | Create/update index without ingestion | ⏳ PENDING | |
| I03 | `--index-only` | Deploy index and exit | ⏳ PENDING | |
| I04 | `--delete-index` | Delete index and exit | ⏳ PENDING | Destructive |
| I05 | `--force-index` | Delete + recreate index, exit | ⏳ PENDING | Destructive |
| I06 | `--setup-index --glob "*.pdf"` | Create index then ingest docs | ⏳ PENDING | |
| I07 | `--setup-index --skip-ingestion` | Create index, skip ingestion | ⏳ PENDING | |

### Category 3: Input Sources
| ID | Command | Expected Result | Status | Notes |
|----|---------|----------------|--------|-------|
| IN01 | `--pdf "file.pdf"` | Process single file | ⏳ PENDING | |
| IN02 | `--file "file.pdf"` | Same as --pdf (alias) | ⏳ PENDING | |
| IN03 | `--glob "docs/*.pdf"` | Process matching files | ⏳ PENDING | |
| IN04 | `--glob "docs/**/*"` | Process all files recursively | ⏳ PENDING | |
| IN05 | No input args (use .env) | Use AZURE_LOCAL_GLOB from env | ⏳ PENDING | |
| IN06 | `--pdf nonexistent.pdf` | Error: file not found | ⏳ PENDING | |
| IN07 | `--glob "nomatch/*.pdf"` | Error: no files found | ⏳ PENDING | |

### Category 4: Document Actions
| ID | Command | Expected Result | Status | Notes |
|----|---------|----------------|--------|-------|
| A01 | `--action add --glob "*.pdf"` | Add/update documents | ⏳ PENDING | |
| A02 | `--action remove --glob "*.pdf"` | Remove documents by filename | ⏳ PENDING | |
| A03 | `--action removeall` | Remove ALL documents | ⏳ PENDING | Destructive |
| A04 | `--glob "*.pdf"` (no action) | Defaults to 'add' | ⏳ PENDING | |

### Category 5: Artifact Management
| ID | Command | Expected Result | Status | Notes |
|----|---------|----------------|--------|-------|
| AR01 | `--clean-artifacts --glob "*.pdf"` | Clean artifacts for files | ⏳ PENDING | |
| AR02 | `--clean-all-artifacts` | Clean ALL artifacts | ⏳ PENDING | Destructive |
| AR03 | `--clean-artifacts` (no glob) | Error: requires --glob or --pdf | ⏳ PENDING | |
| AR04 | `--clean-artifacts --action remove --glob "*.pdf"` | Combined operation | ⏳ PENDING | |

### Category 6: Environment Files
| ID | Command | Expected Result | Status | Notes |
|----|---------|----------------|--------|-------|
| E01 | `--env .env` | Use default env | ⏳ PENDING | |
| E02 | `--env envs/.env.chromadb.example` | Use ChromaDB config | ⏳ PENDING | |
| E03 | `--env envs/.env.cohere.example` | Use Cohere config | ⏳ PENDING | |
| E04 | `--env missing.env` | Warn, continue with system env | ⏳ PENDING | |

### Category 7: Logging & Output
| ID | Command | Expected Result | Status | Notes |
|----|---------|----------------|--------|-------|
| L01 | `--verbose` | Enable debug logging | ⏳ PENDING | |
| L02 | `--no-colors` | Disable colored output | ⏳ PENDING | |
| L03 | `--verbose --no-colors` | Debug logs without colors | ⏳ PENDING | |

### Category 8: Error Handling
| ID | Command | Expected Result | Status | Notes |
|----|---------|----------------|--------|-------|
| ERR01 | No .env and no system env vars | Error with helpful message | ⏳ PENDING | |
| ERR02 | Invalid action value | Argparse error | ⏳ PENDING | |
| ERR03 | `--pdf` and `--glob` together | Last one wins (overrides) | ⏳ PENDING | |
| ERR04 | Ctrl+C during execution | Exit code 130 | ⏳ PENDING | |
| ERR05 | Invalid env file format | Error with line number | ⏳ PENDING | |

### Category 9: Complex Combinations
| ID | Command | Expected Result | Status | Notes |
|----|---------|----------------|--------|-------|
| C01 | `--setup-index --force-index --glob "*.pdf"` | Force recreate, then ingest | ⏳ PENDING | |
| C02 | `--delete-index --skip-ingestion` | Delete index, skip ingestion | ⏳ PENDING | |
| C03 | `--validate --verbose --env test.env` | Validate with custom env | ⏳ PENDING | |
| C04 | `--index-only --verbose --no-colors` | Index with debug, no colors | ⏳ PENDING | |

---

## Detailed Test Results

### 1. Validation & Pre-Check Tests

#### Test V01: Basic Validation
**Command**: `python src\ingestor\cli.py --validate`

**Expected Result**:
- Load configuration from .env
- Validate all settings
- Exit with code 0 if valid, 1 if invalid
- No actual processing

**Actual Result**: ⏳ NOT YET EXECUTED

**Exit Code**: N/A

**Output**:
```
(To be filled after test execution)
```

**Notes**:
- Should check all required environment variables
- Should validate Azure service connectivity
- Should not process any documents

---

#### Test V02: Validation with Verbose Logging
**Command**: `python src\ingestor\cli.py --validate --verbose`

**Expected Result**: Same as V01 but with DEBUG level logs

**Actual Result**: ⏳ NOT YET EXECUTED

---

### 2. Index Management Tests

#### Test I01: Check Index Exists
**Command**: `python src\ingestor\cli.py --check-index`

**Expected Result**:
- Check if index exists in Azure AI Search
- Exit 0 if exists, 1 if not
- Display index name

**Actual Result**: ⏳ NOT YET EXECUTED

---

#### Test I02: Setup Index
**Command**: `python src\ingestor\cli.py --setup-index`

**Expected Result**:
- Create or update Azure AI Search index
- Exit gracefully with message about no input files
- Do not process documents

**Actual Result**: ⏳ NOT YET EXECUTED

---

### 3. Input Source Tests

#### Test IN01: Single File Processing
**Command**: `python src\ingestor\cli.py --pdf "test_document.pdf"`

**Expected Result**:
- Process single PDF file
- Extract, chunk, embed, upload
- Success message with stats

**Actual Result**: ⏳ NOT YET EXECUTED

---

### 4. Document Action Tests

#### Test A01: Add Documents
**Command**: `python src\ingestor\cli.py --action add --glob "documents/*.pdf"`

**Expected Result**:
- Add/update documents in index
- Default behavior (same as no --action)

**Actual Result**: ⏳ NOT YET EXECUTED

---

### 5. Artifact Management Tests

#### Test AR01: Clean Artifacts for Specific Files
**Command**: `python src\ingestor\cli.py --clean-artifacts --glob "documents/*.pdf"`

**Expected Result**:
- Delete blob artifacts for specified files
- Requires blob artifacts mode
- Display count of deleted blobs

**Actual Result**: ⏳ NOT YET EXECUTED

---

### 6. Environment File Tests

#### Test E02: ChromaDB Configuration
**Command**: `python src\ingestor\cli.py --env envs/.env.chromadb.example --validate`

**Expected Result**:
- Load ChromaDB configuration
- Validate offline setup
- Show VECTOR_STORE_MODE=chromadb

**Actual Result**: ⏳ NOT YET EXECUTED

---

### 7. Logging & Output Tests

#### Test L01: Verbose Logging
**Command**: `python src\ingestor\cli.py --verbose --check-index`

**Expected Result**:
- Enable DEBUG level logging
- Show detailed connection info
- More verbose output

**Actual Result**: ⏳ NOT YET EXECUTED

---

### 8. Error Handling Tests

#### Test ERR01: Missing Environment
**Command**: `python src\ingestor\cli.py --env nonexistent.env --validate`

**Expected Result**:
- Warning about missing env file
- Continue with system environment
- May fail validation if required vars missing

**Actual Result**: ⏳ NOT YET EXECUTED

---

## Test Execution Summary

### Statistics
- **Total Test Scenarios**: 45+
- **Executed**: 0
- **Passed**: 0
- **Failed**: 0
- **Skipped**: 0
- **Pending**: 45+

### Status by Category
| Category | Total | Passed | Failed | Pending |
|----------|-------|--------|--------|---------|
| Validation | 4 | 0 | 0 | 4 |
| Index Management | 7 | 0 | 0 | 7 |
| Input Sources | 7 | 0 | 0 | 7 |
| Document Actions | 4 | 0 | 0 | 4 |
| Artifact Management | 4 | 0 | 0 | 4 |
| Environment Files | 4 | 0 | 0 | 4 |
| Logging & Output | 3 | 0 | 0 | 3 |
| Error Handling | 5 | 0 | 0 | 5 |
| Complex Combinations | 4 | 0 | 0 | 4 |

---

## Known Issues & Observations

### Issues Found
(To be filled during testing)

### Best Practices Identified
(To be filled during testing)

### Performance Notes
(To be filled during testing)

---

## Recommendations

### Priority Fixes
(To be filled after testing)

### Enhancement Suggestions
(To be filled after testing)

---

## Test Environment Details

### System Information
- **OS**: Windows 10/11
- **Python Version**: 3.10+
- **Working Directory**: c:\Work\ingest-o-bot

### Dependencies
- azure-search-documents
- azure-ai-documentintelligence
- openai (Azure OpenAI)
- chromadb (optional)
- sentence-transformers (optional)

### Configuration Files Used
- `.env` - Default configuration
- `envs/.env.chromadb.example` - Offline configuration
- `envs/.env.cohere.example` - Cohere embeddings
- `envs/.env.hybrid.example` - Hybrid configuration

---

## Appendix

### A. Complete CLI Help Output
```
(To be captured from --help)
```

### B. Environment Variable Reference
See `.env.example` for complete list of supported environment variables.

### C. Exit Codes
- `0` - Success
- `1` - General error
- `130` - Interrupted by user (Ctrl+C)
- `106` - Virtual environment error

---

**Test Log End**
