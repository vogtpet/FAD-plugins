# -*- coding: utf-8 -*-
"""FAD QGIS plugin (QGIS 3 and QGIS 4)."""

import os
import platform
import urllib.request

from qgis.PyQt.QtCore import QCoreApplication, QRectF, Qt, QUrl
from qgis.PyQt.QtGui import (
    QColor, QDesktopServices, QFont, QIcon, QImage, QPainter, QPen)
from qgis.PyQt.QtWidgets import (
    QApplication, QFileDialog, QMessageBox, QProgressDialog)

try:  # Qt 6 moved QAction from QtWidgets to QtGui
    from qgis.PyQt.QtGui import QAction
except ImportError:
    from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsProject, QgsRasterLayer

from .fad_core import compute_fad, compute_statistics
from .fad_dialog import FadDialog
from .fad_io import output_path, read_input, write_output
from .fad_picker import FadPathDialog
from .fad_stats import read_palette, write_csv, write_report

PLUGIN_VERSION = "1.0.1"
UPDATE_URL = ("https://raw.githubusercontent.com/vogtpet/FAD-plugins/"
              "main/qgis/VERSION")
RELEASE_URL = "https://github.com/vogtpet/FAD-plugins/releases/tag/qgis-v"
DOC_URL = "https://github.com/vogtpet/FAD-plugins/blob/main/qgis/README.md"
GUIDE_URL = ("https://pyguidos-d46552.pages.code.europa.eu/usage/"
             "fragmentation.html")

USE_CUSTOM_PICKER = platform.system() == "Linux"

try:
    FORMAT_RGB32 = QImage.Format.Format_RGB32
    ANTIALIASING = QPainter.RenderHint.Antialiasing
except AttributeError:  # Qt 5
    FORMAT_RGB32 = QImage.Format_RGB32
    ANTIALIASING = QPainter.Antialiasing

def _qt_enum(owner, group, name):
    nested = getattr(owner, group, None)
    if nested is not None and hasattr(nested, name):
        return getattr(nested, name)
    return getattr(owner, name)


MSG_INFORMATION = _qt_enum(QMessageBox, "Icon", "Information")
MSG_YES = _qt_enum(QMessageBox, "StandardButton", "Yes")
MSG_NO = _qt_enum(QMessageBox, "StandardButton", "No")

try:
    WINDOW_MODAL = Qt.WindowModality.WindowModal
except AttributeError:
    WINDOW_MODAL = Qt.WindowModal


def version_tuple(value):
    try:
        return tuple(int(part) for part in str(value).strip().split("."))
    except (TypeError, ValueError):
        return ()


class _Cancelled(Exception):
    pass


class Fad:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.VERSION = PLUGIN_VERSION
        self.actions = []
        self.menu = self.tr(u'&FAD')
        self.toolbar = self.iface.addToolBar(u'FAD')
        self.toolbar.setObjectName(u'FAD')
        self._update_checked = False

        self.dlg = FadDialog()
        self.dlg.input_button.clicked.connect(self.select_input)
        self.dlg.output_button.clicked.connect(self.select_output)
        self.dlg.start_button.clicked.connect(self.start)
        self.dlg.help_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(GUIDE_URL)))

    def tr(self, message):
        return QCoreApplication.translate('Fad', message)

    def add_action(self, icon_path, text, callback, parent=None):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        self.toolbar.addAction(action)
        self.iface.addPluginToMenu(self.menu, action)
        self.actions.append(action)
        return action

    def initGui(self):
        self.add_action(
            os.path.join(self.plugin_dir, "icon.png"),
            text=self.tr(u'FAD'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&FAD'), action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar
        self.dlg.deleteLater()

    def run(self):
        self.check_for_update()
        self.dlg.show()
        self.dlg.raise_()

    def check_for_update(self):
        if self._update_checked:
            return
        self._update_checked = True
        try:
            response = urllib.request.urlopen(UPDATE_URL, timeout=5)
            latest = response.read().decode("utf-8", "ignore").strip()
        except Exception:
            return
        if version_tuple(latest) > version_tuple(PLUGIN_VERSION):
            QMessageBox.information(
                self.dlg, "FAD update",
                "A newer FAD QGIS plugin (%s) is available:\n%s%s"
                % (latest, RELEASE_URL, latest))

    def choose_file(self, title, start=""):
        if USE_CUSTOM_PICKER:
            dialog = FadPathDialog(self.dlg, title, start)
            if dialog.exec():
                return dialog.result_path()
            return ""
        filename, _ = QFileDialog.getOpenFileName(
            self.dlg, title, start, "TIFF images (*.tif *.tiff)")
        return filename or ""

    def choose_folder(self, title, start=""):
        if USE_CUSTOM_PICKER:
            dialog = FadPathDialog(self.dlg, title, start, directory=True)
            if dialog.exec():
                return dialog.result_path()
            return ""
        return QFileDialog.getExistingDirectory(self.dlg, title, start) or ""

    def select_input(self):
        filename = self.choose_file(
            "Select the FAD input image", self.dlg.input_edit.text())
        if filename:
            self.dlg.input_edit.setText(filename)
            if not self.dlg.output_edit.text():
                self.dlg.output_edit.setText(os.path.dirname(filename))

    def select_output(self):
        directory = self.choose_folder(
            "Select the output folder", self.dlg.output_edit.text())
        if directory:
            self.dlg.output_edit.setText(directory)

    def normalise_window(self):
        value = self.dlg.window_spin.value()
        if value % 2 == 0:
            value = value + 1 if value < 999 else value - 1
            self.dlg.window_spin.setValue(value)

    def start(self):
        filename = self.dlg.input_edit.text().strip()
        if not filename:
            QMessageBox.critical(self.dlg, "FAD",
                                 "Please select an input image first.")
            return
        self.normalise_window()
        window = self.dlg.window_spin.value()
        outdir = self.dlg.output_edit.text().strip() or None

        try:
            info = read_input(filename)
        except ValueError as exc:
            QMessageBox.critical(self.dlg, "FAD", str(exc))
            return

        target = output_path(filename, window, outdir)
        target_dir = os.path.dirname(target)
        if not os.path.isdir(target_dir):
            QMessageBox.critical(self.dlg, "FAD",
                                 "The output folder does not exist:\n"
                                 + target_dir)
            return
        if os.path.exists(target):
            answer = QMessageBox.question(
                self.dlg, "FAD",
                "The file already exists and will be overwritten:\n" + target,
                MSG_YES | MSG_NO, MSG_NO)
            if answer != MSG_YES:
                return

        progress = QProgressDialog("Computing FAD...", "Cancel", 0,
                                   info["height"], self.dlg)
        progress.setWindowTitle("FAD")
        progress.setWindowModality(WINDOW_MODAL)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()

        def update_progress(done, total):
            progress.setValue(done)
            QApplication.processEvents()
            if progress.wasCanceled():
                raise _Cancelled()

        try:
            result = compute_fad(info["data"], window, update_progress)
            progress.setValue(info["height"])
            palette = read_palette()
            write_output(target, result, info, window, palette, PLUGIN_VERSION)

            stats = compute_statistics(result)
            stem = os.path.splitext(target)[0]
            write_report(stem + ".txt", stats, filename, target, window,
                         PLUGIN_VERSION)
            write_csv(stem + ".csv", stats)
            self.write_histogram(stem + ".png", stats, palette)

            layer = QgsRasterLayer(target,
                                   os.path.splitext(os.path.basename(target))[0])
            if layer.isValid():
                QgsProject.instance().addMapLayer(layer)
                self.iface.messageBar().pushSuccess(
                    "FAD", "Result written: " + target)
            self.dlg.log.setPlainText(self.summary(stats, target, window))
        except _Cancelled:
            self.dlg.log.appendPlainText("FAD cancelled.")
        except Exception as exc:
            QMessageBox.critical(self.dlg, "FAD", str(exc))
        finally:
            progress.close()

    def summary(self, stats, target, window):
        return (
            "FAD finished\n"
            "Window size : %d x %d pixels\n"
            "Output      : %s\n\n"
            "Classes (foreground pixels)\n"
            "  Rare          %10d  %8.3f %%\n"
            "  Patchy        %10d  %8.3f %%\n"
            "  Transitional  %10d  %8.3f %%\n"
            "  Dominant      %10d  %8.3f %%\n"
            "  Interior      %10d  %8.3f %%\n\n"
            "FAD_av : %.6f\n"
            "AVcon  : %.6f\n"
            % (window, window, target,
               stats["rare"], stats["percent"]["rare"],
               stats["patchy"], stats["percent"]["patchy"],
               stats["transitional"], stats["percent"]["transitional"],
               stats["dominant"], stats["percent"]["dominant"],
               stats["interior"], stats["percent"]["interior"],
               stats["fad_av"], stats["avcon"]))

    def write_histogram(self, path, stats, palette):
        width, height = 900, 520
        left, right, top, bottom = 85, width - 30, 50, height - 65
        image = QImage(width, height, FORMAT_RGB32)
        image.fill(QColor(255, 255, 255))
        painter = QPainter(image)
        painter.setRenderHint(ANTIALIASING)

        frequencies = stats["frequency"]
        foreground = stats["foreground"]
        proportions = [
            frequencies[v] / foreground * 100.0 if foreground else 0.0
            for v in range(101)]
        maximum = max(proportions) if proportions else 0.0
        if maximum <= 0:
            maximum = 1.0

        plot_width = right - left
        plot_height = bottom - top
        bar_width = plot_width / 101.0

        painter.setPen(QPen(QColor(60, 60, 60)))
        painter.drawLine(left, top, left, bottom)
        painter.drawLine(left, bottom, right, bottom)

        for value in range(101):
            pct = proportions[value]
            bar_height = pct / maximum * plot_height
            color = palette.get(value, (255, 255, 255, 255))
            painter.fillRect(
                QRectF(left + value * bar_width, bottom - bar_height,
                       max(1.0, bar_width * 0.9), bar_height),
                QColor(color[0], color[1], color[2]))

        painter.setFont(QFont("Arial", 9))
        for value in range(0, 101, 20):
            x = left + value * bar_width
            painter.drawText(int(x) - 8, bottom + 18, str(value))
        for step in range(5):
            pct = maximum * step / 4.0
            y = bottom - plot_height * step / 4.0
            painter.drawText(8, int(y) + 4, "%.1f" % pct)

        painter.setFont(QFont("Arial", 13, QFont.Weight.Bold
                              if hasattr(QFont, "Weight") else QFont.Bold))
        painter.drawText(left + plot_width // 2 - 110, 28,
                         "Foreground pixel histogram")
        painter.setFont(QFont("Arial", 10))
        painter.drawText(left + plot_width // 2 - 15, height - 15, "FAD")
        painter.save()
        painter.translate(20, top + plot_height // 2 + 50)
        painter.rotate(-90)
        painter.drawText(0, 0, "Frequency [%]")
        painter.restore()
        painter.end()
        image.save(path, "PNG")
