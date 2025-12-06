"""
Test fitting loss callback functionality.
Verifies that the loss callback is properly invoked during fitting.
"""

import pytest
import numpy as np
from carbonxs_core import CarbonXSModel
from carbonxs_fit import CarbonXSFit


def test_fitting_loss_callback():
    """Test that loss callback is called during fitting."""
    # Setup model
    model = CarbonXSModel()
    model.LAM = 1.54
    model.n_layers_model = 2
    
    # Create synthetic data
    x_data = np.linspace(10, 80, 100)
    theta_rad = np.radians(x_data / 2.0)
    s_array = 2 * np.sin(theta_rad) / model.LAM
    
    # True params
    true_params = np.zeros(18)
    true_params[0] = 1000.0  # Scale
    true_params[7] = 2.46    # A
    true_params[8] = 3.35    # d002
    true_params[9] = 50.0    # La
    true_params[10] = 10.0   # M
    
    model.set_parameters(true_params, 2)
    y_true = model.all_inten(s_array, model.params)
    
    # Add noise
    np.random.seed(42)  # For reproducibility
    y_obs = y_true + np.random.normal(0, 10, size=len(y_true))
    
    # Initial guess
    initial_params = true_params.copy()
    initial_params[0] = 800.0
    
    # Refine flags (only refine scale)
    refine_flags = [False]*18
    refine_flags[0] = True
    
    # Callback to collect losses
    losses = []
    def loss_callback(cost):
        losses.append(cost)
        
    # Fit with callback
    fitter = CarbonXSFit(model)
    final_params, res = fitter.fit(
        initial_params, 
        refine_flags, 
        x_data, 
        y_obs, 
        loss_callback=loss_callback, 
        max_nfev=10
    )
    
    # Verify callback was called
    assert len(losses) > 0, "Loss callback should be called at least once"
    
    # Verify losses are positive numbers
    assert all(loss >= 0 for loss in losses), "All losses should be non-negative"
    
    # Verify fit was successful
    assert res.success, f"Fit should succeed, got: {res.message}"


def test_loss_callback_not_required():
    """Test that fitting works without a loss callback."""
    # Setup model
    model = CarbonXSModel()
    model.LAM = 1.54
    model.n_layers_model = 2
    
    # Create simple synthetic data
    x_data = np.linspace(10, 80, 50)
    theta_rad = np.radians(x_data / 2.0)
    s_array = 2 * np.sin(theta_rad) / model.LAM
    
    # Simple params
    params = np.zeros(18)
    params[0] = 1000.0
    params[7] = 2.46
    params[8] = 3.35
    params[9] = 50.0
    params[10] = 10.0
    
    model.set_parameters(params, 2)
    y_obs = model.all_inten(s_array, model.params)
    
    # Fit without callback
    refine_flags = [False]*18
    refine_flags[0] = True
    
    fitter = CarbonXSFit(model)
    final_params, res = fitter.fit(
        params, 
        refine_flags, 
        x_data, 
        y_obs, 
        max_nfev=5
    )
    
    # Should still work
    assert res is not None, "Fit should return a result even without callback"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
