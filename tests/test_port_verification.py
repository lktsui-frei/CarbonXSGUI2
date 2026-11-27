"""
Test Python port verification against Fortran implementation.
Verifies that the Python implementation produces results that match the Fortran code.
"""

import pytest
import numpy as np
import os
from carbonxs_core import CarbonXSModel


def read_carbon_inp(filename):
    """Helper to read carbon.inp files."""
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Parse parameters starting from line 7 (index 6)
    params = []
    for i in range(6, 24):
        parts = lines[i].split()
        params.append(float(parts[0]))
        
    # Parse other settings
    # Line 2: Thmin, Thmax, Lambda, Nskip
    l2 = lines[1].split()
    lam = float(l2[2])
    
    # Line 3: Npar, Nphi, Nsg, Nlayer
    l3 = lines[2].split()
    nphi = int(l3[1])
    nsg = int(l3[2])
    nlayer = int(l3[3])
    
    # Line 4: Rdens, L0, Wd, Ww, Bw
    l4 = lines[3].split()
    rdens = float(l4[0])
    l0 = float(l4[1])
    wd = float(l4[2])
    ww = float(l4[3])
    bw = float(l4[4])
    
    return params, lam, nphi, nsg, nlayer, rdens, l0, wd, ww, bw


def read_carbon_dat(filename):
    """Helper to read carbon.dat files."""
    data = np.loadtxt(filename)
    return data[:, 0], data[:, 2]  # X, Y_fit


@pytest.mark.parametrize("fixture_prefix", ["fortran_1layer", "fortran_2layer"])
def test_port_verification(fixture_prefix):
    """Test that Python port matches immutable Fortran implementation for 1-layer and 2-layer models."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    inp_file = os.path.join(base_dir, 'tests', 'fixtures', f'{fixture_prefix}.inp')
    dat_file = os.path.join(base_dir, 'tests', 'fixtures', f'{fixture_prefix}.dat')
    
    assert os.path.exists(inp_file), f"Fortran fixture not found: {inp_file}"
    assert os.path.exists(dat_file), f"Fortran fixture not found: {dat_file}"
    
    # Load parameters and settings
    params, lam, nphi, nsg, nlayer, rdens, l0, wd, ww, bw = read_carbon_inp(inp_file)
    
    # Load ground truth from Fortran
    x_gt, y_gt = read_carbon_dat(dat_file)
    
    # Setup model
    model = CarbonXSModel()
    model.LAM = lam
    model.NPHI = nphi
    model.NSG = nsg
    model.RDENS = rdens
    model.L0 = l0
    model.WD = wd
    model.WW = ww
    model.BW = bw
    
    model.set_parameters(params, n_layers_model=nlayer)
    
    # Calculate S array
    theta_rad = np.radians(x_gt / 2.0)
    s_array = 2 * np.sin(theta_rad) / lam
    
    # Calculate intensity using Python port
    y_py = model.all_inten(s_array, model.params)
    
    # Compare results
    diff = y_py - y_gt
    rel_err = np.abs(diff) / (np.abs(y_gt) + 1e-6) * 100
    mean_rel_err = np.mean(rel_err)
    boundary_rel_err = np.max(rel_err[-5:])
    
    assert mean_rel_err < 0.1, f"{fixture_prefix} mean relative error {mean_rel_err:.4f}% exceeds 0.1%"
    assert boundary_rel_err < 1.0, (
        f"{fixture_prefix} high-angle boundary relative error {boundary_rel_err:.4f}% exceeds 1.0%"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
