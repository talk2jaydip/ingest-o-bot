# Environment Configuration Fixes - Summary

This document summarizes all changes made to resolve environment configuration confusion and handle multiple scenarios properly.

## Problem Statement

The environment configuration had several confusion points:
1. **Unclear requirements**: Which env vars are required vs optional for different scenarios
2. **Poor error messages**: Generic "X is required" without context or alternatives
3. **Missing validation**: No scenario-based validation to guide users
4. **Scattered documentation**: Configuration examples across many files without clear navigation
5. **No defaults handling**: Code didn't gracefully handle missing/invalid env vars

## Solution Overview

### 1. Created Scenario-Based Validation (`src/ingestor/scenario_validator.py`)

**Purpose:** Validates environment configuration based on specific usage scenarios.

**Features:**
- Auto-detects intended scenario from environment variables
- Validates required/optional/forbidden variables per scenario
- Provides clear, actionable error messages
- Includes setup instructions for each scenario

**Scenarios Supported:**
- `local_dev` - Local development (no Azure required)
- `azure_full` - Full Azure stack (production)
- `offline` - Fully offline (ChromaDB + HuggingFace)
- `hybrid` - Azure Search + local embeddings (cost-optimized)
- `azure_cohere` - Azure Search + Cohere embeddings

**Usage:**
```bash
# Auto-detect and validate current configuration
python -m ingestor.scenario_validator

# Validate specific scenario
python -m ingestor.scenario_validator offline

# From Python
from ingestor.scenario_validator import validate_current_environment
result = validate_current_environment()
print(result.valid, result.errors, result.warnings)
```

**Example Output:**
```
✅ Environment configuration is VALID
   Detected scenario: offline

⚠️  1 warnings:
   - Variable AZURE_SEARCH_SERVICE is set but not used in offline scenario.
```

---

### 2. Enhanced Error Messages in `config.py`

**Before:**
```python
if not endpoint:
    raise ValueError("AZURE_OPENAI_ENDPOINT is required")
```

**After:**
```python
if not endpoint:
    if embeddings_mode in ["huggingface", "cohere", "openai"]:
        # Azure OpenAI not needed for alternative embeddings
        return cls(endpoint=None, ...)
    else:
        raise ValueError(
            "Azure OpenAI configuration is required.\n"
            "  Missing: AZURE_OPENAI_ENDPOINT\n"
            "  \n"
            "  Options:\n"
            "  1. Use Azure OpenAI for embeddings (default):\n"
            "       AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/\n"
            "       AZURE_OPENAI_KEY=your-key\n"
            "  \n"
            "  2. Use alternative embeddings provider:\n"
            "       EMBEDDINGS_MODE=huggingface (local, free)\n"
            "  \n"
            "  See: envs/.env.chromadb.example (offline with HuggingFace)"
        )
```

**Benefits:**
- Context-aware error messages
- Multiple solutions provided
- Links to relevant example files
- Graceful handling when service not needed

**Updated Methods:**
- `SearchConfig.from_env()` - Better Azure Search errors, ChromaDB alternative
- `DocumentIntelligenceConfig.from_env()` - Optional for markitdown mode
- `AzureOpenAIConfig.from_env()` - Optional for alternative embeddings
- `InputConfig.from_env()` - Clear local vs blob guidance
- `PipelineConfig.from_env()` - Wrapped with better error context

---

### 3. Integrated Validation into CLI

**Location:** `src/ingestor/cli.py`

**Changes:**
```python
# Added after dotenv loading:
from ingestor.scenario_validator import validate_current_environment
scenario_result = validate_current_environment(verbose=False)
if scenario_result.scenario:
    if scenario_result.valid:
        print(f"✓ Detected scenario: {scenario_result.scenario.value}")
    else:
        print(f"\n⚠️  Configuration issues detected for scenario: {scenario_result.scenario.value}")
        if scenario_result.errors:
            print(f"   Errors: {len(scenario_result.errors)}")
            for error in scenario_result.errors[:3]:
                print(f"     - {error}")
        print(f"   Run 'python -m ingestor.scenario_validator' for detailed help")
```

**Benefits:**
- Users see configuration issues immediately at startup
- Clear guidance to run validator for details
- Non-blocking warnings (doesn't stop execution unless critical)

---

### 4. Comprehensive Documentation

#### A. Master .env.example (`/.env.example`)

**Features:**
- All scenarios in one file with clear sections
- Each scenario clearly marked with visual separators
- Copy-paste ready configurations
- Inline documentation for every variable
- Security notes and validation commands

**Structure:**
```bash
# ==========================================
# CHOOSE YOUR SCENARIO
# ==========================================
#
# ┌─────────────────────────────────────────────────────────────────┐
# │ SCENARIO A: Local Development (No Azure Required)               │
# │ Best for: Testing, development, learning                        │
# │ Cost: FREE | Setup: 5 min                                       │
# └─────────────────────────────────────────────────────────────────┘
#
# VECTOR_STORE_MODE=chromadb
# EMBEDDINGS_MODE=huggingface
# ...
```

#### B. Complete Configuration Guide (`/ENVIRONMENT_CONFIGURATION_GUIDE.md`)

**Contents:**
- Quick start for each scenario
- Complete variable reference with tables
- Validation & troubleshooting section
- Common error messages with solutions
- Configuration patterns and examples

**Structure:**
1. Quick Start (5 scenarios)
2. Configuration Scenarios (detailed setup for each)
3. Environment Variables Reference (comprehensive tables)
4. Validation & Troubleshooting (error solutions)
5. Common Patterns (switching scenarios, cost optimization)

#### C. Quick Reference Card (`/ENVIRONMENT_QUICK_REFERENCE.md`)

**Purpose:** Fast lookup without reading full docs

**Contents:**
- Quick scenario selector table
- Core variables at a glance
- Copy-paste templates for each scenario
- Common mistakes and fixes
- Validation commands

**Example:**
```
| What I Need              | Scenario       | Key Variables               |
|--------------------------|----------------|-----------------------------|
| Test locally, no costs   | Local Dev      | VECTOR_STORE_MODE=chromadb  |
| Enterprise production    | Azure Full     | AZURE_SEARCH_SERVICE        |
| Reduce embedding costs   | Cost-Optimized | EMBEDDINGS_MODE=huggingface |
```

---

### 5. Configuration Loading Flow

**New Flow with Error Handling:**

```
1. Load .env file
   ↓
2. Run parameter validation (typo detection)
   ↓
3. Run scenario validation (auto-detect + validate)
   ↓
4. Display results (warnings/errors)
   ↓
5. Load PipelineConfig with enhanced errors
   ↓
6. Each config section wrapped with context
   ↓
7. If error: show solutions + validator command
```

**Error Context Chain:**

```python
try:
    search = SearchConfig.from_env()
except ValueError as e:
    raise ValueError(
        f"Azure AI Search configuration error:\n{str(e)}\n\n"
        "Need help? Run: python -m ingestor.scenario_validator"
    ) from e
```

---

## Files Changed

### New Files Created

1. **`src/ingestor/scenario_validator.py`** (436 lines)
   - Scenario-based validation logic
   - Auto-detection of intended scenario
   - Detailed validation reports with help

2. **`ENVIRONMENT_CONFIGURATION_GUIDE.md`** (977 lines)
   - Complete environment configuration guide
   - All scenarios documented
   - Full variable reference
   - Troubleshooting section

3. **`ENVIRONMENT_QUICK_REFERENCE.md`** (432 lines)
   - Quick lookup reference
   - Variable tables by category
   - Common mistakes and fixes

4. **`.env.example`** (366 lines)
   - Master template with all scenarios
   - Comprehensive inline documentation
   - Copy-paste ready configurations

5. **`ENVIRONMENT_CONFIG_FIXES_SUMMARY.md`** (this file)
   - Summary of all changes
   - Implementation details

### Modified Files

1. **`src/ingestor/config.py`**
   - Enhanced error messages in all `from_env()` methods
   - Context-aware error handling
   - Graceful handling when services not needed
   - Better validation messages

2. **`src/ingestor/cli.py`**
   - Integrated scenario validator
   - Display validation results at startup
   - Better error guidance

---

## Usage Examples

### Example 1: Local Development (No Azure)

**Before:** Confusing errors about missing Azure services
```
ERROR: AZURE_OPENAI_ENDPOINT is required
ERROR: AZURE_SEARCH_SERVICE is required
```

**After:** Clear guidance
```bash
# Copy template
cp envs/.env.scenario-development.example .env

# Validate
python -m ingestor.scenario_validator
# Output:
✓ Detected scenario: local_dev
✅ Environment configuration is VALID
```

---

### Example 2: Missing Required Variable

**Before:**
```
ValueError: AZURE_OPENAI_EMBEDDING_DEPLOYMENT is required
```

**After:**
```
ValueError: Azure OpenAI configuration is required.
  Missing: AZURE_OPENAI_EMBEDDING_DEPLOYMENT

  Options:
  1. Use Azure OpenAI for embeddings (default):
       AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
       AZURE_OPENAI_KEY=your-key
       AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

  2. Use alternative embeddings provider:
       EMBEDDINGS_MODE=huggingface (local, free)
       OR
       EMBEDDINGS_MODE=cohere (cloud API)
       COHERE_API_KEY=your-key

  See: envs/.env.chromadb.example (offline with HuggingFace)
       envs/.env.cohere.example (Cohere embeddings)

Need help? Run: python -m ingestor.scenario_validator
```

---

### Example 3: Configuration Mismatch

**Before:** Silent failure or unclear errors

**After:**
```bash
python -m ingestor.scenario_validator
# Output:
❌ Environment configuration is INVALID
   Scenario: hybrid

🚫 1 errors found:
   - AZURE_USE_INTEGRATED_VECTORIZATION must be 'false' when using local embeddings.
     Azure Search cannot use integrated vectorization with HuggingFace embeddings.

📋 Setup Instructions:
  1. Create Azure AI Search service
  2. Install: pip install sentence-transformers
  3. Set VECTOR_STORE_MODE=azure_search
  4. Set EMBEDDINGS_MODE=huggingface
  5. Set AZURE_USE_INTEGRATED_VECTORIZATION=false

See: envs/.env.hybrid.example for full template
```

---

## Scenario Coverage

### All Scenarios Properly Handled

| Scenario | Required Validation | Error Messages | Documentation | Templates |
|----------|---------------------|----------------|---------------|-----------|
| Local Dev | ✅ | ✅ | ✅ | ✅ envs/.env.scenario-development.example |
| Azure Full | ✅ | ✅ | ✅ | ✅ envs/.env.example |
| Offline | ✅ | ✅ | ✅ | ✅ envs/.env.chromadb.example |
| Cost-Optimized | ✅ | ✅ | ✅ | ✅ envs/.env.hybrid.example |
| Multilingual | ✅ | ✅ | ✅ | ✅ envs/.env.cohere.example |

### Edge Cases Covered

1. **Missing optional services**: Gracefully handled (e.g., Azure DI not needed for markitdown mode)
2. **Alternative embeddings**: Clear guidance when Azure OpenAI not needed
3. **Configuration mismatches**: Detected and reported with solutions
4. **Typos in variable names**: Detected with suggestions
5. **Conflicting settings**: Warned (e.g., integrated vectorization with HuggingFace)

---

## Testing Checklist

### Validation Testing
- [x] Auto-detection works for each scenario
- [x] Required variables validated correctly
- [x] Optional variables marked correctly
- [x] Forbidden variables warned appropriately
- [x] Scenario-specific validation logic works

### Error Message Testing
- [x] SearchConfig errors show alternatives
- [x] AzureOpenAI errors show alternative embeddings
- [x] InputConfig errors show local vs blob guidance
- [x] DocumentIntelligence errors show offline option
- [x] All errors include validator command

### CLI Integration Testing
- [x] Validator runs at startup
- [x] Results displayed clearly
- [x] Errors don't block unless critical
- [x] Validation command works: `--validate`
- [x] Scenario validator works as standalone

### Documentation Testing
- [x] All scenarios documented
- [x] All variables documented
- [x] Examples are copy-paste ready
- [x] Links between docs work
- [x] Quick reference accurate

---

## Migration Guide for Users

### For Existing Users

**Your existing .env files will continue to work!** No breaking changes.

**To benefit from improvements:**

1. **Validate current configuration:**
   ```bash
   python -m ingestor.scenario_validator
   ```

2. **Review suggestions** if any issues detected

3. **Optional: Migrate to new format:**
   ```bash
   # Backup current
   cp .env .env.backup

   # Copy new template
   cp .env.example .env

   # Transfer your values to new template
   # (keep scenario section that matches your use case)
   ```

### For New Users

1. **Choose scenario** from ENVIRONMENT_QUICK_REFERENCE.md
2. **Copy template:**
   ```bash
   cp envs/.env.scenario-XXX.example .env
   ```
3. **Fill in values** (follow comments)
4. **Validate:**
   ```bash
   python -m ingestor.scenario_validator
   python -m ingestor.cli --validate
   ```

---

## Benefits Summary

### For Users
✅ Clear error messages with solutions
✅ Auto-detection of intended scenario
✅ Copy-paste ready templates
✅ Quick reference for fast lookup
✅ Validation before running pipeline
✅ Comprehensive troubleshooting guide

### For Developers
✅ Scenario-based validation framework
✅ Reusable validation logic
✅ Extensible to new scenarios
✅ Better error context in logs
✅ Reduced support burden

### For Operations
✅ Pre-flight validation prevents errors
✅ Clear documentation for all scenarios
✅ Cost optimization guidance
✅ Security best practices documented
✅ Easy scenario switching

---

## Future Enhancements

### Potential Additions
1. **Interactive configurator**: CLI wizard to generate .env
2. **More scenarios**: Kubernetes, Docker Compose, etc.
3. **Validation API**: REST endpoint for CI/CD validation
4. **Auto-fix suggestions**: "Run this command to fix"
5. **Configuration diffing**: Compare two .env files

### Already Planned
- [x] Scenario-based validation
- [x] Enhanced error messages
- [x] Comprehensive documentation
- [x] Quick reference card
- [x] Master .env.example

---

## Conclusion

This comprehensive fix addresses all major confusion points in environment configuration:

1. **Clear Requirements**: Scenario-based validation shows exactly what's needed
2. **Better Errors**: Context-aware messages with multiple solutions
3. **Proper Validation**: Auto-detection and validation before running
4. **Complete Documentation**: From quick reference to detailed guides
5. **Graceful Handling**: Code handles missing/invalid vars appropriately

**Result:** Users can now confidently configure the system for any scenario with clear guidance at every step.

---

**Need Help?**
- Quick Reference: [ENVIRONMENT_QUICK_REFERENCE.md](ENVIRONMENT_QUICK_REFERENCE.md)
- Complete Guide: [ENVIRONMENT_CONFIGURATION_GUIDE.md](ENVIRONMENT_CONFIGURATION_GUIDE.md)
- Validation: `python -m ingestor.scenario_validator`
- Setup: [SETUP_GUIDE.md](SETUP_GUIDE.md)
