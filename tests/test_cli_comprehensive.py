#!/usr/bin/env python3
"""Comprehensive CLI test runner for ingest-o-bot.

This script tests all CLI options and combinations, recording results
for regression testing and validation.

Usage:
    python tests/test_cli_comprehensive.py [--env .env.test] [--output results.json]
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Test categories and scenarios
TEST_SCENARIOS = {
    "validation": {
        "V01": {
            "args": ["--validate"],
            "desc": "Basic validation",
            "expected_exit": 0,
            "destructive": False
        },
        "V02": {
            "args": ["--validate", "--verbose"],
            "desc": "Validation with verbose logging",
            "expected_exit": 0,
            "destructive": False
        },
        "V03": {
            "args": ["--validate", "--env", "missing.env"],
            "desc": "Validation with missing env file",
            "expected_exit": [0, 1],  # May pass or fail depending on system env
            "destructive": False
        },
        "V04": {
            "args": ["--pre-check"],
            "desc": "Pre-check alias for validate",
            "expected_exit": 0,
            "destructive": False
        },
    },
    "index_management": {
        "I01": {
            "args": ["--check-index"],
            "desc": "Check if index exists",
            "expected_exit": [0, 1],  # 0 if exists, 1 if not
            "destructive": False
        },
        "I02": {
            "args": ["--setup-index"],
            "desc": "Setup index without ingestion",
            "expected_exit": 0,
            "destructive": False
        },
        "I03": {
            "args": ["--index-only"],
            "desc": "Deploy index and exit",
            "expected_exit": 0,
            "destructive": False
        },
        "I04": {
            "args": ["--delete-index"],
            "desc": "Delete index (DESTRUCTIVE)",
            "expected_exit": 0,
            "destructive": True,
            "skip_by_default": True
        },
        "I05": {
            "args": ["--force-index"],
            "desc": "Force recreate index (DESTRUCTIVE)",
            "expected_exit": 0,
            "destructive": True,
            "skip_by_default": True
        },
    },
    "logging": {
        "L01": {
            "args": ["--verbose", "--check-index"],
            "desc": "Verbose logging",
            "expected_exit": [0, 1],
            "destructive": False
        },
        "L02": {
            "args": ["--no-colors", "--check-index"],
            "desc": "No colored output",
            "expected_exit": [0, 1],
            "destructive": False
        },
        "L03": {
            "args": ["--verbose", "--no-colors", "--check-index"],
            "desc": "Verbose without colors",
            "expected_exit": [0, 1],
            "destructive": False
        },
    },
    "error_handling": {
        "ERR01": {
            "args": ["--action", "invalid"],
            "desc": "Invalid action value",
            "expected_exit": 2,  # argparse error
            "destructive": False,
            "expect_error": True
        },
    },
}


class TestResult:
    """Container for test execution results."""

    def __init__(
        self,
        test_id: str,
        category: str,
        description: str,
        command: List[str],
        exit_code: int,
        expected_exit: int,
        stdout: str,
        stderr: str,
        duration: float,
        timestamp: str
    ):
        self.test_id = test_id
        self.category = category
        self.description = description
        self.command = command
        self.exit_code = exit_code
        self.expected_exit = expected_exit
        self.stdout = stdout
        self.stderr = stderr
        self.duration = duration
        self.timestamp = timestamp
        self.status = self._determine_status()

    def _determine_status(self) -> str:
        """Determine if test passed based on exit code."""
        if isinstance(self.expected_exit, list):
            return "PASS" if self.exit_code in self.expected_exit else "FAIL"
        return "PASS" if self.exit_code == self.expected_exit else "FAIL"

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "test_id": self.test_id,
            "category": self.category,
            "description": self.description,
            "command": " ".join(self.command),
            "exit_code": self.exit_code,
            "expected_exit": self.expected_exit,
            "status": self.status,
            "duration_seconds": round(self.duration, 2),
            "timestamp": self.timestamp,
            "stdout_lines": len(self.stdout.splitlines()),
            "stderr_lines": len(self.stderr.splitlines()),
            "stdout_preview": self.stdout[:500] if self.stdout else "",
            "stderr_preview": self.stderr[:500] if self.stderr else "",
        }


class CLITestRunner:
    """Automated CLI test execution and reporting."""

    def __init__(self, env_file: Optional[str] = None, skip_destructive: bool = True):
        self.env_file = env_file
        self.skip_destructive = skip_destructive
        self.results: List[TestResult] = []
        self.project_root = Path(__file__).parent.parent

    def run_test(
        self,
        test_id: str,
        category: str,
        test_spec: Dict
    ) -> TestResult:
        """Execute a single CLI test."""
        args = test_spec["args"].copy()

        # Add env file if specified
        if self.env_file and "--env" not in args:
            args = ["--env", self.env_file] + args

        # Build command
        cmd = [sys.executable, "-m", "ingestor.cli"] + args

        print(f"  Running {test_id}: {test_spec['desc']}...", end=" ", flush=True)

        start_time = time.time()
        timestamp = datetime.now().isoformat()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.project_root)
            )

            duration = time.time() - start_time

            test_result = TestResult(
                test_id=test_id,
                category=category,
                description=test_spec["desc"],
                command=cmd,
                exit_code=result.returncode,
                expected_exit=test_spec["expected_exit"],
                stdout=result.stdout,
                stderr=result.stderr,
                duration=duration,
                timestamp=timestamp
            )

            status_symbol = "✅" if test_result.status == "PASS" else "❌"
            print(f"{status_symbol} {test_result.status} (exit: {result.returncode}, {duration:.2f}s)")

            return test_result

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print("⏱️ TIMEOUT (60s)")
            return TestResult(
                test_id=test_id,
                category=category,
                description=test_spec["desc"],
                command=cmd,
                exit_code=-1,
                expected_exit=test_spec["expected_exit"],
                stdout="",
                stderr="Test timed out after 60 seconds",
                duration=duration,
                timestamp=timestamp
            )

        except Exception as e:
            duration = time.time() - start_time
            print(f"💥 ERROR: {e}")
            return TestResult(
                test_id=test_id,
                category=category,
                description=test_spec["desc"],
                command=cmd,
                exit_code=-1,
                expected_exit=test_spec["expected_exit"],
                stdout="",
                stderr=f"Exception during test execution: {e}",
                duration=duration,
                timestamp=timestamp
            )

    def run_all_tests(self):
        """Execute all test scenarios."""
        print("=" * 70)
        print("CLI Comprehensive Test Suite")
        print("=" * 70)
        print(f"Project root: {self.project_root}")
        print(f"Environment file: {self.env_file or 'default (.env)'}")
        print(f"Skip destructive: {self.skip_destructive}")
        print("=" * 70)
        print()

        total_tests = 0
        skipped_tests = 0

        for category, tests in TEST_SCENARIOS.items():
            print(f"\n📁 Category: {category.replace('_', ' ').title()}")
            print("-" * 70)

            for test_id, test_spec in tests.items():
                total_tests += 1

                # Skip destructive tests if requested
                if self.skip_destructive and test_spec.get("skip_by_default", False):
                    print(f"  Skipping {test_id}: {test_spec['desc']} (destructive)")
                    skipped_tests += 1
                    continue

                result = self.run_test(test_id, category, test_spec)
                self.results.append(result)

        return total_tests, skipped_tests

    def generate_summary(self) -> Dict:
        """Generate test execution summary."""
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        total = len(self.results)
        total_duration = sum(r.duration for r in self.results)

        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round((passed / total * 100) if total > 0 else 0, 2),
            "total_duration_seconds": round(total_duration, 2),
            "timestamp": datetime.now().isoformat(),
        }

    def save_results(self, output_file: str):
        """Save test results to JSON file."""
        data = {
            "summary": self.generate_summary(),
            "test_results": [r.to_dict() for r in self.results],
            "environment": {
                "env_file": self.env_file,
                "skip_destructive": self.skip_destructive,
                "project_root": str(self.project_root),
            }
        }

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Results saved to: {output_path}")

    def print_summary(self):
        """Print test execution summary to console."""
        summary = self.generate_summary()

        print("\n" + "=" * 70)
        print("TEST EXECUTION SUMMARY")
        print("=" * 70)
        print(f"Total tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✅")
        print(f"Failed: {summary['failed']} ❌")
        print(f"Pass rate: {summary['pass_rate']}%")
        print(f"Total duration: {summary['total_duration_seconds']}s")
        print("=" * 70)

        # Print failed tests if any
        failed_tests = [r for r in self.results if r.status == "FAIL"]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for result in failed_tests:
                print(f"  {result.test_id}: {result.description}")
                print(f"    Expected exit: {result.expected_exit}, Got: {result.exit_code}")
                if result.stderr:
                    print(f"    Error: {result.stderr[:200]}")


def main():
    """Main entry point for CLI test runner."""
    parser = argparse.ArgumentParser(
        description="Comprehensive CLI test runner for ingest-o-bot"
    )
    parser.add_argument(
        "--env",
        type=str,
        help="Environment file to use for testing"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="test-results/cli-test-results.json",
        help="Output file for test results (JSON)"
    )
    parser.add_argument(
        "--include-destructive",
        action="store_true",
        help="Include destructive tests (WARNING: will delete data)"
    )

    args = parser.parse_args()

    # Create and run test runner
    runner = CLITestRunner(
        env_file=args.env,
        skip_destructive=not args.include_destructive
    )

    try:
        total_tests, skipped_tests = runner.run_all_tests()

        # Print and save results
        runner.print_summary()
        runner.save_results(args.output)

        # Exit with appropriate code
        failed = sum(1 for r in runner.results if r.status == "FAIL")
        sys.exit(0 if failed == 0 else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n💥 Fatal error during test execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
