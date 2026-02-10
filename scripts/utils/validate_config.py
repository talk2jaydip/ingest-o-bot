"""Example: How to use the pipeline validator."""

import asyncio
import sys
from pathlib import Path

# Add project root to path (scripts/utils -> project root -> src)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from ingestor.config import PipelineConfig
from ingestor.validator import PipelineValidator


async def main():
    """Run validation example."""
    print("=" * 80)
    print("Pipeline Configuration Validator Example")
    print("=" * 80)
    print()

    try:
        # Load configuration from environment
        config = PipelineConfig.from_env()

        # Create validator
        validator = PipelineValidator(config)

        # Run all validations
        success = await validator.validate_all()

        if success:
            print()
            print("=" * 80)
            print("✅ SUCCESS: All validation checks passed!")
            print("=" * 80)
            print()
            print("Your pipeline is ready to run. You can now:")
            print("  - Process documents with: python -m ingestor.cli --glob 'path/*.pdf'")
            print("  - Set up the index with: python -m ingestor.cli --setup-index")
            print()
            return 0
        else:
            print()
            print("=" * 80)
            print("❌ FAILURE: Some validation checks failed")
            print("=" * 80)
            print()
            print("Please review the errors above and fix the configuration.")
            print("Check docs/guides/VALIDATION.md for detailed guidance on each error.")
            print()
            return 1

    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ ERROR: Validation failed with exception: {e}")
        print("=" * 80)
        print()
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
