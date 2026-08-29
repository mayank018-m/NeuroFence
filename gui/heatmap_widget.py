"""
gui/heatmap_widget.py

Renders a layer x neuron heatmap of mean activation energy, so a
researcher can visually scan for isolated bright cells (candidate dormant/
backdoor neurons) against a mostly-uniform background.
"""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QVBoxLayout, QWidget


class HeatmapWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self.plot = pg.PlotWidget()
        self.plot.setLabel("bottom", "Neuron index")
        self.plot.setLabel("left", "Layer")
        self.image_item = pg.ImageItem()
        self.plot.addItem(self.image_item)

        colormap = pg.colormap.get("inferno")
        self.image_item.setColorMap(colormap)

        self.colorbar = pg.ColorBarItem(colorMap=colormap)
        self.colorbar.setImageItem(self.image_item, insert_in=self.plot.getPlotItem())

        layout.addWidget(self.plot)

    def set_data(self, records, layer_names):
        """
        records: list of PromptActivation (from sandbox.scan_runner)
        layer_names: ordered list of layer name strings, e.g. layer_0..N
        Renders mean absolute activation per (layer, neuron) across all
        recorded prompts.
        """
        if not records:
            return

        per_layer_means = []
        for layer_name in layer_names:
            stacked = np.stack(
                [r.activations[layer_name].numpy() for r in records], axis=0
            )  # (P, H)
            per_layer_means.append(stacked.mean(axis=0))  # (H,)

        matrix = np.stack(per_layer_means, axis=0)  # (num_layers, hidden)
        self.image_item.setImage(matrix.T, autoLevels=True)  # neurons on x, layers on y
        self.colorbar.setLevels((float(matrix.min()), float(matrix.max())))

    def highlight_neuron(self, layer_idx: int, neuron_idx: int):
        """Add a marker box around a specific flagged neuron for the deep-dive view."""
        roi = pg.RectROI(
            [neuron_idx - 0.5, layer_idx - 0.5], [1, 1], pen=pg.mkPen("cyan", width=2)
        )
        roi.removable = True
        self.plot.addItem(roi)
