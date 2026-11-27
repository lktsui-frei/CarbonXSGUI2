import warnings
import pytest
import numpy as np
from carbonxs_core import CarbonXSModel

@pytest.fixture
def model():
    return CarbonXSModel()

def test_f_carb(model):
    """Test Carbon form factor calculation."""
    # Test at s=0
    # Coefficients:
    # a = [2.310000, 1.020000, 1.588600, 0.865000, 0.215600]
    # dfp = -0.017
    # sum(a) + dfp = 5.9992 - 0.017 = 5.9822
    # Actually, f_carb is for s/2 = sin(theta)/lambda.
    # At s=0, exp terms are 1.
    val_0 = model.f_carb(0)
    expected_0 = 2.31 + 1.02 + 1.5886 + 0.865 + 0.2156 - 0.017
    assert np.isclose(val_0, expected_0)

    # Test asymptotic behavior (large s)
    # Should approach dfp + a[4] (since b[4]=0)
    # dfp = -0.017, a[4] = 0.2156
    # expected = -0.017 + 0.2156 = 0.1986
    val_inf = model.f_carb(100)
    assert np.isclose(val_inf, -0.017 + 0.2156)

def test_etag(model):
    """Test Gaussian rod shape calculation."""
    l_val = 100.0
    s0 = 1.0
    dab = 0.0
    
    # Peak should be at s*cos(p) = s0
    # Let p=0, s=s0
    val_peak = model.etag(l_val, s0, s0, 0, dab)
    
    # w = 2.0 / sqrt(3*pi) / l + dab*s0
    w = 2.0 / np.sqrt(3.0 * np.pi) / l_val
    # a_val = (w - dab*s0)/w = 1.0
    # ex = exp(0) = 1.0
    # Result should be 1.0
    assert np.isclose(val_peak, 1.0)
    
    # Test width scaling
    # If we move away from peak, value should drop
    val_off = model.etag(l_val, s0 + w, s0, 0, dab)
    # x = (s0+w) - s0 = w
    # ex = exp(-2 * (w/w)**2) = exp(-2)
    assert np.isclose(val_off, np.exp(-2))

def test_gmod_singularity(model):
    """Test GMOD singularity handling."""
    # We want Real(Q) = 1.0 and Imag(Q) = 0.0
    # Q = EHK * EL
    # For n_layers=1, if pr=1, pt=1, del=0, then EHK=1, EL=exp(i*pi*l) * exp(0)
    # If l=0, EL=1. So Q=1.
    
    h, k = 0, 0
    l_val = 0.0
    m = 10.0
    sm = 0.0
    del_strain = 0.0
    pr = 1.0
    pt = 1.0
    
    # Should return ((m^2 + sm^2)/m) / m = 1 + (sm/m)^2
    # With sm=0, returns 1.0
    val = model.gmod(h, k, l_val, m, sm, del_strain, pr, pt)
    assert np.isclose(val, 1.0)

def test_kern(model):
    """Test convolution kernel."""
    # Identity
    assert np.isclose(model.kern(0.5, 0.5), 1.0)
    
    # Cutoff
    # WD is 2.0 by default
    # L0 is 200.0
    # t = (thj - thi) * L0 / cos(thi)
    # If thj - thi is large enough, t > WD
    thi = 0.5
    # t > 2.0 => (thj - 0.5) * 200 / cos(0.5) > 2.0
    # thj - 0.5 > 0.01 * cos(0.5)
    thj_far = thi + 0.02 # 0.02 * 200 = 4 > 2
    assert model.kern(thi, thj_far) == 0.0
    
    # Negative t
    assert model.kern(thi, thi - 0.01) == 0.0

def test_inten_smoke(model):
    """Smoke test for intensity calculation."""
    # Just ensure it runs and returns a non-negative value
    params = np.zeros(18)
    params[0] = 1.0 # Scale
    params[7] = 2.46 # A
    params[8] = 3.35 # d002
    params[9] = 50.0 # La
    params[10] = 10.0 # M
    params[11] = 1.0 # SM
    
    s = 0.5
    val = model.inten(s, params)
    assert val >= 0.0
    assert np.isfinite(val)

def test_inten_zero_scale(model):
    """Test zero scale factor."""
    params = np.zeros(18)
    # Set valid structural parameters to avoid divide by zero
    params[7] = 2.46 # A
    params[8] = 3.35 # d002
    params[9] = 50.0 # La
    params[10] = 10.0 # M
    params[11] = 1.0 # SM
    
    params[0] = 0.0 # Scale is zero
    
    s = 0.5
    val = model.inten(s, params)
    assert val == 0.0


def test_gmod_zero_q_pr1_and_strain_underflow(model):
    """Test gmod returns 1/m with no NaN or RuntimeWarning when q == 0."""
    m = 10.0
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        # Pr = 1.0 on (1, 0) rod -> ehk = 0 -> q = 0
        g_sm0 = model.gmod(1, 0, np.array([0.5]), m=m, sm=0.0, del_strain=0.01, pr=1.0, pt=0.0)
        g_sm1 = model.gmod(1, 0, np.array([0.5]), m=m, sm=1.0, del_strain=0.01, pr=1.0, pt=0.0)
        # Huge del_strain -> edel underflows to 0 -> q = 0
        g_underflow = model.gmod(0, 0, np.array([1.0]), m=m, sm=1.0, del_strain=100.0, pr=0.0, pt=1.0)

    runtime_warnings = [w for w in caught if issubclass(w.category, RuntimeWarning)]
    assert len(runtime_warnings) == 0, f"Unexpected RuntimeWarnings: {[str(w.message) for w in runtime_warnings]}"
    assert np.isclose(g_sm0[0], 1.0 / m)
    assert np.isclose(g_sm1[0], 1.0 / m)
    assert np.isclose(g_underflow[0], 1.0 / m)


def test_gmod_smooth_near_singularity(model):
    """Test gmod has no catastrophic cancellation or jump near q -> 1."""
    m = 50.0
    sm = 5.0
    g0 = model.gmod(0, 0, np.array([0.0]), m=m, sm=sm, del_strain=0.02, pr=0.0, pt=1.0)[0]
    l_vals = np.array([1e-8, 1e-7, 4e-7, 1e-6, 1e-5, 1e-4])
    g_vals = model.gmod(0, 0, l_vals, m=m, sm=sm, del_strain=0.02, pr=0.0, pt=1.0)

    assert np.all(np.isfinite(g_vals))
    # Near l = 0, G(l) deviates from G(0) by O((m * pi * l)^2) ~ 1e-9 at l=4e-7
    assert abs(g_vals[2] - g0) < 1e-6, f"Cancellation error at l=4e-7: {g_vals[2]} vs {g0}"
    # Smooth monotonic decrease from l=0 for small l on (0,0) rod
    assert np.all(np.diff(np.concatenate([[g0], g_vals])) <= 1e-12)


def test_phint_exact_s1_and_large_nphi(model):
    """Test phint handles exact s == s1 without RuntimeWarning and does not truncate NPHI > 50."""
    a_cell, d002, la, dab = 2.46, 3.35, 50.0, 0.0
    s0 = np.sqrt(4.0 / 3.0) / a_cell
    sig = (2.0 / np.sqrt(3.0 * np.pi) / la + dab * s0) / 2.0
    s1 = s0 - model.NSG * sig

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ph_s1 = model.phint(1, 0, np.array([s1]), a_cell, d002, la, 10.0, 1.0, dab, 0.01, 0.1, 0.0, 0.0)

    runtime_warnings = [w for w in caught if issubclass(w.category, RuntimeWarning)]
    assert len(runtime_warnings) == 0, f"Unexpected RuntimeWarnings: {[str(w.message) for w in runtime_warnings]}"
    assert ph_s1[0] == 0.0

    # NPHI=60 vs NPHI=40 at s=s0 should agree closely (< 1%) rather than truncating at 100 steps
    model.NPHI = 40
    ph_40 = model.phint(1, 0, np.array([s0]), a_cell, d002, la, 10.0, 1.0, dab, 0.01, 0.1, 0.0, 0.0)[0]
    model.NPHI = 60
    ph_60 = model.phint(1, 0, np.array([s0]), a_cell, d002, la, 10.0, 1.0, dab, 0.01, 0.1, 0.0, 0.0)[0]
    assert abs(ph_60 - ph_40) / ph_40 < 0.01, f"NPHI=60 ({ph_60}) diverged from NPHI=40 ({ph_40})"


def test_set_parameters_float64_and_dth_zero_guard(model):
    """Test set_parameters avoids integer truncation in 2-layer mode and all_inten rejects dth == 0."""
    int_params = [1] * 18
    model.set_parameters(int_params, n_layers_model=2)
    assert np.isclose(model.params[10], 0.5), f"Expected 0.5, got {model.params[10]}"
    assert np.isclose(model.params[11], 0.5), f"Expected 0.5, got {model.params[11]}"

    s_dup = np.array([0.2, 0.2, 0.3])
    with pytest.raises(ValueError):
        model.all_inten(s_dup, model.params)
