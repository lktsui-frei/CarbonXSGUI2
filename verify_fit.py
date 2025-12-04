import numpy as np
import matplotlib.pyplot as plt
from carbonxs_core import CarbonXSModel
from carbonxs_fit import CarbonXSFit

def read_carbon_inp(filename):
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
    data = np.loadtxt(filename, delimiter=',')
    return data[:, 0], data[:, 1] # X, Y_obs

def verify_fit():
    # Load initial parameters from examples/carbon.inp (before Fortran refinement)
    params_init, lam, nphi, nsg, nlayer, rdens, l0, wd, ww, bw = read_carbon_inp('examples/carbon.inp')
    
    # Load observed data
    x_obs, y_obs = read_data('examples/crystalline_carbon.dat')
    
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
    with open('examples/carbon.inp', 'r') as f:
        lines = f.readlines()
        for i in range(6, 24):
            parts = lines[i].split()
            if len(parts) > 1:
                refine_flags.append(int(parts[1]) == 1)
            else:
                refine_flags.append(False)
    
    print("Initial Parameters:", params_init)
    print("Refine Flags:", refine_flags)
    
    # Run fit
    print("Starting fit...")
    final_params, res = fitter.fit(params_init, refine_flags, x_obs, y_obs)
    
    print("Fit completed.")
    print("Success:", res.success)
    print("Message:", res.message)
    print("Cost:", res.cost)
    
    print("Final Parameters:", final_params)
    
    # Compare with Fortran result (from carbonxs/carbon.inp which has refined values)
    params_fortran, _, _, _, _, _, _, _, _, _ = read_carbon_inp('carbonxs/carbon.inp')
    print("Fortran Refined Parameters:", params_fortran)
    
    # Calculate percent difference
    diff = np.abs(np.array(final_params) - np.array(params_fortran))
    rel_diff = diff / (np.abs(np.array(params_fortran)) + 1e-6) * 100
    
    print("Relative Difference (%):", rel_diff)
    
    # Plot
    model.set_parameters(final_params, nlayer)
    theta_rad = np.radians(x_obs / 2.0)
    s_array = 2 * np.sin(theta_rad) / lam
    y_calc = model.all_inten(s_array, model.params)
    
    plt.figure(figsize=(10, 6))
    plt.plot(x_obs, y_obs, 'k.', label='Observed')
    plt.plot(x_obs, y_calc, 'r-', label='Python Fit')
    plt.legend()
    plt.title("Python Fit Verification")
    plt.savefig('fit_verification.png')
    print("Plot saved to fit_verification.png")

if __name__ == "__main__":
    verify_fit()
