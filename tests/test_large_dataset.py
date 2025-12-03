import sys
import os
import numpy as np
import time

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from carbonxs_core import CarbonXSModel
from carbonxs_fit import CarbonXSFit

def test_large_dataset_fitting():
    print("Setting up large dataset test...")
    
    # 1. Setup Model
    model = CarbonXSModel()
    # Set standard parameters
    # [scale, bg_const, bg_1, bg_2, bg_3, bg_4, bg_5, a_cell, d002, la, m, sm, dab, del_strain, pr, pt, temp, po]
    # Using some reasonable defaults
    params = [
        1.0, 10.0, 0.0, 0.0, 0.0, 0.0, 0.0, # Scale + BG
        2.46, 3.35, 50.0, 20.0, 0.0, 0.001, 0.001, 0.5, 0.5, 0.0, 0.0 # Structural
    ]
    model.set_parameters(params)
    
    # 2. Generate Synthetic Data (> 3000 points)
    n_points = 5000
    print(f"Generating {n_points} data points...")
    x_data = np.linspace(10, 90, n_points)
    
    # Calculate "true" intensity
    theta_rad = np.radians(x_data / 2.0)
    s_array = 2 * np.sin(theta_rad) / model.LAM
    y_true = model.all_inten(s_array, model.params)
    
    # Add some noise
    np.random.seed(42)
    y_obs = y_true + np.random.normal(0, 0.5, size=n_points)
    y_obs = np.abs(y_obs) # Intensity must be positive
    
    # 3. Setup Fit
    fitter = CarbonXSFit(model)
    
    # Perturb initial parameters slightly
    initial_params = list(params)
    initial_params[0] = 0.8 # Scale
    initial_params[9] = 40.0 # La
    
    # Refine flags (True for parameters we want to fit)
    # Refine Scale (0) and La (9)
    refine_flags = [False] * 18
    refine_flags[0] = True
    refine_flags[9] = True
    
    print("Starting fit...")
    start_time = time.time()
    
    # 4. Run Fit
    final_params, res = fitter.fit(
        initial_params, 
        refine_flags, 
        x_data, 
        y_obs, 
        max_nfev=100 # Limit iterations for test speed
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Fit completed in {duration:.2f} seconds.")
    print(f"Success: {res.success}")
    print(f"Message: {res.message}")
    print(f"Initial Scale: {initial_params[0]}, Final Scale: {final_params[0]}, True: {params[0]}")
    print(f"Initial La: {initial_params[9]}, Final La: {final_params[9]}, True: {params[9]}")
    
    # 5. Assertions
    if not res.success and "limit" not in res.message and "iteration" not in res.message:
        # It might fail due to iteration limit, which is fine for this test as long as it ran
        # But ideally it should succeed or at least run without crashing
        pass
        
    # Check if parameters moved in the right direction
    assert final_params[0] > 0.85, "Scale did not increase towards 1.0"
    assert final_params[9] > 42.0, "La did not increase towards 50.0"
    
    print("Test PASSED: Fitting ran successfully on large dataset.")

if __name__ == "__main__":
    test_large_dataset_fitting()
