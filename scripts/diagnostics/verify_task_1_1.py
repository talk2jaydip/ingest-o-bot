"""Verification script for Task 1.1: --env-file support in Gradio UI.

This script checks that all required components are present.
"""

import re
from pathlib import Path

def check_implementation():
    """Check that Task 1.1 requirements are met."""

    gradio_file = Path("src/ingestor/gradio_app.py")

    if not gradio_file.exists():
        print("❌ gradio_app.py not found!")
        return False

    content = gradio_file.read_text(encoding='utf-8')

    checks = {
        "Environment Configuration section": r'# Environment Configuration Section|Environment Configuration',
        "list_env_files function": r'def list_env_files\(\)',
        "load_env_file function": r'def load_env_file\(',
        "get_active_env_file function": r'def get_active_env_file\(\)',
        "save_uploaded_env_file function": r'def save_uploaded_env_file\(',
        "env_file_dropdown": r'env_file_dropdown',
        "env_file_upload": r'env_file_upload',
        "env_load_button": r'env_load_button',
        "env_reload_button": r'env_reload_button',
        "env_refresh_button": r'env_refresh_button',
        "env_status_display": r'env_status_display',
        "Auto-validate checkbox": r'auto_validate_checkbox',
        "validate_configuration function": r'def validate_configuration\(',
        "handle_env_file_selection": r'def handle_env_file_selection\(',
        "handle_env_file_upload": r'def handle_env_file_upload\(',
        "handle_env_reload": r'def handle_env_reload\(',
        "handle_env_refresh": r'def handle_env_refresh\(',
        "Active Environment tracking": r'_active_env_file',
        "dotenv import": r'from dotenv import load_dotenv',
        "scenario_validator import": r'from ingestor.scenario_validator import',
    }

    print("=" * 70)
    print("Task 1.1 Implementation Verification")
    print("=" * 70)
    print()

    all_passed = True

    for check_name, pattern in checks.items():
        if re.search(pattern, content):
            print(f"✅ {check_name}")
        else:
            print(f"❌ {check_name}")
            all_passed = False

    print()
    print("=" * 70)

    # Additional feature checks
    print("\n📋 Feature Checklist:")
    print()

    features = [
        ("Environment File Selection dropdown", r'Select Environment File'),
        ("Custom .env file upload", r'Upload Custom .env File|file_types=\[".env"\]'),
        ("Load Selected Environment button", r'Load Selected Environment'),
        ("Reload Current button", r'Reload Current'),
        ("Refresh File List button", r'Refresh File List'),
        ("Active Environment display", r'Active Environment'),
        ("Auto-validation on env change", r'Auto-validate on env file change'),
        ("Validation button", r'Validate Configuration'),
        ("Validation results display", r'validation_results|Validation Results'),
        ("Error handling in load functions", r'try:.*except Exception'),
    ]

    for feature_name, pattern in features:
        if re.search(pattern, content, re.DOTALL):
            print(f"✅ {feature_name}")
        else:
            print(f"⚠️  {feature_name} - May need review")

    print()
    print("=" * 70)

    if all_passed:
        print("✅ All core components are present!")
    else:
        print("⚠️  Some components may be missing or need review")

    print()

    # Check for envs directory
    envs_dir = Path("envs")
    if envs_dir.exists() and envs_dir.is_dir():
        env_files = list(envs_dir.glob("*.env*"))
        print(f"✅ envs/ directory exists with {len(env_files)} .env files")
        if env_files:
            print(f"   Sample files:")
            for f in sorted(env_files)[:5]:
                print(f"   - {f.name}")
    else:
        print("⚠️  envs/ directory not found (expected for env file selection)")

    print()
    print("=" * 70)
    print("Verification Complete!")
    print("=" * 70)

    return all_passed


if __name__ == "__main__":
    check_implementation()
