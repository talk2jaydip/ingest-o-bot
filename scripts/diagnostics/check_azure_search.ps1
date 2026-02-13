# PowerShell script to find Azure Search services
Write-Host "Checking for Azure Search services..." -ForegroundColor Cyan

# Method 1: Using Az PowerShell module
if (Get-Module -ListAvailable -Name Az.Search) {
    Import-Module Az.Search
    Get-AzSearchService | Format-Table Name, ResourceGroupName, Location, Sku
} else {
    Write-Host "Az.Search module not installed. Install with:" -ForegroundColor Yellow
    Write-Host "  Install-Module -Name Az.Search -Scope CurrentUser" -ForegroundColor Yellow
}

# Method 2: Using Azure CLI
Write-Host "`nOr use Azure CLI:" -ForegroundColor Cyan
Write-Host "  az login" -ForegroundColor White
Write-Host "  az search service list --output table" -ForegroundColor White
