import pytest
import numpy as np
from carbonxs_core import CarbonXSModel
from carbonxs_fit import CarbonXSFit

@pytest.fixture
def model():
    return CarbonXSModel()

@pytest.fixture
def fitter(model):
    return CarbonXSFit(model)

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
