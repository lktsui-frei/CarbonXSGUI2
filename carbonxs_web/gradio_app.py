import gradio as gr
import numpy as np
import sys
import os
import matplotlib.pyplot as plt

# Ensure parent directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from carbonxs_core import CarbonXSModel
from carbonxs_fit import CarbonXSFit

# Parameter definitions
PARAM_LABELS = [
    "Scale Factor",
    "Background Constant",
    "Background S",
    "Background S^2",
    "Background S^3",
    "Background S^4",
    "Background 1/S",
    "A, In Plane Cell Constant (Å)",
    "d002, Interlayer Spacing (Å)",
    "La, Coherence Length (Å)",
    "M, Number of Layers",
    "SM, Width of M Distribution",
    "DAB, In plane strain",
    "del, Inter Plane Strain",
    "Pr, Probability of Random Stacking",
    "Pt, Probability of 3R Stacking",
    "Debye Waller Factor (Å^2)",
    "PO, Preferred Orientation Factor"
]

# Default values (from examples/CARBON.INP)
DEFAULT_PARAMS = [
    33800.0, 116.78, 483.09, -353.58, 0.0, 0.0, 0.0,
    2.4615, 3.3611, 293.51, 141.69, 2.0, 0.0, 0.024387,
    0.066073, 0.061821, 1.3708, 0.37804
]

def calculate_pattern(
    wavelength, tci_pts, integration_width, sample_density,
    goniometer_radius, sample_depth, sample_width, beam_width, number_layers,
    theta_min, theta_max, step_size,
    *params
):
    try:
        model = CarbonXSModel()
        model.LAM = wavelength
        model.NPHI = int(tci_pts)
        model.NSG = int(integration_width)
        model.RDENS = sample_density
        model.L0 = goniometer_radius
        model.WD = sample_depth
        model.WW = sample_width
        model.BW = beam_width
        model.n_layers_model = int(number_layers) + 1
        
        # Collect params from args
        param_list = list(params)
        model.set_parameters(param_list, model.n_layers_model)
        
        x_array = np.arange(theta_min, theta_max + 0.001, step_size)
        theta_rad = np.radians(x_array / 2.0)
        s_array = 2 * np.sin(theta_rad) / model.LAM
        
        y_calc = model.all_inten(s_array, model.params)
        
        fig = plt.figure(figsize=(10, 6))
        plt.plot(x_array, y_calc, label="Calculated")
        plt.xlabel("2 Theta (degrees)")
        plt.ylabel("Intensity")
        plt.title("CarbonXS Calculation")
        plt.legend()
        plt.grid(True)
        
        return fig, "Calculation successful"
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error: {str(e)}"

def run_fit(
    wavelength, tci_pts, integration_width, sample_density,
    goniometer_radius, sample_depth, sample_width, beam_width, number_layers,
    theta_min, theta_max, step_size,
    data_file,
    *args
):
    # Args contains: 18 params values, then 18 refine flags
    params = list(args[:18])
    refine_flags = list(args[18:])
    
    if data_file is None:
        return (None, "Error: No data file uploaded") + tuple(params)
        
    try:
        # Load data
        # Assuming simple x y format
        data = np.loadtxt(data_file.name)
        if data.shape[1] < 2:
             return (None, "Error: Invalid data file format. Expected at least 2 columns (x, y)") + tuple(params)
             
        x_obs = data[:, 0]
        y_obs = data[:, 1]
        
        # Filter data by theta range
        mask = (x_obs >= theta_min) & (x_obs <= theta_max)
        x_obs = x_obs[mask]
        y_obs = y_obs[mask]
        
        if len(x_obs) == 0:
            return (None, "Error: No data points in specified range") + tuple(params)

        model = CarbonXSModel()
        model.LAM = wavelength
        model.NPHI = int(tci_pts)
        model.NSG = int(integration_width)
        model.RDENS = sample_density
        model.L0 = goniometer_radius
        model.WD = sample_depth
        model.WW = sample_width
        model.BW = beam_width
        model.n_layers_model = int(number_layers) + 1
        
        fitter = CarbonXSFit(model)
        
        final_params, res = fitter.fit(params, refine_flags, x_obs, y_obs)
        
        # Recalculate for plot
        model.set_parameters(final_params, model.n_layers_model)
        theta_rad = np.radians(x_obs / 2.0)
        s_array = 2 * np.sin(theta_rad) / model.LAM
        y_calc = model.all_inten(s_array, model.params)
        
        fig = plt.figure(figsize=(10, 6))
        plt.plot(x_obs, y_obs, 'b.', label="Observed")
        plt.plot(x_obs, y_calc, 'r-', label="Calculated")
        plt.plot(x_obs, y_obs - y_calc, 'g-', label="Difference")
        plt.xlabel("2 Theta (degrees)")
        plt.ylabel("Intensity")
        plt.title("CarbonXS Fit Result")
        plt.legend()
        plt.grid(True)
        
        msg = f"Fit {'Success' if res.success else 'Failed'}: {res.message}\nCost: {res.cost}"
        
        # Return fig, msg, and updated params
        return (fig, msg) + tuple(final_params)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return (None, f"Error: {str(e)}") + tuple(params)

with gr.Blocks(title="CarbonXS Web") as app:
    gr.Markdown("# CarbonXS Web Interface")
    
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Accordion("Diffractometer & Model Settings", open=False):
                wavelength = gr.Number(value=1.5418, label="Wavelength (Å)")
                tci_pts = gr.Number(value=10, label="TCI Points", precision=0)
                integration_width = gr.Number(value=3, label="Integration Width", precision=0)
                sample_density = gr.Number(value=1.0, label="Sample Density")
                goniometer_radius = gr.Number(value=200.0, label="Goniometer Radius (mm)")
                sample_depth = gr.Number(value=2.0, label="Sample Depth (mm)")
                sample_width = gr.Number(value=20.0, label="Sample Width (mm)")
                beam_width = gr.Number(value=1.0, label="Beam Width (mm)")
                number_layers = gr.Dropdown(choices=[("1 Layer", 0), ("2 Layers", 1)], value=0, label="Model Layers")
                
            with gr.Accordion("Range Settings", open=True):
                theta_min = gr.Number(value=10.0, label="2Theta Min")
                theta_max = gr.Number(value=90.0, label="2Theta Max")
                step_size = gr.Number(value=0.1, label="Step Size")
            
            gr.Markdown("### Parameters")
            param_inputs = []
            refine_inputs = []
            
            for i, label in enumerate(PARAM_LABELS):
                with gr.Row():
                    p_input = gr.Number(value=DEFAULT_PARAMS[i], label=label, scale=2)
                    r_input = gr.Checkbox(label="Refine", value=False, scale=1)
                    param_inputs.append(p_input)
                    refine_inputs.append(r_input)
                    
        with gr.Column(scale=2):
            plot_output = gr.Plot(label="Diffraction Pattern")
            msg_output = gr.Textbox(label="Output", lines=3)
            
            with gr.Row():
                calc_btn = gr.Button("Calculate", variant="primary")
                fit_btn = gr.Button("Fit", variant="secondary")
            
            data_upload = gr.File(label="Upload Data File (x y format)")

    # Event handlers
    calc_inputs = [
        wavelength, tci_pts, integration_width, sample_density,
        goniometer_radius, sample_depth, sample_width, beam_width, number_layers,
        theta_min, theta_max, step_size
    ] + param_inputs
    
    calc_btn.click(
        fn=calculate_pattern,
        inputs=calc_inputs,
        outputs=[plot_output, msg_output]
    )
    
    fit_inputs = [
        wavelength, tci_pts, integration_width, sample_density,
        goniometer_radius, sample_depth, sample_width, beam_width, number_layers,
        theta_min, theta_max, step_size,
        data_upload
    ] + param_inputs + refine_inputs
    
    fit_outputs = [plot_output, msg_output] + param_inputs
    
    fit_btn.click(
        fn=run_fit,
        inputs=fit_inputs,
        outputs=fit_outputs
    )

if __name__ == "__main__":
    app.launch()
