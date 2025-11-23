#!/bin/bash
# CarbonXS GUI Installation and Launch Script

set -e  # Exit on error

ENV_NAME="carbon_xs_gui"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================="
echo "CarbonXS GUI Installer & Launcher"
echo "========================================="
echo ""

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "ERROR: conda not found!"
    echo ""
    echo "Please install Anaconda or Miniconda first:"
    echo "  https://docs.conda.io/en/latest/miniconda.html"
    echo ""
    echo "Alternatively, you can manually create a Python 3.9+ venv:"
    echo "  python3.9 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo "  python CarbonXS_GUI.py"
    exit 1
fi

# Check if environment exists
if conda env list | grep -q "^${ENV_NAME} "; then
    echo "✓ Environment '${ENV_NAME}' already exists"
else
    echo "Creating conda environment '${ENV_NAME}' with Python 3.9..."
    conda create -n "${ENV_NAME}" python=3.9 -y
    echo "✓ Environment created"
fi

echo ""
echo "Installing/updating dependencies..."
conda run -n "${ENV_NAME}" pip install -r "${SCRIPT_DIR}/requirements.txt" --quiet

echo ""
echo "Verifying installation..."
if conda run -n "${ENV_NAME}" python "${SCRIPT_DIR}/verify_installation.py"; then
    echo ""
    echo "========================================="
    echo "Installation successful!"
    echo "========================================="
    echo ""
    echo "Launching CarbonXS GUI..."
    echo ""
    
    # Launch the GUI
    cd "${SCRIPT_DIR}"
    conda run -n "${ENV_NAME}" python CarbonXS_GUI.py
else
    echo ""
    echo "ERROR: Installation verification failed"
    echo "Please check the error messages above"
    exit 1
fi
