from fastapi.testclient import TestClient
from ..main import app
import numpy as np
import sys
import os

# Ensure parent directory is in path for imports if running pytest from here
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "CarbonXS API is running"}

def test_calculate():
    # Parameters from examples/CARBON.INP
    params = [
        33800.0,   # Scale
        116.78,    # BG Const
        483.09,    # BG S
        -353.58,   # BG S^2
        0.0,       # BG S^3
        0.0,       # BG S^4
        0.0,       # BG 1/S
        2.4615,    # A
        3.3611,    # d002
        293.51,    # La
        141.69,    # M
        2.0,       # SM
        0.0,       # DAB
        0.024387,  # del
        0.066073,  # Pr
        0.061821,  # Pt
        1.3708,    # B
        0.37804    # PO
    ]
    
    settings = {
        "wavelength": 1.5418,
        "tci_pts": 10,
        "integration_width": 3,
        "sample_density": 0.5,
        "goniometer_radius": 205.0,
        "sample_depth": 2.0,
        "sample_width": 25.0,
        "beam_width": 1.5,
        "number_layers": 0 # 1 layer model
    }
    
    payload = {
        "params": params,
        "settings": settings,
        "theta_min": 15.0,
        "theta_max": 120.0,
        "step_size": 0.1
    }
    
    response = client.post("/api/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "x" in data
    assert "y_calc" in data
    assert len(data["x"]) == len(data["y_calc"])
    assert len(data["x"]) > 0

def test_fit():
    # Create synthetic data
    x_obs = np.linspace(15, 120, 1051).tolist()
    y_obs = [100.0] * 1051 
    
    params = [
        33800.0,   # Scale
        116.78,    # BG Const
        483.09,    # BG S
        -353.58,   # BG S^2
        0.0,       # BG S^3
        0.0,       # BG S^4
        0.0,       # BG 1/S
        2.4615,    # A
        3.3611,    # d002
        293.51,    # La
        141.69,    # M
        2.0,       # SM
        0.0,       # DAB
        0.024387,  # del
        0.066073,  # Pr
        0.061821,  # Pt
        1.3708,    # B
        0.37804    # PO
    ]
    
    refine_flags = [False] * 18
    refine_flags[0] = True # Refine scale factor
    
    settings = {
        "wavelength": 1.5418,
        "tci_pts": 10,
        "integration_width": 3,
        "sample_density": 0.5,
        "goniometer_radius": 205.0,
        "sample_depth": 2.0,
        "sample_width": 25.0,
        "beam_width": 1.5,
        "number_layers": 0
    }
    
    payload = {
        "params": params,
        "refine_flags": refine_flags,
        "x_obs": x_obs,
        "y_obs": y_obs,
        "settings": settings
    }
    
    response = client.post("/api/fit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "final_params" in data
    assert "y_calc" in data
    assert len(data["final_params"]) == 18
