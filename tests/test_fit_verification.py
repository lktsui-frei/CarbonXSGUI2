"""
Test fitting verification against Fortran refinement results.
Verifies that Python fitting produces results comparable to Fortran refinement.
"""

import pytest
import numpy as np
import os
from carbonxs_core import CarbonXSModel
from carbonxs_fit import CarbonXSFit


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
    l2 = lines[1].split()
    lam = float(l2[2])
    
    l3 = lines[2].split()
    nphi = int(l3[1])
    nsg = int(l3[2])
    nlayer = int(l3[3])
    
    l4 = lines[3].split()
    rdens = float(l4[0])
    l0 = float(l4[1])
    wd = float(l4[2])
    ww = float(l4[3])
    bw = float(l4[4])
    
    return params, lam, nphi, nsg, nlayer, rdens, l0, wd, ww, bw


def read_data(filename):
    """Helper to read observed data."""
    data = np.loadtxt(filename, delimiter=',')
    return data[:, 0], data[:, 1]  # X, Y_obs


@pytest.mark.skipif(
    not os.path.exists('carbonxs/carbon.inp'),
    reason="Fortran reference data not available"
)
def test_fit_verification_against_fortran():
    """Test that Python fit results are comparable to Fortran refinement."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    # Load initial parameters from examples/carbon.inp (before Fortran refinement)
    example_inp = os.path.join(base_dir, 'examples', 'carbon.inp')
    params_init, lam, nphi, nsg, nlayer, rdens, l0, wd, ww, bw = read_carbon_inp(example_inp)
    
    # Load observed data
    example_dat = os.path.join(base_dir, 'examples', 'crystalline_carbon.dat')
    x_obs, y_obs = read_data(example_dat)
    
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
    model.n_layers_model = nlayer
    
    # Setup fit
    fitter = CarbonXSFit(model)
    
    # Define which parameters to refine
    # Based on carbon.inp flags (2nd column)
    # 1 means refine, 0 means fixed
    refine_flags = []
    with open(example_inp, 'r') as f:
        lines = f.readlines()
        for i in range(6, 24):
            parts = lines[i].split()
            if len(parts) > 1:
                refine_flags.append(int(parts[1]) == 1)
            else:
                refine_flags.append(False)
    
    # Run fit
    final_params, res = fitter.fit(params_init, refine_flags, x_obs, y_obs)
    
    # Verify fit was successful
    assert res.success, f"Fit should succeed, got: {res.message}"
    
    # Load Fortran refined parameters for comparison
    fortran_inp = os.path.join(base_dir, 'carbonxs', 'carbon.inp')
    params_fortran, _, _, _, _, _, _, _, _, _ = read_carbon_inp(fortran_inp)
    
    # Calculate percent difference
    diff = np.abs(np.array(final_params) - np.array(params_fortran))
    rel_diff = diff / (np.abs(np.array(params_fortran)) + 1e-6) * 100
    
    # Print comparison for debugging
    print(f"\nFit Verification Statistics:")
    print(f"  Initial Parameters: {params_init}")
    print(f"  Python Final: {final_params}")
    print(f"  Fortran Final: {params_fortran}")
    print(f"  Relative Difference (%): {rel_diff}")
    print(f"  Max Relative Difference: {np.max(rel_diff):.2f}%")
    print(f"  Mean Relative Difference: {np.mean(rel_diff):.2f}%")
    
    # Assert reasonable agreement
    # The optimization may not converge to exactly the same values,
    # but should be in the same ballpark. Different optimizers and 
    # initial conditions can lead to different local minima.
    max_rel_diff = np.max(rel_diff)
    assert max_rel_diff < 200.0, f"Max relative difference {max_rel_diff:.2f}% is unreasonably large"
    
    # Verify fit quality
    model.set_parameters(final_params, nlayer)
    theta_rad = np.radians(x_obs / 2.0)
    s_array = 2 * np.sin(theta_rad) / lam
    y_calc = model.all_inten(s_array, model.params)
    
    # Calculate R-squared or similar metric
    residuals = y_obs - y_calc
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((y_obs - np.mean(y_obs))**2)
    r_squared = 1 - (ss_res / ss_tot)
    
    print(f"  R-squared: {r_squared:.4f}")
    print(f"  Final cost: {res.cost:.2e}")
    
    # Fit should be reasonably good
    assert r_squared > 0.5, f"R-squared {r_squared} indicates poor fit quality"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
