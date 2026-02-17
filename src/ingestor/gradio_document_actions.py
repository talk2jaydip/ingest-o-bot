"""
Document Actions for Gradio UI - Remove/RemoveAll functionality.

This module provides UI components and functions for removing documents
from the search index with optional artifact cleanup.
"""

import asyncio
import logging
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)


def search_documents_to_remove(pattern: str, search_documents_by_filename_func) -> Dict[str, Any]:
    """Search for documents to remove and return table with checkboxes.

    Args:
        pattern: Filename pattern to search for
        search_documents_by_filename_func: Function to search documents

    Returns:
        Dictionary with table data and status info
    """
    if not pattern or pattern.strip() == "":
        return {
            "table": [],
            "status": "*Enter a search pattern and click Search*"
        }

    docs = search_documents_by_filename_func(pattern)

    if not docs:
        return {
            "table": [],
            "status": "**No documents found** 😞\n\nTry a different search pattern."
        }

    # Format for dataframe with checkbox column
    rows = []
    total_chunks = 0
    for doc in docs:
        rows.append([
            False,  # Checkbox (unchecked by default)
            doc["filename"],
            doc["chunk_count"],
            doc["category"] or "—"
        ])
        total_chunks += doc["chunk_count"]

    status_info = f"""
**✅ Found {len(docs)} document(s)** with **{total_chunks} total chunks**

Select documents to remove using the checkboxes in the first column.
"""

    return {
        "table": rows,
        "status": status_info
    }


def show_remove_confirmation(table_data: Any, clean_artifacts: bool) -> Dict[str, Any]:
    """Show confirmation dialog for document removal.

    Args:
        table_data: Table data (DataFrame or list)
        clean_artifacts: Whether to clean artifacts

    Returns:
        Dictionary with confirmation UI updates
    """
    if not table_data or len(table_data) == 0:
        return {
            "visible": False,
            "status": "⚠️ No documents in table. Please search first."
        }

    # Convert to list if pandas DataFrame
    import pandas as pd
    if isinstance(table_data, pd.DataFrame):
        table_data = table_data.values.tolist()

    # Get selected documents (checkbox = True)
    selected_docs = []
    total_chunks = 0
    for row in table_data:
        if len(row) >= 4 and row[0] is True:  # Checkbox is checked
            selected_docs.append({
                "filename": row[1],
                "chunks": row[2]
            })
            total_chunks += row[2]

    if len(selected_docs) == 0:
        return {
            "visible": False,
            "status": "⚠️ No documents selected. Check the boxes in the first column."
        }

    # Build confirmation message
    doc_list = "\n".join([f"- **{doc['filename']}** ({doc['chunks']} chunks)" for doc in selected_docs[:10]])
    if len(selected_docs) > 10:
        doc_list += f"\n- ... and {len(selected_docs) - 10} more documents"

    artifacts_msg = "\n\n**🧹 Artifacts will also be cleaned from blob storage.**" if clean_artifacts else ""

    confirm_msg = f"""
### ⚠️ Confirm Document Removal

You are about to remove:
- **{len(selected_docs)} document(s)**
- **{total_chunks} total chunks**
{artifacts_msg}

**Documents to remove:**
{doc_list}

**This action cannot be undone!**

Are you sure you want to continue?
"""

    return {
        "visible": True,
        "message": confirm_msg,
        "pending_docs": selected_docs,
        "status": f"⚠️ Awaiting confirmation to remove {len(selected_docs)} documents..."
    }


def execute_remove_documents(pending_docs: List[Dict], clean_artifacts: bool) -> Dict[str, Any]:
    """Execute the document removal operation.

    Args:
        pending_docs: List of documents to remove
        clean_artifacts: Whether to clean artifacts

    Returns:
        Dictionary with operation results
    """
    if not pending_docs or len(pending_docs) == 0:
        return {
            "confirm_visible": False,
            "progress_visible": False,
            "status": "⚠️ No documents to remove."
        }

    try:
        from ingestor.config import PipelineConfig
        from ingestor.search_uploader import create_search_uploader
        from ingestor.artifact_storage import create_artifact_storage

        # Show progress
        progress_log = "🗑️ Starting document removal...\n\n"

        # Load config
        config = PipelineConfig.from_env()
        search_uploader = create_search_uploader(config.search)

        total_deleted = 0
        total_artifacts_cleaned = 0

        # Remove each document
        for idx, doc in enumerate(pending_docs, 1):
            filename = doc["filename"]
            progress_log += f"[{idx}/{len(pending_docs)}] Removing: {filename}\n"

            # Delete from search index
            try:
                deleted = asyncio.run(search_uploader.delete_documents_by_filename(filename))
                total_deleted += deleted
                progress_log += f"  ✅ Removed {deleted} chunks from index\n"
            except Exception as e:
                progress_log += f"  ❌ Error removing from index: {e}\n"
                logger.error(f"Error removing {filename} from index: {e}", exc_info=True)

            # Clean artifacts if requested
            if clean_artifacts:
                try:
                    artifact_storage = create_artifact_storage(config.artifacts)
                    if hasattr(artifact_storage, 'delete_document_artifacts'):
                        artifacts_deleted = asyncio.run(artifact_storage.delete_document_artifacts(filename))
                        total_artifacts_cleaned += artifacts_deleted
                        progress_log += f"  🧹 Cleaned {artifacts_deleted} artifact blobs\n"
                except Exception as e:
                    progress_log += f"  ⚠️ Could not clean artifacts: {e}\n"
                    logger.error(f"Error cleaning artifacts for {filename}: {e}", exc_info=True)

            progress_log += "\n"

        progress_log += "="*60 + "\n"
        progress_log += f"✅ REMOVAL COMPLETE\n\n"
        progress_log += f"📊 Summary:\n"
        progress_log += f"  - Documents processed: {len(pending_docs)}\n"
        progress_log += f"  - Chunks deleted: {total_deleted}\n"
        if clean_artifacts:
            progress_log += f"  - Artifacts cleaned: {total_artifacts_cleaned}\n"
        progress_log += "="*60 + "\n"

        return {
            "confirm_visible": False,
            "progress": progress_log,
            "progress_visible": True,
            "status": f"✅ Successfully removed {len(pending_docs)} documents ({total_deleted} chunks)",
            "pending_docs": [],
            "table": []  # Clear table
        }

    except Exception as e:
        error_msg = f"❌ Error during removal: {str(e)}"
        logger.error(error_msg, exc_info=True)

        return {
            "confirm_visible": False,
            "progress": error_msg,
            "progress_visible": True,
            "status": error_msg
        }


def refresh_removeall_stats(search_documents_by_filename_func) -> Dict[str, Any]:
    """Refresh statistics for remove all operation.

    Args:
        search_documents_by_filename_func: Function to search documents

    Returns:
        Dictionary with stats display and data
    """
    try:
        # Get all documents
        docs = search_documents_by_filename_func("*", max_results=10000)

        if not docs:
            stats_md = """
### 📊 Index Statistics

**Index is empty or not connected**

No documents found in the index.
"""
            return {
                "display": stats_md,
                "stats": {"doc_count": 0, "chunk_count": 0}
            }

        total_docs = len(docs)
        total_chunks = sum(doc["chunk_count"] for doc in docs)

        stats_md = f"""
### 📊 Index Statistics

- **Total Documents:** {total_docs:,}
- **Total Chunks:** {total_chunks:,}

⚠️ **All of these will be deleted if you proceed with Remove All!**
"""

        return {
            "display": stats_md,
            "stats": {"doc_count": total_docs, "chunk_count": total_chunks}
        }

    except Exception as e:
        error_md = f"""
### ❌ Error Loading Statistics

Could not load index statistics: {str(e)}

Please check your connection and try again.
"""
        return {
            "display": error_md,
            "stats": {}
        }


def check_removeall_confirmation(confirmation_text: str, clean_artifacts: bool, stats: Dict) -> Dict[str, Any]:
    """Check if confirmation text matches and show final step.

    Args:
        confirmation_text: Text entered by user
        clean_artifacts: Whether to clean artifacts
        stats: Current index statistics

    Returns:
        Dictionary with final confirmation UI updates
    """
    if confirmation_text == "REMOVE ALL":
        doc_count = stats.get("doc_count", 0)
        chunk_count = stats.get("chunk_count", 0)

        artifacts_warning = ""
        if clean_artifacts:
            artifacts_warning = "\n\n🧹 **ALL ARTIFACTS will also be deleted from blob storage!**"

        final_msg = f"""
### 🚨 FINAL WARNING 🚨

You are about to:
- Delete **{doc_count:,} documents**
- Delete **{chunk_count:,} chunks**
- **This cannot be undone!**
{artifacts_warning}

Click "REMOVE ALL DOCUMENTS NOW" to proceed.
"""
        return {
            "visible": True,
            "message": final_msg
        }
    else:
        return {
            "visible": False,
            "message": ""
        }


def execute_removeall(clean_artifacts: bool, stats: Dict) -> Dict[str, Any]:
    """Execute remove all operation with progress tracking.

    Args:
        clean_artifacts: Whether to clean artifacts
        stats: Current index statistics

    Returns:
        Dictionary with operation results
    """
    try:
        from ingestor.config import PipelineConfig
        from ingestor.search_uploader import create_search_uploader
        from ingestor.artifact_storage import create_artifact_storage

        progress_log = "🗑️ REMOVE ALL OPERATION STARTED\n"
        progress_log += "="*60 + "\n\n"

        doc_count = stats.get("doc_count", 0)
        chunk_count = stats.get("chunk_count", 0)

        progress_log += f"📊 Index Statistics:\n"
        progress_log += f"  - Documents to remove: {doc_count:,}\n"
        progress_log += f"  - Chunks to remove: {chunk_count:,}\n"
        progress_log += f"  - Clean artifacts: {'YES' if clean_artifacts else 'NO'}\n\n"

        # Load config
        config = PipelineConfig.from_env()

        # Delete all documents from index
        progress_log += "🗑️ Deleting all documents from index...\n"
        search_uploader = create_search_uploader(config.search)

        deleted_count = asyncio.run(search_uploader.delete_all_documents())
        progress_log += f"✅ Deleted {deleted_count:,} documents from index\n\n"

        # Clean all artifacts if requested
        if clean_artifacts:
            progress_log += "🧹 Cleaning all artifacts from blob storage...\n"
            try:
                artifact_storage = create_artifact_storage(config.artifacts)
                if hasattr(artifact_storage, 'delete_all_artifacts'):
                    artifacts_deleted = asyncio.run(artifact_storage.delete_all_artifacts())
                    progress_log += f"✅ Cleaned {artifacts_deleted:,} artifact blobs\n\n"
                else:
                    progress_log += "⚠️ Artifact storage does not support delete_all_artifacts\n\n"
            except Exception as e:
                progress_log += f"❌ Error cleaning artifacts: {e}\n\n"
                logger.error(f"Error cleaning all artifacts: {e}", exc_info=True)

        progress_log += "="*60 + "\n"
        progress_log += "✅ REMOVE ALL OPERATION COMPLETE\n"
        progress_log += "="*60 + "\n"

        return {
            "progress": progress_log,
            "progress_visible": True,
            "step3_visible": False,
            "step2_visible": False,
            "enable_checkbox": False,
            "confirmation_text": "",
            "stats_display": "### 📊 Index Statistics\n**Index is now empty**"
        }

    except Exception as e:
        error_log = f"❌ ERROR DURING REMOVE ALL\n\n{str(e)}\n\nOperation failed!"
        logger.error(f"Remove all failed: {e}", exc_info=True)

        return {
            "progress": error_log,
            "progress_visible": True
        }
