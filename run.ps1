# CarbonXS GUI Installation and Launch Script for Windows
# PowerShell script to set up conda environment and launch CarbonXS GUI

$ErrorActionPreference = "Stop"  # Exit on error

$ENV_NAME = "carbon_xs_gui"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "CarbonXS GUI Installer & Launcher" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if conda is available
$condaCommand = Get-Command conda -ErrorAction SilentlyContinue
if (-not $condaCommand) {
    Write-Host "ERROR: conda not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Anaconda or Miniconda first:"
    Write-Host "  https://docs.conda.io/en/latest/miniconda.html"
    Write-Host ""
    Write-Host "Alternatively, you can manually create a Python 3.9+ venv:"
    Write-Host "  python -m venv venv"
    Write-Host "  .\venv\Scripts\Activate.ps1"
    Write-Host "  pip install -r requirements.txt"
    Write-Host "  python CarbonXS_GUI.py"
    exit 1
}

# Check if environment exists using conda info (more reliable than string parsing)
$envExistsResult = conda info --envs | Select-String -Pattern "^$ENV_NAME\s"

if ($envExistsResult) {
    Write-Host "[OK] Environment '${ENV_NAME}' already exists" -ForegroundColor Green
} else {
    Write-Host "Creating conda environment '${ENV_NAME}' with Python 3.9..." -ForegroundColor Yellow
    
    # Use -ErrorAction Stop with a try/catch block for robust error handling
    try {
        conda create -n $ENV_NAME python=3.9 -y
        Write-Host "[OK] Environment created" -ForegroundColor Green
        
        # Force Conda index refresh after successful creation (This is a good guardrail)
        Write-Host "Forcing Conda index refresh..." -ForegroundColor DarkYellow
        conda env list | Out-Null
        
    } catch {
        Write-Host "ERROR: Failed to create conda environment: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Installing/updating dependencies..." -ForegroundColor Yellow
conda run --no-capture-output -n $ENV_NAME pip install -r "$SCRIPT_DIR\requirements.txt"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Verifying installation..." -ForegroundColor Yellow
conda run -n $ENV_NAME python "$SCRIPT_DIR\tests\test_installation.py"
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "Installation successful!" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Launching CarbonXS GUI..." -ForegroundColor Cyan
    Write-Host ""
    
    # Launch the GUI
    Push-Location $SCRIPT_DIR
    try {
        conda run -n $ENV_NAME python CarbonXS_GUI.py
    } finally {
        Pop-Location
    }
} else {
    Write-Host ""
    Write-Host "ERROR: Installation verification failed" -ForegroundColor Red
    Write-Host "Please check the error messages above"
    exit 1
}