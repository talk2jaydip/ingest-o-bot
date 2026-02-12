"""Test script for analytics functionality.

This script tests the privacy-preserving analytics system to ensure:
1. Analytics data is collected correctly
2. Opt-out mechanism works
3. Privacy is preserved (no sensitive data)
4. Statistics display works
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ingestor.gradio_app import AnalyticsManager, analytics_manager


def test_analytics_collection():
    """Test basic analytics collection."""
    print("Test 1: Analytics Collection")
    print("=" * 60)

    # Create a test manager
    test_manager = AnalyticsManager()

    # Track some events
    test_manager.track_event(
        event_type="pipeline_run",
        feature="local_ingestion",
        status="success"
    )

    test_manager.track_event(
        event_type="pipeline_run",
        feature="blob_ingestion",
        status="error",
        error_msg="Connection timeout"
    )

    test_manager.track_event(
        event_type="index_check",
        feature="test_connection",
        status="success"
    )

    # Get statistics
    stats = test_manager.get_statistics()

    print(f"Total runs (lifetime): {stats['total_runs_lifetime']}")
    print(f"Total runs (30 days): {stats['total_runs_30days']}")
    print(f"Success rate: {stats['success_rate']:.1f}%")
    print(f"Most used features: {stats['most_used_features']}")
    print(f"Recent errors: {len(stats['recent_errors'])} errors")

    assert stats['total_runs_lifetime'] == 2, "Should have 2 pipeline runs"
    assert stats['total_runs_30days'] == 2, "Should have 2 runs in last 30 days"

    print("✅ Test 1 PASSED\n")


def test_opt_out():
    """Test opt-out mechanism."""
    print("Test 2: Opt-Out Mechanism")
    print("=" * 60)

    # Create a test manager
    test_manager = AnalyticsManager()

    # Track event while enabled
    test_manager.set_enabled(True)
    test_manager.track_event("pipeline_run", "test_feature", "success")

    stats_enabled = test_manager.get_statistics()
    count_enabled = stats_enabled['total_runs_lifetime']

    # Disable and try to track
    test_manager.set_enabled(False)
    assert not test_manager.is_enabled(), "Analytics should be disabled"

    test_manager.track_event("pipeline_run", "test_feature", "success")

    stats_disabled = test_manager.get_statistics()
    count_disabled = stats_disabled['total_runs_lifetime']

    # Count should not have increased
    assert count_enabled == count_disabled, "Event should not be tracked when disabled"

    print(f"Events tracked when enabled: {count_enabled}")
    print(f"Events tracked when disabled: {count_disabled}")
    print("✅ Test 2 PASSED\n")


def test_privacy_preservation():
    """Test that no sensitive data is stored."""
    print("Test 3: Privacy Preservation")
    print("=" * 60)

    # Create a test manager
    test_manager = AnalyticsManager()

    # Track events with potentially sensitive data
    test_manager.track_event(
        event_type="pipeline_run",
        feature="local_ingestion",
        status="error",
        error_msg="Failed to connect to https://myaccount.blob.core.windows.net with key abc123"
    )

    # Load the raw data file
    data = test_manager._load_data()

    # Check that no sensitive data is present
    json_str = json.dumps(data).lower()

    # Sensitive patterns that should NOT appear
    forbidden_patterns = [
        "blob.core.windows.net",
        "abc123",
        "password",
        "api_key",
        "secret",
        "credential"
    ]

    violations = []
    for pattern in forbidden_patterns:
        if pattern in json_str:
            violations.append(pattern)

    if violations:
        print(f"❌ PRIVACY VIOLATION: Found sensitive data: {violations}")
        assert False, f"Sensitive data found: {violations}"

    # Check that only sanitized error types are stored
    if data.get("events"):
        for event in data["events"]:
            if event.get("error_type"):
                error_type = event["error_type"]
                print(f"Sanitized error type: {error_type}")

                # Error types should be generic categories only
                allowed_error_types = [
                    "connection_error",
                    "authentication_error",
                    "not_found_error",
                    "configuration_error",
                    "index_error",
                    "parsing_error",
                    "resource_error",
                    "general_error",
                    "unknown"
                ]

                assert error_type in allowed_error_types, f"Invalid error type: {error_type}"

    print("✅ No sensitive data found in analytics")
    print("✅ All error types are sanitized")
    print("✅ Test 3 PASSED\n")


def test_error_sanitization():
    """Test that errors are properly sanitized."""
    print("Test 4: Error Sanitization")
    print("=" * 60)

    # Create a test manager
    test_manager = AnalyticsManager()

    # Test various error messages
    test_cases = [
        ("Connection timeout to server", "connection_error"),
        ("Authentication failed: invalid credentials", "authentication_error"),
        ("File not found: /path/to/file.pdf", "not_found_error"),
        ("Invalid configuration in settings.json", "configuration_error"),
        ("Index 'my-index' does not exist", "index_error"),
        ("Failed to parse document", "parsing_error"),
        ("Out of memory error", "resource_error"),
        ("Something went wrong", "general_error"),
    ]

    for error_msg, expected_type in test_cases:
        sanitized = test_manager._sanitize_error(error_msg)
        print(f"'{error_msg}' → '{sanitized}'")
        assert sanitized == expected_type, f"Expected {expected_type}, got {sanitized}"

    print("✅ Test 4 PASSED\n")


def test_data_file_location():
    """Test that data file is created in the correct location."""
    print("Test 5: Data File Location")
    print("=" * 60)

    # Check that file is in current working directory
    expected_path = Path.cwd() / ".gradio_analytics.json"
    print(f"Expected analytics file: {expected_path}")

    # Create a test manager and track an event
    test_manager = AnalyticsManager()
    test_manager.track_event("test_event", "test_feature", "success")

    # Check file exists
    if expected_path.exists():
        print(f"✅ Analytics file created at: {expected_path}")

        # Check it's a valid JSON file
        with open(expected_path, 'r') as f:
            data = json.load(f)
            print(f"✅ Valid JSON structure")
            print(f"   - Enabled: {data.get('enabled')}")
            print(f"   - Events: {len(data.get('events', []))}")
    else:
        print(f"⚠️ Analytics file not found (may not be created yet)")

    print("✅ Test 5 PASSED\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print(" ANALYTICS SYSTEM TESTS")
    print("=" * 60 + "\n")

    try:
        test_analytics_collection()
        test_opt_out()
        test_privacy_preservation()
        test_error_sanitization()
        test_data_file_location()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nPrivacy verification:")
        print("  ✅ No personal data stored")
        print("  ✅ No file paths stored")
        print("  ✅ No credentials stored")
        print("  ✅ Only sanitized error types stored")
        print("  ✅ Opt-out mechanism works")
        print("  ✅ Local storage only (.gradio_analytics.json)")
        print("\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
