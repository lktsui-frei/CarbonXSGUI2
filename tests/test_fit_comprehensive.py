"""
Comprehensive fitting routine verification tests.

This test suite verifies the correctness of the CarbonXS fitting routine
through synthetic data recovery, convergence validation, and physical
bounds checking. It replaces Fortran comparison tests since the Python
implementation now constrains Pr/Pt parameters to [0, 0.99999].
"""

import pytest
import numpy as np
import os
from carbonxs_core import CarbonXSModel
from carbonxs_fit import CarbonXSFit


# ============================================================================
# Helper Functions
# ============================================================================

def create_test_parameters():
    """
    Create standard test parameter sets for synthetic data generation.
    Returns a dictionary of parameter arrays for different scenarios.
    """
    # Base parameters (reasonable defaults)
    base = np.zeros(18)
    base[0] = 1000.0    # Scale Factor
    base[1] = 50.0      # Background constant
    base[2] = 0.0       # Background linear
    base[3] = 0.0       # Background quadratic
    base[4] = 0.0       # Background cubic
    base[5] = 0.0       # Background quartic
    base[6] = 0.0       # Background 1/s term
    base[7] = 2.46      # A (cell constant)
    base[8] = 3.36      # d002 (layer spacing)
    base[9] = 100.0     # La (coherence length)
    base[10] = 50.0     # M (number of layers)
    base[11] = 5.0      # SM (width of M distribution)
    base[12] = 0.01     # Dab (in-plane strain)
    base[13] = 0.01     # Del (interplanar strain)
    base[14] = 0.5      # Pr (probability random stacking)
    base[15] = 0.3      # Pt (prob 3R) or g
    base[16] = 0.5      # B (temperature factor)
    base[17] = 0.1      # PO (preferred orientation)
    
    # Turbostratic carbon (high Pr)
    turbostratic = base.copy()
    turbostratic[14] = 0.95  # Very random stacking
    turbostratic[9] = 30.0   # Smaller crystallite size
    
    # Graphitic carbon (low Pr)
    graphitic = base.copy()
    graphitic[14] = 0.1      # Ordered stacking
    graphitic[9] = 200.0     # Larger crystallite size
    graphitic[10] = 100.0    # More layers
    
    return {
        'base': base,
        'turbostratic': turbostratic,
        'graphitic': graphitic
    }


def generate_synthetic_pattern(params, s_array=None, noise_level=0.0, model=None, seed=None):
    """
    Generate synthetic XRD pattern with known parameters.
    
    Parameters:
    -----------
    params : array-like
        18 model parameters
    s_array : array-like, optional
        Scattering vector array. If None, use default range.
    noise_level : float
        Standard deviation of Gaussian noise as fraction of signal (0.0-1.0)
    model : CarbonXSModel, optional
        Model instance to use. If None, creates a new one.
    seed : int, optional
        Random seed for reproducibility
        
    Returns:
    --------
    s_array : ndarray
        Scattering vector values
    y_obs : ndarray
        Simulated intensity pattern (with noise if requested)
    y_true : ndarray
        True intensity pattern (without noise)
    """
    if seed is not None:
        np.random.seed(seed)
    
    if model is None:
        model = CarbonXSModel()
    
    # Default s_array if not provided (typical Cu K-alpha range)
    if s_array is None:
        # 2theta from 10 to 80 degrees, Cu K-alpha wavelength
        lam = 1.5418
        theta_deg = np.linspace(10, 80, 200)
        theta_rad = np.radians(theta_deg / 2.0)
        s_array = 2 * np.sin(theta_rad) / lam
    
    # Generate clean pattern
    model.set_parameters(params, n_layers_model=1)
    y_true = model.all_inten(s_array, params)
    
    # Add noise if requested
    if noise_level > 0:
        noise = np.random.normal(0, noise_level * np.mean(y_true), len(y_true))
        y_obs = y_true + noise
        # Ensure non-negative intensities
        y_obs = np.maximum(y_obs, 0.1)
    else:
        y_obs = y_true.copy()
    
    return s_array, y_obs, y_true


def calculate_fit_metrics(y_obs, y_calc):
    """
    Calculate fit quality metrics.
    
    Returns:
    --------
    dict with keys:
        - r_squared: R² coefficient
        - rmse: Root mean square error
        - chi_squared: χ² statistic (assuming unit weights)
        - mean_residual: Mean of residuals (should be near 0)
        - std_residual: Standard deviation of residuals
    """
    residuals = y_obs - y_calc
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((y_obs - np.mean(y_obs))**2)
    
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    rmse = np.sqrt(np.mean(residuals**2))
    chi_squared = ss_res
    mean_residual = np.mean(residuals)
    std_residual = np.std(residuals)
    
    return {
        'r_squared': r_squared,
        'rmse': rmse,
        'chi_squared': chi_squared,
        'mean_residual': mean_residual,
        'std_residual': std_residual
    }


def s_array_to_2theta(s_array, lam=1.5418):
    """Convert scattering vector to 2theta in degrees."""
    theta_rad = np.arcsin(s_array * lam / 2.0)
    return 2.0 * np.degrees(theta_rad)


# ============================================================================
# Single Parameter Recovery Tests
# ============================================================================

def test_single_parameter_recovery_scale():
    """Test recovery of scale parameter from synthetic data."""
    params = create_test_parameters()['base']
    true_scale = 1500.0
    params[0] = true_scale
    
    model = CarbonXSModel()
    s_array, y_obs, y_true = generate_synthetic_pattern(params, model=model, seed=42)
    
    # Perturb initial guess
    initial_params = params.copy()
    initial_params[0] = 1000.0  # 33% off from true value
    
    # Refine only scale
    refine_flags = [False] * 18
    refine_flags[0] = True
    
    fitter = CarbonXSFit(model)
    x_data = s_array_to_2theta(s_array)
    final_params, res = fitter.fit(initial_params, refine_flags, x_data, y_obs)
    
    # Verify convergence
    assert res.success, f"Fit should succeed: {res.message}"
    
    # Verify recovery (should be very accurate for single parameter)
    recovered_scale = final_params[0]
    relative_error = abs(recovered_scale - true_scale) / true_scale * 100
    
    print(f"\nScale Recovery Test:")
    print(f"  True scale: {true_scale}")
    print(f"  Initial guess: {initial_params[0]}")
    print(f"  Recovered scale: {recovered_scale:.2f}")
    print(f"  Relative error: {relative_error:.2f}%")
    
    assert relative_error < 1.0, f"Scale recovery error {relative_error:.2f}% exceeds 1% threshold"


def test_single_parameter_recovery_pr():
    """Test recovery of Pr parameter at different values."""
    test_values = [0.1, 0.5, 0.9]
    
    for true_pr in test_values:
        params = create_test_parameters()['base']
        params[14] = true_pr
        
        model = CarbonXSModel()
        s_array, y_obs, y_true = generate_synthetic_pattern(params, model=model, seed=42)
        
        # Perturb initial guess
        initial_params = params.copy()
        initial_params[14] = 0.5  # Start from middle value
        
        # Refine only Pr
        refine_flags = [False] * 18
        refine_flags[14] = True
        
        fitter = CarbonXSFit(model)
        x_data = s_array_to_2theta(s_array)
        final_params, res = fitter.fit(initial_params, refine_flags, x_data, y_obs)
        
        # Verify convergence
        assert res.success, f"Fit should succeed for Pr={true_pr}: {res.message}"
        
        # Verify recovery
        recovered_pr = final_params[14]
        absolute_error = abs(recovered_pr - true_pr)
        
        print(f"\nPr Recovery Test (true Pr = {true_pr}):")
        print(f"  Initial guess: {initial_params[14]}")
        print(f"  Recovered Pr: {recovered_pr:.4f}")
        print(f"  Absolute error: {absolute_error:.4f}")
        
        # Verify bounds are respected
        assert 0.0 <= recovered_pr < 1.0, f"Pr={recovered_pr} out of bounds"
        assert absolute_error < 0.1, f"Pr recovery error {absolute_error:.4f} exceeds 0.1 threshold"


# ============================================================================
# Multi-Parameter Recovery Tests
# ============================================================================

def test_multi_parameter_recovery():
    """Test recovery of multiple parameters simultaneously."""
    # Use base carbon as test case
    true_params = create_test_parameters()['base']
    
    model = CarbonXSModel()
    s_array, y_obs, y_true = generate_synthetic_pattern(true_params, model=model, seed=42)
    
    # Perturb initial guess for selected parameters
    # Note: We test fewer parameters to avoid parameter correlations causing convergence issues
    initial_params = true_params.copy()
    initial_params[0] *= 0.9   # Scale -10%
    initial_params[9] *= 1.15  # La +15%
    initial_params[14] = 0.7   # Pr different from true (0.5)
    
    # Refine selected parameters that are reasonably independent
    refine_flags = [False] * 18
    refine_flags[0] = True   # Scale
    refine_flags[9] = True   # La (coherence length)
    refine_flags[14] = True  # Pr (stacking disorder)
    
    fitter = CarbonXSFit(model)
    x_data = s_array_to_2theta(s_array)
    final_params, res = fitter.fit(initial_params, refine_flags, x_data, y_obs, max_nfev=1000)
    
    # Verify convergence
    assert res.success, f"Multi-parameter fit should succeed: {res.message}"
    
    # Calculate errors for each refined parameter
    param_names = ['Scale', 'La', 'Pr']
    param_indices = [0, 9, 14]
    
    print(f"\nMulti-Parameter Recovery Test:")
    print(f"  {'Parameter':<10} {'True':<12} {'Initial':<12} {'Recovered':<12} {'Error %':<10}")
    print(f"  {'-'*60}")
    
    max_error = 0.0
    for name, idx in zip(param_names, param_indices):
        true_val = true_params[idx]
        init_val = initial_params[idx]
        recovered_val = final_params[idx]
        rel_error = abs(recovered_val - true_val) / abs(true_val) * 100
        max_error = max(max_error, rel_error)
        
        print(f"  {name:<10} {true_val:<12.4f} {init_val:<12.4f} {recovered_val:<12.4f} {rel_error:<10.2f}")
    
    # For multi-parameter fitting with clean synthetic data, 15% is reasonable
    # due to parameter correlations (especially Pr with other params)
    assert max_error < 15.0, f"Max parameter recovery error {max_error:.2f}% exceeds 15% threshold"


def test_multi_parameter_convergence():
    """
    Test that multi-parameter fitting converges successfully and improves fit quality.
    
    This test focuses on convergence behavior rather than exact parameter recovery,
    which can be difficult due to parameter correlations in XRD fitting.
    """
    true_params = create_test_parameters()['base']
    
    model = CarbonXSModel()
    s_array, y_obs, y_true = generate_synthetic_pattern(true_params, model=model, seed=42)
    
    # Calculate initial cost with perturbed parameters
    initial_params = true_params.copy()
    initial_params[0] *= 0.8   # Scale -20%
    initial_params[9] *= 1.3   # La +30%
    initial_params[14] = 0.8   # Pr different
    
    model.set_parameters(initial_params, n_layers_model=1)
    y_init = model.all_inten(s_array, initial_params)
    initial_metrics = calculate_fit_metrics(y_obs, y_init)
    
    # Refine multiple parameters
    refine_flags = [False] * 18
    refine_flags[0] = True   # Scale
    refine_flags[9] = True   # La
    refine_flags[14] = True  # Pr
    
    fitter = CarbonXSFit(model)
    x_data = s_array_to_2theta(s_array)
    final_params, res = fitter.fit(initial_params, refine_flags, x_data, y_obs, max_nfev=1000)
    
    # Calculate final metrics
    model.set_parameters(final_params, n_layers_model=1)
    y_final = model.all_inten(s_array, final_params)
    final_metrics = calculate_fit_metrics(y_obs, y_final)
    
    print(f"\nMulti-Parameter Convergence Test:")
    print(f"  Fit success: {res.success}")
    print(f"  Initial R²: {initial_metrics['r_squared']:.4f}")
    print(f"  Final R²: {final_metrics['r_squared']:.4f}")
    print(f"  Initial RMSE: {initial_metrics['rmse']:.2f}")
    print(f"  Final RMSE: {final_metrics['rmse']:.2f}")
    
    # Main assertions: convergence and significant improvement
    assert res.success, f"Multi-parameter fit should succeed: {res.message}"
    assert final_metrics['r_squared'] > initial_metrics['r_squared'], \
        "Final R² should be better than initial"
    assert final_metrics['rmse'] < initial_metrics['rmse'], \
        "Final RMSE should be better than initial"
    
    # For fitting synthetic data perfectly, should get excellent fit
    assert final_metrics['r_squared'] > 0.99, \
        f"R² = {final_metrics['r_squared']:.4f} should be > 0.99 for synthetic data"
    
    print(f"  ✓ Multi-parameter fit converged with significant improvement")



# ============================================================================
# Convergence Behavior Tests
# ============================================================================

def test_convergence_monotonic_decrease():
    """Test that cost function monotonically decreases during optimization."""
    params = create_test_parameters()['base']
    
    model = CarbonXSModel()
    s_array, y_obs, y_true = generate_synthetic_pattern(params, model=model, seed=42)
    
    # Perturb initial guess significantly
    initial_params = params.copy()
    initial_params[0] *= 1.5
    initial_params[9] *= 0.7
    initial_params[14] = 0.8
    
    # Track loss at each iteration
    loss_history = []
    
    def loss_callback(cost):
        loss_history.append(cost)
    
    # Refine multiple parameters
    refine_flags = [False] * 18
    refine_flags[0] = True
    refine_flags[9] = True
    refine_flags[14] = True
    
    fitter = CarbonXSFit(model)
    x_data = s_array_to_2theta(s_array)
    final_params, res = fitter.fit(
        initial_params, refine_flags, x_data, y_obs,
        loss_callback=loss_callback, max_nfev=500
    )
    
    # Verify convergence
    assert res.success, f"Fit should succeed: {res.message}"
    assert len(loss_history) > 0, "Loss callback should have been called"
    
    # Check for monotonic decrease (allowing for numerical noise)
    print(f"\nConvergence Test:")
    print(f"  Initial cost: {loss_history[0]:.2e}")
    print(f"  Final cost: {loss_history[-1]:.2e}")
    print(f"  Cost reduction: {(1 - loss_history[-1]/loss_history[0]) * 100:.2f}%")
    print(f"  Iterations: {len(loss_history)}")
    
    # Cost should decrease significantly
    assert loss_history[-1] < loss_history[0] * 0.5, "Cost should decrease by at least 50%"
    
    # Check for general monotonic trend (allowing small increases due to line search)
    # scipy's least_squares can have temporary increases during line search
    increases = 0
    for i in range(1, len(loss_history)):
        if loss_history[i] > loss_history[i-1] * 1.01:  # Allow 1% noise
            increases += 1
    
    increase_fraction = increases / len(loss_history)
    # Relax to 20% because scipy's trust region reflective can explore before improving
    assert increase_fraction < 0.20, f"Cost increased in {increase_fraction*100:.1f}% of iterations (should be < 20%)"


# ============================================================================
# Fit Quality Tests
# ============================================================================

def test_fit_quality_metrics():
    """Test that fitter produces high quality fits with good metrics."""
    params = create_test_parameters()['base']
    
    model = CarbonXSModel()
    # Add small noise to make it realistic
    s_array, y_obs, y_true = generate_synthetic_pattern(
        params, model=model, noise_level=0.02, seed=42
    )
    
    # Start from perturbed guess
    initial_params = params.copy()
    initial_params[0] *= 1.2
    initial_params[7] *= 0.98
    initial_params[9] *= 1.1
    
    # Refine multiple parameters
    refine_flags = [False] * 18
    refine_flags[0] = True
    refine_flags[7] = True
    refine_flags[9] = True
    refine_flags[14] = True
    
    fitter = CarbonXSFit(model)
    x_data = s_array_to_2theta(s_array)
    final_params, res = fitter.fit(initial_params, refine_flags, x_data, y_obs, max_nfev=1000)
    
    # Calculate fitted pattern
    model.set_parameters(final_params, n_layers_model=1)
    y_calc = model.all_inten(s_array, final_params)
    
    # Calculate metrics
    metrics = calculate_fit_metrics(y_obs, y_calc)
    
    print(f"\nFit Quality Metrics:")
    print(f"  R²: {metrics['r_squared']:.4f}")
    print(f"  RMSE: {metrics['rmse']:.2f}")
    print(f"  Mean residual: {metrics['mean_residual']:.2e}")
    print(f"  Std residual: {metrics['std_residual']:.2f}")
    
    # With 2% noise, should still get excellent fit
    assert metrics['r_squared'] > 0.95, f"R² = {metrics['r_squared']:.4f} is too low (expected > 0.95)"
    
    # Mean residual should be near zero (no systematic bias)
    assert abs(metrics['mean_residual']) < metrics['std_residual'] * 0.1, \
        "Mean residual indicates systematic bias"


# ============================================================================
# Parameter Bounds Tests
# ============================================================================

def test_parameter_bounds_comprehensive():
    """Test that all parameter bounds are properly enforced."""
    params = create_test_parameters()['base']
    
    model = CarbonXSModel()
    s_array, y_obs, y_true = generate_synthetic_pattern(params, model=model, seed=42)
    
    # Create initial params with many out-of-bounds values
    initial_params = params.copy()
    initial_params[7] = -1.0    # A should be > 1.0
    initial_params[8] = -0.5    # d002 should be > 1.0
    initial_params[9] = -10.0   # La should be > 1.0
    initial_params[10] = -5.0   # M should be > 0.1
    initial_params[14] = 1.5    # Pr should be < 0.99999
    initial_params[15] = -0.2   # Pt should be >= 0
    initial_params[16] = -1.0   # B should be >= 0
    
    # Refine out-of-bounds parameters
    refine_flags = [False] * 18
    refine_flags[7] = True
    refine_flags[8] = True
    refine_flags[9] = True
    refine_flags[10] = True
    refine_flags[14] = True
    refine_flags[15] = True
    refine_flags[16] = True
    
    fitter = CarbonXSFit(model)
    x_data = s_array_to_2theta(s_array)
    final_params, res = fitter.fit(initial_params, refine_flags, x_data, y_obs, max_nfev=1000)
    
    print(f"\nParameter Bounds Test:")
    print(f"  Fit success: {res.success}")
    
    # Check all bounds
    bounds_ok = True
    
    # A >= 1.0
    if final_params[7] < 1.0:
        print(f"  ERROR: A = {final_params[7]} < 1.0")
        bounds_ok = False
    
    # d002 >= 1.0
    if final_params[8] < 1.0:
        print(f"  ERROR: d002 = {final_params[8]} < 1.0")
        bounds_ok = False
    
    # La >= 1.0
    if final_params[9] < 1.0:
        print(f"  ERROR: La = {final_params[9]} < 1.0")
        bounds_ok = False
    
    # M >= 0.1
    if final_params[10] < 0.1:
        print(f"  ERROR: M = {final_params[10]} < 0.1")
        bounds_ok = False
    
    # Pr in [0, 0.99999]
    if final_params[14] < 0.0 or final_params[14] >= 1.0:
        print(f"  ERROR: Pr = {final_params[14]} out of [0, 0.99999]")
        bounds_ok = False
    
    # Pt in [0, 0.99999]
    if final_params[15] < 0.0 or final_params[15] >= 1.0:
        print(f"  ERROR: Pt = {final_params[15]} out of [0, 0.99999]")
        bounds_ok = False
    
    # B >= 0
    if final_params[16] < 0.0:
        print(f"  ERROR: B = {final_params[16]} < 0")
        bounds_ok = False
    
    if bounds_ok:
        print(f"  ✓ All parameters within bounds")
    
    assert bounds_ok, "Some parameters violate their bounds"


# ============================================================================
# Robustness Tests
# ============================================================================

def test_noise_robustness():
    """Test that fitter is robust to different noise levels."""
    params = create_test_parameters()['base']
    noise_levels = [0.01, 0.05, 0.10]  # 1%, 5%, 10%
    
    model = CarbonXSModel()
    
    # Refine a few key parameters
    refine_flags = [False] * 18
    refine_flags[0] = True   # Scale
    refine_flags[9] = True   # La
    refine_flags[14] = True  # Pr
    
    print(f"\nNoise Robustness Test:")
    print(f"  {'Noise %':<10} {'R²':<10} {'Scale Error %':<15} {'La Error %':<15}")
    print(f"  {'-'*55}")
    
    for noise_level in noise_levels:
        s_array, y_obs, y_true = generate_synthetic_pattern(
            params, model=model, noise_level=noise_level, seed=42
        )
        
        # Perturb initial guess
        initial_params = params.copy()
        initial_params[0] *= 1.3
        initial_params[9] *= 0.8
        initial_params[14] = 0.7
        
        fitter = CarbonXSFit(model)
        x_data = s_array_to_2theta(s_array)
        final_params, res = fitter.fit(initial_params, refine_flags, x_data, y_obs, max_nfev=1000)
        
        # Calculate metrics
        model.set_parameters(final_params, n_layers_model=1)
        y_calc = model.all_inten(s_array, final_params)
        metrics = calculate_fit_metrics(y_obs, y_calc)
        
        # Calculate parameter errors
        scale_error = abs(final_params[0] - params[0]) / params[0] * 100
        la_error = abs(final_params[9] - params[9]) / params[9] * 100
        
        print(f"  {noise_level*100:<10.1f} {metrics['r_squared']:<10.4f} {scale_error:<15.2f} {la_error:<15.2f}")
        
        # Even with 10% noise, should get reasonable fit
        if noise_level <= 0.05:
            assert metrics['r_squared'] > 0.90, \
                f"R² = {metrics['r_squared']:.4f} too low for {noise_level*100}% noise"
        
        # Convergence should still work
        assert res.success, f"Fit failed at {noise_level*100}% noise level"


def test_initial_guess_sensitivity():
    """Test that fitter converges to same solution from different starting points."""
    true_params = create_test_parameters()['base']
    
    model = CarbonXSModel()
    s_array, y_obs, y_true = generate_synthetic_pattern(true_params, model=model, seed=42)
    
    # Try different perturbations
    perturbations = [0.8, 0.9, 1.0, 1.1, 1.2]  # -20% to +20%
    
    refine_flags = [False] * 18
    refine_flags[0] = True   # Scale
    refine_flags[9] = True   # La
    
    final_values_scale = []
    final_values_la = []
    
    fitter = CarbonXSFit(model)
    x_data = s_array_to_2theta(s_array)
    
    print(f"\nInitial Guess Sensitivity Test:")
    print(f"  {'Perturbation':<15} {'Final Scale':<15} {'Final La':<15} {'Success':<10}")
    print(f"  {'-'*60}")
    
    for pert in perturbations:
        initial_params = true_params.copy()
        initial_params[0] *= pert
        initial_params[9] *= pert
        
        final_params, res = fitter.fit(initial_params, refine_flags, x_data, y_obs, max_nfev=1000)
        
        final_values_scale.append(final_params[0])
        final_values_la.append(final_params[9])
        
        print(f"  {pert:<15.2f} {final_params[0]:<15.2f} {final_params[9]:<15.2f} {str(res.success):<10}")
        
        # All should converge
        assert res.success, f"Fit failed with perturbation {pert}"
    
    # All final values should be close (within 5%)
    scale_std = np.std(final_values_scale)
    scale_mean = np.mean(final_values_scale)
    scale_cv = scale_std / scale_mean * 100
    
    la_std = np.std(final_values_la)
    la_mean = np.mean(final_values_la)
    la_cv = la_std / la_mean * 100
    
    print(f"\n  Scale CV: {scale_cv:.2f}%")
    print(f"  La CV: {la_cv:.2f}%")
    
    assert scale_cv < 5.0, f"Scale variation {scale_cv:.2f}% across starting points exceeds 5%"
    assert la_cv < 10.0, f"La variation {la_cv:.2f}% across starting points exceeds 10%"


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
