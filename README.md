# CarbonXS GUI

A Python-based GUI application for analyzing carbon X-ray diffraction patterns using least squares fitting.

## Overview

CarbonXS has been fully ported from Fortran to pure Python, using NumPy and SciPy for numerical computations. The application provides a graphical interface for loading diffraction data, setting parameters, and performing fits to extract structural information about carbon materials.

## Quick Start

The easiest way to get started:

**On Linux/Mac:**
```bash
./firstsetup.sh
```

**On Windows (PowerShell):**
```powershell
.\firstsetup.ps1
```

This will automatically:
1. Create a virtual environment (if needed)
2. Install all dependencies
3. Verify the installation
4. Launch the GUI

After first-time setup, you can use the faster launch script:

**On Linux/Mac:**
```bash
./launch.sh
```

**On Windows (PowerShell):**
```powershell
.\launch.ps1
```

## Installation

### Recommended: uv Environment

The easiest way to get started is to use [`uv`](https://docs.astral.sh/uv/), a fast Python package installer and resolver.

```bash
# Create a new virtual environment
uv venv --python 3.9

# Install dependencies
uv pip install -r requirements.txt

# Run the application
uv run python CarbonXS_GUI.py
```

### Alternative: Virtual Environment (venv)

If you prefer to use the standard Python `venv` module instead of `uv`:

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate  # On Windows

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

**Note:** On some Linux systems, older Qt versions may have system library dependencies. If you encounter any import errors, ensure your system has the required Qt dependencies installed.

### Verify Installation

After installing dependencies, run:

```bash
uv run pytest tests/test_installation.py -v
```

This checks that all required packages (`numpy`, `scipy`, `matplotlib`, `PySide6`, `ujson`, `appdirs`, and internal modules) are installed and importable. To run the full test suite:

```bash
uv run pytest -v
```

## Documentation

Full documentation is available in the [docs/](docs/README.md) folder:

- [Documentation Overview](docs/README.md)
- [Installation Guide](docs/installation.md)
- [User Tutorial](docs/tutorial.md)
- [References & Credits](docs/references.md)

## Running the Application

```bash
python CarbonXS_GUI.py
```

## Example Data

Example diffraction data and parameter files are provided in the `examples/` directory:

- `examples/crystalline_carbon.dat` - Example XRD data
- `examples/carbon.inp` - Example parameter file

## Features

- Pure Python implementation (no Fortran dependencies)
- Graphical user interface for parameter adjustment
- Real-time pattern calculation
- Least squares fitting using scipy.optimize
- Support for 1-layer and 2-layer carbon models
- Import/export parameter files
- Plot comparison between observed and calculated patterns
- Automatic parameter bounding (prevents singularities for Pr/Pt parameters)
- Real-time fitting loss graph (log scale)

## Requirements

- Python 3.9+
- NumPy >= 2.0 (compatible with PySide6 6.10+)
- SciPy >= 1.4.1
- Matplotlib >= 3.6.0
- PySide6 >= 6.0.0
- ujson >= 1.35
- appdirs >= 1.4.3

## Development

### Verification & Tests

Automated tests in `tests/` verify dependencies, physics parity against the original Fortran code, fitting reproducibility, and GUI/I/O behavior:

- [tests/test_installation.py](tests/test_installation.py) - Verifies required dependencies and module imports
- [tests/test_port_verification.py](tests/test_port_verification.py) - Verifies core calculation logic against Fortran reference behavior
- [tests/test_fit.py](tests/test_fit.py) - Verifies fitting engine and reproducibility

Run the entire suite with:

```bash
uv run pytest -v
```

### Project Structure

```
carbon_xs_gui_2/
├── CarbonXS_GUI.py          # Main GUI application
├── carbonxs_core.py         # Core calculation engine (ported from Fortran)
├── carbonxs_fit.py          # Fitting engine using scipy
├── qt_compat.py             # PySide6 compatibility layer
├── scalable_mw.py           # Auto-generated Qt UI file
├── text_file_viewer.py      # Auto-generated Qt dialog
├── data_io.py               # Data import/export utilities
├── requirements.txt         # Python dependencies
├── examples/                # Example data files
├── tests/                   # Automated pytest verification & regression suite
├── carbonxs/                # Original Fortran code (for reference)
└── docs/                    # Markdown documentation and reference manuals
```

## License

See LICENSE file for details.
