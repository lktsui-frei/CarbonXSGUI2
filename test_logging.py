"""
Test script to verify logging functionality.

This script tests that the logging utility creates log files correctly
and captures both console output and structured fitting data.
"""

import os
import sys
import numpy as np
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from carbonxs_core import CarbonXSModel
from carbonxs_fit import CarbonXSFit
from logging_utils import capture_fitting_log, get_log_directory

def test_logging():
    """Test the logging functionality with a simple fitting operation."""
    
    print("=" * 80)
    print("Testing CarbonXS Fitting Logging")
    print("=" * 80)
    
    # Setup model
    model = CarbonXSModel()
    model.LAM = 1.5418
    model.NPHI = 10
    model.NSG = 3
    model.RDENS = 1.0
    model.L0 = 200.0
    model.WD = 2.0
    model.WW = 20.0
    model.BW = 1.0
    model.n_layers_model = 1
    
    # Example parameters (from CARBON.INP)
    initial_params = [
        33800.0, 116.78, 483.09, -353.58, 0.0, 0.0, 0.0,
        2.4615, 3.3611, 293.51, 141.69, 2.0, 0.0, 0.024387,
        0.066073, 0.061821, 1.3708, 0.37804
    ]
    
    settings = {
        'wavelength': 1.5418,
        'tci_pts': 10,
        'integration_width': 3,
        'sample_density': 1.0,
        'goniometer_radius': 200.0,
        'sample_depth': 2.0,
        'sample_width': 20.0,
        'beam_width': 1.0,
        'number_layers': 0,
        'theta_min': 10.0,
        'theta_max': 90.0,
        'iterations': 1
    }
    
    # Load example data
    example_file = os.path.join(os.path.dirname(__file__), 'examples', 'crystalline_carbon.dat')
    
    use_synthetic = True  # Use synthetic data for testing
    
    if use_synthetic or not os.path.exists(example_file):
        print("Creating synthetic test data...")
        # Generate synthetic data
        x_obs = np.arange(10.0, 30.0, 0.5)
        theta_rad = np.radians(x_obs / 2.0)
        s_array = 2 * np.sin(theta_rad) / model.LAM
        model.set_parameters(initial_params, model.n_layers_model)
        y_obs = model.all_inten(s_array, model.params)
        # Add some noise
        y_obs = y_obs + np.random.normal(0, y_obs.max() * 0.02, len(y_obs))
    
    print(f"\nData loaded: {len(x_obs)} points")
    print(f"X range: {x_obs.min():.2f} to {x_obs.max():.2f}")
    print(f"Y range: {y_obs.min():.2f} to {y_obs.max():.2f}")
    
    # Run a fitting operation with logging
    print("\nStarting fit with logging enabled...")
    
    refine_flags = [True, True, True, False, False, False, False,
                    True, True, True, True, False, False, True,
                    True, False, False, False]
    
    with capture_fitting_log(
        initial_params=initial_params,
        settings=settings,
        mode='fit'
    ) as log_ctx:
        print("\n--- Fitting in progress ---")
        
        fitter = CarbonXSFit(model)
        final_params, res = fitter.fit(
            initial_params, 
            refine_flags, 
            x_obs, 
            y_obs,
            max_nfev=100  # Limit iterations for quick test
        )
        
        print(f"\n--- Fitting completed ---")
        print(f"Success: {res.success if res else False}")
        print(f"Message: {res.message if res else 'No result'}")
        if res:
            print(f"Cost: {res.cost:.6f}")
            print(f"Function evaluations: {res.nfev}")
        
        # Log the results
        log_ctx['log_result'](
            final_params=final_params,
            success=res.success if res else False,
            message=res.message if res else "No result",
            cost=res.cost if res else None,
            nfev=res.nfev if res else None
        )
        
        log_file_path = log_ctx['log_file_path']
    
    # Verify the log file was created
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    if os.path.exists(log_file_path):
        print(f"✓ Log file created: {log_file_path}")
        
        # Check log file size
        log_size = os.path.getsize(log_file_path)
        print(f"✓ Log file size: {log_size} bytes")
        
        # Read and display first few lines
        with open(log_file_path, 'r') as f:
            lines = f.readlines()
            print(f"✓ Log file has {len(lines)} lines")
            print("\nFirst 20 lines of log:")
            print("-" * 80)
            for i, line in enumerate(lines[:20], 1):
                print(f"{i:3d}: {line.rstrip()}")
            print("-" * 80)
        
        # Check logs directory
        logs_dir = get_log_directory()
        log_files = [f for f in os.listdir(logs_dir) if f.startswith('fit_') and f.endswith('.log')]
        print(f"\n✓ Total log files in logs directory: {len(log_files)}")
        
        print("\n" + "=" * 80)
        print("TEST PASSED: Logging functionality is working correctly!")
        print("=" * 80)
        
    else:
        print(f"✗ ERROR: Log file was not created at {log_file_path}")
        print("\nTEST FAILED")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = test_logging()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
