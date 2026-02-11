# Known Limitations

This document lists known limitations and areas for future enhancement in the ingestor pipeline.

---

## 1. Hyperlink Extraction

### Azure Document Intelligence Limitation

**Issue:** Azure Document Intelligence API does **not** extract hyperlinks from any document type.

**Official Status:**
- Confirmed by Microsoft in GitHub Issue #40069
- Feature requested but not yet implemented
- As of API version 2024-11-30 (latest GA), hyperlink extraction is not supported

**Impact:**
- Hyperlinks in source documents are not automatically preserved
- Link URLs are lost unless extracted through alternative methods

### Current Implementation Status

#### ✅ PDF Documents - **SUPPORTED**

**Solution:** PyMuPDF-based hyperlink extraction

**Features:**
- Extracts external URLs from PDF link annotations
- Extracts internal page references
- Converts links to markdown format: `[text](url)`
- Preserves URLs from PageFooter comments
- Handles multi-line links

**Location:** `src/ingestor/di_extractor.py`

**Example:**
```markdown
# Original PDF text:
"More details can be found here."
(with hyperlink: https://example.com/details)

# Extracted text:
"More details can be found [here.](https://example.com/details)"
```

**Limitations:**
- Multi-line links with surrounding quotes may not be perfectly matched
- Links split across different PDF annotations may require manual review

#### ❌ Office Documents (DOCX/PPTX) - **NOT SUPPORTED**

**Why:** Office documents require parsing the internal XML structure from the ZIP container to extract hyperlinks.

**Technical Details:**
- DOCX files store hyperlinks in `document.xml` and `document.xml.rels`
- PPTX files store hyperlinks in `slide*.xml` and `slide*.xml.rels`
- Azure DI does not expose this relationship data
- Would require python-docx/python-pptx or direct XML parsing

**Workaround Options:**

**Option 1: Direct XML Parsing (Recommended)**
```python
import zipfile
from xml.etree import ElementTree as ET

# Parse hyperlinks from Office XML without full document parsing
with zipfile.ZipFile(io.BytesIO(file_bytes)) as zip_file:
    # For DOCX: Read document.xml and document.xml.rels
    # For PPTX: Read slide*.xml and slide*.xml.rels
    # Extract hyperlink relationships
```

**Option 2: python-docx / python-pptx**
```python
from docx import Document

doc = Document(io.BytesIO(file_bytes))
for paragraph in doc.paragraphs:
    for run in paragraph.runs:
        if run.hyperlink:
            # Extract hyperlink.address and run.text
```

**Status:** TODO - Enhancement for future release

---

## 2. Future Enhancements

### Priority 1: Office Document Hyperlinks

**Task:** Implement hyperlink extraction for DOCX/PPTX files

**Approach:**
1. Use lightweight XML parsing from existing `file_bytes` (no additional file reads)
2. Extract hyperlink relationships from Office XML structure
3. Apply same markdown conversion as PDF hyperlinks
4. Integrate into `office_extractor.py`

**Estimated Impact:**
- Preserves important reference links in Office documents
- Improves document fidelity and user experience
- Enables clickable citations in RAG responses

### Priority 2: Advanced Link Handling

**Potential Improvements:**
- Better handling of multi-line quoted links
- Link text normalization across whitespace variations
- Support for footnote-style link references
- Link validation and broken link detection

---

## 3. Monitoring Azure Document Intelligence Updates

**Action Items:**
- Monitor GitHub Issue #40069 for updates
- Check Azure Document Intelligence API changelog for hyperlink features
- Update implementation if native hyperlink support becomes available

**Resources:**
- [Azure DI GitHub](https://github.com/Azure/azure-sdk-for-python/issues)
- [Azure DI Changelog](https://learn.microsoft.com/azure/ai-services/document-intelligence/changelog-release-history)
- [Azure DI Features](https://learn.microsoft.com/azure/ai-services/document-intelligence/concept-layout)

---

## 4. Summary

| Feature | PDF | DOCX | PPTX | Status |
|---------|-----|------|------|--------|
| **Hyperlink Extraction** | ✅ PyMuPDF | ❌ Not Implemented | ❌ Not Implemented | Partial |
| **External URLs** | ✅ Supported | ❌ | ❌ | Partial |
| **Internal Links** | ✅ Page refs | ❌ | ❌ | Partial |
| **Markdown Format** | ✅ `[text](url)` | ❌ | ❌ | Partial |

**Key Takeaways:**
- ✅ PDF hyperlink extraction is production-ready
- ❌ Office document hyperlinks require additional implementation
- 📋 Enhancement tracked for future release
- 🔍 Monitoring Azure DI for native hyperlink support

---

**Last Updated:** 2026-02-11
**Related Documentation:** [Features - Hyperlink Extraction](17_FEATURES.md#hyperlink-extraction)
