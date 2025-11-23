import numpy as np
import matplotlib.pyplot as plt
from carbonxs_core import CarbonXSModel

def read_carbon_inp(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Parse parameters starting from line 7 (index 6)
    params = []
    for i in range(6, 24):
        parts = lines[i].split()
        params.append(float(parts[0]))
        
    # Parse other settings
    # Line 2: Thmin, Thmax, Lambda, Nskip
    l2 = lines[1].split()
    lam = float(l2[2])
    
    # Line 3: Npar, Nphi, Nsg, Nlayer
    l3 = lines[2].split()
    nphi = int(l3[1])
    nsg = int(l3[2])
    nlayer = int(l3[3])
    
    # Line 4: Rdens, L0, Wd, Ww, Bw
    l4 = lines[3].split()
    rdens = float(l4[0])
    l0 = float(l4[1])
    wd = float(l4[2])
    ww = float(l4[3])
    bw = float(l4[4])
    
    return params, lam, nphi, nsg, nlayer, rdens, l0, wd, ww, bw

def read_carbon_dat(filename):
    data = np.loadtxt(filename)
    return data[:, 0], data[:, 2] # X, Y_fit

def verify():
    # Load parameters and settings
    params, lam, nphi, nsg, nlayer, rdens, l0, wd, ww, bw = read_carbon_inp('carbonxs/carbon.inp')
    
    # Load ground truth
    x_gt, y_gt = read_carbon_dat('carbonxs/carbon.dat')
    
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
    
    # Calculate S array
    # S = 2*sin(theta)/lambda
    # theta = x/2 (degrees) -> radians
    theta_rad = np.radians(x_gt / 2.0)
    s_array = 2 * np.sin(theta_rad) / lam
    
    # Calculate intensity
    # Use model.params which has been rescaled
    y_py = model.all_inten(s_array, model.params)
    
    # Compare
    diff = y_py - y_gt
    max_diff = np.max(np.abs(diff))
    rms_diff = np.sqrt(np.mean(diff**2))
    rel_err = np.mean(np.abs(diff) / (np.abs(y_gt) + 1e-6)) * 100
    
    print(f"Max Difference: {max_diff:.6e}")
    print(f"RMS Difference: {rms_diff:.6e}")
    print(f"Mean Relative Error: {rel_err:.6f}%")
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(x_gt, y_gt, label='Fortran (Ground Truth)', alpha=0.7)
    plt.plot(x_gt, y_py, label='Python (Port)', linestyle='--', alpha=0.7)
    plt.plot(x_gt, diff, label='Difference', alpha=0.5)
    plt.legend()
    plt.title(f"Verification: Python vs Fortran\nRMS Diff: {rms_diff:.4e}")
    plt.xlabel("2 Theta")
    plt.ylabel("Intensity")
    plt.grid(True)
    plt.savefig('verification_plot.png')
    print("Plot saved to verification_plot.png")

if __name__ == "__main__":
    verify()
