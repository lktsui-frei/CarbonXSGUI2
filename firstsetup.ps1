# CarbonXS GUI Installation and Launch Script for Windows
# PowerShell script to set up environment and launch CarbonXS GUI

$ErrorActionPreference = "Stop"  # Exit on error

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "CarbonXS GUI Installer & Launcher" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if uv is available
$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvCommand) {
    Write-Host "ERROR: uv not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install uv first:"
    Write-Host "  powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`""
    Write-Host ""
    exit 1
}

Push-Location $SCRIPT_DIR

try {
    if (-not (Test-Path ".venv")) {
        Write-Host "Creating virtual environment with Python 3.9..." -ForegroundColor Yellow
        uv venv --python 3.9
        Write-Host "[OK] Environment created" -ForegroundColor Green
    } else {
        Write-Host "[OK] Environment already exists" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "Installing/updating dependencies..." -ForegroundColor Yellow
    uv pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
        exit 1
    }

    Write-Host ""
    Write-Host "Verifying installation..." -ForegroundColor Yellow
    uv run python tests\test_installation.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "=========================================" -ForegroundColor Green
        Write-Host "Installation successful!" -ForegroundColor Green
        Write-Host "=========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Launching CarbonXS GUI..." -ForegroundColor Cyan
        Write-Host ""
        
        # Launch the GUI
        uv run python CarbonXS_GUI.py
    } else {
        Write-Host ""
        Write-Host "ERROR: Installation verification failed" -ForegroundColor Red
        Write-Host "Please check the error messages above"
        exit 1
    }
} finally {
    Pop-Location
}