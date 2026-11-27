import pytest
import numpy as np
import os
from carbonxs_core import CarbonXSModel
from carbonxs_fit import CarbonXSFit

@pytest.fixture
def model():
    return CarbonXSModel()

@pytest.fixture
def fitter(model):
    return CarbonXSFit(model)

def read_carbon_inp(filename):
    """Helper to read carbon.inp files."""
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    params = []
    refine_flags = []
    for i in range(6, 24):  # Lines 7-24 in file (1-indexed) are indices 6-23 (0-indexed)
        parts = lines[i].split()
        params.append(float(parts[0]))
        refine_flags.append(int(parts[1]) == 1)
        
    l2 = lines[1].split()
    theta_min = float(l2[0])
    theta_max = float(l2[1])
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
    
    l5 = lines[4].split()
    iterations = int(l5[0])
    
    return {
        'params': params,
        'refine_flags': refine_flags,
        'theta_min': theta_min,
        'theta_max': theta_max,
        'lam': lam,
        'nphi': nphi,
        'nsg': nsg,
        'nlayer': nlayer,
        'rdens': rdens,
        'l0': l0,
        'wd': wd,
        'ww': ww,
        'bw': bw,
        'iterations': iterations
    }

def test_residuals_zero(fitter, model):
    """Test residuals are zero when obs matches calc."""
    # Setup dummy parameters
    params = np.zeros(18)
    params[0] = 1.0 # Scale
    params[7] = 2.46 # A
    params[8] = 3.35 # d002
    params[9] = 50.0 # La
    params[10] = 10.0 # M
    params[11] = 1.0 # SM
    
    # Generate synthetic data
    s_array = np.linspace(0.1, 1.0, 10)
    model.set_parameters(params)
    y_calc = model.all_inten(s_array, model.params)
    
    # Test residuals
    refine_mask = np.zeros(18, dtype=bool)
    refined_params = np.array([])
    
    res = fitter.residuals(refined_params, params, refine_mask, s_array, y_calc)
    
    assert np.allclose(res, 0.0)

def test_residuals_weights(fitter, model):
    """Test residuals with weights."""
    params = np.zeros(18)
    params[0] = 1.0
    params[7] = 2.46
    params[8] = 3.35
    params[9] = 50.0
    params[10] = 10.0
    params[11] = 1.0
    
    s_array = np.linspace(0.1, 1.0, 10)
    model.set_parameters(params)
    y_calc = model.all_inten(s_array, model.params)
    
    # Perturb observation
    y_obs = y_calc + 1.0
    weights = np.ones_like(y_obs) * 0.5
    
    refine_mask = np.zeros(18, dtype=bool)
    refined_params = np.array([])
    
    res = fitter.residuals(refined_params, params, refine_mask, s_array, y_obs, weights)
    
    # Diff is -1.0, weight is 0.5 -> res should be -0.5
    assert np.allclose(res, -0.5)

def test_fit_with_example_data():
    """Test fitting with example carbon.inp and crystalline_carbon.dat."""
    # Get paths to example files
    base_dir = os.path.dirname(os.path.dirname(__file__))
    inp_file = os.path.join(base_dir, 'examples', 'carbon.inp')
    dat_file = os.path.join(base_dir, 'examples', 'crystalline_carbon.dat')
    
    assert os.path.exists(inp_file), f"Example file not found: {inp_file}"
    assert os.path.exists(dat_file), f"Example data not found: {dat_file}"
    
    # Load parameters and settings from carbon.inp
    config = read_carbon_inp(inp_file)
    
    # Load observed data
    data = np.loadtxt(dat_file, delimiter=',')
    x_obs = data[:, 0]
    y_obs = data[:, 1]
    
    # Setup model
    model = CarbonXSModel()
    model.LAM = config['lam']
    model.NPHI = config['nphi']
    model.NSG = config['nsg']
    model.RDENS = config['rdens']
    model.L0 = config['l0']
    model.WD = config['wd']
    model.WW = config['ww']
    model.BW = config['bw']
    model.n_layers_model = config['nlayer']
    
    # Create fitter
    fitter = CarbonXSFit(model)
    
    # Calculate initial cost
    model.set_parameters(config['params'], model.n_layers_model)
    theta_rad = np.radians(x_obs / 2.0)
    s_array = 2 * np.sin(theta_rad) / model.LAM
    y_init = model.all_inten(s_array, model.params)
    initial_cost = np.sum((y_init - y_obs)**2)
    
    # Run fit with max_nfev
    max_nfev = config['iterations'] * 100
    final_params, res = fitter.fit(
        config['params'], 
        config['refine_flags'], 
        x_obs, 
        y_obs, 
        max_nfev=max_nfev
    )
    
    # Verify fit completed successfully
    assert res is not None, "Fit should return a result object"
    assert res.success, f"Fit should succeed but got: {res.message}"
    
    # Verify fit didn't exceed max_nfev
    assert res.nfev <= max_nfev, f"Fit used {res.nfev} evaluations, exceeding limit of {max_nfev}"
    
    # Verify fit improved the cost (or at least didn't make it worse)
    final_cost = res.cost * 2  # res.cost is sum of squared residuals / 2
    print(f"\nFit Statistics:")
    print(f"  Initial cost: {initial_cost:.2e}")
    print(f"  Final cost: {final_cost:.2e}")
    print(f"  Function evaluations: {res.nfev}/{max_nfev}")
    print(f"  Optimality: {res.optimality:.2e}")
    
    # The fit should either improve or stay roughly the same
    # (sometimes already at optimum)
    assert final_cost <= initial_cost * 1.1, "Fit should not significantly worsen the cost"
    
    # Verify parameters changed (at least one refined parameter should change)
    params_changed = np.any(~np.isclose(config['params'], final_params))
    if np.any(config['refine_flags']):
        assert params_changed, "At least one parameter should change during fitting"
    
    print(f"  ✓ Test passed - fit completed successfully!")


def test_default_poisson_weights_bounds_and_tolerances(fitter, model):
    """Test default Poisson weighting, explicit unweighted option, bounds, and ftol/xtol."""
    lower, upper = fitter._get_parameter_bounds()
    assert lower[0] == 0.0, f"Scale lower bound should be 0.0, got {lower[0]}"
    assert upper[14] == 1.0, f"Pr upper bound should be 1.0, got {upper[14]}"
    assert upper[15] == 1.0, f"Pt upper bound should be 1.0, got {upper[15]}"

    params = np.zeros(18)
    params[0] = 100.0
    params[7] = 2.46
    params[8] = 3.35
    params[9] = 50.0
    params[10] = 10.0
    params[11] = 1.0

    lam = 1.5418
    x_obs = np.linspace(20.0, 80.0, 61)
    s_array = 2.0 * np.sin(np.radians(x_obs / 2.0)) / lam
    model.set_parameters(params, n_layers_model=1)
    y_true = model.all_inten(s_array, model.params)
    # Add constant offset +100 so residual at optimum isn't zero and weighting affects cost
    y_obs = y_true + 100.0

    refine_flags = [False] * 18
    refine_flags[0] = True
    init = params.copy()
    init[0] = 90.0

    final_poisson, res_poisson = fitter.fit(init, refine_flags, x_obs, y_obs, ftol=1e-6, xtol=1e-6)
    final_unweighted, res_unweighted = fitter.fit(init, refine_flags, x_obs, y_obs, weights=None, ftol=1e-6, xtol=1e-6)

    assert res_poisson.success and res_unweighted.success
    # Poisson weighting and unweighted weighting should produce different optimal Scale when residual != 0
    assert not np.isclose(final_poisson[0], final_unweighted[0], rtol=1e-4)
