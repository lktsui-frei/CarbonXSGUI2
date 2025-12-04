# Windows Setup and Launch Instructions

This document explains how to set up and run CarbonXS GUI on Windows using PowerShell.

## Prerequisites

- **Anaconda or Miniconda** installed on your system
  - Download from: https://docs.conda.io/en/latest/miniconda.html
- **PowerShell** (comes with Windows)

## Scripts Overview

### `run.ps1` - Full Setup and Launch
This script performs a complete setup:
1. Checks for conda installation
2. Creates a conda environment named `carbon_xs_gui` with Python 3.9 (if not exists)
3. Installs/updates all dependencies from `requirements.txt`
4. Verifies the installation
5. Launches the CarbonXS GUI

**Use this script the first time** or when you need to update dependencies.

### `launch.ps1` - Quick Launch
This script quickly launches the GUI assuming the environment is already set up.
- Faster startup time
- Skips environment creation and dependency installation
- Use this for subsequent launches after initial setup

## Usage

### First Time Setup and Launch

1. Open PowerShell in the project directory
2. You may need to enable script execution (run as Administrator if needed):
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
3. Run the setup script:
   ```powershell
   .\run.ps1
   ```

### Subsequent Launches

After the initial setup, you can use the quick launch script:
```powershell
.\launch.ps1
```

Or run the full setup script again if you need to update dependencies:
```powershell
.\run.ps1
```

## Troubleshooting

### PowerShell Execution Policy Error
If you get an error about script execution being disabled:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Conda Not Found
Make sure conda is in your PATH. After installing Anaconda/Miniconda:
1. Close and reopen PowerShell
2. Or restart your computer
3. Verify with: `conda --version`

### Manual Environment Creation
If you prefer not to use conda or encounter issues:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python CarbonXS_GUI.py
```

## Environment Details

- **Environment Name**: `carbon_xs_gui`
- **Python Version**: 3.9
- **Dependencies**: See `requirements.txt`
