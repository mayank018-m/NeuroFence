"""
gui/main_window.py
NeuroFence — professional SOC-style desktop interface.

Backend/API compatibility:
- gui.scan_worker.ScanWorker
- gui.heatmap_widget.HeatmapWidget
- report.pdf_report.generate_pdf_report

Run:
    python main.py
"""

from __future__ import annotations

import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGridLayout,
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
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gui.heatmap_widget import HeatmapWidget
from gui.scan_worker import ScanWorker
from report.pdf_report import generate_pdf_report


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

BG = "#0B0F14"
SIDEBAR = "#0F151C"
CARD = "#121A23"
CARD_2 = "#151F2A"
BORDER = "#263442"
TEXT = "#F1F5F9"
MUTED = "#8FA1B5"
CYAN = "#00D4FF"
GREEN = "#22C55E"
AMBER = "#F59E0B"
RED = "#EF4444"
WHITE = "#FFFFFF"


APP_QSS = f"""
QMainWindow, QWidget {{
    background: {BG};
    color: {TEXT};
    font-family: "Segoe UI";
    font-size: 13px;
}}

QFrame#Sidebar {{
    background: {SIDEBAR};
    border-right: 1px solid {BORDER};
}}

QFrame#TopBar {{
    background: {BG};
    border-bottom: 1px solid {BORDER};
}}

QFrame#Card, QGroupBox {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}

QGroupBox {{
    margin-top: 12px;
    padding: 18px 12px 12px 12px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    color: {MUTED};
    background: {CARD};
}}

QLabel#Brand {{
    color: {TEXT};
    font-size: 21px;
    font-weight: 700;
}}

QLabel#BrandAccent {{
    color: {CYAN};
    font-size: 21px;
    font-weight: 700;
}}

QLabel#SectionTitle {{
    color: {TEXT};
    font-size: 19px;
    font-weight: 700;
}}

QLabel#PageSubtitle {{
    color: {MUTED};
    font-size: 12px;
}}

QLabel#Muted {{
    color: {MUTED};
}}

QLabel#CardTitle {{
    color: {MUTED};
    font-size: 11px;
    font-weight: 600;
}}

QLabel#CardValue {{
    color: {TEXT};
    font-size: 25px;
    font-weight: 700;
}}

QLabel#StatusPill {{
    background: #10251A;
    color: {GREEN};
    border: 1px solid #1C5B35;
    border-radius: 12px;
    padding: 5px 10px;
    font-weight: 700;
}}

QPushButton {{
    background: #17222D;
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 8px 13px;
}}

QPushButton:hover {{
    background: #1D2B38;
    border-color: #3A5265;
}}

QPushButton:pressed {{
    background: #101820;
}}

QPushButton:disabled {{
    color: #536272;
    background: #111820;
    border-color: #1A2530;
}}

QPushButton#PrimaryButton {{
    background: {CYAN};
    color: #031018;
    border: 0;
    font-weight: 800;
}}

QPushButton#PrimaryButton:hover {{
    background: #39DEFF;
}}

QPushButton#DangerButton {{
    color: {RED};
}}

QPushButton#NavButton {{
    text-align: left;
    padding: 11px 13px;
    border: 0;
    border-radius: 7px;
    background: transparent;
    color: {MUTED};
}}

QPushButton#NavButton:hover {{
    background: #17212B;
    color: {TEXT};
}}

QPushButton#NavButton[active="true"] {{
    background: #102833;
    color: {CYAN};
    border-left: 3px solid {CYAN};
}}

QLineEdit, QSpinBox, QTextEdit, QListWidget {{
    background: #0D141C;
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 7px;
    selection-background-color: #174E60;
}}

QLineEdit:focus, QSpinBox:focus, QTextEdit:focus {{
    border-color: #277B91;
}}

QProgressBar {{
    background: #0D141C;
    border: 1px solid {BORDER};
    border-radius: 6px;
    text-align: center;
    color: {TEXT};
    height: 12px;
}}

QProgressBar::chunk {{
    background: {CYAN};
    border-radius: 5px;
}}

QTableWidget {{
    background: #0D141C;
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    gridline-color: #1D2833;
    selection-background-color: #143B4A;
    selection-color: {WHITE};
}}

QHeaderView::section {{
    background: #151F2A;
    color: {MUTED};
    border: 0;
    border-bottom: 1px solid {BORDER};
    padding: 9px;
    font-weight: 600;
}}

QScrollArea {{
    border: 0;
    background: transparent;
}}

QSplitter::handle {{
    background: {BORDER};
}}

QToolTip {{
    background: #18232E;
    color: {TEXT};
    border: 1px solid #385063;
    padding: 6px;
}}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("NeuroFence — AI Model Security & Forensics")
        self.resize(1440, 900)
        self.setMinimumSize(1180, 720)

        self.model_path = None
        self.scan_result = None
        self.detection_report = None
        self.worker = None

        self.nav_buttons = []
        self._build_ui()

    # ------------------------------------------------------------------
    # Generic UI helpers
    # ------------------------------------------------------------------

    def _card(self, title: str, value: str, accent: str = TEXT):
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 13, 16, 13)
        layout.setSpacing(4)

        title_label = QLabel(title.upper())
        title_label.setObjectName("CardTitle")

        value_label = QLabel(value)
        value_label.setObjectName("CardValue")
        value_label.setStyleSheet(f"color: {accent};")

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        return card, value_label

    def _section_header(self, title: str, subtitle: str = ""):
        box = QVBoxLayout()
        box.setSpacing(2)

        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")
        box.addWidget(title_label)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setObjectName("PageSubtitle")
            box.addWidget(sub)

        return box

    def _make_nav_button(self, text: str, page_index: int):
        btn = QPushButton(text)
        btn.setObjectName("NavButton")
        btn.setProperty("active", page_index == 0)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self._set_page(page_index))
        self.nav_buttons.append(btn)
        return btn

    # ------------------------------------------------------------------
    # Main UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root)

        # ---------------- Sidebar ----------------
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(235)

        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(16, 22, 16, 18)
        side_layout.setSpacing(5)

        brand_row = QHBoxLayout()
        brand = QLabel("Neuro")
        brand.setObjectName("Brand")
        accent = QLabel("Fence")
        accent.setObjectName("BrandAccent")
        brand_row.addWidget(brand)
        brand_row.addWidget(accent)
        brand_row.addStretch()
        side_layout.addLayout(brand_row)

        version = QLabel("AI MODEL SECURITY PLATFORM")
        version.setObjectName("PageSubtitle")
        side_layout.addWidget(version)
        side_layout.addSpacing(22)

        self.nav_dashboard = self._make_nav_button("  ◈   Dashboard", 0)
        self.nav_scanner = self._make_nav_button("  ⌕   Model Scanner", 1)
        self.nav_forensics = self._make_nav_button("  ◉   Neuron Forensics", 2)
        self.nav_weights = self._make_nav_button("  ◫   Weight Analysis", 3)
        self.nav_reports = self._make_nav_button("  ▤   Reports", 4)
        self.nav_settings = self._make_nav_button("  ⚙   Settings", 5)

        for b in self.nav_buttons:
            side_layout.addWidget(b)

        side_layout.addStretch()

        status = QFrame()
        status.setObjectName("Card")
        status_layout = QVBoxLayout(status)
        status_layout.setContentsMargins(12, 11, 12, 11)

        s1 = QLabel("ENGINE STATUS")
        s1.setObjectName("CardTitle")
        s2 = QLabel("●  Ready")
        s2.setStyleSheet(f"color: {GREEN}; font-weight: 700;")
        s3 = QLabel("Local forensic engine")
        s3.setObjectName("PageSubtitle")

        status_layout.addWidget(s1)
        status_layout.addWidget(s2)
        status_layout.addWidget(s3)
        side_layout.addWidget(status)

        root_layout.addWidget(sidebar)

        # ---------------- Main stack ----------------
        self.pages = QStackedWidget()
        root_layout.addWidget(self.pages, 1)

        self.dashboard_page = self._build_dashboard_page()
        self.scanner_page = self._build_scanner_page()
        self.forensics_page = self._build_forensics_page()
        self.weights_page = self._build_placeholder_page(
            "Weight Analysis",
            "Statistical inspection of model parameters, outliers and distribution anomalies."
        )
        self.reports_page = self._build_placeholder_page(
            "Forensic Reports",
            "Export and review generated NeuroFence investigation reports."
        )
        self.settings_page = self._build_placeholder_page(
            "Settings & About",
            "NeuroFence configuration and platform information."
        )

        for page in (
            self.dashboard_page,
            self.scanner_page,
            self.forensics_page,
            self.weights_page,
            self.reports_page,
            self.settings_page,
        ):
            self.pages.addWidget(page)

        self._set_page(0)

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    def _build_dashboard_page(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(18)

        # top bar
        top = QHBoxLayout()
        title_block = self._section_header(
            "Security Operations Dashboard",
            "Continuous forensic visibility into LLM weight integrity and neuron behavior.",
        )
        top.addLayout(title_block)
        top.addStretch()

        self.dashboard_status = QLabel("● SYSTEM READY")
        self.dashboard_status.setObjectName("StatusPill")
        top.addWidget(self.dashboard_status)

        outer.addLayout(top)

        # KPI cards
        grid = QGridLayout()
        grid.setSpacing(12)

        c1, self.score_value = self._card("Safety Score", "—", GREEN)
        c2, self.neurons_value = self._card("Neurons Scanned", "—")
        c3, self.anomaly_value = self._card("Anomalies", "—", AMBER)
        c4, self.verdict_value = self._card("Verdict", "NO SCAN", MUTED)

        grid.addWidget(c1, 0, 0)
        grid.addWidget(c2, 0, 1)
        grid.addWidget(c3, 0, 2)
        grid.addWidget(c4, 0, 3)

        outer.addLayout(grid)

        # model intelligence
        model_card = QFrame()
        model_card.setObjectName("Card")
        ml = QVBoxLayout(model_card)
        ml.setContentsMargins(16, 14, 16, 14)
        ml.setSpacing(8)

        row = QHBoxLayout()
        heading = QLabel("MODEL INTELLIGENCE")
        heading.setObjectName("CardTitle")
        row.addWidget(heading)
        row.addStretch()

        self.model_badge = QLabel("NO MODEL LOADED")
        self.model_badge.setStyleSheet(
            f"color: {MUTED}; border: 1px solid {BORDER}; "
            "border-radius: 10px; padding: 4px 9px;"
        )
        row.addWidget(self.model_badge)
        ml.addLayout(row)

        self.model_summary = QLabel(
            "Load a local Hugging Face model directory containing .safetensors files "
            "to begin a forensic investigation."
        )
        self.model_summary.setObjectName("Muted")
        self.model_summary.setWordWrap(True)
        ml.addWidget(self.model_summary)

        outer.addWidget(model_card)

        # quick actions
        actions = QHBoxLayout()
        actions.setSpacing(10)

        load = QPushButton("＋  Load Model")
        load.clicked.connect(self.on_browse)

        scan = QPushButton("▶  Run Forensic Scan")
        scan.setObjectName("PrimaryButton")
        scan.clicked.connect(lambda: self._set_page(1))

        report = QPushButton("▣  Export Report")
        report.clicked.connect(self.on_export_report)

        actions.addWidget(load)
        actions.addWidget(scan)
        actions.addWidget(report)
        actions.addStretch()

        outer.addLayout(actions)

        # evidence / status
        bottom = QHBoxLayout()
        bottom.setSpacing(12)

        evidence = QFrame()
        evidence.setObjectName("Card")
        evl = QVBoxLayout(evidence)
        evl.setContentsMargins(16, 14, 16, 14)

        h = QLabel("FORENSIC EVIDENCE")
        h.setObjectName("CardTitle")
        evl.addWidget(h)

        self.dashboard_evidence = QLabel(
            "No scan completed yet.\n\n"
            "After a scan, this panel will summarize anomaly evidence, "
            "trigger correlation and the highest-risk neurons."
        )
        self.dashboard_evidence.setObjectName("Muted")
        self.dashboard_evidence.setWordWrap(True)
        evl.addWidget(self.dashboard_evidence)
        bottom.addWidget(evidence, 1)

        workflow = QFrame()
        workflow.setObjectName("Card")
        wl = QVBoxLayout(workflow)
        wl.setContentsMargins(16, 14, 16, 14)

        h2 = QLabel("INVESTIGATION WORKFLOW")
        h2.setObjectName("CardTitle")
        wl.addWidget(h2)

        for text in (
            "01   Load model",
            "02   Fire forensic corpus",
            "03   Analyze activation anomalies",
            "04   Inspect trigger-correlated neurons",
            "05   Export evidence report",
        ):
            lab = QLabel(text)
            lab.setObjectName("Muted")
            wl.addWidget(lab)

        bottom.addWidget(workflow, 1)
        outer.addLayout(bottom, 1)

        return page

    # ------------------------------------------------------------------
    # Scanner
    # ------------------------------------------------------------------

    def _build_scanner_page(self):
        page = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)

        outer = QVBoxLayout(page)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(15)

        outer.addLayout(
            self._section_header(
                "Model Scanner",
                "Configure and launch a controlled activation-forensics scan.",
            )
        )

        model_card = QFrame()
        model_card.setObjectName("Card")
        ml = QVBoxLayout(model_card)
        ml.setContentsMargins(16, 14, 16, 14)

        r = QHBoxLayout()
        r.addWidget(QLabel("MODEL DIRECTORY"))
        r.addStretch()

        self.path_label = QLabel("No model loaded")
        self.path_label.setObjectName("Muted")
        self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self.on_browse)

        r.addWidget(self.path_label, 1)
        r.addWidget(browse_btn)
        ml.addLayout(r)

        self.metadata_text = QTextEdit()
        self.metadata_text.setReadOnly(True)
        self.metadata_text.setMinimumHeight(105)
        self.metadata_text.setMaximumHeight(150)
        self.metadata_text.setPlaceholderText("Model metadata will appear here after loading/scanning.")
        ml.addWidget(self.metadata_text)

        outer.addWidget(model_card)

        config_card = QFrame()
        config_card.setObjectName("Card")
        cl = QVBoxLayout(config_card)
        cl.setContentsMargins(16, 14, 16, 14)
        cl.setSpacing(10)

        title = QLabel("SCAN CONFIGURATION")
        title.setObjectName("CardTitle")
        cl.addWidget(title)

        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        form.addWidget(QLabel("Baseline prompts"), 0, 0)
        self.n_baseline_spin = QSpinBox()
        self.n_baseline_spin.setRange(20, 5000)
        self.n_baseline_spin.setValue(300)
        form.addWidget(self.n_baseline_spin, 0, 1)

        form.addWidget(QLabel("Random prompts"), 0, 2)
        self.n_random_spin = QSpinBox()
        self.n_random_spin.setRange(10, 3000)
        self.n_random_spin.setValue(150)
        form.addWidget(self.n_random_spin, 0, 3)

        form.addWidget(QLabel("Edge cases"), 1, 0)
        self.n_edge_spin = QSpinBox()
        self.n_edge_spin.setRange(5, 500)
        self.n_edge_spin.setValue(40)
        form.addWidget(self.n_edge_spin, 1, 1)

        form.addWidget(QLabel("Custom triggers"), 1, 2)
        self.custom_triggers_edit = QLineEdit()
        self.custom_triggers_edit.setPlaceholderText("e.g. Pineapple, ACTIVATE_NOW")
        form.addWidget(self.custom_triggers_edit, 1, 3)

        cl.addLayout(form)

        buttons = QHBoxLayout()
        self.scan_btn = QPushButton("▶  Run Forensic Scan")
        self.scan_btn.setObjectName("PrimaryButton")
        self.scan_btn.setEnabled(False)
        self.scan_btn.clicked.connect(self.on_run_scan)

        self.export_btn = QPushButton("▣  Export PDF Report")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.on_export_report)

        buttons.addWidget(self.scan_btn)
        buttons.addWidget(self.export_btn)
        buttons.addStretch()
        cl.addLayout(buttons)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        cl.addWidget(self.progress_bar)

        self.progress_label = QLabel("Ready — waiting for a model.")
        self.progress_label.setObjectName("Muted")
        cl.addWidget(self.progress_label)

        outer.addWidget(config_card)

        # live verdict
        verdict_card = QFrame()
        verdict_card.setObjectName("Card")
        vl = QHBoxLayout(verdict_card)
        vl.setContentsMargins(18, 14, 18, 14)

        vtext = QVBoxLayout()
        vtitle = QLabel("CURRENT ASSESSMENT")
        vtitle.setObjectName("CardTitle")
        self.verdict_label = QLabel("NO SCAN")
        self.verdict_label.setStyleSheet(f"color: {MUTED}; font-size: 22px; font-weight: 800;")
        vtext.addWidget(vtitle)
        vtext.addWidget(self.verdict_label)

        vl.addLayout(vtext)
        vl.addStretch()

        self.score_big = QLabel("— / 100")
        self.score_big.setStyleSheet(f"color: {GREEN}; font-size: 30px; font-weight: 800;")
        vl.addWidget(self.score_big)

        outer.addWidget(verdict_card)

        return scroll

    # ------------------------------------------------------------------
    # Forensics
    # ------------------------------------------------------------------

    def _build_forensics_page(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(12)

        outer.addLayout(
            self._section_header(
                "Neuron Forensics",
                "Activation heatmap, ranked anomalies and trigger evidence.",
            )
        )

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # left: heatmap
        heat_card = QFrame()
        heat_card.setObjectName("Card")
        hl = QVBoxLayout(heat_card)
        hl.setContentsMargins(10, 10, 10, 10)

        heat_title = QLabel("ACTIVATION FORENSICS")
        heat_title.setObjectName("CardTitle")
        hl.addWidget(heat_title)

        self.heatmap = HeatmapWidget()
        hl.addWidget(self.heatmap, 1)
        splitter.addWidget(heat_card)

        # right: anomalies + deep dive
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(10)

        anomaly_card = QFrame()
        anomaly_card.setObjectName("Card")
        al = QVBoxLayout(anomaly_card)
        al.setContentsMargins(12, 12, 12, 12)

        ah = QHBoxLayout()
        at = QLabel("SUSPICIOUS NEURONS")
        at.setObjectName("CardTitle")
        ah.addWidget(at)
        ah.addStretch()

        self.anomaly_count_label = QLabel("0 findings")
        self.anomaly_count_label.setObjectName("Muted")
        ah.addWidget(self.anomaly_count_label)
        al.addLayout(ah)

        self.anomaly_table = QTableWidget(0, 6)
        self.anomaly_table.setHorizontalHeaderLabels(
            ["Layer", "Neuron", "Max Z", "Selectivity", "Score", "Trigger"]
        )
        self.anomaly_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.anomaly_table.verticalHeader().setVisible(False)
        self.anomaly_table.setAlternatingRowColors(False)
        self.anomaly_table.itemSelectionChanged.connect(self.on_anomaly_selected)
        al.addWidget(self.anomaly_table, 1)

        rl.addWidget(anomaly_card, 3)

        deep_card = QFrame()
        deep_card.setObjectName("Card")
        dl = QVBoxLayout(deep_card)
        dl.setContentsMargins(12, 12, 12, 12)

        dh = QLabel("DEEP DIVE — TRIGGERING PROMPTS")
        dh.setObjectName("CardTitle")
        dl.addWidget(dh)

        self.deep_dive_list = QListWidget()
        self.deep_dive_list.setMinimumHeight(150)
        dl.addWidget(self.deep_dive_list)

        rl.addWidget(deep_card, 2)

        splitter.addWidget(right)
        splitter.setSizes([650, 650])

        outer.addWidget(splitter, 1)

        return page

    # ------------------------------------------------------------------
    # Placeholder pages
    # ------------------------------------------------------------------

    def _build_placeholder_page(self, title: str, subtitle: str):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)

        layout.addLayout(self._section_header(title, subtitle))

        card = QFrame()
        card.setObjectName("Card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 20, 20, 20)

        label = QLabel(
            "Module ready for integration.\n\n"
            "The current NeuroFence scan engine remains unchanged; "
            "this interface separates future analysis modules into dedicated workspaces."
        )
        label.setObjectName("Muted")
        label.setWordWrap(True)
        cl.addWidget(label)
        cl.addStretch()

        layout.addWidget(card, 1)
        return page

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _set_page(self, index: int):
        self.pages.setCurrentIndex(index)

        for i, btn in enumerate(self.nav_buttons):
            btn.setProperty("active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def on_browse(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select local Hugging Face model directory"
        )
        if not directory:
            return

        has_safetensors = any(
            f.lower().endswith(".safetensors") for f in os.listdir(directory)
        )

        if not has_safetensors:
            QMessageBox.warning(
                self,
                "Unsupported model format",
                "No .safetensors files were found.\n\n"
                "NeuroFence refuses legacy .bin/pickle checkpoints for safety. "
                "Convert the model to safetensors first.",
            )
            self.scan_btn.setEnabled(False)
            return

        self.model_path = directory
        short_path = directory if len(directory) < 70 else "…" + directory[-67:]

        self.path_label.setText(short_path)
        self.path_label.setToolTip(directory)
        self.scan_btn.setEnabled(True)

        self.model_badge.setText("MODEL READY")
        self.model_badge.setStyleSheet(
            f"color: {GREEN}; border: 1px solid #1C5B35; "
            "border-radius: 10px; padding: 4px 9px;"
        )

        self.model_summary.setText(
            f"Ready for forensic analysis: {os.path.basename(directory)}"
        )

        self.metadata_text.setPlainText(
            f"Directory: {directory}\n"
            f"Format: Hugging Face / safetensors\n"
            f"Status: Ready for forensic scan"
        )

        self.dashboard_status.setText("● MODEL READY")
        self.dashboard_status.setStyleSheet(
            f"background: #10251A; color: {GREEN}; "
            "border: 1px solid #1C5B35; border-radius: 12px; "
            "padding: 5px 10px; font-weight: 700;"
        )

        self._set_page(1)

    def on_run_scan(self):
        if not self.model_path:
            return

        self.scan_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Initializing forensic engine…")

        self.verdict_label.setText("SCANNING")
        self.verdict_label.setStyleSheet(
            f"color: {CYAN}; font-size: 22px; font-weight: 800;"
        )
        self.score_big.setText("— / 100")

        self.dashboard_status.setText("● SCAN IN PROGRESS")
        self.dashboard_status.setStyleSheet(
            f"background: #102733; color: {CYAN}; "
            "border: 1px solid #19586A; border-radius: 12px; "
            "padding: 5px 10px; font-weight: 700;"
        )

        self.worker = ScanWorker(
            self.model_path,
            n_baseline=self.n_baseline_spin.value(),
            n_random=self.n_random_spin.value(),
            n_edge_case=self.n_edge_spin.value(),
            extra_trigger_words=[
                t.strip()
                for t in self.custom_triggers_edit.text().split(",")
                if t.strip()
            ],
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.finished_ok.connect(self.on_scan_finished)
        self.worker.failed.connect(self.on_scan_failed)
        self.worker.start()

        self._set_page(2)

    def on_progress(self, done: int, total: int):
        pct = int(done / max(total, 1) * 100)
        self.progress_bar.setValue(pct)
        self.progress_label.setText(
            f"Analyzing activation corpus  •  {done:,} / {total:,} prompts  •  {pct}%"
        )

    def on_scan_failed(self, message: str):
        self.scan_btn.setEnabled(True)

        self.progress_label.setText("Scan failed.")
        self.dashboard_status.setText("● SCAN ERROR")
        self.dashboard_status.setStyleSheet(
            f"background: #2B1518; color: {RED}; "
            "border: 1px solid #673039; border-radius: 12px; "
            "padding: 5px 10px; font-weight: 700;"
        )

        self.verdict_label.setText("SCAN FAILED")
        self.verdict_label.setStyleSheet(
            f"color: {RED}; font-size: 22px; font-weight: 800;"
        )

        QMessageBox.critical(self, "Forensic scan failed", message)

    def on_scan_finished(self, scan_result, detection_report):
        self.scan_result = scan_result
        self.detection_report = detection_report

        self.scan_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.progress_label.setText("Forensic scan completed successfully.")

        meta = scan_result.metadata

        hashes = ", ".join(
            f"{k}={v[:16]}…"
            for k, v in meta.get("weight_file_hashes", {}).items()
        )

        self.metadata_text.setPlainText(
            f"Model: {meta.get('model_name', 'Unknown')}\n"
            f"Parameters: {meta.get('num_parameters', 0):,}    "
            f"Layers: {meta.get('num_layers', '—')}    "
            f"Hidden size: {meta.get('hidden_size', '—')}\n"
            f"Weight SHA-256: {hashes or 'Unavailable'}"
        )

        verdict = detection_report.verdict
        score = detection_report.safety_score
        anomalies = detection_report.anomalies

        self.verdict_label.setText(verdict.replace("_", " "))
        self.score_big.setText(f"{score:.1f} / 100")

        if verdict == "CLEAN":
            verdict_color = GREEN
            self.dashboard_status.setText("● NO CRITICAL FINDINGS")
        elif verdict == "SUSPICIOUS":
            verdict_color = AMBER
            self.dashboard_status.setText("● REVIEW REQUIRED")
        else:
            verdict_color = RED
            self.dashboard_status.setText("● HIGH RISK DETECTED")

        self.verdict_label.setStyleSheet(
            f"color: {verdict_color}; font-size: 22px; font-weight: 800;"
        )
        self.score_big.setStyleSheet(
            f"color: {verdict_color}; font-size: 30px; font-weight: 800;"
        )
        self.verdict_value.setText(verdict.replace("_", " "))
        self.verdict_value.setStyleSheet(
            f"color: {verdict_color}; font-size: 25px; font-weight: 700;"
        )
        self.score_value.setText(f"{score:.1f}")
        self.score_value.setStyleSheet(
            f"color: {verdict_color}; font-size: 25px; font-weight: 700;"
        )
        self.neurons_value.setText(f"{detection_report.num_neurons_scanned:,}")
        self.anomaly_value.setText(str(len(anomalies)))

        self.dashboard_status.setStyleSheet(
            f"background: {'#10251A' if verdict == 'CLEAN' else '#2A2010' if verdict == 'SUSPICIOUS' else '#2B1518'}; "
            f"color: {verdict_color}; border: 1px solid "
            f"{'#1C5B35' if verdict == 'CLEAN' else '#684E16' if verdict == 'SUSPICIOUS' else '#673039'}; "
            "border-radius: 12px; padding: 5px 10px; font-weight: 700;"
        )

        if scan_result.records:
            layer_names = list(scan_result.records[0].activations.keys())
            self.heatmap.set_data(scan_result.records, layer_names)

        self._populate_anomaly_table(anomalies)
        self.anomaly_count_label.setText(f"{len(anomalies)} findings")

        if anomalies:
            top = anomalies[0]
            evidence = (
                f"Highest-ranked anomaly: {top.layer} / neuron {top.neuron_index}\n"
                f"Max Z-score: {top.max_z_score:.2f}\n"
                f"Selectivity: {top.selectivity * 100:.2f}%\n"
                f"Anomaly score: {top.anomaly_score:.2f}\n"
                f"Trigger correlation: {'YES' if top.trigger_correlated else 'NO'}"
            )
        else:
            evidence = (
                "No neurons crossed the configured anomaly thresholds.\n\n"
                "The model did not produce a statistically significant "
                "dormant-spike finding in this scan."
            )

        self.dashboard_evidence.setText(evidence)

    def _populate_anomaly_table(self, anomalies):
        self.anomaly_table.setRowCount(len(anomalies))

        for row, a in enumerate(anomalies):
            values = [
                a.layer,
                str(a.neuron_index),
                f"{a.max_z_score:.2f}",
                f"{a.selectivity * 100:.2f}%",
                f"{a.anomaly_score:.2f}",
                "YES" if a.trigger_correlated else "NO",
            ]

            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)

                if a.trigger_correlated:
                    if col == 5:
                        item.setForeground(Qt.red)
                        item.setFont(QFont("Segoe UI", 10, QFont.Bold))

                self.anomaly_table.setItem(row, col, item)

    def on_anomaly_selected(self):
        rows = self.anomaly_table.selectionModel().selectedRows()
        if not rows or not self.detection_report:
            return

        idx = rows[0].row()
        if idx >= len(self.detection_report.anomalies):
            return

        anomaly = self.detection_report.anomalies[idx]

        self.deep_dive_list.clear()
        for prompt in anomaly.top_prompts:
            self.deep_dive_list.addItem(
                prompt if prompt.strip() else "<empty prompt>"
            )

        try:
            layer_idx = int(anomaly.layer.split("_")[-1])
            self.heatmap.highlight_neuron(layer_idx, anomaly.neuron_index)
        except (ValueError, IndexError):
            pass

    def on_export_report(self):
        if not self.scan_result or not self.detection_report:
            QMessageBox.information(
                self,
                "No scan available",
                "Run a forensic scan before exporting a report.",
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save NeuroFence Forensic Report",
            "neurofence_report.pdf",
            "PDF Files (*.pdf)",
        )

        if not path:
            return

        try:
            generate_pdf_report(
                self.scan_result.metadata,
                self.detection_report,
                path,
            )
            self._set_page(4)
            QMessageBox.information(
                self,
                "Report exported",
                f"Forensic report saved to:\n{path}",
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Report export failed",
                str(exc),
            )


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(APP_QSS)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
