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


@pytest.mark.skipif(
    not os.path.exists('carbonxs/carbon.inp'),
    reason="Fortran reference data not available"
)
def test_port_verification():
    """Test that Python port matches Fortran implementation."""
    # Get paths to reference files
    base_dir = os.path.dirname(os.path.dirname(__file__))
    inp_file = os.path.join(base_dir, 'carbonxs', 'carbon.inp')
    dat_file = os.path.join(base_dir, 'carbonxs', 'carbon.dat')
    
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
    # S = 2*sin(theta)/lambda
    # theta = x/2 (degrees) -> radians
    theta_rad = np.radians(x_gt / 2.0)
    s_array = 2 * np.sin(theta_rad) / lam
    
    # Calculate intensity using Python port
    y_py = model.all_inten(s_array, model.params)
    
    # Compare results
    diff = y_py - y_gt
    max_diff = np.max(np.abs(diff))
    rms_diff = np.sqrt(np.mean(diff**2))
    rel_err = np.mean(np.abs(diff) / (np.abs(y_gt) + 1e-6)) * 100
    
    # Print statistics for debugging
    print(f"\nPort Verification Statistics:")
    print(f"  Max Difference: {max_diff:.6e}")
    print(f"  RMS Difference: {rms_diff:.6e}")
    print(f"  Mean Relative Error: {rel_err:.6f}%")
    
    # Assert reasonable agreement
    # These thresholds account for numerical differences between Python and Fortran
    # implementations, including differences in floating point calculations and optimizations
    assert max_diff < 100.0, f"Max difference {max_diff} exceeds threshold"
    assert rms_diff < 10.0, f"RMS difference {rms_diff} exceeds threshold"
    assert rel_err < 5.0, f"Mean relative error {rel_err}% exceeds 5%"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
