#!/bin/bash
# CarbonXS GUI Installation and Launch Script

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================="
echo "CarbonXS GUI Installer & Launcher"
echo "========================================="
echo ""

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "ERROR: uv not found!"
    echo ""
    echo "Please install uv first:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    exit 1
fi

cd "${SCRIPT_DIR}"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment with Python 3.9..."
    uv venv --python 3.9
    echo "✓ Environment created"
else
    echo "✓ Environment already exists"
fi

echo ""
echo "Installing/updating dependencies..."
uv pip install -r requirements.txt --quiet

echo ""
echo "Verifying installation..."
if uv run python tests/test_installation.py; then
    echo ""
    echo "========================================="
    echo "Installation successful!"
    echo "========================================="
    echo ""
    echo "Launching CarbonXS GUI..."
    echo ""
    
    # Launch the GUI
    uv run python CarbonXS_GUI.py
else
    echo ""
    echo "ERROR: Installation verification failed"
    echo "Please check the error messages above"
    exit 1
fi
