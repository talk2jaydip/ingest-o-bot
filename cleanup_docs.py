#!/usr/bin/env python3
"""
Documentation Cleanup Script
Removes files that violate the documentation policy per .claude/.claude.md
"""

import os
import sys
from pathlib import Path

# Files to remove (relative to project root)
FILES_TO_REMOVE = [
    # Root directory - Summary files (violate policy)
    "ENVIRONMENT_CONFIG_FIXES_SUMMARY.md",
    "ENVIRONMENT_CONFIGURATION_GUIDE.md",
    "ENVIRONMENT_QUICK_REFERENCE.md",
    "ENV_IMPROVEMENTS_SUMMARY.md",
    "IMPLEMENTATION_SUMMARY.md",
    "PLUGGABLE_ARCHITECTURE_SUMMARY.md",
    "TESTING_RESULTS.md",

    # Root directory - Temporary files
    "analyze_test_results.py",
    "benchmark_output.log",
    "test_output.log",
    "test2.log",
    "test_offline.log",
    "nul",

    # docs/ directory - Summary files
    "docs/CLI-TESTING-SUMMARY.md",
    "docs/cli-test-results.md",
    "docs/cli-test-execution-guide.md",
    "docs/architecture/ARCHITECTURE_UPDATE_SUMMARY.md",

    # examples/playbooks/ - Summary files
    "examples/playbooks/PLAYBOOKS_SUMMARY.md",
    "examples/playbooks/QUICK_REFERENCE.md",
]

def main():
    project_root = Path(__file__).parent
    removed_count = 0
    not_found_count = 0

    print("Documentation Cleanup Script")
    print("=" * 60)
    print(f"Project root: {project_root}")
    print(f"Files to remove: {len(FILES_TO_REMOVE)}")
    print()

    for file_path in FILES_TO_REMOVE:
        full_path = project_root / file_path

        if full_path.exists():
            try:
                full_path.unlink()
                print(f"✓ Removed: {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"✗ Error removing {file_path}: {e}")
        else:
            print(f"○ Not found: {file_path}")
            not_found_count += 1

    print()
    print("=" * 60)
    print(f"Summary:")
    print(f"  Removed: {removed_count} files")
    print(f"  Not found: {not_found_count} files")
    print(f"  Total processed: {len(FILES_TO_REMOVE)} files")

    return 0

if __name__ == "__main__":
    sys.exit(main())
