# PowerShell script to start Voice Dictation Assistant with hotkey cleanup
# This script clears existing hotkey registrations before starting the application

Write-Host "Voice Dictation Assistant - Startup Script" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python not found. Please install Python and try again." -ForegroundColor Red
    exit 1
}

# Clear existing hotkey registrations
Write-Host "`nClearing existing hotkey registrations..." -ForegroundColor Yellow
try {
    python clear_hotkeys.py
    Write-Host "Hotkey cleanup completed" -ForegroundColor Green
} catch {
    Write-Host "Hotkey cleanup had issues, but continuing..." -ForegroundColor Yellow
}

# Wait a moment for cleanup to complete
Start-Sleep -Seconds 2

# Start the Voice Dictation Assistant
Write-Host "`nStarting Voice Dictation Assistant..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to exit the application" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Green

try {
    python run_voice_assistant.py
} catch {
    Write-Host "`nApplication failed to start: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Try running the cleanup script manually: python clear_hotkeys.py" -ForegroundColor Yellow
}

Write-Host "`nApplication closed." -ForegroundColor Green 