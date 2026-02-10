#!/usr/bin/env python3
"""
Environment Scenario Switcher

Helper script to switch between different environment configurations.
"""

import argparse
import shutil
from pathlib import Path
from typing import List, Dict

REPO_ROOT = Path(__file__).parent.parent
ENVS_DIR = REPO_ROOT / "envs"
ENV_FILE = REPO_ROOT / ".env"

# Scenario definitions
SCENARIOS: Dict[str, Dict[str, str]] = {
    "1": {
        "name": "Local Development",
        "file": "env.scenario1-local-dev.example",
        "pattern": "Local Input → Local Artifacts",
        "description": "Development, debugging, testing without cloud costs",
        "use_case": "Developers working on features locally"
    },
    "2": {
        "name": "Production Deployment",
        "file": "env.scenario2-blob-prod.example",
        "pattern": "Blob Input → Blob Artifacts",
        "description": "Production deployment with Azure Blob Storage",
        "use_case": "Production environments, scheduled processing"
    },
    "3": {
        "name": "Hybrid Testing",
        "file": "env.scenario3-local-to-blob.example",
        "pattern": "Local Input → Blob Artifacts",
        "description": "Test locally with production-like storage",
        "use_case": "Integration testing, CI/CD, team collaboration"
    },
    "4": {
        "name": "Production Debug",
        "file": "env.scenario4-blob-to-local.example",
        "pattern": "Blob Input → Local Artifacts",
        "description": "Debug production files locally",
        "use_case": "Troubleshooting production issues, QA validation"
    },
    "5": {
        "name": "Fully Offline",
        "file": "env.scenario5-offline.example",
        "pattern": "Local Input → Local Artifacts (No Azure)",
        "description": "Air-gapped environment, no Azure services",
        "use_case": "Secure environments, development without Azure"
    }
}


def list_scenarios() -> None:
    """List all available scenarios."""
    print("\nAvailable Environment Scenarios:")
    print("=" * 70)

    for key, scenario in SCENARIOS.items():
        print(f"\n[{key}] {scenario['name']}")
        print(f"    Pattern: {scenario['pattern']}")
        print(f"    Description: {scenario['description']}")
        print(f"    Use Case: {scenario['use_case']}")
        print(f"    File: {scenario['file']}")

    print("\n" + "=" * 70)


def backup_current_env() -> bool:
    """Backup current .env file if it exists."""
    if ENV_FILE.exists():
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = REPO_ROOT / f".env.backup_{timestamp}"

        print(f"Backing up current .env to: {backup_file.name}")
        shutil.copy(ENV_FILE, backup_file)
        return True
    return False


def switch_scenario(scenario_key: str, no_backup: bool = False) -> bool:
    """Switch to specified scenario."""
    if scenario_key not in SCENARIOS:
        print(f"Error: Invalid scenario '{scenario_key}'")
        print("Valid scenarios: " + ", ".join(SCENARIOS.keys()))
        return False

    scenario = SCENARIOS[scenario_key]
    source_file = ENVS_DIR / scenario["file"]

    if not source_file.exists():
        print(f"Error: Scenario file not found: {source_file}")
        return False

    # Backup current .env if exists
    if not no_backup:
        backup_current_env()

    # Copy scenario to .env
    print(f"\nSwitching to Scenario {scenario_key}: {scenario['name']}")
    print(f"Pattern: {scenario['pattern']}")
    shutil.copy(source_file, ENV_FILE)

    print(f"\n✓ .env file updated from: {scenario['file']}")
    print("\n" + "=" * 70)
    print("IMPORTANT: Edit .env with your real credentials!")
    print("=" * 70)
    print("\nPlaceholders to replace:")
    print("  - your-tenant-id-here")
    print("  - your-client-id-here")
    print("  - your-client-secret-here")
    print("  - your-search-service")
    print("  - your-search-key-here")
    print("  - your-openai-key-here")
    print("  - your-storage-account")
    print("  - your-storage-key-here")
    print("\nEdit .env: nano .env  (or your preferred editor)")
    print("\nThen test: ingestor --help")

    return True


def interactive_switch() -> None:
    """Interactive scenario selection."""
    list_scenarios()

    print("\nWhich scenario do you want to use?")
    choice = input("Enter scenario number (1-5) or 'q' to quit: ").strip()

    if choice.lower() == 'q':
        print("Cancelled.")
        return

    if choice not in SCENARIOS:
        print(f"Invalid choice: {choice}")
        return

    # Confirm
    scenario = SCENARIOS[choice]
    print(f"\nYou selected: [{choice}] {scenario['name']}")
    print(f"Pattern: {scenario['pattern']}")

    if ENV_FILE.exists():
        confirm = input("\n.env file exists. Create backup? (Y/n): ").strip().lower()
        no_backup = confirm == 'n'
    else:
        no_backup = True

    confirm = input("\nProceed with switch? (Y/n): ").strip().lower()
    if confirm in ('', 'y', 'yes'):
        switch_scenario(choice, no_backup)
    else:
        print("Cancelled.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Switch between environment configuration scenarios",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python scripts/switch_env.py

  # Direct switch to scenario
  python scripts/switch_env.py --scenario 2

  # List available scenarios
  python scripts/switch_env.py --list

  # Switch without backup
  python scripts/switch_env.py --scenario 1 --no-backup
        """
    )

    parser.add_argument(
        "--scenario", "-s",
        choices=list(SCENARIOS.keys()),
        help="Scenario number to switch to (1-5)"
    )

    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available scenarios"
    )

    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Don't backup current .env file"
    )

    args = parser.parse_args()

    # List scenarios
    if args.list:
        list_scenarios()
        return

    # Direct switch
    if args.scenario:
        switch_scenario(args.scenario, args.no_backup)
        return

    # Interactive mode
    interactive_switch()


if __name__ == "__main__":
    main()
