"""Index management operations: create, validate, backup, delete."""

import os
from ingestor import IndexDeploymentManager


def main():
    """Demonstrate index management operations."""
    print("🔧 Azure AI Search Index Management")
    print("=" * 60)

    # Get credentials from environment
    search_service = os.getenv("AZURE_SEARCH_SERVICE")
    search_key = os.getenv("AZURE_SEARCH_KEY")
    index_name = os.getenv("AZURE_SEARCH_INDEX", "documents-index")

    if not search_service or not search_key:
        print("❌ Error: AZURE_SEARCH_SERVICE and AZURE_SEARCH_KEY required")
        print("   Set these in your .env file")
        return 1

    # Build endpoint
    endpoint = f"https://{search_service}.search.windows.net"

    # Create manager
    manager = IndexDeploymentManager(
        endpoint=endpoint,
        api_key=search_key,
        index_name=index_name,
        verbose=True
    )

    print(f"\n📊 Index: {index_name}")
    print(f"🔗 Service: {search_service}")
    print()

    # Menu
    while True:
        print("\n" + "=" * 60)
        print("Choose an operation:")
        print("=" * 60)
        print("1. Check if index exists")
        print("2. Validate index configuration")
        print("3. Backup index")
        print("4. Deploy/update index")
        print("5. Deploy index (force recreate)")
        print("6. Delete index")
        print("0. Exit")
        print("=" * 60)

        choice = input("\nEnter choice (0-6): ").strip()

        if choice == "0":
            print("\n👋 Goodbye!")
            break

        elif choice == "1":
            # Check existence
            print("\n🔍 Checking if index exists...")
            exists = manager.index_exists()
            if exists:
                print(f"✅ Index '{index_name}' exists")
            else:
                print(f"ℹ️  Index '{index_name}' does not exist")

        elif choice == "2":
            # Validate
            print("\n🔍 Validating index configuration...")
            if not manager.index_exists():
                print(f"❌ Index '{index_name}' does not exist")
                continue

            success = manager.validate_index()
            if success:
                print("\n✅ Index validation passed!")
            else:
                print("\n⚠️  Index validation found issues")

        elif choice == "3":
            # Backup
            print("\n📦 Creating index backup...")
            backup_file = manager.backup_current_index()
            if backup_file:
                print(f"\n✅ Backup saved: {backup_file}")
            else:
                print("\n❌ Backup failed")

        elif choice == "4":
            # Deploy (update)
            print("\n🚀 Deploying index (update mode)...")
            print("   This will create the index if it doesn't exist")
            print("   or update it if it does (without deleting data)")
            confirm = input("\nProceed? (y/n): ").strip().lower()

            if confirm == "y":
                try:
                    success = manager.deploy_index(
                        force=False,
                        dry_run=False,
                        skip_if_exists=True
                    )
                    if success:
                        print("\n✅ Index deployment successful!")
                    else:
                        print("\n❌ Index deployment failed")
                except Exception as e:
                    print(f"\n❌ Error: {e}")

        elif choice == "5":
            # Deploy (force)
            print("\n⚠️  WARNING: Force recreate will DELETE all data!")
            print("   This will:")
            print("   1. Backup current index (if exists)")
            print("   2. Delete existing index")
            print("   3. Create fresh index")
            confirm = input("\nAre you sure? Type 'yes' to proceed: ").strip().lower()

            if confirm == "yes":
                try:
                    success = manager.deploy_index(
                        force=True,
                        dry_run=False,
                        skip_if_exists=False
                    )
                    if success:
                        print("\n✅ Index recreated successfully!")
                    else:
                        print("\n❌ Index recreation failed")
                except Exception as e:
                    print(f"\n❌ Error: {e}")
            else:
                print("\n❌ Operation cancelled")

        elif choice == "6":
            # Delete
            print("\n⚠️  WARNING: This will delete the index and ALL data!")
            confirm = input("\nType 'yes' to confirm deletion: ").strip().lower()

            if confirm == "yes":
                print("\n🗑️  Deleting index...")
                success = manager.delete_index()
                if success:
                    print(f"\n✅ Index '{index_name}' deleted")
                else:
                    print(f"\n❌ Failed to delete index")
            else:
                print("\n❌ Deletion cancelled")

        else:
            print("\n❌ Invalid choice. Please enter 0-6.")

    return 0


if __name__ == "__main__":
    exit(main())
