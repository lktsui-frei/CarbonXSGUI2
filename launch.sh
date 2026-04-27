#!/bin/bash
# Quick launch script for CarbonXS GUI (assumes environment already set up)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "ERROR: uv not found!"
    echo "Please run ./firstsetup.sh first to set up the environment"
    exit 1
fi

cd "${SCRIPT_DIR}"

if [ ! -d ".venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please run ./firstsetup.sh first to set up the environment"
    exit 1
fi

echo "Launching CarbonXS GUI..."
uv run python CarbonXS_GUI.py
