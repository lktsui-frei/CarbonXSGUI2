from pydantic import BaseModel, Field
from typing import List, Optional

class ModelSettings(BaseModel):
    wavelength: float = Field(..., description="Wavelength (Angstrom)")
    tci_pts: int = Field(..., description="Number of points for TCI integration")
    integration_width: int = Field(..., description="Integration width")
    sample_density: float = Field(..., description="Sample density")
    goniometer_radius: float = Field(..., description="Goniometer radius (mm)")
    sample_depth: float = Field(..., description="Sample depth (mm)")
    sample_width: float = Field(..., description="Sample width (mm)")
    beam_width: float = Field(..., description="Beam width (mm)")
    number_layers: int = Field(..., description="Number of layers (0 for 1-layer, 1 for 2-layer model)")

class CalculationRequest(BaseModel):
    params: List[float] = Field(..., min_items=18, max_items=18, description="The 18 model parameters")
    settings: ModelSettings
    theta_min: float = Field(10.0, description="Minimum 2Theta")
    theta_max: float = Field(90.0, description="Maximum 2Theta")
    step_size: float = Field(0.1, description="Step size for 2Theta")

class CalculationResponse(BaseModel):
    x: List[float] = Field(..., description="2Theta values")
    y_calc: List[float] = Field(..., description="Calculated Intensity")
    params: List[float] = Field(..., description="Parameters used for calculation")

class FittingRequest(BaseModel):
    params: List[float] = Field(..., min_items=18, max_items=18, description="Initial parameters")
    refine_flags: List[bool] = Field(..., min_items=18, max_items=18, description="Flags for parameters to refine")
    x_obs: List[float] = Field(..., description="Observed 2Theta values")
    y_obs: List[float] = Field(..., description="Observed Intensity values")
    weights: Optional[List[float]] = Field(None, description="Weights for fitting")
    settings: ModelSettings

class FittingResponse(BaseModel):
    final_params: List[float] = Field(..., description="Refined parameters")
    y_calc: List[float] = Field(..., description="Calculated Intensity with final parameters")
    success: bool
    message: str
