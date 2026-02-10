"""Monitor when Azure Search has finished generating embeddings."""
import asyncio
import os
import time
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizableTextQuery

load_dotenv('.env')

async def check_vector_search():
    """Check if vector search returns results."""
    search_service = os.getenv("AZURE_SEARCH_SERVICE")
    search_endpoint = f"https://{search_service}.search.windows.net"
    index_name = os.getenv("AZURE_SEARCH_INDEX")
    api_key = os.getenv("AZURE_SEARCH_KEY")

    credential = AzureKeyCredential(api_key)
    client = SearchClient(endpoint=search_endpoint, index_name=index_name, credential=credential)

    try:
        vector_query = VectorizableTextQuery(
            text="example table data",
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
        async for _ in result:
            vector_results += 1

        return vector_results > 0
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        await client.close()

async def monitor():
    """Monitor until embeddings are ready."""
    print("=" * 80)
    print("MONITORING INTEGRATED VECTORIZATION")
    print("=" * 80)
    print(f"Index: {os.getenv('AZURE_SEARCH_INDEX')}")
    print(f"Checking every 30 seconds...")
    print()

    start_time = time.time()
    check_count = 0

    while True:
        check_count += 1
        elapsed = int(time.time() - start_time)
        elapsed_min = elapsed // 60
        elapsed_sec = elapsed % 60

        print(f"[Check {check_count}] Elapsed time: {elapsed_min}m {elapsed_sec}s", end=" ... ")

        ready = await check_vector_search()

        if ready:
            print("[SUCCESS]")
            print()
            print("=" * 80)
            print("EMBEDDINGS ARE READY!")
            print("=" * 80)
            print(f"Total time: {elapsed_min}m {elapsed_sec}s")
            print()
            print("Your integrated vectorization is now working.")
            print("Vector search will return results.")
            break
        else:
            print("[WAITING]")

            if check_count == 1:
                print("  Azure Search is generating embeddings in the background...")
                print("  This typically takes 5-10 minutes.")

            if elapsed > 600:  # 10 minutes
                print()
                print("  Note: It's been over 10 minutes. If this continues:")
                print("  1. Check Azure Portal for indexer status")
                print("  2. Verify your OpenAI endpoint and key in .env")
                print("  3. Check if there are any errors in Azure Search logs")

            # Wait 30 seconds before next check
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(monitor())
