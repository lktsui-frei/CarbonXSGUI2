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
