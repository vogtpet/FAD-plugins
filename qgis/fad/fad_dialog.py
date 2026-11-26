# -*- coding: utf-8 -*-
"""Programmatic FAD dialog (Qt5/Qt6)."""

import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
    QPushButton, QSpinBox, QVBoxLayout)


class FadDialog(QDialog):
    def __init__(self, parent=None):
        super(FadDialog, self).__init__(parent)
        self.setWindowTitle("FAD - Foreground Area Density")
        self.setWindowIcon(QIcon(os.path.join(
            os.path.dirname(__file__), "icon.png")))
        self.resize(760, 520)

        self.input_edit = QLineEdit()
        self.input_button = QPushButton("Select...")
        input_row = QHBoxLayout()
        input_row.addWidget(QLabel("Input TIFF"))
        input_row.addWidget(self.input_edit, 1)
        input_row.addWidget(self.input_button)

        self.window_spin = QSpinBox()
        self.window_spin.setRange(3, 999)
        self.window_spin.setSingleStep(2)
        self.window_spin.setValue(27)
        window_row = QHBoxLayout()
        window_row.addWidget(QLabel("Window size (odd, pixels)"))
        window_row.addWidget(self.window_spin)
        window_row.addWidget(QLabel(
            "FAD: proportion of foreground in a W x W window"))
        window_row.addStretch(1)

        self.output_edit = QLineEdit()
        self.output_button = QPushButton("Select...")
        self.output_edit.setPlaceholderText(
            "Leave empty to write next to the input image")
        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("Output folder"))
        output_row.addWidget(self.output_edit, 1)
        output_row.addWidget(self.output_button)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlainText(
            "Input: single-band 8-bit TIFF/GeoTIFF with GTB values\n"
            "  0 = missing/nodata, 1 = background, 2 = foreground,\n"
            "  3 and 4 = optional special background classes.\n\n"
            "Output: <input>_frag_fad_<W>.tif with palette and GTB "
            "metadata, plus .txt, .csv and .png statistics.")

        self.start_button = QPushButton("Start FAD")
        self.help_button = QPushButton("FAD guide")
        self.close_button = QPushButton("Close")
        self.start_button.setDefault(True)
        buttons = QHBoxLayout()
        buttons.addWidget(self.help_button)
        buttons.addStretch(1)
        buttons.addWidget(self.start_button)
        buttons.addWidget(self.close_button)

        layout = QVBoxLayout(self)
        layout.addLayout(input_row)
        layout.addLayout(window_row)
        layout.addLayout(output_row)
        layout.addWidget(self.log, 1)
        layout.addLayout(buttons)

        self.close_button.clicked.connect(self.close)
        self.window_spin.editingFinished.connect(self.normalise_window)

    def normalise_window(self):
        value = self.window_spin.value()
        if value % 2 == 0:
            self.window_spin.setValue(max(3, value + 1))
