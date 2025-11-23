#!/bin/bash
# Quick launch script for CarbonXS GUI (assumes environment already set up)

ENV_NAME="carbon_xs_gui"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "ERROR: conda not found!"
    echo "Please run ./run.sh first to set up the environment"
    exit 1
fi

# Check if environment exists
if ! conda env list | grep -q "^${ENV_NAME} "; then
    echo "ERROR: Environment '${ENV_NAME}' not found!"
    echo "Please run ./run.sh first to set up the environment"
    exit 1
fi

cd "${SCRIPT_DIR}"
echo "Launching CarbonXS GUI..."
conda run -n "${ENV_NAME}" python CarbonXS_GUI.py
