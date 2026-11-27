import os
import warnings

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from qt_compat import QtGui
import CarbonXS_GUI


@pytest.fixture(scope="module")
def qapp():
    app = QtGui.QApplication.instance()
    if app is None:
        app = QtGui.QApplication([])
    yield app


@pytest.fixture
def main_window(qapp, tmp_path, monkeypatch):
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(CarbonXS_GUI, "user_data_directory", str(tmp_path))
    win = CarbonXS_GUI.MainWindow("1.3.1-test")
    win.hide()
    yield win
    win.close()


def test_no_runtime_warning_on_calculate_worker_disconnect(main_window, monkeypatch):
    """Reproduce and verify fix for PySide6 loss_signal disconnect RuntimeWarning after calculate."""
    monkeypatch.setattr(main_window, "write_results_to_disk", lambda _res: None)
    monkeypatch.setattr(main_window, "plot_fit_results", lambda: None)

    params = [p.value() for p in main_window.parameter_list]
    settings = main_window.extract_settings()
    wt = CarbonXS_GUI.WorkerThread("calculate", params, settings)
    main_window.worker_thread = wt
    wt.finished_signal.connect(main_window.on_worker_finished)
    wt.error_signal.connect(main_window.on_worker_error)

    dummy_result = {"mode": "calculate", "x": [20.0, 20.1], "y_calc": [10.0, 10.0], "params": params}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        main_window.on_worker_finished(dummy_result)

    runtime_warnings = [w for w in caught if issubclass(w.category, RuntimeWarning)]
    assert len(runtime_warnings) == 0, f"Unexpected RuntimeWarnings: {[str(w.message) for w in runtime_warnings]}"

    # Also check on_worker_error when loss_signal was not connected
    wt2 = CarbonXS_GUI.WorkerThread("calculate", params, settings)
    main_window.worker_thread = wt2
    wt2.finished_signal.connect(main_window.on_worker_finished)
    wt2.error_signal.connect(main_window.on_worker_error)
    monkeypatch.setattr(QtGui.QMessageBox, "critical", lambda *args, **kwargs: None)

    with warnings.catch_warnings(record=True) as caught_err:
        warnings.simplefilter("always")
        main_window.on_worker_error("simulated error")

    runtime_warnings_err = [w for w in caught_err if issubclass(w.category, RuntimeWarning)]
    assert len(runtime_warnings_err) == 0, f"Unexpected RuntimeWarnings: {[str(w.message) for w in runtime_warnings_err]}"


def test_console_stream_flush_and_isatty():
    """ConsoleStream should implement flush() and isatty() for stdout/stderr compatibility."""
    stream = CarbonXS_GUI.ConsoleStream()
    stream.flush()
    assert stream.isatty() is False


def test_menu_actions_not_double_connected(qapp, tmp_path, monkeypatch):
    """Triggering Fitting menu actions should invoke their handlers only once."""
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(CarbonXS_GUI, "user_data_directory", str(tmp_path))

    calls = {"calc": 0, "start": 0, "call_fit": 0, "abort": 0}
    monkeypatch.setattr(CarbonXS_GUI.MainWindow, "calculate_pattern", lambda self, append_to_buffer=True: calls.__setitem__("calc", calls["calc"] + 1))
    monkeypatch.setattr(CarbonXS_GUI.MainWindow, "start_fitting_process", lambda self: calls.__setitem__("start", calls["start"] + 1))
    monkeypatch.setattr(CarbonXS_GUI.MainWindow, "call_fit_program", lambda self: calls.__setitem__("call_fit", calls["call_fit"] + 1))
    monkeypatch.setattr(CarbonXS_GUI.MainWindow, "abort_fit_process", lambda self: calls.__setitem__("abort", calls["abort"] + 1))

    win = CarbonXS_GUI.MainWindow("1.3.1-test")
    win.hide()
    try:
        win.menu_calculate_pattern.trigger()
        win.menu_start_fit.trigger()
        win.menu_abort_fit.trigger()
    finally:
        win.close()

    assert calls["calc"] == 1, f"Expected 1 calculate call, got {calls['calc']}"
    assert calls["start"] == 1 and calls["call_fit"] == 0, f"Expected start=1, call_fit=0, got {calls}"
    assert calls["abort"] == 1, f"Expected 1 abort call, got {calls['abort']}"


def test_worker_cooperative_abort_and_empty_refine_flags(main_window):
    """WorkerThread supports cooperative abort and handles refine_flags all False cleanly."""
    import numpy as np
    params = [p.value() for p in main_window.parameter_list]
    params[0] = 100.0
    params[7] = 2.46
    params[8] = 3.35
    params[9] = 50.0
    params[10] = 10.0
    params[11] = 1.0
    settings = {
        "theta_min": 20.0,
        "theta_max": 60.0,
        "iterations": 10,
        "epsilon": 0.001,
        "nskip": 1,
        "number_layers": 0,
        "tci_pts": 10,
        "integration_width": 3,
        "wavelength": 1.5418,
        "sample_depth": 2.0,
        "sample_width": 20.0,
        "goniometer_radius": 200.0,
        "beam_width": 1.0,
        "sample_density": 1.0,
    }
    x_obs = np.linspace(20.0, 60.0, 41)
    y_obs = np.ones_like(x_obs) * 100.0

    # Empty refine flags (all False) should not crash with AttributeError on res.success
    wt_empty = CarbonXS_GUI.WorkerThread("fit", params, settings, data=(x_obs, y_obs), refine_flags=[False] * 18)
    results = []
    errors = []
    wt_empty.finished_signal.connect(results.append)
    wt_empty.error_signal.connect(errors.append)
    wt_empty.run()
    assert not errors, f"Unexpected errors: {errors}"
    assert len(results) == 1
    assert results[0]["mode"] == "fit"

    # Cooperative abort_event
    wt_abort = CarbonXS_GUI.WorkerThread("fit", params, settings, data=(x_obs, y_obs), refine_flags=[True] + [False] * 17)
    assert hasattr(wt_abort, "request_abort")
    wt_abort.request_abort()
    aborted = []
    wt_abort.aborted_signal.connect(lambda: aborted.append(True))
    wt_abort.run()
    assert aborted == [True]
