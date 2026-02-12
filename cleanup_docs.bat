@echo off
echo Documentation Cleanup Script
echo ============================================================
echo Project root: %CD%
echo.

REM Root directory - Summary files
if exist "ENVIRONMENT_CONFIG_FIXES_SUMMARY.md" (
    del "ENVIRONMENT_CONFIG_FIXES_SUMMARY.md"
    echo [REMOVED] ENVIRONMENT_CONFIG_FIXES_SUMMARY.md
)
if exist "ENVIRONMENT_CONFIGURATION_GUIDE.md" (
    del "ENVIRONMENT_CONFIGURATION_GUIDE.md"
    echo [REMOVED] ENVIRONMENT_CONFIGURATION_GUIDE.md
)
if exist "ENVIRONMENT_QUICK_REFERENCE.md" (
    del "ENVIRONMENT_QUICK_REFERENCE.md"
    echo [REMOVED] ENVIRONMENT_QUICK_REFERENCE.md
)
if exist "ENV_IMPROVEMENTS_SUMMARY.md" (
    del "ENV_IMPROVEMENTS_SUMMARY.md"
    echo [REMOVED] ENV_IMPROVEMENTS_SUMMARY.md
)
if exist "IMPLEMENTATION_SUMMARY.md" (
    del "IMPLEMENTATION_SUMMARY.md"
    echo [REMOVED] IMPLEMENTATION_SUMMARY.md
)
if exist "PLUGGABLE_ARCHITECTURE_SUMMARY.md" (
    del "PLUGGABLE_ARCHITECTURE_SUMMARY.md"
    echo [REMOVED] PLUGGABLE_ARCHITECTURE_SUMMARY.md
)
if exist "TESTING_RESULTS.md" (
    del "TESTING_RESULTS.md"
    echo [REMOVED] TESTING_RESULTS.md
)

REM Root directory - Temporary files
if exist "analyze_test_results.py" (
    del "analyze_test_results.py"
    echo [REMOVED] analyze_test_results.py
)
if exist "benchmark_output.log" (
    del "benchmark_output.log"
    echo [REMOVED] benchmark_output.log
)
if exist "test_output.log" (
    del "test_output.log"
    echo [REMOVED] test_output.log
)
if exist "test2.log" (
    del "test2.log"
    echo [REMOVED] test2.log
)
if exist "test_offline.log" (
    del "test_offline.log"
    echo [REMOVED] test_offline.log
)
if exist "nul" (
    del "nul"
    echo [REMOVED] nul
)

REM docs/ directory - Summary files
if exist "docs\CLI-TESTING-SUMMARY.md" (
    del "docs\CLI-TESTING-SUMMARY.md"
    echo [REMOVED] docs\CLI-TESTING-SUMMARY.md
)
if exist "docs\cli-test-results.md" (
    del "docs\cli-test-results.md"
    echo [REMOVED] docs\cli-test-results.md
)
if exist "docs\cli-test-execution-guide.md" (
    del "docs\cli-test-execution-guide.md"
    echo [REMOVED] docs\cli-test-execution-guide.md
)
if exist "docs\architecture\ARCHITECTURE_UPDATE_SUMMARY.md" (
    del "docs\architecture\ARCHITECTURE_UPDATE_SUMMARY.md"
    echo [REMOVED] docs\architecture\ARCHITECTURE_UPDATE_SUMMARY.md
)

REM examples/playbooks/ - Summary files
if exist "examples\playbooks\PLAYBOOKS_SUMMARY.md" (
    del "examples\playbooks\PLAYBOOKS_SUMMARY.md"
    echo [REMOVED] examples\playbooks\PLAYBOOKS_SUMMARY.md
)
if exist "examples\playbooks\QUICK_REFERENCE.md" (
    del "examples\playbooks\QUICK_REFERENCE.md"
    echo [REMOVED] examples\playbooks\QUICK_REFERENCE.md
)

echo.
echo ============================================================
echo Cleanup complete!
echo.
