"""Quick check of embeddings in search index."""
import asyncio
import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizableTextQuery

load_dotenv('.env')

async def check_embeddings():
    search_service = os.getenv("AZURE_SEARCH_SERVICE")
    search_endpoint = f"https://{search_service}.search.windows.net"
    index_name = os.getenv("AZURE_SEARCH_INDEX")
    api_key = os.getenv("AZURE_SEARCH_KEY")

    print(f"Index: {index_name}")
    print(f"Endpoint: {search_endpoint}\n")

    credential = AzureKeyCredential(api_key)
    client = SearchClient(endpoint=search_endpoint, index_name=index_name, credential=credential)

    try:
        # Check total documents
        result = await client.search(search_text="*", top=1, include_total_count=True)
        total_docs = await result.get_count()
        print(f"Total documents: {total_docs}\n")

        if total_docs == 0:
            print("No documents in index!")
            return

        # Sample 5 documents
        print("Checking embeddings in 5 sample documents:")
        print("-" * 80)
        result = await client.search(
            search_text="*",
            select=["id", "embeddings", "content"],
            top=5
        )

        docs_with_embeddings = 0
        docs_with_null = 0
        docs_with_empty_array = 0

        i = 0
        async for doc in result:
            i += 1
            embeddings = doc.get("embeddings", "FIELD_NOT_PRESENT")
            content_preview = doc.get("content", "")[:50]

            if embeddings == "FIELD_NOT_PRESENT":
                status = "OMITTED (correct for integrated vectorization)"
            elif embeddings is None:
                status = "NULL (PROBLEM - Azure Search can't vectorize null!)"
                docs_with_null += 1
            elif isinstance(embeddings, list) and len(embeddings) == 0:
                status = "[] (expected for integrated vectorization)"
                docs_with_empty_array += 1
            elif isinstance(embeddings, list) and len(embeddings) > 0:
                status = f"[...{len(embeddings)} values...] (client-side embeddings)"
                docs_with_embeddings += 1
            else:
                status = f"UNKNOWN: {type(embeddings)}"

            print(f"Doc {i}: {doc['id']}")
            print(f"  Content: {content_preview}...")
            print(f"  Embeddings: {status}")
            print()

        # Try vector search
        print("\n" + "="*80)
        print("Testing vector search:")
        print("-" * 80)

        try:
            vector_query = VectorizableTextQuery(
                text="test query",
                k_nearest_neighbors=3,
                fields="embeddings"
            )

            result = await client.search(
                search_text=None,
                vector_queries=[vector_query],
                select=["id", "content"],
                top=3
            )

            vector_results = 0
            async for doc in result:
                vector_results += 1
                content_preview = doc.get("content", "")[:80]
                print(f"  Result {vector_results}: {doc['id']}")
                print(f"    Content: {content_preview}...")

            print(f"\nVector search returned {vector_results} results")

            if vector_results > 0:
                print("[SUCCESS] Vector search is WORKING!")
            else:
                print("[FAIL] Vector search returned NO results")

        except Exception as e:
            print(f"[ERROR] Vector search FAILED: {e}")

        # Summary
        print("\n" + "="*80)
        print("DIAGNOSIS:")
        print("="*80)

        if docs_with_null > 0:
            print("\n[PROBLEM] Documents have NULL embeddings!")
            print("\nExplanation:")
            print("  - Your documents were uploaded with 'embeddings: null'")
            print("  - Azure Search CANNOT generate embeddings for null fields")
            print("  - The field must be OMITTED entirely, not set to null")
            print("\nSOLUTION:")
            print("  1. Delete existing documents:")
            print("     python -m ingestor.cli --action removeall")
            print("  2. Re-upload with corrected code:")
            print("     python -m ingestor.cli")
            print("  3. Wait 5-10 minutes for Azure Search to generate embeddings")
            print("  4. Test again with: python check_embeddings.py")

        elif docs_with_empty_array > 0:
            print("\n[OK] Configuration looks correct!")
            print("  - Documents have empty embeddings [] (expected for integrated vectorization)")
            print("  - Azure Search should be generating embeddings in the background")
            print("\nNext steps:")
            print("  - If vector search works: Everything is fine!")
            print("  - If vector search fails: Wait 5-10 minutes, Azure is still processing")

        elif docs_with_embeddings > 0:
            print("\n[INFO] Using CLIENT-SIDE embeddings")
            print("  - Documents have embeddings already populated")
            print("  - This is fine, but you're not using integrated vectorization")
            print("  - Your .env has AZURE_USE_INTEGRATED_VECTORIZATION=true")
            print("  - But documents seem to be using client-side embeddings")

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(check_embeddings())
