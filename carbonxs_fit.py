import numpy as np
from scipy.optimize import least_squares
from carbonxs_core import CarbonXSModel

class CarbonXSFit:
    def __init__(self, model):
        self.model = model
        
    def residuals(self, refined_params, full_params, refine_mask, s_array, y_obs, weights=None):
        """
        Calculate residuals for least_squares
        refined_params: List of parameters being refined
        full_params: All 18 parameters (some fixed, some updated from refined_params)
        refine_mask: Boolean array indicating which parameters are refined
        s_array: Scattering vector array
        y_obs: Observed intensity
        weights: Optional weights (1/sigma)
        """
        # Update full_params with refined_params
        current_params = full_params.copy()
        current_params[refine_mask] = refined_params
        
        print(f"DEBUG: Residuals called. Refined params: {refined_params}")
        
        # Calculate model intensity
        # Note: model.all_inten expects parameters in the "calculation" scale if n_layers=2
        # But here we are dealing with "user-facing" parameters usually.
        # However, carbonxs_core.set_parameters handles the rescaling.
        # But wait, all_inten takes 'params' argument.
        # And in verify_port.py we saw that we need to pass the RESCALED parameters to all_inten.
        
        # So we should use model.set_parameters to handle the rescaling logic
        # and then pass model.params to all_inten.
        
        self.model.set_parameters(current_params, self.model.n_layers_model)
        y_calc = self.model.all_inten(s_array, self.model.params)
        
        diff = y_calc - y_obs
        
        if weights is not None:
            return diff * weights
        else:
            return diff
            
    def _get_parameter_bounds(self):
        """
        Define physical bounds for all 18 parameters.
        Returns tuple of (lower_bounds, upper_bounds) arrays.
        """
        # Initialize with very wide bounds (-inf, inf)
        lower = np.full(18, -np.inf)
        upper = np.full(18, np.inf)
        
        # Parameter indices (0-based):
        # 0: Scale
        # 1-6: Background parameters
        # 7: A (Cell constant) > 0
        lower[7] = 1.0  # Reasonable lower bound for A
        
        # 8: d002 (Layer spacing) > 0
        lower[8] = 1.0
        
        # 9: La (Coherence length) > 0
        lower[9] = 1.0
        
        # 10: M (Number of layers) > 0
        lower[10] = 0.1
        
        # 11: SM (Width of M distribution) > 0
        lower[11] = 0.0
        
        # 12: Dab (In plane strain) >= 0
        lower[12] = 0.0
        
        # 13: Del (Interplanar strain) >= 0
        lower[13] = 0.0
        
        # 14: Pr (Probability of Random Stacking) 0 <= Pr < 1
        # Constrain to slightly less than 1 to avoid singularity
        lower[14] = 0.0
        upper[14] = 0.99999
        
        # 15: Pt (Prob 3R) or g (Fraction low strain) 0 <= Pt < 1
        lower[15] = 0.0
        upper[15] = 0.99999
        
        # 16: B (Temp factor) >= 0
        lower[16] = 0.0
        
        # 17: PO (Preferred orientation) >= 0
        lower[17] = 0.0
        
        return lower, upper

    def fit(self, initial_params, refine_flags, x_data, y_data, weights=None, max_nfev=None):
        """
        Perform the least squares fit.
        initial_params: Initial guess for all 18 parameters
        refine_flags: Boolean list/array of length 18, True if parameter should be refined
        x_data: 2theta values (degrees)
        y_data: Observed intensity
        weights: Optional weights (1/sigma)
        """
        # Convert x_data (2theta) to s_array
        theta_rad = np.radians(x_data / 2.0)
        s_array = 2 * np.sin(theta_rad) / self.model.LAM
        
        initial_params = np.array(initial_params)
        refine_mask = np.array(refine_flags, dtype=bool)
        
        # Extract parameters to be refined
        x0 = initial_params[refine_mask]
        
        if len(x0) == 0:
            print("No parameters to refine.")
            return initial_params, None
            
        # Get bounds
        lower_bounds, upper_bounds = self._get_parameter_bounds()
        
        # Extract bounds for refined parameters
        refined_lower = lower_bounds[refine_mask]
        refined_upper = upper_bounds[refine_mask]
        
        # Ensure initial guess is within bounds
        x0 = np.clip(x0, refined_lower, refined_upper)
        
        # Run optimization
        res = least_squares(
            self.residuals, 
            x0, 
            bounds=(refined_lower, refined_upper),
            args=(initial_params, refine_mask, s_array, y_data, weights),
            max_nfev=max_nfev,
            verbose=0  # Set to 0 to reduce console output
        )
        
        # Construct final parameters
        final_params = initial_params.copy()
        final_params[refine_mask] = res.x
        
        return final_params, res
