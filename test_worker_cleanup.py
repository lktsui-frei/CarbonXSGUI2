"""
Test for WorkerThread cleanup and signal disconnection.

This test verifies that the WorkerThread properly disconnects signals
and schedules deletion to prevent Qt crashes.
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from qt_compat import QtGui, QtCore, Qt
import numpy as np
from CarbonXS_GUI import WorkerThread

def test_worker_thread_cleanup():
    """Test that WorkerThread completes and cleans up properly."""
    
    print("=" * 80)
    print("Testing WorkerThread Cleanup")
    print("=" * 80)
    
    # Create Qt application
    app = QtGui.QApplication.instance()
    if app is None:
        app = QtGui.QApplication(sys.argv)
    
    # Setup test data
    params = [
        33800.0, 116.78, 483.09, -353.58, 0.0, 0.0, 0.0,
        2.4615, 3.3611, 293.51, 141.69, 2.0, 0.0, 0.024387,
        0.066073, 0.061821, 1.3708, 0.37804
    ]
    
    settings = {
        'wavelength': 1.5418,
        'tci_pts': 10,
        'integration_width': 3,
        'sample_density': 1.0,
        'goniometer_radius': 200.0,
        'sample_depth': 2.0,
        'sample_width': 20.0,
        'beam_width': 1.0,
        'number_layers': 0,
        'theta_min': 10.0,
        'theta_max': 30.0,
        'iterations': 1
    }
    
    # Generate synthetic data
    x_data = np.arange(10.0, 30.0, 0.5)
    y_data = np.random.random(len(x_data)) * 1000 + 100
    data = (x_data, y_data)
    
    refine_flags = [True, True, True, False, False, False, False,
                    True, True, True, True, False, False, True,
                    True, False, False, False]
    
    # Test 1: Calculate mode
    print("\nTest 1: Calculate mode thread cleanup")
    print("-" * 80)
    
    worker = WorkerThread('calculate', params, settings, data)
    
    result_received = {'value': False}
    error_received = {'value': False}
    
    def on_finished(result):
        result_received['value'] = True
        print(f"✓ Finished signal received: {result['mode']}")
    
    def on_error(error_msg):
        error_received['value'] = True
        print(f"✗ Error signal received: {error_msg}")
    
    worker.finished_signal.connect(on_finished)
    worker.error_signal.connect(on_error)
    
    worker.start()
    
    # Wait for thread to complete
    timeout = 5000  # 5 seconds
    if not worker.wait(timeout):
        print("✗ FAIL: Thread did not complete within timeout")
        return False
    
    # Process events to ensure signals are delivered
    app.processEvents()
    time.sleep(0.1)
    app.processEvents()
    
    if not result_received['value']:
        print("✗ FAIL: Finished signal not received")
        return False
    
    if error_received['value']:
        print("✗ FAIL: Error signal received unexpectedly")
        return False
    
    # Test signal disconnection
    print("\nTest 2: Signal disconnection")
    print("-" * 80)
    
    try:
        worker.finished_signal.disconnect()
        worker.error_signal.disconnect()
        print("✓ Signals disconnected successfully")
    except Exception as e:
        print(f"✗ FAIL: Could not disconnect signals: {e}")
        return False
    
    # Test deleteLater
    print("\nTest 3: deleteLater() scheduling")
    print("-" * 80)
    
    try:
        worker.deleteLater()
        print("✓ deleteLater() called successfully")
    except Exception as e:
        print(f"✗ FAIL: deleteLater() failed: {e}")
        return False
    
    # Process events to allow deletion
    app.processEvents()
    time.sleep(0.1)
    app.processEvents()
    
    # Test 4: Fit mode (quick test with limited iterations)
    print("\nTest 4: Fit mode thread cleanup")
    print("-" * 80)
    
    worker2 = WorkerThread('fit', params, settings, data, refine_flags)
    
    result_received2 = {'value': False}
    
    def on_finished2(result):
        result_received2['value'] = True
        print(f"✓ Fit finished signal received: success={result.get('success', 'N/A')}")
    
    worker2.finished_signal.connect(on_finished2)
    worker2.error_signal.connect(lambda msg: print(f"Error: {msg}"))
    
    worker2.start()
    
    # Wait for thread to complete (fit takes longer)
    timeout = 10000  # 10 seconds
    if not worker2.wait(timeout):
        print("✗ FAIL: Fit thread did not complete within timeout")
        return False
    
    # Process events
    app.processEvents()
    time.sleep(0.1)
    app.processEvents()
    
    if not result_received2['value']:
        print("✗ FAIL: Fit finished signal not received")
        return False
    
    # Cleanup
    try:
        worker2.finished_signal.disconnect()
        worker2.error_signal.disconnect()
        worker2.deleteLater()
        print("✓ Fit thread cleaned up successfully")
    except Exception as e:
        print(f"✗ FAIL: Fit thread cleanup failed: {e}")
        return False
    
    # Final event processing
    app.processEvents()
    time.sleep(0.2)
    app.processEvents()
    
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED: WorkerThread cleanup working correctly")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    try:
        success = test_worker_thread_cleanup()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
