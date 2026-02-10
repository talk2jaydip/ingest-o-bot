"""Azure AI Search uploader - direct document upload without indexers/skillsets."""

from typing import Optional

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient

from .config import SearchConfig
from .logging_utils import get_logger
from .models import ChunkDocument

logger = get_logger(__name__)

# Maximum batch size for Azure AI Search (matches prepdocslib)
MAX_BATCH_SIZE = 1000


class SearchUploader:
    """Uploads chunk documents directly to Azure AI Search index."""
    
    def __init__(self, config: SearchConfig, use_merge_or_upload: bool = True):
        """Initialize search uploader.
        
        Args:
            config: Search configuration
            use_merge_or_upload: If True, use merge_or_upload_documents (idempotent).
                                If False, use upload_documents (replaces documents).
        """
        self.config = config
        self.use_merge_or_upload = use_merge_or_upload
        
        # Create search client
        credential = AzureKeyCredential(config.api_key) if config.api_key else None
        self.client = SearchClient(
            endpoint=config.endpoint,
            index_name=config.index_name,
            credential=credential
        )
    
    async def upload_documents(self, chunk_docs: list[ChunkDocument], include_embeddings: bool = True) -> int:
        """Upload chunk documents to Search index with batching.
        
        Uses batch upload (MAX_BATCH_SIZE = 1000) matching prepdocslib behavior.
        Supports merge_or_upload for idempotent operations.
        
        Args:
            chunk_docs: List of chunk documents to upload
            include_embeddings: If True, include embeddings (client-side). If False, use integrated vectorization.
        
        Returns number of documents uploaded.
        """
        if not chunk_docs:
            return 0
        
        # Convert to Search document format
        search_docs = [doc.to_search_document(include_embeddings=include_embeddings) for doc in chunk_docs]
        
        total_docs = len(search_docs)
        logger.info(f"Uploading {total_docs} documents to index '{self.config.index_name}' (batches of {MAX_BATCH_SIZE})")
        
        # Split into batches (matching prepdocslib)
        batches = [search_docs[i:i + MAX_BATCH_SIZE] for i in range(0, total_docs, MAX_BATCH_SIZE)]
        
        total_succeeded = 0
        total_failed = 0
        
        try:
            for batch_index, batch in enumerate(batches):
                batch_num = batch_index + 1
                logger.info(f"Uploading batch {batch_num}/{len(batches)} ({len(batch)} documents)")
                
                # Use merge_or_upload for idempotency, or upload_documents to replace
                if self.use_merge_or_upload:
                    result = await self.client.merge_or_upload_documents(documents=batch)
                else:
                    result = await self.client.upload_documents(documents=batch)
                
                # Count successful/failed uploads in this batch
                batch_succeeded = sum(1 for r in result if r.succeeded)
                batch_failed = len(result) - batch_succeeded
                
                total_succeeded += batch_succeeded
                total_failed += batch_failed
                
                if batch_failed > 0:
                    # Log failed documents for debugging
                    failed_docs = [r for r in result if not r.succeeded]
                    for failed in failed_docs[:5]:  # Log first 5 failures
                        logger.warning(f"Failed to upload document {failed.key}: {failed.error_message}")
                    if len(failed_docs) > 5:
                        logger.warning(f"... and {len(failed_docs) - 5} more failures")
                
                logger.info(f"Batch {batch_num}: {batch_succeeded} succeeded, {batch_failed} failed")
            
            if total_failed > 0:
                logger.warning(f"Total: {total_succeeded} succeeded, {total_failed} failed out of {total_docs} documents")
            else:
                logger.info(f"Successfully uploaded all {total_succeeded} documents")
            
            return total_succeeded
        
        except Exception as e:
            logger.error(f"Error uploading documents to Search: {e}")
            raise
    
    async def delete_documents_by_filename(self, filename: str) -> int:
        """Delete all documents with a specific sourcefile.

        Args:
            filename: Full filename (e.g., "document.pdf"). Will use basename WITH extension for matching.

        Returns number of documents deleted.
        """
        import os
        import asyncio

        # Get base filename WITH extension (matches updated sourcefile format)
        # e.g., "path/to/document.pdf" -> "document.pdf"
        base_filename = os.path.basename(filename)

        # Escape single quotes for OData filter (replace ' with '')
        escaped_filename = base_filename.replace("'", "''")
        
        logger.info(f"Deleting documents for sourcefile: {base_filename}")
        
        total_deleted = 0
        
        try:
            # Loop until no more documents found (handles > 1000 chunks)
            while True:
                # Search for documents with this filename
                search_result = await self.client.search(
                    search_text="",
                    filter=f"sourcefile eq '{escaped_filename}'",
                    select=["id"],
                    top=1000,  # Batch size limit
                    include_total_count=True
                )
                
                result_count = await search_result.get_count()
                if result_count == 0:
                    break
                
                doc_ids = []
                async for result in search_result:
                    doc_ids.append({"id": result["id"]})
                
                if not doc_ids:
                    if result_count < 1000:
                        break
                    else:
                        continue
                
                # Delete documents
                result = await self.client.delete_documents(documents=doc_ids)
                
                succeeded = sum(1 for r in result if r.succeeded)
                total_deleted += succeeded
                logger.info(f"Deleted batch of {succeeded} documents")
                
                # Wait for index to update (matches prepdocs behavior)
                await asyncio.sleep(2)
            
            logger.info(f"Total deleted {total_deleted} documents for {base_filename}")
            return total_deleted
        
        except Exception as e:
            logger.error(f"Error deleting documents from Search: {e}")
            raise
    
    async def delete_all_documents(self) -> int:
        """Delete all documents from the index.
        
        WARNING: This will delete ALL documents in the index!
        Returns number of documents deleted.
        """
        logger.warning(f"Deleting ALL documents from index '{self.config.index_name}'")
        
        total_deleted = 0
        
        try:
            while True:
                # Search for all documents
                search_result = await self.client.search(
                    search_text="*",
                    select=["id"],
                    top=1000
                )
                
                doc_ids = []
                async for result in search_result:
                    doc_ids.append({"id": result["id"]})
                
                if not doc_ids:
                    break
                
                # Delete batch
                result = await self.client.delete_documents(documents=doc_ids)
                succeeded = sum(1 for r in result if r.succeeded)
                total_deleted += succeeded
                
                logger.info(f"Deleted batch of {succeeded} documents")
        
        except Exception as e:
            logger.error(f"Error deleting all documents: {e}")
            raise
        
        logger.info(f"Total deleted: {total_deleted} documents")
        return total_deleted
    
    async def close(self):
        """Close the Search client."""
        await self.client.close()


def create_search_uploader(config: SearchConfig) -> SearchUploader:
    """Factory function to create search uploader."""
    return SearchUploader(config)

