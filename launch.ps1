# Quick launch script for CarbonXS GUI (assumes environment already set up)
# PowerShell script for Windows

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check if uv is available
$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvCommand) {
    Write-Host "ERROR: uv not found!" -ForegroundColor Red
    Write-Host "Please run .\firstsetup.ps1 first to set up the environment"
    exit 1
}

Push-Location $SCRIPT_DIR
try {
    if (-not (Test-Path ".venv")) {
        Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
        Write-Host "Please run .\firstsetup.ps1 first to set up the environment"
        exit 1
    }

    Write-Host "Launching CarbonXS GUI..." -ForegroundColor Cyan
    uv run python CarbonXS_GUI.py
} finally {
    Pop-Location
}
