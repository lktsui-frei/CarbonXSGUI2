import pytest
import numpy as np
import os
from carbonxs_core import CarbonXSModel
from carbonxs_fit import CarbonXSFit

# Helper to read INP files
def read_carbon_inp(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    params = []
    for i in range(6, 24):
        parts = lines[i].split()
        params.append(float(parts[0]))
        
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

@pytest.mark.parametrize("fixture_prefix", ["fortran_1layer", "fortran_2layer"])
def test_regression_vs_fortran(fixture_prefix):
    """Compare Python output against immutable Fortran ground truth."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    inp_file = os.path.join(base_dir, 'tests', 'fixtures', f'{fixture_prefix}.inp')
    dat_file = os.path.join(base_dir, 'tests', 'fixtures', f'{fixture_prefix}.dat')
    
    assert os.path.exists(inp_file), f"{inp_file} not found"
    assert os.path.exists(dat_file), f"{dat_file} not found"
    
    # Load parameters
    params, lam, nphi, nsg, nlayer, rdens, l0, wd, ww, bw = read_carbon_inp(inp_file)
    
    # Load ground truth
    data = np.loadtxt(dat_file)
    x_gt = data[:, 0]
    y_gt = data[:, 2]
    
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
    
    # Calculate
    theta_rad = np.radians(x_gt / 2.0)
    s_array = 2 * np.sin(theta_rad) / lam
    y_py = model.all_inten(s_array, model.params)
    
    diff = y_py - y_gt
    rel = np.abs(diff) / (np.abs(y_gt) + 1e-6) * 100
    rel_err = np.mean(rel)
    boundary_rel = np.max(rel[-5:])
    
    assert rel_err < 0.1
    assert boundary_rel < 1.0

def test_model_consistency():
    """Test 1-layer vs 2-layer parameter rescaling."""
    model = CarbonXSModel()
    
    # Dummy params
    params = np.ones(18)
    # A(11) -> index 10 (M)
    # A(12) -> index 11 (SM)
    # A(14) -> index 13 (Del)
    # A(15) -> index 14 (Pr)
    # A(16) -> index 15 (Pt)
    
    # Test 2-layer rescaling
    model.set_parameters(params, n_layers_model=2)
    
    # Check rescaling
    # M /= 2.0 -> 0.5
    assert np.isclose(model.params[10], 0.5)
    # SM /= 2.0 -> 0.5
    assert np.isclose(model.params[11], 0.5)
    # Del *= 2.0 -> 2.0
    assert np.isclose(model.params[13], 2.0)
    # Pr *= 2.0 -> 2.0
    assert np.isclose(model.params[14], 2.0)
    # Pt *= 2.0 -> 2.0
    assert np.isclose(model.params[15], 2.0)
    
    # Test 1-layer (no rescaling)
    model.set_parameters(params, n_layers_model=1)
    assert np.isclose(model.params[10], 1.0)
