import numpy as np
from scipy.special import j0
import math

class CarbonXSModel:
    def __init__(self):
        self.LAM = 1.5418
        self.NPHI = 10
        self.NSG = 3
        self.RDENS = 1.0
        self.L0 = 200.0
        self.WD = 2.0
        self.WW = 20.0
        self.BW = 1.0
        self.MU = 0.9  # Absorption of carbon (mm^-1)
        
        # Parameters A(1) to A(18)
        self.params = np.zeros(19)
        self.n_layers_model = 1 # 1 or 2

    def set_parameters(self, params, n_layers_model=1):
        """
        Sets the model parameters.
        params: list or array of 18 parameters.
        """
        self.params = np.array(params)
        self.n_layers_model = n_layers_model
        
        # Rescale for 2 layer model as in Fortran code
        if self.n_layers_model == 2:
             self.params[10] /= 2.0
             self.params[11] /= 2.0
             self.params[13] *= 2.0
             self.params[14] *= 2.0
             self.params[15] *= 2.0

    def f_carb(self, stl):
        """
        Carbon form factor
        stl: sin(theta)/lambda = s/2
        Vectorized version.
        """
        # Coefficients from Fortran code
        a = np.array([2.310000, 1.020000, 1.588600, 0.865000, 0.215600])
        b = np.array([20.843900, 10.207500, 0.568700, 51.651200, 0.000000])
        dfp = -0.017
        
        # stl can be an array
        stl_sq = stl**2
        
        # Use broadcasting: a is (5,), stl_sq is (N,) -> (5, N)
        # Or just sum manually
        val = dfp
        for i in range(5):
            val += a[i] * np.exp(-b[i] * stl_sq)
        return val

    def etag(self, l, s, s0, p, dab):
        """
        Calculate Gaussian rod shape in the AB plane
        Vectorized version.
        """
        x = s * np.cos(p) - s0
        w = 2.0 / np.sqrt(3.0 * np.pi) / l + dab * s0
        ex = np.exp(-2 * (x / w)**2)
        a_val = (w - dab * s0) / w
        return a_val * ex

    def gmod(self, h, k, l_val, m, sm, del_strain, pr, pt):
        """
        Calculate Crystal Modulation Function G(s)
        Vectorized version.
        """
        dhk = 1.0 if (h == 0 and k == 0) else 0.0
        
        # Phase factors
        e1pil = np.exp(1j * np.pi * l_val)
        e2pil = np.exp(1j * 2 * np.pi * l_val)
        edel = np.exp(-2 * (np.pi * del_strain * l_val)**2)
        
        if self.n_layers_model == 1:
            ehk = pr * dhk + (1 - pr) * np.cos(2.0/3.0 * np.pi * (h - k))
            if pt < 1.0:
                el = e1pil * (pt + (1 - pt) * edel)
            else:
                el = e1pil * edel
        else: # 2 layer model
            ehk = pr * dhk + (1 - pr) + pt * (np.exp(1j * 4.0/3.0 * np.pi * (h - k)) - 1.0)
            el = e2pil * edel
            
        q = ehk * el
        
        # Modulation function
        # Check for singularities (Real(Q) == 1.0)
        # Using a small epsilon for float comparison
        mask_singularity = (np.abs(q.real - 1.0) < 1e-6) & (np.abs(q.imag) < 1e-6)
        
        gg = np.zeros_like(q.real)
        
        # Handle singularity
        if np.any(mask_singularity):
            gg[mask_singularity] = (m**2 + sm**2) / m
            
        # Handle normal case
        mask_normal = ~mask_singularity
        if np.any(mask_normal):
            q_norm = q[mask_normal]
            lq = np.log(q_norm)
            qm = np.exp(m * lq)
            es = 0.5 * (sm * lq)**2
            
            # IF (REAL(ES) .GT. 5.0) ES=CMPLX(5.0D0,DIMAG(ES))
            mask_es = es.real > 5.0
            if np.any(mask_es):
                es[mask_es] = 5.0 + 1j * es[mask_es].imag
            
            es = np.exp(es)
            
            gg[mask_normal] = ((1 + q_norm) / (1 - q_norm) + 
                               2.0 / m * q_norm * (qm * es - 1) / (1 - q_norm)**2).real
            
        return gg / m

    def igran(self, phi, s, s0, h, k, d002, la, m, sm, dab, del_strain, pr, pt, po):
        """
        Integrand for PHI integral
        Vectorized version.
        """
        l_val = s * 2 * d002 * np.sin(phi)
        
        g = self.gmod(h, k, l_val, m, sm, del_strain / (2.0 * d002), pr, pt)
        et = self.etag(la, s, s0, phi, dab)
        poc = np.exp(-po * np.cos(phi)**2)
        
        if self.n_layers_model == 1:
            cs = 1.0
        else:
            cs = 2.0 * np.cos(np.pi * ((h - k) / 3.0 + l_val / 2.0))**2
            
        return g * et * poc * cs

    def kern(self, thi, thj):
        """
        Calculate convolution kernel value for a pair of angles
        """
        if thi == thj:
            return 1.0
        t = (thj - thi) * self.L0 / np.cos(thi)
        if t < 0.0:
            return 0.0
        eps = 1.0e-4
        if t > self.WD + eps:
            return 0.0
        sin_thj = np.sin(thj)
        tan_thj = np.tan(thj)
        t1 = 0.5 * (self.WW - self.BW / (2 * sin_thj)) * tan_thj
        
        denom = sin_thj * np.cos(thj)
        if abs(denom) < 1e-10: denom = 1e-10
        exp_term = np.exp(-2 * self.MU * self.RDENS * self.L0 * (thj - thi) / denom)
        
        if t <= t1:
            return exp_term
        t2 = 0.5 * (self.WW + self.BW / (2 * sin_thj)) * tan_thj
        if t <= t2:
            return exp_term * (t2 - t) / (t2 - t1)
        return 0.0

    def phint(self, h, k, s_array, a_cell, d002, la, m, sm, dab, del_strain, pr, pt, po):
        """
        Calculate Phi integral numerically for an array of s values
        """
        s0 = np.sqrt(4.0/3.0 * (h**2 + k**2 + h*k)) / a_cell
        
        # Determine integration limits in S
        sig = (2.0 / np.sqrt(3.0 * np.pi) / la + dab * s0) / 2.0
        s1 = s0 - self.NSG * sig
        s2 = s0 + self.NSG * sig
        
        # Masks for regions
        mask_zero = s_array < s1
        mask_full = (s_array >= s1) & (s_array < s2)
        mask_two = s_array >= s2
        
        ph_int = np.zeros_like(s_array)
        
        # Pre-calculate phi limits
        # Avoid division by zero or domain errors
        ratio1 = np.clip(s1 / s_array, -1.0, 1.0)
        ratio2 = np.clip(s2 / s_array, -1.0, 1.0)
        
        phi1 = np.arccos(ratio1)
        phi2 = np.arccos(ratio2)
        
        # We need to integrate over phi.
        # Instead of adaptive loop, use fixed grid.
        # NPHI points.
        
        # Region 1: Full intersection (s1 <= s < s2)
        # Integration range: [-phi1, phi1]
        # dphi = (phi1 - (-phi1)) / (nphi_eff - 1) = 2*phi1 / (nphi_eff - 1)
        # In original code: nphi1 = int(2 * phi1 / dphi) + 1
        # where dphi = (phi1 - phi2) / (NPHI - 1)
        # This is tricky because dphi depends on phi2 which is defined even if s < s2?
        # Yes, phi2 is arccos(s2/s).
        
        dphi_base = (phi1 - phi2) / (self.NPHI - 1)
        
        # Handle Full Intersection
        if np.any(mask_full):
            s_full = s_array[mask_full]
            phi1_full = phi1[mask_full]
            dphi_full = dphi_base[mask_full]
            
            # Number of points varies per s, which is hard to vectorize perfectly.
            # But we can use a fixed grid relative to phi1.
            # Original code: phi starts at -phi1, steps by dphi until phi1.
            # nphi1 = int(2 * phi1 / dphi) + 1
            
            # Let's approximate by using a fixed number of points scaled to cover [-phi1, phi1]
            # Or better, construct a 2D grid (N_s, N_steps)
            # Max steps might be large.
            
            # Let's try to match the original logic but vectorize the loop over steps.
            # Max steps is roughly 2*phi1 / dphi.
            # dphi is roughly (phi1 - phi2)/9.
            # If s is close to s1, phi1 ~ 0, phi2 ~ 0.
            # If s is close to s2, phi1 ~ arccos(s1/s2), phi2 ~ 0.
            
            # To keep it simple and vectorized, let's use a fixed grid of points for integration
            # that covers the maximum possible range, and mask out invalid points?
            # No, that's inefficient.
            
            # Alternative: Use a fixed number of points (e.g. 2*NPHI) for the integration
            # and interpolate?
            # Or just loop over a reasonable number of steps (e.g. 20) and sum.
            
            # Let's use the max nphi1 across the batch?
            nphi1_vals = (2 * phi1_full / dphi_full).astype(np.intp) + 1
            max_nphi1 = np.max(nphi1_vals) if len(nphi1_vals) > 0 else 0
            
            # Limit max steps to avoid memory explosion
            max_nphi1 = min(max_nphi1, 100) 
            
            # Create grid: shape (max_nphi1, N_full)
            steps = np.arange(max_nphi1)[:, np.newaxis]
            phi_grid = -phi1_full + steps * dphi_full
            
            # Mask points where step > nphi1_vals
            valid_mask = steps < nphi1_vals
            
            # Compute integrand
            # Flatten for computation then reshape?
            # Or rely on broadcasting: s_full is (N_full,), phi_grid is (max_nphi1, N_full)
            
            # We need s0, etc for these points
            # s0 is scalar (depends on h,k)
            
            # igran expects arrays of same shape or broadcastable
            # s_full broadcast to (max_nphi1, N_full)
            
            ig = self.igran(phi_grid, s_full, s0, h, k, d002, la, m, sm, dab, del_strain, pr, pt, po)
            
            # Zero out invalid points
            ig[~valid_mask] = 0.0
            
            # Sum
            ph_int[mask_full] = np.sum(ig, axis=0) * dphi_full
            
        # Handle Two Intersections (s >= s2)
        if np.any(mask_two):
            s_two = s_array[mask_two]
            phi2_two = phi2[mask_two]
            dphi_two = dphi_base[mask_two]
            
            # Positive side: [phi2, phi2 + (NPHI-1)*dphi]
            # Negative side: [-phi2, -phi2 - (NPHI-1)*dphi]
            
            # Grid for positive side
            steps = np.arange(self.NPHI)[:, np.newaxis] # (10, 1)
            phi_pos = phi2_two + steps * dphi_two # (10, N_two)
            
            ig_pos = self.igran(phi_pos, s_two, s0, h, k, d002, la, m, sm, dab, del_strain, pr, pt, po)
            sum_pos = np.sum(ig_pos, axis=0)
            
            # Grid for negative side
            phi_neg = -phi2_two - steps * dphi_two
            
            ig_neg = self.igran(phi_neg, s_two, s0, h, k, d002, la, m, sm, dab, del_strain, pr, pt, po)
            sum_neg = np.sum(ig_neg, axis=0)
            
            ph_int[mask_two] = (sum_pos + sum_neg) * dphi_two
            
        return ph_int

    def inten(self, s_array, params):
        """
        Calculate scattered powder intensity at wavevector S (vectorized)
        Handles both scalar and array inputs.
        """
        # Handle scalar input
        is_scalar = np.isscalar(s_array)
        if is_scalar:
            s_array = np.array([s_array])
            
        scale = params[0]
        a_cell = params[7]
        d002 = params[8]
        la = params[9]
        m = params[10]
        sm = params[11]
        dab = params[12]
        del_strain = params[13]
        pr = params[14]
        pt = params[15]
        temp_factor = params[16]
        po = params[17]
        
        hk_list = [(0,0), (1,0), (1,1), (2,0), (2,1)]
        mult_list = [1, 6, 6, 6, 12]
        
        th = np.arcsin(s_array * self.LAM / 2.0)
        psi = 13.3 * np.pi / 180.0
        pol = 0.5 * (1 + np.cos(2*th)**2 * np.cos(2*psi)**2) / s_array
        
        dwf = np.exp(-2.0 * temp_factor * (s_array/2.0)**2)
        
        yfit = np.zeros_like(s_array)
        
        for i, (h, k) in enumerate(hk_list):
            alpha = 2 * np.cos(2.0 * np.pi / 3.0 * (h - k)) * self.f_carb(s_array/2.0)
            
            ph = self.phint(h, k, s_array, a_cell, d002, la, m, sm, dab, del_strain, pr, pt, po)
            
            yfit += mult_list[i] * pol * alpha**2 * dwf * ph
            
        result = scale * yfit
        
        if is_scalar:
            return result[0]
        return result

    def all_inten(self, s_array, params):
        """
        Calculate scattered powder intensity for the whole pattern
        Vectorized version.
        """
        ndat = len(s_array)
        
        # Calculate raw intensities
        y_raw = self.inten(s_array, params)
            
        # Convolution
        if ndat > 1:
            dth = np.arcsin(s_array[1] * self.LAM / 2.0) - np.arcsin(s_array[0] * self.LAM / 2.0)
        else:
            dth = 0.01
            
        th = np.arcsin(s_array * self.LAM / 2.0)
        foot = 1.0 / np.sin(th)
        th_max = self.WD / self.L0 * np.cos(th)
        nj = (th_max / dth).astype(np.intp)
        
        # Construct convolution matrix?
        # A full matrix would be (1151, 1151), which is fine (~10MB).
        
        # Create meshgrid for i and j
        i_idx = np.arange(ndat)
        j_idx = np.arange(ndat)
        I, J = np.meshgrid(i_idx, j_idx, indexing='ij')
        
        # Masks for valid j range
        # j_start = i + 1
        # j_end = i + nj + 1
        # So i < j <= i + nj
        
        mask_conv = (J > I) & (J <= I + nj[:, np.newaxis])
        
        # Compute contributions where mask is true
        # We need th[i] and th[j]
        TH_I = th[:, np.newaxis]
        TH_J = th[np.newaxis, :]
        
        # Kern(th_i, th_j)
        # Vectorized Kern
        # T = (TH_J - TH_I) * L0 / cos(TH_I)
        T = (TH_J - TH_I) * self.L0 / np.cos(TH_I)
        
        # T1, T2 depend on TH_J
        SIN_THJ = np.sin(TH_J)
        TAN_THJ = np.tan(TH_J)
        
        T1 = 0.5 * (self.WW - self.BW / (2 * SIN_THJ)) * TAN_THJ
        T2 = 0.5 * (self.WW + self.BW / (2 * SIN_THJ)) * TAN_THJ
        
        # Broadcast T1, T2 to shape (ndat, ndat)
        T1 = np.broadcast_to(T1, (ndat, ndat))
        T2 = np.broadcast_to(T2, (ndat, ndat))
        
        # Compute EXP_TERM safely
        # Only compute where mask_conv is true to avoid overflow when TH_J < TH_I
        EXP_TERM = np.zeros_like(T)
        
        # We need to compute exp only where it matters (mask_conv)
        # But to be safe and vectorized, we can use np.where or just compute on valid indices
        
        # Argument for exp
        # -2 * MU * RDENS * L0 * (TH_J - TH_I) / (SIN_THJ * np.cos(TH_J))
        # Denominator check
        denom = SIN_THJ * np.cos(TH_J)
        # Avoid division by zero
        denom = np.where(np.abs(denom) < 1e-10, 1e-10, denom)
        
        arg = -2 * self.MU * self.RDENS * self.L0 * (TH_J - TH_I) / denom
        
        # Only compute exp where arg is safe (e.g. < 700) and mask_conv is true
        # If mask_conv is true, TH_J > TH_I, so arg should be negative (safe)
        # But let's be careful
        
        safe_mask = mask_conv & (arg < 700)
        EXP_TERM[safe_mask] = np.exp(arg[safe_mask])
        
        KK = np.zeros_like(T)
        
        mask_t1 = (T <= T1) & mask_conv
        mask_t2 = (T > T1) & (T <= T2) & mask_conv
        
        KK[mask_t1] = EXP_TERM[mask_t1]
        KK[mask_t2] = EXP_TERM[mask_t2] * (T2[mask_t2] - T[mask_t2]) / (T2[mask_t2] - T1[mask_t2])
        
        # DT
        DT = dth * self.L0 / np.cos(TH_J) * (1.0 + TAN_THJ * (TH_J - TH_I)) * foot[:, np.newaxis]
        
        # Convolution sum: 0.5 * dt * (kk * y_raw[j] + k_old * y_raw[j-1])
        # This is tricky because k_old depends on the previous j in the loop.
        # k_old is kern(th, th_{j-1}).
        # In the matrix, K_old[i, j] = K[i, j-1].
        
        # Let's construct the matrix M such that yc = M @ y_raw
        # Term: 0.5 * DT * KK * y_raw[j]
        # Term: 0.5 * DT * K_OLD * y_raw[j-1]
        
        # We can compute the full matrix of coefficients.
        
        # M[i, j] += 0.5 * DT[i, j] * KK[i, j]
        # M[i, j-1] += 0.5 * DT[i, j] * KK[i, j-1]  (approx K_old)
        
        # Actually, let's just compute the sum directly.
        # yc[i] = sum_j ( 0.5 * DT[i,j] * (KK[i,j] * y_raw[j] + KK[i,j-1] * y_raw[j-1]) )
        
        # Shifted arrays for j-1
        # We need to handle indices carefully.
        
        # Let's simplify:
        # contribution from j to i:
        # coeff_j = 0.5 * DT[i,j] * KK[i,j]
        # coeff_j_minus_1 = 0.5 * DT[i,j] * KK[i,j-1]
        
        # We can accumulate these into a single matrix M.
        M = np.zeros((ndat, ndat))
        
        # Term 1: y_raw[j]
        # Only where mask_conv is true
        M[mask_conv] += 0.5 * DT[mask_conv] * KK[mask_conv]
        
        # Term 2: y_raw[j-1]
        # We need to add 0.5 * DT[i,j] * KK[i,j-1] to M[i, j-1]
        
        # Get indices where mask is true
        rows, cols = np.nonzero(mask_conv)
        
        # Set diagonal of KK to 1.0 because Kern(th, th) = 1.0
        # This is needed for KK_prev which shifts KK
        KK[np.arange(ndat), np.arange(ndat)] = 1.0
        
        # KK_prev = KK[rows, cols-1]
        KK_prev = np.zeros_like(KK)
        KK_prev[:, 1:] = KK[:, :-1]
        
        # Using np.add.at for safety
        np.add.at(M, (rows, cols-1), 0.5 * DT[rows, cols] * KK_prev[rows, cols])
        
        # Compute convolution part
        yc = M @ y_raw
        
        # Tail correction (vectorized)
        # thj = th + dth * nj
        THJ_tail = th + dth * nj
        
        DT_tail = (th_max + th - THJ_tail) * self.L0 / np.cos(th_max) * (1.0 + np.tan(th_max) * (th_max - th)) * foot
        FRAC_tail = (th_max + th - THJ_tail) / dth
        
        # KKMAX = Kern(th, th + th_max)
        # T_tail = th_max * L0 / cos(th) -> WD
        # So T = WD.
        # If T > WD + eps -> 0.
        # If T <= T1 ...
        
        # Let's implement a helper for single-point kern
        # But we can just inline the logic or make kern accept arrays
        
        # Kern(th, th+th_max)
        # T = (th+th_max - th)*L0/cos(th) = th_max*L0/cos(th) = WD
        # T = WD.
        # If T > WD + eps -> 0.
        # If T <= T1 ...
        
        T_tail_val = np.full_like(th, self.WD)
        TH_target = th + th_max
        SIN_THT = np.sin(TH_target)
        TAN_THT = np.tan(TH_target)
        
        T1_tail = 0.5 * (self.WW - self.BW / (2 * SIN_THT)) * TAN_THT
        T2_tail = 0.5 * (self.WW + self.BW / (2 * SIN_THT)) * TAN_THT
        
        denom_tail = SIN_THT * np.cos(TH_target)
        denom_tail = np.where(np.abs(denom_tail) < 1e-10, 1e-10, denom_tail)
        EXP_tail = np.exp(-2 * self.MU * self.RDENS * self.L0 * th_max / denom_tail)
        
        KK_MAX = np.zeros_like(th)
        mask_tail1 = T_tail_val <= T1_tail
        mask_tail2 = (T_tail_val > T1_tail) & (T_tail_val <= T2_tail)
        
        KK_MAX[mask_tail1] = EXP_tail[mask_tail1]
        KK_MAX[mask_tail2] = EXP_tail[mask_tail2] * (T2_tail[mask_tail2] - T_tail_val[mask_tail2]) / (T2_tail[mask_tail2] - T1_tail[mask_tail2])
        
        # JJ = min(ndat - 1, i + nj)
        JJ = np.minimum(ndat - 1, i_idx + nj)
        JJ1 = np.minimum(ndat - 1, i_idx + nj + 1)
        
        Y_MAX = FRAC_tail * y_raw[JJ1] + (1 - FRAC_tail) * y_raw[JJ]
        
        # Re-compute K_OLD for tail to be safe
        # K_OLD = Kern(th, th_jj)
        # JJ = min(ndat - 1, i + nj)
        # TH_prev should be th[JJ] or th + dth * (JJ - i)
        
        TH_prev = th + dth * (JJ - i_idx)
        SIN_THP = np.sin(TH_prev)
        TAN_THP = np.tan(TH_prev)
        
        # T_prev = (TH_prev - th) * L0 / cos(th)
        T_tail_prev = (TH_prev - th) * self.L0 / np.cos(th)
        
        T1_prev = 0.5 * (self.WW - self.BW / (2 * SIN_THP)) * TAN_THP
        T2_prev = 0.5 * (self.WW + self.BW / (2 * SIN_THP)) * TAN_THP
        
        denom_prev = SIN_THP * np.cos(TH_prev)
        denom_prev = np.where(np.abs(denom_prev) < 1e-10, 1e-10, denom_prev)
        EXP_prev = np.exp(-2 * self.MU * self.RDENS * self.L0 * (TH_prev - th) / denom_prev)
        
        K_OLD_tail = np.zeros_like(th)
        mask_prev1 = T_tail_prev <= T1_prev
        mask_prev2 = (T_tail_prev > T1_prev) & (T_tail_prev <= T2_prev)
        
        K_OLD_tail[mask_prev1] = EXP_prev[mask_prev1]
        K_OLD_tail[mask_prev2] = EXP_prev[mask_prev2] * (T2_prev[mask_prev2] - T_tail_prev[mask_prev2]) / (T2_prev[mask_prev2] - T1_prev[mask_prev2])
        
        yc += 0.5 * DT_tail * (KK_MAX * Y_MAX + K_OLD_tail * y_raw[JJ])
        
        # Normalization
        norm = 2.0 * self.MU * self.RDENS
        yc *= norm
        
        # Background
        bg = params[1] + params[2]*s_array + params[3]*s_array**2 + params[4]*s_array**3 + params[5]*s_array**4 + params[6]/s_array
        yc += bg
        
        return yc
