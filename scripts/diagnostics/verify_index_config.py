"""Verify the index has integrated vectorizer configured."""
import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient

load_dotenv('.env')

def verify_index():
    """Check if index has vectorizer configured."""
    search_service = os.getenv("AZURE_SEARCH_SERVICE")
    search_endpoint = f"https://{search_service}.search.windows.net"
    index_name = os.getenv("AZURE_SEARCH_INDEX")
    api_key = os.getenv("AZURE_SEARCH_KEY")

    print("=" * 80)
    print("INDEX CONFIGURATION VERIFICATION")
    print("=" * 80)
    print(f"Index: {index_name}")
    print(f"Endpoint: {search_endpoint}\n")

    credential = AzureKeyCredential(api_key)
    client = SearchIndexClient(endpoint=search_endpoint, credential=credential)

    try:
        index = client.get_index(index_name)

        print("Vector Search Configuration:")
        print("-" * 80)

        if hasattr(index, 'vector_search') and index.vector_search:
            vs = index.vector_search

            # Check vectorizers
            if hasattr(vs, 'vectorizers') and vs.vectorizers:
                print(f"\n[OK] Vectorizers configured: {len(vs.vectorizers)}")
                for i, vectorizer in enumerate(vs.vectorizers):
                    print(f"  Vectorizer {i+1}:")
                    print(f"    Name: {vectorizer.vectorizer_name if hasattr(vectorizer, 'vectorizer_name') else vectorizer.name}")
                    print(f"    Type: {type(vectorizer).__name__}")
                    if hasattr(vectorizer, 'parameters'):
                        params = vectorizer.parameters
                        if hasattr(params, 'resource_url'):
                            print(f"    OpenAI Endpoint: {params.resource_url}")
                        if hasattr(params, 'deployment_name'):
                            print(f"    Deployment: {params.deployment_name}")
                        if hasattr(params, 'model_name'):
                            print(f"    Model: {params.model_name}")
            else:
                print("\n[PROBLEM] No vectorizers configured!")
                print("  The index is missing the AzureOpenAIVectorizer.")
                print("  This is why embeddings are not being generated.")

            # Check profiles
            if hasattr(vs, 'profiles') and vs.profiles:
                print(f"\n[OK] Vector profiles configured: {len(vs.profiles)}")
                for i, profile in enumerate(vs.profiles):
                    print(f"  Profile {i+1}:")
                    print(f"    Name: {profile.name}")
                    if hasattr(profile, 'vectorizer_name') and profile.vectorizer_name:
                        print(f"    Vectorizer: {profile.vectorizer_name} [INTEGRATED]")
                    else:
                        print(f"    Vectorizer: None [CLIENT-SIDE ONLY]")
                    if hasattr(profile, 'algorithm_configuration_name'):
                        print(f"    Algorithm: {profile.algorithm_configuration_name}")
                    if hasattr(profile, 'compression_name'):
                        print(f"    Compression: {profile.compression_name}")
            else:
                print("\n[WARNING] No vector profiles configured")

            # Check algorithms
            if hasattr(vs, 'algorithms') and vs.algorithms:
                print(f"\n[OK] Vector algorithms configured: {len(vs.algorithms)}")
        else:
            print("[ERROR] No vector search configuration found!")
            print("  The index doesn't have vector search enabled.")

        # Check embeddings field
        print("\n\nEmbeddings Field Configuration:")
        print("-" * 80)

        embeddings_field = None
        for field in index.fields:
            if field.name == "embeddings":
                embeddings_field = field
                break

        if embeddings_field:
            print("[OK] Embeddings field found")
            print(f"  Type: {embeddings_field.type}")
            print(f"  Searchable: {embeddings_field.searchable}")
            if hasattr(embeddings_field, 'vector_search_profile_name'):
                print(f"  Vector Profile: {embeddings_field.vector_search_profile_name}")
            if hasattr(embeddings_field, 'dimensions'):
                print(f"  Dimensions: {embeddings_field.dimensions}")
        else:
            print("[ERROR] Embeddings field not found!")

        # Final verdict
        print("\n" + "=" * 80)
        print("VERDICT:")
        print("=" * 80)

        has_vectorizer = (hasattr(index, 'vector_search') and
                         index.vector_search and
                         hasattr(index.vector_search, 'vectorizers') and
                         index.vector_search.vectorizers and
                         len(index.vector_search.vectorizers) > 0)

        if has_vectorizer:
            print("\n[SUCCESS] Index has integrated vectorizer configured!")
            print("  Azure Search WILL generate embeddings automatically.")
            print("  Wait 5-10 minutes for background processing to complete.")
        else:
            print("\n[PROBLEM] Index is MISSING integrated vectorizer!")
            print("  Azure Search CANNOT generate embeddings.")
            print("  The index needs to be recreated with vectorizer configuration.")
            print("\n  Run: python -m ingestor.cli --force-index")

    except Exception as e:
        print(f"[ERROR] Failed to get index: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_index()
