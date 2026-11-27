# Installation Guide

[Documentation Home](README.md) · [User Tutorial](tutorial.md) · [References](references.md)

CarbonXS GUI is a pure-Python application supporting Windows, macOS, and Linux on Python 3.9 or later. No Fortran compiler or pre-compiled `CARBONXS` executable is required.

---

## Quick Start (Recommended: `uv`)

The repository includes setup and launcher scripts powered by [`uv`](https://docs.astral.sh/uv/), which automatically creates a Python 3.9 virtual environment (`.venv`), installs all dependencies from [requirements.txt](../requirements.txt), runs the installation test suite, and launches the GUI.

### Windows (PowerShell)

1. Install `uv` if you do not already have it:

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. Clone or download the repository, open PowerShell in the project folder, and run the first-time setup script ([firstsetup.ps1](../firstsetup.ps1)):

   ```powershell
   .\firstsetup.ps1
   ```

3. For subsequent launches, run ([launch.ps1](../launch.ps1)):

   ```powershell
   .\launch.ps1
   ```

### Linux & macOS

1. Install `uv` if you do not already have it:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. In the project directory, run the setup script ([firstsetup.sh](../firstsetup.sh)):

   ```bash
   chmod +x firstsetup.sh launch.sh
   ./firstsetup.sh
   ```

3. For subsequent launches, run ([launch.sh](../launch.sh)):

   ```bash
   ./launch.sh
   ```

---

## Manual Setup

If you prefer setting up the virtual environment yourself instead of using the setup scripts:

### Option A: Manual setup with `uv`

```bash
uv venv --python 3.9 .venv
uv pip install -r requirements.txt
uv run python CarbonXS_GUI.py
```

### Option B: Standard Python `venv` + `pip`

```bash
python -m venv .venv
```

Activate the environment:

- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
- **Windows (CMD):** `.venv\Scripts\activate.bat`
- **Linux / macOS:** `source .venv/bin/activate`

Then install dependencies and launch:

```bash
pip install -r requirements.txt
python CarbonXS_GUI.py
```

### Core Dependencies

Defined in [requirements.txt](../requirements.txt):

- `numpy >= 2.0`
- `scipy >= 1.4.1`
- `matplotlib >= 3.6.0`
- `PySide6 >= 6.0.0`
- `ujson >= 1.35`
- `appdirs >= 1.4.3`
- `pytest` (for verification and regression tests)

---

## Verifying the Installation

To verify all Python dependencies import cleanly:

```bash
uv run pytest tests/test_installation.py -v
```

To run the full test suite (physics engine stability, Fortran parity, fitting reproducibility, and GUI/I/O tests):

```bash
uv run pytest -v
```

---

## Platform Notes

- **Linux (`PySide6` / Qt6 platform plugins):** Minimal or headless Linux distributions may require system OpenGL/XCB libraries before Qt6 windows can open. On Debian/Ubuntu, for example:
  ```bash
  sudo apt-get install libxcb-cursor0 libegl1 libxkbcommon-x11-0
  ```
- **Windows:** No Visual C++ 2008 Redistributable or separate Qt4/PySide1 installer is required; PySide6 wheels bundle the needed Qt runtime libraries.
- **macOS:** Apple Silicon and Intel Macs are both supported via standard PySide6 and NumPy/SciPy wheels.

---

## Original Fortran Reference Code

The [carbonxs/](../carbonxs/) directory contains the original Fortran source (`CARBONXS.FOR`) and sample input/output files for historical reference and numerical regression testing. It is **not** compiled or executed by CarbonXS GUI at runtime.
