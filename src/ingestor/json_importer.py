"""JSON bulk import for Azure AI Search.

Supports importing pre-formatted documents from JSON files directly to Azure Search index.
Useful for data migration, testing, and batch uploads from external sources.
"""

import json
from pathlib import Path
from typing import Optional

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient

from .config import SearchConfig
from .logging_utils import get_logger

logger = get_logger(__name__)

MAX_BATCH_SIZE = 1000


async def import_json_to_azure_search(
    json_path: str,
    config: SearchConfig,
    max_batch_concurrency: int = 5
) -> int:
    """Import documents from JSON file to Azure AI Search.

    JSON Format:
    - Array of objects, each object represents one document
    - Must include required fields: id, content
    - Can include optional fields: embeddings, filename, url, etc.
    - Fields must match Azure Search index schema

    Example JSON:
    [
        {
            "id": "doc1-chunk1",
            "content": "Document text...",
            "embeddings": [0.1, 0.2, ...],  // Optional if using integrated vectorization
            "filename": "document.pdf",
            "sourcepage": "document.pdf-1",
            "sourcefile": "document",
            "pageNumber": 1
        },
        ...
    ]

    Args:
        json_path: Path to JSON file
        config: Azure Search configuration
        max_batch_concurrency: Maximum concurrent batch uploads

    Returns:
        Number of documents successfully uploaded

    Raises:
        FileNotFoundError: If JSON file doesn't exist
        ValueError: If JSON format is invalid
        RuntimeError: If upload fails
    """

    # Load JSON file
    json_path_obj = Path(json_path)
    if not json_path_obj.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    logger.info(f"Loading JSON from: {json_path}")

    with open(json_path_obj, 'r', encoding='utf-8') as f:
        documents = json.load(f)

    if not isinstance(documents, list):
        raise ValueError("JSON must be an array of document objects")

    total_docs = len(documents)
    logger.info(f"Loaded {total_docs} documents from JSON")

    # Validate required fields
    for i, doc in enumerate(documents):
        if not isinstance(doc, dict):
            raise ValueError(f"Document at index {i} is not an object")
        if 'id' not in doc:
            raise ValueError(f"Document at index {i} missing required field: 'id'")
        if 'content' not in doc:
            raise ValueError(f"Document at index {i} missing required field: 'content'")

    logger.info("✓ JSON validation passed")

    # Create Search client
    credential = AzureKeyCredential(config.api_key) if config.api_key else None
    client = SearchClient(
        endpoint=config.endpoint,
        index_name=config.index_name,
        credential=credential
    )

    # Upload in batches
    batches = [documents[i:i + MAX_BATCH_SIZE] for i in range(0, total_docs, MAX_BATCH_SIZE)]

    total_succeeded = 0
    total_failed = 0

    try:
        for batch_index, batch in enumerate(batches):
            batch_num = batch_index + 1
            logger.info(f"Uploading batch {batch_num}/{len(batches)} ({len(batch)} documents)")

            result = await client.merge_or_upload_documents(documents=batch)

            batch_succeeded = sum(1 for r in result if r.succeeded)
            batch_failed = len(result) - batch_succeeded

            total_succeeded += batch_succeeded
            total_failed += batch_failed

            if batch_failed > 0:
                failed_docs = [r for r in result if not r.succeeded]
                for failed in failed_docs[:5]:
                    logger.warning(f"Failed: {failed.key} - {failed.error_message}")
                if len(failed_docs) > 5:
                    logger.warning(f"... and {len(failed_docs) - 5} more failures")

            logger.info(f"Batch {batch_num}: {batch_succeeded} succeeded, {batch_failed} failed")

        if total_failed > 0:
            logger.warning(f"Import completed with errors: {total_succeeded} succeeded, {total_failed} failed")
        else:
            logger.info(f"✓ Successfully imported all {total_succeeded} documents")

        return total_succeeded

    except Exception as e:
        logger.error(f"Import failed: {e}")
        raise

    finally:
        await client.close()
