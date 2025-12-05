import numpy as np
from carbonxs_core import CarbonXSModel
from carbonxs_fit import CarbonXSFit

def test_fitting_loss_callback():
    print("Testing fitting loss callback...")
    
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
    true_params[0] = 1000.0 # Scale
    true_params[7] = 2.46 # A
    true_params[8] = 3.35 # d002
    true_params[9] = 50.0 # La
    true_params[10] = 10.0 # M
    
    model.set_parameters(true_params, 2)
    y_true = model.all_inten(s_array, model.params)
    
    # Add noise
    y_obs = y_true + np.random.normal(0, 10, size=len(y_true))
    
    # Initial guess
    initial_params = true_params.copy()
    initial_params[0] = 800.0
    
    # Refine flags (only refine scale)
    refine_flags = [False]*18
    refine_flags[0] = True
    
    # Callback
    losses = []
    def loss_callback(cost):
        losses.append(cost)
        print(f"Callback received cost: {cost}")
        
    # Fit
    fitter = CarbonXSFit(model)
    fitter.fit(initial_params, refine_flags, x_data, y_obs, loss_callback=loss_callback, max_nfev=10)
    
    if len(losses) > 0:
        print(f"Success! Received {len(losses)} loss updates.")
    else:
        print("Failure! No loss updates received.")

if __name__ == "__main__":
    test_fitting_loss_callback()
