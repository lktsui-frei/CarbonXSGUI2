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
        
        # Modulation function: handle singularities q == 1 and q == 0, plus q -> 1 Taylor branch
        scale_m = max(abs(m), abs(sm), 1.0)
        dist_one = np.abs(1.0 - q)
        mask_exact = dist_one < 1e-12
        mask_near = (~mask_exact) & (dist_one < 1e-3) & (dist_one * scale_m < 1e-2)
        mask_zero = np.abs(q) < 1e-15

        gg = np.zeros_like(q.real)

        if np.any(mask_exact):
            gg[mask_exact] = (m**2 + sm**2) / m

        if np.any(mask_near):
            delta = 1.0 - q[mask_near]
            e1 = -m
            e2 = -0.5 * m + 0.5 * sm**2
            e3 = -(1.0 / 3.0) * m + 0.5 * sm**2
            e4 = -0.25 * m + (11.0 / 24.0) * sm**2
            d2 = e2 + 0.5 * e1**2
            d3 = e3 + e1 * e2 + (e1**3) / 6.0
            d4 = e4 + e1 * e3 + 0.5 * e2**2 + 0.5 * (e1**2) * e2 + (e1**4) / 24.0
            gg[mask_near] = (
                (m**2 + sm**2) / m
                + (2.0 / m) * (d3 - d2) * delta
                + (2.0 / m) * (d4 - d3) * (delta**2)
            ).real

        if np.any(mask_zero):
            gg[mask_zero] = 1.0

        # Handle normal case
        mask_normal = (~mask_exact) & (~mask_near) & (~mask_zero)
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

    def _kern_vec(self, thi, thj):
        """
        Vectorized convolution kernel for arrays or scalars of angles (radians).
        Matches Fortran KERN(THI, THJ) semantics.
        """
        thi_arr, thj_arr = np.broadcast_arrays(np.asarray(thi, dtype=np.float64), np.asarray(thj, dtype=np.float64))
        out = np.zeros_like(thi_arr, dtype=np.float64)

        same_mask = thi_arr == thj_arr
        out[same_mask] = 1.0

        t = (thj_arr - thi_arr) * self.L0 / np.cos(thi_arr)
        eps = 1.0e-4
        active = (~same_mask) & (t >= 0.0) & (t <= self.WD + eps)
        if not np.any(active):
            return out

        thj_a = thj_arr[active]
        t_a = t[active]
        sin_thj = np.sin(thj_a)
        tan_thj = np.tan(thj_a)

        t1 = 0.5 * (self.WW - self.BW / (2.0 * sin_thj)) * tan_thj
        t2 = 0.5 * (self.WW + self.BW / (2.0 * sin_thj)) * tan_thj

        denom = sin_thj * np.cos(thj_a)
        denom = np.where(np.abs(denom) < 1e-10, 1e-10, denom)
        arg = -2.0 * self.MU * self.RDENS * self.L0 * (thj_a - thi_arr[active]) / denom
        exp_term = np.where(arg < 700.0, np.exp(np.minimum(arg, 700.0)), np.exp(700.0))

        val = np.zeros_like(t_a)
        m1 = t_a <= t1
        m2 = (t_a > t1) & (t_a <= t2)
        val[m1] = exp_term[m1]
        val[m2] = exp_term[m2] * (t2[m2] - t_a[m2]) / (t2[m2] - t1[m2])

        out[active] = val
        return out

    def kern(self, thi, thj):
        """
        Calculate convolution kernel value for a pair of angles
        """
        return float(self._kern_vec(thi, thj))

    def phint(self, h, k, s_array, a_cell, d002, la, m, sm, dab, del_strain, pr, pt, po):
        """
        Calculate Phi integral numerically for an array of s values
        """
        s_array = np.asarray(s_array, dtype=np.float64)
        s0 = np.sqrt(4.0 / 3.0 * (h**2 + k**2 + h * k)) / a_cell

        # Determine integration limits in S
        sig = (2.0 / np.sqrt(3.0 * np.pi) / la + dab * s0) / 2.0
        s1 = s0 - self.NSG * sig
        s2 = s0 + self.NSG * sig

        # Strict region masks matching CARBONXS.FOR (avoids 0/0 when s == s1)
        mask_pos = s_array > 0.0
        mask_full = mask_pos & (s_array > s1) & (s_array < s2)
        mask_two = mask_pos & (s_array > s2)

        ph_int = np.zeros_like(s_array, dtype=np.float64)
        if not (np.any(mask_full) or np.any(mask_two)):
            return ph_int

        # Guard s_array <= 0 before division
        s_safe = np.where(mask_pos, s_array, 1.0)
        ratio1 = np.clip(s1 / s_safe, -1.0, 1.0)
        ratio2 = np.clip(s2 / s_safe, -1.0, 1.0)

        phi1 = np.arccos(ratio1)
        phi2 = np.arccos(ratio2)

        nphi_denom = max(int(self.NPHI) - 1, 1)
        dphi_base = (phi1 - phi2) / float(nphi_denom)

        # Handle Full Intersection (s1 < s < s2): phi2 == 0, so step count is 2*(NPHI-1) + 1
        if np.any(mask_full):
            s_full = s_array[mask_full]
            phi1_full = phi1[mask_full]
            dphi_full = dphi_base[mask_full]

            nphi1 = 2 * nphi_denom + 1
            steps = np.arange(nphi1)[:, np.newaxis]
            phi_grid = -phi1_full + steps * dphi_full

            ig = self.igran(phi_grid, s_full, s0, h, k, d002, la, m, sm, dab, del_strain, pr, pt, po)
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
        Calculate scattered powder intensity for the whole pattern.
        Uses a banded vectorized loop matching Fortran ALLINTEN semantics in O(N * max_nj) memory.
        """
        s_array = np.asarray(s_array, dtype=np.float64)
        ndat = len(s_array)
        if ndat == 0:
            return np.array([], dtype=np.float64)

        # Calculate raw intensities
        y_raw = self.inten(s_array, params)

        th = np.arcsin(s_array * self.LAM / 2.0)
        if ndat > 1:
            dth = th[1] - th[0]
        else:
            dth = 0.01

        foot = 1.0 / np.sin(th)
        th_max = self.WD / self.L0 * np.cos(th)
        nj = (th_max / dth).astype(np.intp)

        # Banded convolution matching CARBONXS.FOR lines 414-428:
        # Extrapolates THJ = TH + DTH * step and clamps data index JJ = min(ndat - 1, i + step).
        yc = np.zeros(ndat, dtype=np.float64)
        max_nj = int(np.max(nj)) if ndat > 0 else 0
        k_old = np.ones(ndat, dtype=np.float64)
        idx = np.arange(ndat)

        for step in range(1, max_nj + 1):
            active = step <= nj
            if not np.any(active):
                continue
            th_a = th[active]
            thj = th_a + dth * step
            kk = self._kern_vec(th_a, thj)
            dt = dth * self.L0 / np.cos(thj) * (1.0 + np.tan(thj) * (thj - th_a)) * foot[active]
            jj = np.minimum(ndat - 1, idx[active] + step)
            jj_prev = np.maximum(0, jj - 1)
            yc[active] += 0.5 * dt * (kk * y_raw[jj] + k_old[active] * y_raw[jj_prev])
            k_old[active] = kk

        # Tail correction between last grid point and end of kernel (CARBONXS.FOR lines 432-440).
        # k_old holds the exact Fortran KOLD (1.0 if nj == 0, else KERN(th, th + dth * nj)).
        thj_tail = th + dth * nj
        dt_tail = (th_max + th - thj_tail) * self.L0 / np.cos(th_max) * (1.0 + np.tan(th_max) * (th_max - th)) * foot
        frac_tail = (th_max + th - thj_tail) / dth
        kk_max = self._kern_vec(th, th + th_max)

        jj_tail = np.minimum(ndat - 1, idx + nj)
        jj1_tail = np.minimum(ndat - 1, idx + nj + 1)
        y_max = frac_tail * y_raw[jj1_tail] + (1.0 - frac_tail) * y_raw[jj_tail]

        yc += 0.5 * dt_tail * (kk_max * y_max + k_old * y_raw[jj_tail])

        # Normalization
        norm = 2.0 * self.MU * self.RDENS
        yc *= norm

        # Background
        bg = (
            params[1]
            + params[2] * s_array
            + params[3] * s_array**2
            + params[4] * s_array**3
            + params[5] * s_array**4
            + params[6] / s_array
        )
        yc += bg

        return yc
