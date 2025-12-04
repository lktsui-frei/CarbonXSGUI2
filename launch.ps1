# Quick launch script for CarbonXS GUI (assumes environment already set up)
# PowerShell script for Windows

$ENV_NAME = "carbon_xs_gui"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check if conda is available
$condaCommand = Get-Command conda -ErrorAction SilentlyContinue
if (-not $condaCommand) {
    Write-Host "ERROR: conda not found!" -ForegroundColor Red
    Write-Host "Please run .\run.ps1 first to set up the environment"
    exit 1
}

# Check if environment exists
$envExists = conda env list | Select-String -Pattern "^${ENV_NAME}\s"
if (-not $envExists) {
    Write-Host "ERROR: Environment '${ENV_NAME}' not found!" -ForegroundColor Red
    Write-Host "Please run .\run.ps1 first to set up the environment"
    exit 1
}

Push-Location $SCRIPT_DIR
try {
    Write-Host "Launching CarbonXS GUI..." -ForegroundColor Cyan
    conda run -n $ENV_NAME python CarbonXS_GUI.py
} finally {
    Pop-Location
}
