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


def test_worker_applies_theta_nskip_and_step05(main_window):
    """WorkerThread filters by theta_min..theta_max and nskip, and uses 0.05 step without data."""
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
        "theta_max": 40.0,
        "iterations": 5,
        "epsilon": 0.001,
        "nskip": 2,
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

    # Calculate without data -> step 0.05 from 20.0 to 40.0 -> 401 points
    wt_calc = CarbonXS_GUI.WorkerThread("calculate", params, settings, data=None)
    calc_res = []
    wt_calc.finished_signal.connect(calc_res.append)
    wt_calc.run()
    assert len(calc_res) == 1
    assert np.isclose(calc_res[0]["x"][1] - calc_res[0]["x"][0], 0.05)

    # Fit with full 10..60 data -> filtered to 20..40 and strided by nskip=2
    x_full = np.arange(10.0, 60.05, 0.5)  # 101 pts; 20..40 has 41 pts; nskip=2 -> 21 pts
    y_full = np.ones_like(x_full) * 100.0
    wt_fit = CarbonXS_GUI.WorkerThread("fit", params, settings, data=(x_full, y_full), refine_flags=[False] * 18)
    fit_res = []
    wt_fit.finished_signal.connect(fit_res.append)
    wt_fit.run()
    assert len(fit_res) == 1
    assert len(fit_res[0]["x"]) == 21
    assert fit_res[0]["x"][0] >= 20.0 and fit_res[0]["x"][-1] <= 40.0


def test_runtime_outputs_isolated_from_carbonxs(main_window, tmp_path):
    """write_results_to_disk writes to user_data_directory/last_run without touching carbonxs/."""
    carbonxs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "carbonxs")
    dat_mtime_before = os.path.getmtime(os.path.join(carbonxs_dir, "carbon.dat"))
    inp_mtime_before = os.path.getmtime(os.path.join(carbonxs_dir, "carbon.inp"))

    main_window.x_data = [20.0, 20.1]
    main_window.y_data = [100.0, 110.0]
    result = {"mode": "calculate", "x": [20.0, 20.1], "y_calc": [99.0, 109.0]}
    main_window.write_results_to_disk(result)

    last_run_dir = tmp_path / "last_run"
    assert (last_run_dir / "carbon.dat").exists()
    assert (last_run_dir / "carbon.inp").exists()
    assert (last_run_dir / "carbon.out").exists()
    assert os.path.getmtime(os.path.join(carbonxs_dir, "carbon.dat")) == dat_mtime_before
    assert os.path.getmtime(os.path.join(carbonxs_dir, "carbon.inp")) == inp_mtime_before


def test_prev_fit_ax_loss_undo_and_dead_code(main_window, monkeypatch):
    """Verify prev_fit preservation, update_loss_plot after plot_difference, undo buttons, and dead code removal."""
    monkeypatch.setattr(main_window, "write_results_to_disk", lambda _res: None)

    # 1. Dead QProcess methods removed
    assert not hasattr(main_window, "on_process_message")
    assert not hasattr(main_window, "fitting_finished")

    # 2. prev_x_fit / prev_y_fit populated on second finish
    params = [p.value() for p in main_window.parameter_list]
    main_window.x_data = [20.0, 21.0, 22.0]
    main_window.y_data = [100.0, 120.0, 110.0]
    res1 = {"mode": "calculate", "x": [20.0, 21.0, 22.0], "y_calc": [90.0, 110.0, 100.0], "params": params}
    main_window.on_worker_finished(res1)
    res2 = {"mode": "calculate", "x": [20.0, 21.0, 22.0], "y_calc": [95.0, 115.0, 105.0], "params": params}
    main_window.on_worker_finished(res2)
    assert main_window.prev_x_fit == [20.0, 21.0, 22.0]
    assert main_window.prev_y_fit == [90.0, 110.0, 100.0]

    # 3. update_loss_plot after plot_difference must not crash or draw onto detached axes
    main_window.plot_difference()
    main_window.loss_data = [1.0] * 9
    main_window.update_loss_plot(0.5)  # 10th call triggers draw

    # 4. Undo/redo button state respected on on_worker_finished when append_to_buffer=False
    main_window.append_to_buffer = False
    main_window.undo_buffer = [
        CarbonXS_GUI.FittingParams(main_window.parameter_list, main_window.parameter_enable_list, main_window.fit_settings, main_window.diff_settings)
    ]
    main_window.undo_index = 0
    main_window.on_worker_finished(res2)
    assert not main_window.back_button.isEnabled()
    assert not main_window.forward_button.isEnabled()


def test_data_io_closes_files_and_roundtrips(tmp_path):
    """data_io read/write functions close file handles cleanly without ResourceWarning."""
    import numpy as np
    import data_io

    mdi_path = tmp_path / "test.mdi"
    x = np.linspace(20.0, 22.0, 11)
    y = np.linspace(100.0, 200.0, 11)
    ras_path = tmp_path / "test.ras"
    ras_path.write_text("RAS_INT_START\n20.0 100.0 1.0\n21.0 150.0 1.0\nRAS_INT_END\n")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ResourceWarning)
        data_io.write_mdi_file(str(mdi_path), x, y)
        rx, ry = data_io.read_mdi_file(str(mdi_path))
        tx, ty = data_io.read_ras_file(str(ras_path))

    res_warnings = [w for w in caught if issubclass(w.category, ResourceWarning)]
    assert len(res_warnings) == 0, f"Unclosed file handles: {[str(w.message) for w in res_warnings]}"
    assert len(rx) == len(x) and len(ry) == len(y)
    assert list(tx) == [20.0, 21.0] and list(ty) == [100.0, 150.0]
