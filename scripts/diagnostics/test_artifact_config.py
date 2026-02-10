#!/usr/bin/env python3
"""
Test script to demonstrate the simplified artifact storage configuration.

This script shows how artifacts mode is determined based on different env var combinations.
"""

import os
import sys
sys.path.insert(0, 'src')

from ingestor.config import InputMode, ArtifactsMode, ArtifactsConfig


def test_scenario(name: str, env_vars: dict, expected_mode: ArtifactsMode):
    """Test a configuration scenario."""
    print(f"\n{'=' * 70}")
    print(f"Scenario: {name}")
    print(f"{'=' * 70}")

    # Backup and set env vars
    backup = {}
    for key in ['AZURE_ARTIFACTS_DIR', 'AZURE_ARTIFACTS_MODE', 'AZURE_STORE_ARTIFACTS_TO_BLOB']:
        backup[key] = os.environ.get(key)
        if key in os.environ:
            del os.environ[key]

    for key, value in env_vars.items():
        if value is not None:
            os.environ[key] = value
            print(f"  {key}={value}")
        else:
            print(f"  {key}=<not set>")

    # Test the configuration
    input_mode = InputMode(env_vars.get('INPUT_MODE', 'local'))
    config = ArtifactsConfig.from_env(input_mode=input_mode)

    print(f"\n  Result: Artifacts mode = {config.mode.value}")

    if config.mode == expected_mode:
        print(f"  ✓ PASS: Got expected mode '{expected_mode.value}'")
    else:
        print(f"  ✗ FAIL: Expected '{expected_mode.value}', got '{config.mode.value}'")

    # Restore env vars
    for key, value in backup.items():
        if value is not None:
            os.environ[key] = value
        elif key in os.environ:
            del os.environ[key]

    return config.mode == expected_mode


def main():
    """Run all test scenarios."""
    print("=" * 70)
    print("ARTIFACT STORAGE CONFIGURATION TESTS")
    print("=" * 70)

    results = []

    # Scenario 1: Local input → local artifacts (default)
    results.append(test_scenario(
        "Local Input → Local Artifacts (Default)",
        {
            'INPUT_MODE': 'local',
        },
        ArtifactsMode.LOCAL
    ))

    # Scenario 2: Blob input → blob artifacts (automatic)
    results.append(test_scenario(
        "Blob Input → Blob Artifacts (Automatic)",
        {
            'INPUT_MODE': 'blob',
        },
        ArtifactsMode.BLOB
    ))

    # Scenario 3: Blob input with AZURE_ARTIFACTS_DIR override → local
    results.append(test_scenario(
        "Blob Input + AZURE_ARTIFACTS_DIR Override → Local (Debug)",
        {
            'INPUT_MODE': 'blob',
            'AZURE_ARTIFACTS_DIR': './debug_artifacts',
        },
        ArtifactsMode.LOCAL
    ))

    # Scenario 4: Local input with deprecated AZURE_STORE_ARTIFACTS_TO_BLOB flag
    results.append(test_scenario(
        "Local Input + AZURE_STORE_ARTIFACTS_TO_BLOB=true → Blob (Deprecated)",
        {
            'INPUT_MODE': 'local',
            'AZURE_STORE_ARTIFACTS_TO_BLOB': 'true',
        },
        ArtifactsMode.BLOB
    ))

    # Scenario 5: AZURE_ARTIFACTS_DIR overrides everything
    results.append(test_scenario(
        "AZURE_ARTIFACTS_DIR Overrides Everything → Local",
        {
            'INPUT_MODE': 'blob',
            'AZURE_ARTIFACTS_DIR': './override',
            'AZURE_STORE_ARTIFACTS_TO_BLOB': 'true',
        },
        ArtifactsMode.LOCAL
    ))

    # Summary
    print(f"\n{'=' * 70}")
    print(f"SUMMARY")
    print(f"{'=' * 70}")
    passed = sum(results)
    total = len(results)
    print(f"  Passed: {passed}/{total}")
    print(f"  Failed: {total - passed}/{total}")

    if passed == total:
        print(f"\n  ✓ All tests passed!")
        return 0
    else:
        print(f"\n  ✗ Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
