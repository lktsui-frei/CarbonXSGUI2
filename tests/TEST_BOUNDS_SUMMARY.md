# Comprehensive Fit Verification Test Bounds Summary

## Test Tolerances and Acceptance Criteria

### Single Parameter Recovery Tests

| Test | Parameter | Acceptance Criterion | Rationale |
|------|-----------|---------------------|-----------|
| `test_single_parameter_recovery_scale` | Scale | **< 1% relative error** | Scale is linear and well-constrained, should recover accurately |
| `test_single_parameter_recovery_pr` | Pr | **< 0.1 absolute error** | Tests at Pr = 0.1, 0.5, 0.9; reasonable tolerance for stacking parameter |

### Multi-Parameter Recovery Tests

| Test | Parameters | Acceptance Criterion | Rationale |
|------|-----------|---------------------|-----------|
| `test_multi_parameter_recovery` | Scale, La, Pr | **< 15% relative error** | Parameter correlations limit exact recovery; tests 3 relatively independent params |
| `test_multi_parameter_convergence` | Scale, La, Pr | **R² > 0.99** | Focuses on fit quality rather than exact parameter recovery |

### Convergence Behavior Tests

| Test | Metric | Acceptance Criterion | Rationale |
|------|--------|---------------------|-----------|
| `test_convergence_monotonic_decrease` | Cost reduction | **≥ 50% decrease** | Optimizer must significantly improve fit |
| | Cost increases | **< 20% of iterations** | scipy least_squares can explore during line search |
| | Cost increase tolerance | **< 1% per step** | Small numerical noise is acceptable |

### Fit Quality Tests

| Test | Metric | Acceptance Criterion | Rationale |
|------|--------|---------------------|-----------|
| `test_fit_quality_metrics` | R² (2% noise) | **> 0.95** | Should maintain excellent fit despite realistic noise |
| | Mean residual | **< 10% of std** | No systematic bias in residuals |

### Parameter Bounds Tests

| Test | Parameter | Physical Bounds | Enforcement Method |
|------|-----------|----------------|-------------------|
| `test_parameter_bounds_comprehensive` | A (cell constant) | **≥ 1.0 Å** | Lower bound in fitter |
| | d002 (layer spacing) | **≥ 1.0 Å** | Lower bound in fitter |
| | La (coherence length) | **≥ 1.0 Å** | Lower bound in fitter |
| | M (# layers) | **≥ 0.1** | Lower bound in fitter |
| | Pr (random stacking) | **[0, 0.99999]** | Both bounds in fitter |
| | Pt (3R prob / g) | **[0, 0.99999]** | Both bounds in fitter |
| | B (temperature factor) | **≥ 0** | Lower bound in fitter |
| | PO (preferred orientation) | **≥ 0** | Lower bound in fitter |

### Robustness Tests

| Test | Condition | Acceptance Criterion | Rationale |
|------|-----------|---------------------|-----------|
| `test_noise_robustness` | 1% noise | **R² > 0.90** | High quality data |
| | 5% noise | **R² > 0.90** | Typical experimental data |
| | 10% noise | **Convergence** | Poor quality data - just needs to succeed |
| `test_initial_guess_sensitivity` | ±20% perturbation | **CV < 5% (scale)** | Scale should converge consistently |
| | | **CV < 10% (La)** | Structural parameters have more variability |

## Summary Table: Quick Reference

| Test Category | Key Metric | Threshold | Pass/Fail Boundary |
|--------------|------------|-----------|-------------------|
| **Scale Recovery** | Relative Error | 1% | Strict - linear parameter |
| **Pr Recovery** | Absolute Error | 0.1 | Moderate - nonlinear but single param |
| **Multi-Param Recovery** | Relative Error | 15% | Relaxed - accounts for correlations |
| **Multi-Param Convergence** | R² | 0.99 | Strict - synthetic data should fit perfectly |
| **Cost Reduction** | Decrease | 50% | Moderate - must improve significantly |
| **Cost Monotonicity** | Increase Fraction | 20% | Relaxed - allows line search exploration |
| **Fit Quality (2% noise)** | R² | 0.95 | Strict - low noise should fit well |
| **Fit Quality (5% noise)** | R² | 0.90 | Moderate - typical experimental data |
| **Parameter Bounds** | All params | Physical bounds | Strict - must never violate |
| **Initial Guess Sensitivity** | CV | 5-10% | Moderate - local minimum stability |

## Design Philosophy

The bounds were chosen based on:

1. **Physical Meaning**: Parameters with clear physical meaning (scale, bounds) have stricter tolerances
2. **Parameter Correlations**: Correlated parameters (La, M, Pr) have relaxed tolerances when fitted together
3. **Noise Levels**: Higher noise → relaxed criteria (but must still converge)
4. **Optimizer Behavior**: scipy's trust region reflective can explore → allow temporary cost increases
5. **Real-World Applicability**: Tolerances reflect what's achievable in practice, not mathematical ideals

## Usage Notes

- **Single parameter tests** validate algorithmic correctness with strict bounds
- **Multi-parameter tests** validate real-world applicability with realistic bounds  
- **Robustness tests** validate stability under adverse conditions
- **Bounds tests** validate safety (no unphysical results)

These bounds collectively ensure the fitting routine is:
- ✓ Algorithmically correct
- ✓ Practically useful
- ✓ Robust to noise and initial conditions
- ✓ Safe (enforces physical constraints)
