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
        # A(1)   - Overall scale factor
        # A(2)   - Background constant
        # A(3)   - Background slope
        # A(4)   - Background 2TH**2 Coefficient
        # A(5)   - Background 2TH**3 Coefficient
        # A(6)   - Background 2TH**4 Coefficient
        # A(7)   - 1/S Background term
        # A(8)   - A        Cell constant
        # A(9)   - D002        Layer spacing
        # A(10)  - La        partical size in AB plane
        # A(11)  - M        # of layers along C
        # A(12)  - SM        Width of M distribution (Gets rid of ripples)
        # A(13)  - Dab        In plane strain
        # A(14)  - Del        C axis strain
        # A(15)  - Pr        Probability of a random shift
        # A(16)  - 1 layer :g        Fraction of unstrained materialn
        #          2 layer :Pt        Probablilty of 3R (ABC) stacking
        # A(17)  - B        Temperature factor
        # A(18)  - PO        Preferred orientation parameter
        self.params = np.zeros(19) # 1-indexed in Fortran, so 19 elements to keep indices aligned or just map 0-17
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
             # Note: The Fortran code does this rescaling in the main loop before calling fitting
             # We apply it here so that self.params contains the values used for calculation
             # A(11) -> params[10] (M)
             # A(12) -> params[11] (SM)
             # A(14) -> params[13] (Del)
             # A(15) -> params[14] (Pr)
             # A(16) -> params[15] (Pt)
             
             self.params[10] /= 2.0
             self.params[11] /= 2.0
             self.params[13] *= 2.0
             self.params[14] *= 2.0
             self.params[15] *= 2.0

    def f_carb(self, stl):
        """
        Carbon form factor
        stl: sin(theta)/lambda = s/2
        """
        # Coefficients from Fortran code
        a = [2.310000, 1.020000, 1.588600, 0.865000, 0.215600]
        b = [20.843900, 10.207500, 0.568700, 51.651200, 0.000000]
        dfp = -0.017
        
        val = dfp
        stl_sq = stl**2
        for i in range(5):
            val += a[i] * np.exp(-b[i] * stl_sq)
        return val

    def etag(self, l, s, s0, p, dab):
        """
        Calculate Gaussian rod shape in the AB plane
        l: Coherence length in AB plane (La)
        s: Magnitude of scattering vector
        s0: Magnitude of HK rod vector
        p: Phi angle
        dab: AB plane strain
        """
        x = s * np.cos(p) - s0
        w = 2.0 / np.sqrt(3.0 * np.pi) / l + dab * s0
        ex = np.exp(-2 * (x / w)**2)
        a_val = (w - dab * s0) / w
        return a_val * ex

    def gmod(self, h, k, l_val, m, sm, del_strain, pr, pt):
        """
        Calculate Crystal Modulation Function G(s)
        l_val: L index (continuous) = S * 2 * d002 * sin(phi)
        """
        dhk = 1.0 if (h == 0 and k == 0) else 0.0
        
        # Phase factors
        # E1PIL =EXP(CMPLX(0.0D0,1*PI*L)) -> exp(i * pi * l)
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
            # EHK=PR*DHK + 1-PR + PT * (EXP(CMPLX(0,4.0D0/3.0D0*PI*(H-K)))-1.0D0)
            ehk = pr * dhk + (1 - pr) + pt * (np.exp(1j * 4.0/3.0 * np.pi * (h - k)) - 1.0)
            el = e2pil * edel
            
        q = ehk * el
        
        # Modulation function
        # Check for singularities (Real(Q) == 1.0)
        # Using a small epsilon for float comparison
        if abs(q.real - 1.0) < 1e-6 and abs(q.imag) < 1e-6:
            gg = (m**2 + sm**2) / m
        else:
            # LQ =LOG(Q)
            # Note: Complex log
            lq = np.log(q)
            qm = np.exp(m * lq)
            es = 0.5 * (sm * lq)**2
            
            # IF (REAL(ES) .GT. 5.0) ES=CMPLX(5.0D0,DIMAG(ES))
            if es.real > 5.0:
                es = complex(5.0, es.imag)
            
            es = np.exp(es)
            
            # GG =(1+Q)/(1-Q) + 2.0/M*Q*(QM*ES-1)/(1-Q)**2
            gg = (1 + q) / (1 - q) + 2.0 / m * q * (qm * es - 1) / (1 - q)**2
            
        return gg.real / m

    def igran(self, phi, s, s0, h, k, d002, la, m, sm, dab, del_strain, pr, pt, po):
        """
        Integrand for PHI integral
        """
        # L=S*2*D002*SIN(PHI)
        l_val = s * 2 * d002 * np.sin(phi)
        
        # G=GMOD(...)
        # Note: Fortran passes DEL/(2.0D0*D002) as DEL argument to GMOD?
        # Line 812: G=GMOD(H,K,L,M,SM,DEL/(2.0D0*D002),PR,PT,...)
        # So the 'del' passed to GMOD is actually strain / (2*d002)?
        # Wait, A(14) is "del, Inter Plane Strain".
        # In GMOD, DEL is used as: EDEL =EXP(-2*(PI*DEL*L)**2)
        # If we pass A(14)/(2*d002), then term is (pi * A(14)/(2*d002) * L)**2
        # L = S * 2 * d002 * sin(phi)
        # So term is (pi * A(14) * S * sin(phi))**2
        # This makes sense, strain relative to d-spacing.
        
        g = self.gmod(h, k, l_val, m, sm, del_strain / (2.0 * d002), pr, pt)
        
        # ET=ETAG(...)
        et = self.etag(la, s, s0, phi, dab)
        
        # POC=EXP(-PO*COS(PHI)**2)
        poc = np.exp(-po * np.cos(phi)**2)
        
        # Structure factor CS
        if self.n_layers_model == 1:
            cs = 1.0
        else:
            # CS=2.0D0*COS(PI*((H-K)/3.0D0+L/2.0D0))**2
            cs = 2.0 * np.cos(np.pi * ((h - k) / 3.0 + l_val / 2.0))**2
            
        return g * et * poc * cs

    def safe_acos(self, x):
        if x >= 1.0: return 0.0
        if x <= -1.0: return np.pi
        return np.arccos(x)

    def kern(self, thi, thj):
        """
        Kernel for the convolution routine
        thi: Measured Theta (radians)
        thj: Convoluted Theta (radians)
        """
        if thi == thj:
            return 1.0
        
        # Depth in sample
        # T=(THJ-THI)*L0/COS(THI)
        # Note: Fortran uses COS(THI), check if it should be COS(THJ)? 
        # Code says COS(THI).
        
        t = (thj - thi) * self.L0 / np.cos(thi)
        
        if t < 0.0:
            return 0.0
        
        eps = 1.0e-4
        if t > self.WD + eps:
            return 0.0
            
        sin_thj = np.sin(thj)
        tan_thj = np.tan(thj)
        
        # T1 = 0.5*(WW-BW/(2*SIN(THJ)))*TAN(THJ)
        t1 = 0.5 * (self.WW - self.BW / (2 * sin_thj)) * tan_thj
        
        # Exponential term
        # EXP(-2*MU*RDENS*L0*(THJ-THI)/(SIN(THJ)*COS(THJ)))
        # Note: SIN(THJ)*COS(THJ) = 0.5*SIN(2*THJ)
        exp_term = np.exp(-2 * self.MU * self.RDENS * self.L0 * (thj - thi) / (sin_thj * np.cos(thj)))
        
        if t <= t1:
            return exp_term
            
        # T2 = 0.5*(WW+BW/(2*SIN(THJ)))*TAN(THJ)
        t2 = 0.5 * (self.WW + self.BW / (2 * sin_thj)) * tan_thj
        
        if t <= t2:
            return exp_term * (t2 - t) / (t2 - t1)
            
        return 0.0

    def phint(self, h, k, s, a_cell, d002, la, m, sm, dab, del_strain, pr, pt, po):
        """
        Calculate Phi integral numerically
        """
        # Rod scattering vector
        # S0=SQRT(4.0D0/3.0D0*(H**2 + K**2 + H*K))/A
        s0 = np.sqrt(4.0/3.0 * (h**2 + k**2 + h*k)) / a_cell
        
        # Determine integration limits in S
        # SIG=(2.0/SQRT(3.0*PI)/LA+DAB*S0)/2.0
        sig = (2.0 / np.sqrt(3.0 * np.pi) / la + dab * s0) / 2.0
        s1 = s0 - self.NSG * sig
        s2 = s0 + self.NSG * sig
        
        if s < s1:
            return 0.0
            
        # Calculate Angular limits
        # Check for domain errors in acos
        if s1/s > 1.0: phi1 = 0.0
        elif s1/s < -1.0: phi1 = np.pi
        else: phi1 = np.arccos(s1/s)
        
        if s2/s > 1.0: phi2 = 0.0
        elif s2/s < -1.0: phi2 = np.pi
        else: phi2 = np.arccos(s2/s)

        dphi = (phi1 - phi2) / (self.NPHI - 1)
        
        ph_int = 0.0
        
        # Full intersection
        if s > s1 and s < s2:
            phi = -phi1
            nphi1 = int(2 * phi1 / dphi) + 1
            for i in range(nphi1):
                ph_int += self.igran(phi, s, s0, h, k, d002, la, m, sm, dab, del_strain, pr, pt, po)
                phi += dphi
                
        # Two intersections
        if s > s2:
            # Positive side
            phi = phi2
            for i in range(self.NPHI):
                ph_int += self.igran(phi, s, s0, h, k, d002, la, m, sm, dab, del_strain, pr, pt, po)
                phi += dphi
            
            # Negative side
            phi = -phi2
            for i in range(self.NPHI):
                ph_int += self.igran(phi, s, s0, h, k, d002, la, m, sm, dab, del_strain, pr, pt, po)
                phi -= dphi # Note: Fortran says PHI=PHI-DPHI
                
        return ph_int * dphi

    def inten(self, s, params):
        """
        Calculate scattered powder intensity at wavevector S
        """
        # Unpack parameters
        # Note: params is 0-indexed here, matching A(1)..A(18)
        scale = params[0]
        # Background parameters are added later in ALLINTEN in Fortran, but INTEN calculates the structural part
        
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
        
        # Rods
        hk_list = [(0,0), (1,0), (1,1), (2,0), (2,1)]
        mult_list = [1, 6, 6, 6, 12]
        
        # Polarization factor
        th = np.arcsin(s * self.LAM / 2.0)
        psi = 13.3 * np.pi / 180.0
        pol = 0.5 * (1 + np.cos(2*th)**2 * np.cos(2*psi)**2) / s # Note: Fortran divides by S? Yes.
        
        # Debye Waller Factor
        dwf = np.exp(-2.0 * temp_factor * (s/2.0)**2)
        
        yfit = 0.0
        
        for i, (h, k) in enumerate(hk_list):
            # Structure factor info
            # ALPHA=2*COS(2.0D0*PI/3.0D0*(H-K))*FCARB(S/2.0D0)
            alpha = 2 * np.cos(2.0 * np.pi / 3.0 * (h - k)) * self.f_carb(s/2.0)
            
            # Tangent cylinder integral
            ph = self.phint(h, k, s, a_cell, d002, la, m, sm, dab, del_strain, pr, pt, po)
            
            yfit += mult_list[i] * pol * alpha**2 * dwf * ph
            
        return scale * yfit

    def all_inten(self, s_array, params):
        """
        Calculate scattered powder intensity for the whole pattern
        s_array: Array of scattering vectors
        params: Model parameters
        """
        ndat = len(s_array)
        yc = np.zeros(ndat)
        y_raw = np.zeros(ndat)
        
        # Calculate raw intensities
        # This loop can be slow in Python. 
        # Ideally we would vectorize INTEN, but it calls PHINT which has loops and conditional logic.
        # For now, keep it as a loop.
        for i in range(ndat):
            y_raw[i] = self.inten(s_array[i], params)
            
        # Convolution
        if ndat > 1:
            dth = np.arcsin(s_array[1] * self.LAM / 2.0) - np.arcsin(s_array[0] * self.LAM / 2.0)
        else:
            dth = 0.01 # Fallback
        
        for i in range(ndat):
            th = np.arcsin(s_array[i] * self.LAM / 2.0)
            foot = 1.0 / np.sin(th)
            th_max = self.WD / self.L0 * np.cos(th)
            nj = int(th_max / dth)
            
            k_old = 1.0
            
            # Convolution sum
            # Limit j to valid range
            j_start = i + 1
            j_end = min(i + nj + 1, ndat)
            
            for j in range(j_start, j_end):
                thj = th + dth * (j - i)
                kk = self.kern(th, thj)
                dt = dth * self.L0 / np.cos(thj) * (1.0 + np.tan(thj) * (thj - th)) * foot
                
                yc[i] += 0.5 * dt * (kk * y_raw[j] + k_old * y_raw[j-1])
                k_old = kk
                
            # Tail correction
            # THJ  =TH+DTH*NJ
            thj = th + dth * nj
            
            # DT   =(THMAX+TH-THJ)*L0/COS(THMAX)*(1.0+TAN(THMAX)*(THMAX-TH))*FOOT
            dt = (th_max + th - thj) * self.L0 / np.cos(th_max) * (1.0 + np.tan(th_max) * (th_max - th)) * foot
            
            # FRAC =(THMAX+TH-THJ)/DTH
            frac = (th_max + th - thj) / dth
            
            # KKMAX=KERN(TH,TH+THMAX)
            kk_max = self.kern(th, th + th_max)
            
            jj = min(ndat - 1, i + nj)
            jj1 = min(ndat - 1, i + nj + 1)
            
            # YMAX =FRAC*Y(JJ1) + (1-FRAC)*Y(JJ)
            y_max = frac * y_raw[jj1] + (1 - frac) * y_raw[jj]
            
            yc[i] += 0.5 * dt * (kk_max * y_max + k_old * y_raw[jj])
            
            # Normalization
            norm = 2.0 * self.MU * self.RDENS
            yc[i] *= norm
            
            # Background
            s_val = s_array[i]
            bg = params[1] + params[2]*s_val + params[3]*s_val**2 + params[4]*s_val**3 + params[5]*s_val**4 + params[6]/s_val
            yc[i] += bg
            
        return yc
