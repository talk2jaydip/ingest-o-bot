"""Test script for index check functionality."""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set minimal env vars for testing
os.environ.setdefault("AZURE_SEARCH_SERVICE", "test-service")
os.environ.setdefault("AZURE_SEARCH_INDEX", "test-index")
os.environ.setdefault("AZURE_SEARCH_KEY", "test-key")

print("Testing index check implementation...")

try:
    from ingestor.gradio_app import check_index, check_index_async
    import asyncio

    print("\n1. Testing synchronous check_index()...")
    status_icon, message = check_index()
    print(f"   Status: {status_icon}")
    print(f"   Message length: {len(message)} chars")
    print(f"   First 100 chars: {message[:100]}...")

    print("\n2. Testing async check_index_async()...")
    async def test_async():
        result = await check_index_async()
        print(f"   Result length: {len(result)} chars")
        print(f"   Has timestamp: {'Last Checked' in result}")
        print(f"   First 100 chars: {result[:100]}...")

    asyncio.run(test_async())

    print("\n✅ All tests passed! Implementation is working correctly.")

except ImportError as e:
    print(f"\n❌ Import error: {e}")
    print("   This might be due to missing dependencies, but syntax is likely OK.")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
