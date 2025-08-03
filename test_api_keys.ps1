# PowerShell script to test API key configuration
# This script helps diagnose and fix Windows DPAPI decryption errors

Write-Host "🚀 Voice Dictation Assistant - API Key Configuration Test" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python and try again." -ForegroundColor Red
    exit 1
}

# Check if required packages are installed
Write-Host "`n📦 Checking required packages..." -ForegroundColor Yellow

$requiredPackages = @("pywin32", "pydantic", "pyyaml")
$missingPackages = @()

foreach ($package in $requiredPackages) {
    try {
        python -c "import $package" 2>$null
        Write-Host "✅ $package" -ForegroundColor Green
    } catch {
        Write-Host "❌ $package" -ForegroundColor Red
        $missingPackages += $package
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Host "`n⚠️  Missing packages detected. Installing..." -ForegroundColor Yellow
    foreach ($package in $missingPackages) {
        Write-Host "Installing $package..." -ForegroundColor Yellow
        pip install $package
    }
}

# Run the API key test
Write-Host "`n🔍 Running API Key Configuration Test..." -ForegroundColor Yellow
python test_api_key_fixes.py

Write-Host "`n✅ Test completed!" -ForegroundColor Green
Write-Host "If you encountered issues, please check the output above for recommendations." -ForegroundColor Cyan 