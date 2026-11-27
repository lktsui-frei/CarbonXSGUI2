# CarbonXS GUI Documentation

Welcome to the documentation for **CarbonXS GUI**, a graphical interface and pure-Python calculation and fitting engine for analyzing X-ray diffraction (XRD) patterns of graphitic and disordered (hard/turbostratic) carbons.

![CarbonXS GUI main window](img/screenshot_main.png)

## Overview

CarbonXS GUI brings the structural refinement model originally developed in Fortran by Hang Shi, J. N. Reimers, and J. R. Dahn into a modern, self-contained Python desktop application built with NumPy, SciPy, Matplotlib, and PySide6. No external Fortran compiler or separate `CARBONXS` binary is required.

### Key Features

- **Pure-Python Physics & Fitting Engine:** Implements the full 1-layer and 2-layer CarbonXS scattering model in [carbonxs_core.py](../carbonxs_core.py) and bounded Trust Region Reflective least-squares fitting in [carbonxs_fit.py](../carbonxs_fit.py), with Fortran-compatible Poisson weighting ($w_i = 1/\sqrt{\max(Y_i, 1)}$) and $O(N)$ banded instrumental convolution.
- **No Dataset Size Limit:** Removed the legacy 3,000-point Fortran array cap — load and fit high-resolution XRD scans directly.
- **Interactive Pattern & Live Progress Plots:** View the diffraction pattern alongside the calculated fit, background curve, residual difference plot, previous fit comparison, optional log/linear Y-axis scaling, axis locking, and a live log-scale **Fitting Progress** loss curve.
- **Fit Results Summary & Diagnostics:** Automatically displays final vs. initial values, estimated standard deviations (ESDs), reduced $\chi^2$, and crystallite stack height $L_c \pm \sigma_{L_c}$ upon fit completion, with full correlation matrices written to `carbon.out`.
- **Flexible Import & Export:** Load `.mdi` (Jade), `.ras` (Rigaku), `.xy`, and custom delimited text files; save and reload parameters as `.json` or legacy `carbon.inp`; export full CarbonXS outputs (`_carbon_out.txt`, `_carbon_dat.txt`, `_carbon.inp`) or fitted curves as `.mdi`.
- **Cooperative Abort:** Safely cancel long-running fits at any time from the UI without terminating external processes.

## Documentation Pages

- [Installation Guide](installation.md) — Quick setup with `uv`, manual `venv` installation, platform notes, and test verification.
- [User Tutorial](tutorial.md) — Step-by-step guide to parameters, settings, loading XRD data, running calculations and fits, plotting controls, exporting results, and keyboard shortcuts.
- [References & Credits](references.md) — Academic papers, the original CarbonXS Fortran manual, conference presentations, and asset attributions.
- [Project README](../README.md) — Repository overview and developer layout.

## Credits

- **Original Fortran CarbonXS Model:** Hang Shi, J. N. Reimers, and J. R. Dahn (Simon Fraser University).
- **CarbonXS GUI & Python Port:** Lok-kun Tsui (`lok-kun.tsui.t6r@research.f-rei.go.jp`).

Please report bugs or feature requests on the [GitHub Issues page](https://github.com/lktsui-frei/CarbonXSGUI2/issues).
