"""
gui/scan_worker.py

Runs the (potentially slow) model scan on a background QThread so the PyQt
UI stays responsive, and emits progress/result signals back to the main
window.
"""

from __future__ import annotations

from PyQt5.QtCore import QThread, pyqtSignal

from detector.anomaly_detector import analyze
from sandbox.scan_runner import run_scan


class ScanWorker(QThread):
    progress = pyqtSignal(int, int)  # done, total
    finished_ok = pyqtSignal(object, object)  # ScanResult, DetectionReport
    failed = pyqtSignal(str)

    def __init__(self, model_path: str, n_baseline: int, n_random: int, n_edge_case: int,
                 extra_trigger_words=None):
        super().__init__()
        self.model_path = model_path
        self.n_baseline = n_baseline
        self.n_random = n_random
        self.n_edge_case = n_edge_case
        self.extra_trigger_words = extra_trigger_words or []

    def run(self):
        try:
            result = run_scan(
                self.model_path,
                n_baseline=self.n_baseline,
                n_random=self.n_random,
                n_edge_case=self.n_edge_case,
                extra_trigger_words=self.extra_trigger_words,
                progress_cb=lambda done, total: self.progress.emit(done, total),
            )
            detection = analyze(result.records)
            self.finished_ok.emit(result, detection)
        except Exception as exc:  # noqa: BLE001 - surface any failure to the UI
            self.failed.emit(str(exc))
