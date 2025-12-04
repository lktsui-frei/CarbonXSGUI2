import sys
import os
import time
import threading
import queue

# Mock the GUI environment
from carbonxs_core import CarbonXSModel
from carbonxs_fit import CarbonXSFit
import numpy as np

# WorkerThread class adapted to use threading.Thread
class WorkerThread(threading.Thread):
    def __init__(self, mode, params, settings, data=None, refine_flags=None, callback=None):
        super(WorkerThread, self).__init__()
        self.mode = mode
        self.params = params
        self.settings = settings
        self.data = data
        self.refine_flags = refine_flags
        self.callback = callback
        self.daemon = True # Allow program to exit if thread is stuck
        
    def run(self):
        print("WorkerThread started")
        try:
            model = CarbonXSModel()
            # Set model constants from settings
            model.LAM = self.settings['wavelength']
            model.NPHI = int(self.settings['tci_pts'])
            model.NSG = int(self.settings['integration_width'])
            model.RDENS = self.settings['sample_density']
            model.L0 = self.settings['goniometer_radius']
            model.WD = self.settings['sample_depth']
            model.WW = self.settings['sample_width']
            model.BW = self.settings['beam_width']
            model.n_layers_model = int(self.settings['number_layers']) + 1 
            
            if self.mode == 'fit':
                fitter = CarbonXSFit(model)
                x_obs = self.data[0]
                y_obs = self.data[1]
                
                # Get max function evaluations from iterations setting
                max_nfev = int(self.settings.get('iterations', 100)) * 100
                print(f"DEBUG: Starting fit with max_nfev={max_nfev}")
                
                final_params, res = fitter.fit(self.params, self.refine_flags, x_obs, y_obs, max_nfev=max_nfev)
                
                result = {
                    'mode': 'fit',
                    'success': res.success,
                    'message': res.message
                }
                if self.callback:
                    self.callback(result)
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error: {e}")
        print("WorkerThread finished")

def test_thread():
    # Load data
    print("Loading data...")
    data = np.loadtxt('examples/crystalline_carbon.dat', delimiter=',')
    x_data = data[:, 0]
    y_data = data[:, 1]
    
    # Load params
    print("Loading params...")
    with open('examples/carbon.inp', 'r') as f:
        lines = f.readlines()
    
    params = []
    refine_flags = []
    for i in range(6, 24):
        parts = lines[i].split()
        params.append(float(parts[0]))
        refine_flags.append(int(parts[1]) == 1)
        
    settings = {
        'wavelength': 1.54180,
        'tci_pts': 10,
        'integration_width': 3,
        'sample_density': 0.500,
        'goniometer_radius': 205.000,
        'sample_depth': 2.000,
        'sample_width': 25.000,
        'beam_width': 1.500,
        'number_layers': 1,
        'iterations': 8,
        'theta_min': 15.0,
        'theta_max': 120.0
    }
    
    result_queue = queue.Queue()
    
    def on_finished(result):
        result_queue.put(result)
    
    # Create thread
    thread = WorkerThread('fit', params, settings, (x_data, y_data), refine_flags, callback=on_finished)
    
    print("Starting thread...")
    thread.start()
    
    # Simulate main loop
    start_time = time.time()
    while thread.is_alive():
        time.sleep(0.1)
        if time.time() - start_time > 30:
            print("Timeout reached!")
            break
            
    if not result_queue.empty():
        print(f"Fit finished: {result_queue.get()}")
    else:
        print("Fit did not finish in time.")

if __name__ == "__main__":
    test_thread()
