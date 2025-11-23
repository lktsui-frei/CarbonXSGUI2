from fastapi import APIRouter, HTTPException
from ..models import CalculationRequest, CalculationResponse, FittingRequest, FittingResponse
import numpy as np
import sys
import os

# Add parent directory to path to import legacy modules
# This assumes the app is run from the root directory or carbonxs_web is in python path
# But to be safe we add the root directory relative to this file
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from carbonxs_core import CarbonXSModel
from carbonxs_fit import CarbonXSFit

router = APIRouter()

@router.post("/calculate", response_model=CalculationResponse)
def calculate_pattern(request: CalculationRequest):
    try:
        model = CarbonXSModel()
        # Set model constants
        model.LAM = request.settings.wavelength
        model.NPHI = request.settings.tci_pts
        model.NSG = request.settings.integration_width
        model.RDENS = request.settings.sample_density
        model.L0 = request.settings.goniometer_radius
        model.WD = request.settings.sample_depth
        model.WW = request.settings.sample_width
        model.BW = request.settings.beam_width
        model.n_layers_model = request.settings.number_layers + 1
        
        model.set_parameters(request.params, model.n_layers_model)
        
        # Generate X array
        x_array = np.arange(request.theta_min, request.theta_max + 0.001, request.step_size)
        theta_rad = np.radians(x_array / 2.0)
        s_array = 2 * np.sin(theta_rad) / model.LAM
        
        y_calc = model.all_inten(s_array, model.params)
        
        return CalculationResponse(
            x=x_array.tolist(),
            y_calc=y_calc.tolist(),
            params=request.params
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fit", response_model=FittingResponse)
def fit_pattern(request: FittingRequest):
    try:
        model = CarbonXSModel()
        # Set model constants
        model.LAM = request.settings.wavelength
        model.NPHI = request.settings.tci_pts
        model.NSG = request.settings.integration_width
        model.RDENS = request.settings.sample_density
        model.L0 = request.settings.goniometer_radius
        model.WD = request.settings.sample_depth
        model.WW = request.settings.sample_width
        model.BW = request.settings.beam_width
        model.n_layers_model = request.settings.number_layers + 1
        
        fitter = CarbonXSFit(model)
        
        # Convert lists to numpy arrays
        x_obs = np.array(request.x_obs)
        y_obs = np.array(request.y_obs)
        weights = np.array(request.weights) if request.weights else None
        
        final_params, res = fitter.fit(
            request.params, 
            request.refine_flags, 
            x_obs, 
            y_obs, 
            weights=weights
        )
        
        # Recalculate with final params
        model.set_parameters(final_params, model.n_layers_model)
        theta_rad = np.radians(x_obs / 2.0)
        s_array = 2 * np.sin(theta_rad) / model.LAM
        y_calc = model.all_inten(s_array, model.params)
        
        return FittingResponse(
            final_params=final_params.tolist(),
            y_calc=y_calc.tolist(),
            success=res.success if res else False,
            message=res.message if res else "Fit failed"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
