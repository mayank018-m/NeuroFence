"""
gui/main_window.py

NeuroFence desktop forensic application. Lets a researcher:
  1. Browse to a local HF model directory (safetensors only).
  2. Kick off a scan (fuzzing + activation tracking) on a background thread.
  3. View a live progress bar, then a neuron activation heatmap.
  4. Inspect a ranked list of flagged/anomalous neurons ("deep dive" panel
     shows the exact prompts that triggered each one).
  5. Export a PDF forensic report.

Run with:  python main.py
"""

from __future__ import annotations
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gui.heatmap_widget import HeatmapWidget
from gui.scan_worker import ScanWorker
from report.pdf_report import generate_pdf_report

VERDICT_STYLE = {
    "CLEAN": "color: #1a7f37; font-weight: bold;",
    "SUSPICIOUS": "color: #b08800; font-weight: bold;",
    "LIKELY_BACKDOORED": "color: #c92a2a; font-weight: bold;",
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NeuroFence — LLM Weight Poisoning & Backdoor Scanner")
        self.resize(1280, 800)

        self.model_path = None
        self.scan_result = None
        self.detection_report = None
        self.worker = None

        self._build_ui()

    # ------------------------------------------------------------------ #
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)

        # -- top bar: model selection ------------------------------------
        top_bar = QHBoxLayout()
        self.path_label = QLabel("No model loaded.")
        self.path_label.setStyleSheet("color: #555;")
        browse_btn = QPushButton("Load Model Directory…")
        browse_btn.clicked.connect(self.on_browse)

        top_bar.addWidget(browse_btn)
        top_bar.addWidget(self.path_label, stretch=1)
        root_layout.addLayout(top_bar)

        # -- metadata panel ------------------------------------------------
        self.metadata_box = QGroupBox("Model Metadata")
        meta_layout = QVBoxLayout(self.metadata_box)
        self.metadata_text = QTextEdit()
        self.metadata_text.setReadOnly(True)
        self.metadata_text.setMaximumHeight(110)
        meta_layout.addWidget(self.metadata_text)
        root_layout.addWidget(self.metadata_box)

        # -- scan controls ---------------------------------------------
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Baseline prompts:"))
        self.n_baseline_spin = QSpinBox()
        self.n_baseline_spin.setRange(20, 5000)
        self.n_baseline_spin.setValue(300)
        controls.addWidget(self.n_baseline_spin)

        controls.addWidget(QLabel("Random prompts:"))
        self.n_random_spin = QSpinBox()
        self.n_random_spin.setRange(10, 3000)
        self.n_random_spin.setValue(150)
        controls.addWidget(self.n_random_spin)

        controls.addWidget(QLabel("Edge cases:"))
        self.n_edge_spin = QSpinBox()
        self.n_edge_spin.setRange(5, 500)
        self.n_edge_spin.setValue(40)
        controls.addWidget(self.n_edge_spin)

        controls.addWidget(QLabel("Custom triggers:"))
        self.custom_triggers_edit = QLineEdit()
        self.custom_triggers_edit.setPlaceholderText("e.g. Pineapple, ACTIVATE_NOW")
        self.custom_triggers_edit.setMaximumWidth(220)
        controls.addWidget(self.custom_triggers_edit)

        self.scan_btn = QPushButton("Run Forensic Scan")
        self.scan_btn.setEnabled(False)
        self.scan_btn.clicked.connect(self.on_run_scan)
        controls.addWidget(self.scan_btn)

        self.export_btn = QPushButton("Export PDF Report")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.on_export_report)
        controls.addWidget(self.export_btn)

        controls.addStretch(1)
        root_layout.addLayout(controls)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        root_layout.addWidget(self.progress_bar)

        self.verdict_label = QLabel("")
        self.verdict_label.setAlignment(Qt.AlignCenter)
        self.verdict_label.setStyleSheet("font-size: 16px; padding: 6px;")
        root_layout.addWidget(self.verdict_label)

        # -- main split: heatmap | anomaly table + deep dive -------------
        splitter = QSplitter(Qt.Horizontal)

        self.heatmap = HeatmapWidget()
        splitter.addWidget(self.heatmap)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel("Flagged Neurons (ranked by anomaly score)"))

        self.anomaly_table = QTableWidget(0, 6)
        self.anomaly_table.setHorizontalHeaderLabels(
            ["Layer", "Neuron", "Max Z", "Selectivity", "Score", "Trigger?"]
        )
        self.anomaly_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.anomaly_table.itemSelectionChanged.connect(self.on_anomaly_selected)
        right_layout.addWidget(self.anomaly_table, stretch=2)

        right_layout.addWidget(QLabel("Deep Dive: prompts that triggered the selected neuron"))
        self.deep_dive_list = QListWidget()
        right_layout.addWidget(self.deep_dive_list, stretch=1)

        splitter.addWidget(right_panel)
        splitter.setSizes([650, 630])
        root_layout.addWidget(splitter, stretch=1)

    # ------------------------------------------------------------------ #
    # Handlers
    # ------------------------------------------------------------------ #
    def on_browse(self):
        directory = QFileDialog.getExistingDirectory(self, "Select local HF model directory")
        if not directory:
            return
        self.model_path = directory
        self.path_label.setText(directory)

        has_safetensors = any(f.endswith(".safetensors") for f in os.listdir(directory))
        if not has_safetensors:
            QMessageBox.warning(
                self,
                "No safetensors found",
                "This directory has no .safetensors weight files. NeuroFence "
                "will refuse to load legacy .bin/pickle checkpoints for "
                "safety reasons. Convert the model first.",
            )
            self.scan_btn.setEnabled(False)
            return

        self.metadata_text.setPlainText(
            f"Directory: {directory}\nSafetensors files detected. Ready to scan."
        )
        self.scan_btn.setEnabled(True)

    def on_run_scan(self):
        if not self.model_path:
            return
        self.scan_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.verdict_label.setText("Scanning…")
        self.verdict_label.setStyleSheet("font-size: 16px; padding: 6px; color: #555;")

        self.worker = ScanWorker(
            self.model_path,
            n_baseline=self.n_baseline_spin.value(),
            n_random=self.n_random_spin.value(),
            n_edge_case=self.n_edge_spin.value(),
            extra_trigger_words=[
                t.strip() for t in self.custom_triggers_edit.text().split(",") if t.strip()
            ],
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.finished_ok.connect(self.on_scan_finished)
        self.worker.failed.connect(self.on_scan_failed)
        self.worker.start()

    def on_progress(self, done: int, total: int):
        pct = int(done / max(total, 1) * 100)
        self.progress_bar.setValue(pct)

    def on_scan_failed(self, message: str):
        self.scan_btn.setEnabled(True)
        QMessageBox.critical(self, "Scan failed", message)
        self.verdict_label.setText("Scan failed.")
        self.verdict_label.setStyleSheet("font-size: 16px; padding: 6px; color: #c92a2a;")

    def on_scan_finished(self, scan_result, detection_report):
        self.scan_result = scan_result
        self.detection_report = detection_report
        self.scan_btn.setEnabled(True)
        self.export_btn.setEnabled(True)

        meta = scan_result.metadata
        self.metadata_text.setPlainText(
            f"Model: {meta['model_name']}\n"
            f"Parameters: {meta['num_parameters']:,}   Layers: {meta['num_layers']}   "
            f"Hidden size: {meta['hidden_size']}\n"
            f"Weight file SHA-256: "
            + ", ".join(f"{k}={v[:16]}…" for k, v in meta["weight_file_hashes"].items())
        )

        verdict = detection_report.verdict
        self.verdict_label.setText(
            f"Verdict: {verdict}    |    Safety Score: {detection_report.safety_score}/100"
        )
        self.verdict_label.setStyleSheet(
            f"font-size: 16px; padding: 6px; {VERDICT_STYLE.get(verdict, '')}"
        )

        layer_names = list(scan_result.records[0].activations.keys())
        self.heatmap.set_data(scan_result.records, layer_names)

        self._populate_anomaly_table(detection_report.anomalies)

    def _populate_anomaly_table(self, anomalies):
        self.anomaly_table.setRowCount(len(anomalies))
        for row, a in enumerate(anomalies):
            values = [
                a.layer,
                str(a.neuron_index),
                f"{a.max_z_score:.1f}",
                f"{a.selectivity * 100:.2f}%",
                f"{a.anomaly_score:.2f}",
                "YES" if a.trigger_correlated else "no",
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                if a.trigger_correlated:
                    item.setBackground(Qt.red)
                self.anomaly_table.setItem(row, col, item)

    def on_anomaly_selected(self):
        rows = self.anomaly_table.selectionModel().selectedRows()
        if not rows or not self.detection_report:
            return
        idx = rows[0].row()
        anomaly = self.detection_report.anomalies[idx]

        self.deep_dive_list.clear()
        for prompt in anomaly.top_prompts:
            self.deep_dive_list.addItem(prompt if prompt.strip() else "<empty prompt>")

        try:
            layer_idx = int(anomaly.layer.split("_")[-1])
            self.heatmap.highlight_neuron(layer_idx, anomaly.neuron_index)
        except (ValueError, IndexError):
            pass

    def on_export_report(self):
        if not self.scan_result or not self.detection_report:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Forensic Report", "neurofence_report.pdf", "PDF Files (*.pdf)"
        )
        if not path:
            return
        try:
            generate_pdf_report(self.scan_result.metadata, self.detection_report, path)
            QMessageBox.information(self, "Report saved", f"Forensic report saved to:\n{path}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Failed to save report", str(exc))


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
