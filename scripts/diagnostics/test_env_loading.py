"""Test script for environment file loading functionality in Gradio UI."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the functions we need to test
from src.ingestor.gradio_app import (
    list_env_files,
    get_env_file_display_name,
    load_env_file,
    get_active_env_file,
)


def test_list_env_files():
    """Test listing environment files."""
    print("Test 1: Listing environment files...")
    env_files = list_env_files()
    print(f"  Found {len(env_files)} env files")
    if env_files:
        print(f"  First few files:")
        for f in env_files[:5]:
            print(f"    - {get_env_file_display_name(f)}")
    print()


def test_load_env_file():
    """Test loading an environment file."""
    print("Test 2: Loading environment file...")

    # Get list of env files
    env_files = list_env_files()

    if not env_files:
        print("  ⚠️  No env files found to test")
        return

    # Try to load the first env file
    test_file = env_files[0]
    print(f"  Loading: {get_env_file_display_name(test_file)}")

    success, message = load_env_file(test_file)

    if success:
        print(f"  ✅ {message}")
        print(f"  Active env file: {get_active_env_file()}")
    else:
        print(f"  ❌ {message}")
    print()


def test_reload_default():
    """Test reloading default .env file."""
    print("Test 3: Reloading default .env...")

    success, message = load_env_file(None)

    if success:
        print(f"  ✅ {message}")
        print(f"  Active env file: {get_active_env_file()}")
    else:
        print(f"  ❌ {message}")
    print()


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Environment File Loading Functionality")
    print("=" * 60)
    print()

    try:
        test_list_env_files()
        test_load_env_file()
        test_reload_default()

        print("=" * 60)
        print("All tests completed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
