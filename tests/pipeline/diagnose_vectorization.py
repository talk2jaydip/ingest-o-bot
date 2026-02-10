"""Diagnose integrated vectorization issues and provide recommendations."""

import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizableTextQuery

# Load environment
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


async def diagnose():
    """Diagnose integrated vectorization setup and provide recommendations."""

    # Get credentials
    search_service = os.getenv("AZURE_SEARCH_SERVICE")
    search_endpoint = f"https://{search_service}.search.windows.net" if search_service else os.getenv("AZURE_SEARCH_ENDPOINT")
    index_name = os.getenv("AZURE_SEARCH_INDEX")
    api_key = os.getenv("AZURE_SEARCH_KEY")

    print("="*80)
    print("INTEGRATED VECTORIZATION DIAGNOSTIC")
    print("="*80)
    print(f"\nIndex: {index_name}")
    print(f"Endpoint: {search_endpoint}\n")

    credential = AzureKeyCredential(api_key)
    client = SearchClient(endpoint=search_endpoint, index_name=index_name, credential=credential)

    try:
        # Step 1: Check document count
        print("[Step 1] Checking documents...")
        result = await client.search(search_text="*", top=1, include_total_count=True)
        total_docs = await result.get_count()
        print(f"  Total documents: {total_docs}")

        if total_docs == 0:
            print("\n[PROBLEM] No documents in index!")
            print("  Action: Upload documents first")
            return

        # Step 2: Sample documents to check embeddings field
        print("\n[Step 2] Sampling documents...")
        result = await client.search(
            search_text="*",
            select=["id", "embeddings", "content"],
            top=5
        )

        docs_checked = 0
        docs_with_embeddings = 0
        docs_with_null = 0
        docs_with_empty_array = 0

        async for doc in result:
            docs_checked += 1
            embeddings = doc.get("embeddings", None)

            if embeddings is None:
                docs_with_null += 1
            elif isinstance(embeddings, list) and len(embeddings) == 0:
                docs_with_empty_array += 1
            elif isinstance(embeddings, list) and len(embeddings) > 0:
                docs_with_embeddings += 1

        print(f"  Sampled: {docs_checked} documents")
        print(f"    - With embeddings: {docs_with_embeddings}")
        print(f"    - With empty array []: {docs_with_empty_array}")
        print(f"    - With null: {docs_with_null}")

        # Step 3: Try vector search
        print("\n[Step 3] Testing vector search...")
        try:
            # Get sample content for better query
            sample_result = await client.search(search_text="*", select=["content"], top=1)
            sample_content = None
            async for doc in sample_result:
                content = doc.get("content", "")
                # Extract first few words
                words = content.split()[:3]
                if words:
                    sample_content = " ".join(words)
                break

            test_query = sample_content if sample_content else "test query"
            print(f"  Query: '{test_query}'")

            vector_query = VectorizableTextQuery(
                text=test_query,
                k_nearest_neighbors=3,
                fields="embeddings"
            )

            result = await client.search(
                search_text=None,
                vector_queries=[vector_query],
                select=["id"],
                top=3
            )

            vector_results = 0
            async for _ in result:
                vector_results += 1

            print(f"  Vector search results: {vector_results}")

        except Exception as e:
            print(f"  [ERROR] Vector search failed: {e}")
            vector_results = 0

        # Diagnosis
        print("\n" + "="*80)
        print("DIAGNOSIS & RECOMMENDATIONS")
        print("="*80)

        if docs_with_embeddings > 0:
            print("\n[INFO] Documents have embeddings in stored field")
            print("  This indicates CLIENT-SIDE embeddings were used.")
            print("  Integrated vectorization is NOT being used.")
            print("\n  Recommendation:")
            print("  - This is fine if you want to use client-side embeddings")
            print("  - To use integrated vectorization, set AZURE_USE_INTEGRATED_VECTORIZATION=true")
            print("  - Re-upload documents to omit embeddings field")

        elif docs_with_null > 0:
            print("\n[PROBLEM] Documents have NULL embeddings!")
            print("  Cause: Documents uploaded with 'embeddings: null'")
            print("  Impact: Integrated vectorizer CANNOT generate embeddings for these documents")
            print("  Azure Search requires the field to be OMITTED, not set to null")
            print("\n  Solution: RE-UPLOAD DOCUMENTS")
            print("  1. The code has been fixed to omit the embeddings field")
            print("  2. Delete and re-upload documents:")
            print("     python -m cli  # This will delete old chunks and upload new ones")
            print("  3. Wait 5-10 minutes for Azure Search to generate embeddings")
            print("  4. Run verification again:")
            print("     python test_pipeline/verify_vectorization.py")

        elif docs_with_empty_array > 0 and vector_results == 0:
            print("\n[WAITING] Embeddings field is empty (expected)")
            print("  Status: Azure Search is generating embeddings in background")
            print("  This is NORMAL for integrated vectorization!")
            print("\n  Timeline:")
            print("  - Documents uploaded: Just now (or recently)")
            print("  - Embedding generation: 5-30 minutes (depending on document count)")
            print("  - Vector search ready: After embeddings are generated")
            print("\n  Action: WAIT")
            print("  1. Wait 5-10 minutes")
            print("  2. Run verification again:")
            print("     python test_pipeline/verify_vectorization.py")
            print("  3. If still not working after 30 minutes, check Azure Portal")

        elif docs_with_empty_array > 0 and vector_results > 0:
            print("\n[SUCCESS] Integrated vectorization is working!")
            print("  - Stored embeddings field is empty (expected)")
            print("  - Vector search returns results (confirming embeddings exist)")
            print("  - Azure Search successfully generated embeddings")

        else:
            print("\n[UNKNOWN] Unexpected state")
            print("  Please check your index configuration and documents manually")

        # Additional checks
        print("\n" + "="*80)
        print("ADDITIONAL INFO")
        print("="*80)

        # Check if AZURE_USE_INTEGRATED_VECTORIZATION is set
        use_integrated = os.getenv("AZURE_USE_INTEGRATED_VECTORIZATION", "false").lower() == "true"
        print(f"\nEnvironment variable AZURE_USE_INTEGRATED_VECTORIZATION: {use_integrated}")
        if not use_integrated and docs_with_empty_array > 0:
            print("  [WARN] Variable is FALSE but documents have no embeddings!")
            print("  This suggests documents were uploaded with integrated vectorization")
            print("  but the setting doesn't match. Please verify your configuration.")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(diagnose())
