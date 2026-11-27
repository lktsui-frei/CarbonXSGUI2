import numpy as np
from scipy.optimize import least_squares
from carbonxs_core import CarbonXSModel

class FitAbortedError(Exception):
    """Raised when a fit is cancelled via abort_event."""


class CarbonXSFit:
    def __init__(self, model):
        self.model = model
        
    def residuals(self, refined_params, full_params, refine_mask, s_array, y_obs, weights=None, loss_callback=None, abort_event=None):
        """
        Calculate residuals for least_squares
        refined_params: List of parameters being refined
        full_params: All 18 parameters (some fixed, some updated from refined_params)
        refine_mask: Boolean array indicating which parameters are refined
        s_array: Scattering vector array
        y_obs: Observed intensity
        weights: Optional weights (1/sigma)
        loss_callback: Optional callback function(cost)
        abort_event: Optional threading.Event for cooperative cancellation
        """
        if abort_event is not None and abort_event.is_set():
            raise FitAbortedError("Fit aborted by user.")
        # Update full_params with refined_params
        current_params = full_params.copy()
        current_params[refine_mask] = refined_params
        
        # print(f"DEBUG: Residuals called. Refined params: {refined_params}")
        
        # Calculate model intensity
        self.model.set_parameters(current_params, self.model.n_layers_model)
        y_calc = self.model.all_inten(s_array, self.model.params)
        
        diff = y_calc - y_obs
        
        if weights is not None:
            diff = diff * weights
            
        if loss_callback is not None:
            # Calculate cost (0.5 * sum(residuals**2))
            cost = 0.5 * np.sum(diff**2)
            loss_callback(cost)
            
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
        # 0: Scale >= 0
        lower[0] = 0.0
        # 1-6: Background parameters
        # 7: A (Cell constant) > 0
        lower[7] = 1.0  # Reasonable lower bound for A
        
        # 8: d002 (Layer spacing) > 0
        lower[8] = 1.0
        
        # 9: La (Coherence length) > 0
        lower[9] = 1.0
        
        # 10: M (Number of layers) > 0
        lower[10] = 0.1
        
        # 11: SM (Width of M distribution) >= 0
        lower[11] = 0.0
        
        # 12: Dab (In plane strain) >= 0
        lower[12] = 0.0
        
        # 13: Del (Interplanar strain) >= 0
        lower[13] = 0.0
        
        # 14: Pr (Probability of Random Stacking) 0 <= Pr <= 1
        lower[14] = 0.0
        upper[14] = 1.0
        
        # 15: Pt (Prob 3R) or g (Fraction low strain) 0 <= Pt <= 1
        lower[15] = 0.0
        upper[15] = 1.0
        
        # 16: B (Temp factor) >= 0
        lower[16] = 0.0
        
        # 17: PO (Preferred orientation) >= 0
        lower[17] = 0.0
        
        return lower, upper

    def fit(self, initial_params, refine_flags, x_data, y_data, weights="poisson", max_nfev=None, loss_callback=None, ftol=1e-8, xtol=1e-8, abort_event=None):
        """
        Perform the least squares fit.
        initial_params: Initial guess for all 18 parameters
        refine_flags: Boolean list/array of length 18, True if parameter should be refined
        x_data: 2theta values (degrees)
        y_data: Observed intensity
        weights: 'poisson' (default, 1/sqrt(max(y, 1.0))), None (unweighted), or array of weights
        max_nfev: Maximum number of function evaluations
        loss_callback: Optional callback function(cost)
        ftol, xtol: Convergence tolerances passed to scipy.optimize.least_squares
        """
        # Convert x_data (2theta) to s_array
        theta_rad = np.radians(x_data / 2.0)
        s_array = 2 * np.sin(theta_rad) / self.model.LAM
        
        initial_params = np.asarray(initial_params, dtype=np.float64)
        y_data = np.asarray(y_data, dtype=np.float64)
        refine_mask = np.array(refine_flags, dtype=bool)

        if isinstance(weights, str) and weights.lower() == "poisson":
            resolved_weights = 1.0 / np.sqrt(np.maximum(y_data, 1.0))
        elif weights is None:
            resolved_weights = None
        else:
            resolved_weights = np.asarray(weights, dtype=np.float64)
        
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
            args=(initial_params, refine_mask, s_array, y_data, resolved_weights, loss_callback, abort_event),
            x_scale='jac',
            ftol=ftol,
            xtol=xtol,
            max_nfev=max_nfev,
            verbose=0
        )
        
        # Construct final parameters
        final_params = initial_params.copy()
        final_params[refine_mask] = res.x
        
        return final_params, res

    def compute_fit_statistics(self, final_params, refine_mask, res):
        """
        Compute Fortran-compatible fit statistics from scipy OptimizeResult:
        reduced_chi2, parameter ESDs (siga), 18x18 correlation matrix (%), and Lc +/- slc.
        """
        final_params = np.asarray(final_params, dtype=np.float64)
        mask = np.asarray(refine_mask, dtype=bool)
        npar = len(final_params)

        siga = np.zeros(npar, dtype=np.float64)
        corr = np.zeros((npar, npar), dtype=np.float64)
        reduced_chi2 = 0.0

        if res is not None and hasattr(res, 'fun') and res.fun is not None:
            ndat = len(res.fun)
            mfit = int(np.sum(mask))
            dof = max(ndat - mfit, 1)
            reduced_chi2 = float(np.sum(res.fun**2) / dof)

            if mfit > 0 and hasattr(res, 'jac') and res.jac is not None and res.jac.size > 0:
                cov_sub = np.linalg.pinv(res.jac.T @ res.jac)
                cov_full = np.zeros((npar, npar), dtype=np.float64)
                refined_idx = np.flatnonzero(mask)
                cov_full[np.ix_(refined_idx, refined_idx)] = cov_sub

                siga = np.sqrt(np.maximum(np.diag(cov_full), 0.0))
                denom = np.outer(siga, siga)
                valid = denom > 0.0
                corr[valid] = (cov_full[valid] / denom[valid]) * 100.0

        d002 = final_params[8]
        m_layers = final_params[10]
        lc = float(d002 * m_layers)
        rel_sq = 0.0
        if abs(d002) > 1e-12:
            rel_sq += (siga[8] / d002) ** 2
        if abs(m_layers) > 1e-12:
            rel_sq += (siga[10] / m_layers) ** 2
        slc = float(abs(lc) * np.sqrt(rel_sq))

        return {
            'reduced_chi2': reduced_chi2,
            'siga': siga,
            'corr': corr,
            'lc': lc,
            'slc': slc,
        }

