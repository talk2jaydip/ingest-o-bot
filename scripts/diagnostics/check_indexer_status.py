"""Check Azure Search indexer status for integrated vectorization."""
import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexerClient

load_dotenv('.env')

def check_indexers():
    """Check all indexers and their status."""
    search_service = os.getenv("AZURE_SEARCH_SERVICE")
    search_endpoint = f"https://{search_service}.search.windows.net"
    api_key = os.getenv("AZURE_SEARCH_KEY")

    print("=" * 80)
    print("INDEXER STATUS CHECK")
    print("=" * 80)
    print(f"Endpoint: {search_endpoint}\n")

    credential = AzureKeyCredential(api_key)
    client = SearchIndexerClient(endpoint=search_endpoint, credential=credential)

    try:
        # List all indexers
        indexers = client.get_indexers()
        indexer_list = list(indexers)

        if not indexer_list:
            print("[PROBLEM] No indexers found!")
            print("\nExplanation:")
            print("  Integrated vectorization requires an indexer to process documents.")
            print("  Your index has a vectorizer configured, but no indexer is running.")
            print("\nThis means:")
            print("  - Documents are uploaded with empty embeddings []")
            print("  - But no background process is generating embeddings")
            print("  - Vector search will never work without an indexer")
            print("\n[ROOT CAUSE IDENTIFIED]")
            print("  The index was created with integrated vectorizer configuration,")
            print("  but Azure Search needs an INDEXER + DATA SOURCE to trigger embedding generation.")
            print("\nSOLUTION:")
            print("  For integrated vectorization to work automatically, you need:")
            print("  1. A data source (blob storage, cosmos db, etc.)")
            print("  2. An indexer that reads from the data source")
            print("  3. The indexer processes documents and triggers vectorization")
            print("\nALTERNATIVE SOLUTION:")
            print("  Since you're uploading documents directly (not via indexer),")
            print("  you should use CLIENT-SIDE embeddings instead:")
            print("  1. Set AZURE_USE_INTEGRATED_VECTORIZATION=false in .env")
            print("  2. Re-run: python -m ingestor.cli --force-index")
            print("  3. Documents will be uploaded WITH embeddings already generated")
            return False

        print(f"Found {len(indexer_list)} indexer(s):\n")

        for indexer in indexer_list:
            print(f"Indexer: {indexer.name}")
            print(f"  Target Index: {indexer.target_index_name}")
            print(f"  Data Source: {indexer.data_source_name}")

            # Get indexer status
            try:
                status = client.get_indexer_status(indexer.name)
                print(f"  Status: {status.status}")

                if status.last_result:
                    print(f"  Last Run: {status.last_result.end_time}")
                    print(f"  Items Processed: {status.last_result.item_count}")
                    print(f"  Errors: {status.last_result.error_count}")

                    if status.last_result.errors:
                        print("\n  Errors:")
                        for error in status.last_result.errors[:5]:  # Show first 5 errors
                            print(f"    - {error.error_message}")

                if status.execution_history:
                    print(f"\n  Recent Executions: {len(status.execution_history)}")

            except Exception as e:
                print(f"  [ERROR] Could not get status: {e}")

            print()

        return True

    except Exception as e:
        print(f"[ERROR] Failed to check indexers: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    has_indexers = check_indexers()

    if not has_indexers:
        print("\n" + "=" * 80)
        print("RECOMMENDATION")
        print("=" * 80)
        print("\nYour setup: Direct document upload (no indexer)")
        print("Best approach: Use CLIENT-SIDE embeddings")
        print("\nRun these commands:")
        print("  1. Edit .env: Set AZURE_USE_INTEGRATED_VECTORIZATION=false")
        print("  2. python -m ingestor.cli --force-index")
        print("  3. Embeddings will be generated immediately during upload")
