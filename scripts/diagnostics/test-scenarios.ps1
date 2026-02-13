# PowerShell script to test all environment scenarios
# Usage: .\test-scenarios.ps1

$ErrorActionPreference = "Stop"

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Testing All Environment Scenarios" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$TestPDF = "test-documents\sample.pdf"
$BackupEnv = ".env.backup"

# Check for test document
if (-not (Test-Path $TestPDF)) {
    Write-Host "WARNING: No test document found at $TestPDF" -ForegroundColor Yellow
    Write-Host "Please add a test PDF file or update script" -ForegroundColor Yellow
    $TestPDF = $null
}

# Backup current .env
if (Test-Path .env) {
    Write-Host "Backing up current .env to $BackupEnv" -ForegroundColor Gray
    Copy-Item .env $BackupEnv -Force
}

# Test function
function Test-Scenario {
    param(
        [string]$Name,
        [string]$EnvFile,
        [string]$ValidationType
    )

    Write-Host ""
    Write-Host "====================================" -ForegroundColor Yellow
    Write-Host "Testing: $Name" -ForegroundColor Yellow
    Write-Host "====================================" -ForegroundColor Yellow

    # Copy template
    Write-Host "Copying $EnvFile..." -ForegroundColor Gray
    Copy-Item $EnvFile .env -Force

    # Validate
    Write-Host "Running validation..." -ForegroundColor Gray
    $validation = python -m ingestor.scenario_validator $ValidationType 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Validation failed" -ForegroundColor Red
        Write-Host $validation -ForegroundColor Red
        return $false
    }
    Write-Host "✓ Validation passed" -ForegroundColor Green

    # Pre-check
    Write-Host "Running pre-check..." -ForegroundColor Gray
    $precheck = python -m ingestor.cli --validate 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Pre-check failed" -ForegroundColor Red
        Write-Host $precheck -ForegroundColor Red
        return $false
    }
    Write-Host "✓ Pre-check passed" -ForegroundColor Green

    # Test processing
    if ($TestPDF -and (Test-Path $TestPDF)) {
        Write-Host "Testing document processing..." -ForegroundColor Gray
        $process = python -m ingestor.cli --pdf $TestPDF 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ Processing failed" -ForegroundColor Red
            Write-Host $process -ForegroundColor Red
            return $false
        }
        Write-Host "✓ Processing test passed" -ForegroundColor Green
    } else {
        Write-Host "⚠ Skipping processing test (no test PDF)" -ForegroundColor Yellow
    }

    Write-Host "✓ $Name : ALL TESTS PASSED" -ForegroundColor Green
    return $true
}

# Track results
$results = @{}

# Test Scenario 1: Azure Local Input
$results["Azure Local Input"] = Test-Scenario `
    -Name "Azure Local Input" `
    -EnvFile "envs\.env.azure-local-input.example" `
    -ValidationType "azure_full"

# Test Scenario 2: Azure + ChromaDB
$results["Azure + ChromaDB"] = Test-Scenario `
    -Name "Azure + ChromaDB Hybrid" `
    -EnvFile "envs\.env.azure-chromadb-hybrid.example" `
    -ValidationType "hybrid"

# Test Scenario 3: Fully Offline
$results["Fully Offline"] = Test-Scenario `
    -Name "Fully Offline" `
    -EnvFile "envs\.env.offline-with-vision.example" `
    -ValidationType "offline"

# Restore original .env
if (Test-Path $BackupEnv) {
    Write-Host ""
    Write-Host "Restoring original .env from backup" -ForegroundColor Gray
    Move-Item $BackupEnv .env -Force
}

# Summary
Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Test Results Summary" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

$allPassed = $true
foreach ($scenario in $results.Keys) {
    $status = if ($results[$scenario]) { "PASSED" } else { "FAILED"; $allPassed = $false }
    $color = if ($results[$scenario]) { "Green" } else { "Red" }
    Write-Host "$scenario : $status" -ForegroundColor $color
}

Write-Host ""
if ($allPassed) {
    Write-Host "✓ All scenarios tested successfully!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ Some scenarios failed" -ForegroundColor Red
    exit 1
}
