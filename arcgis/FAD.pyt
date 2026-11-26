# -*- coding: utf-8 -*-
"""
/***************************************************************************
 FAD ArcGIS toolbox
 Foreground Area Density (FAD)

 Native implementation of the binary FAD method from pyGuidos 2.6.5.
 No GDAL, pyGuidos or extra runtime is required.

 This program is free software: you can redistribute it and/or modify it
 under the terms of the GNU General Public License, version 3 or later
 (GPL-3.0-or-later).
***************************************************************************/
"""

import os
import sys
import tempfile
from time import strftime

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

import numpy as np
import arcpy

sys.path.insert(0, os.path.dirname(__file__))

from fad_core import compute_fad, compute_statistics
from fad_stats import read_palette, write_csv, write_histogram, write_report
from fad_tags import write_tiff_tags

PLUGIN_VERSION = "1.0.0"
UPDATE_URL = ("https://raw.githubusercontent.com/vogtpet/FAD-plugins/"
              "main/arcgis/VERSION")
RELEASE_URL = "https://github.com/vogtpet/FAD-plugins/releases/tag/arcgis-v"
GTB_LINK = "https://forest.jrc.ec.europa.eu/en/activities/lpa/gtb/"


def version_tuple(value):
    try:
        return tuple(int(part) for part in str(value).strip().split("."))
    except (TypeError, ValueError):
        return ()


def check_for_update(messages):
    try:
        response = urlopen(UPDATE_URL, timeout=5)
        data = response.read()
        if not isinstance(data, str):
            data = data.decode("utf-8", "ignore")
        latest = data.strip()
        if version_tuple(latest) > version_tuple(PLUGIN_VERSION):
            messages.AddWarningMessage(
                "A newer FAD ArcGIS plugin (%s) is available: %s%s"
                % (latest, RELEASE_URL, latest))
    except Exception:
        pass


def write_clr(path, palette):
    handle = open(path, "w")
    try:
        for value in range(256):
            color = palette.get(value, (255, 255, 255, 255))
            handle.write("%d %d %d %d\n"
                         % (value, color[0], color[1], color[2]))
    finally:
        handle.close()


class Toolbox(object):
    def __init__(self):
        self.label = "FAD Tools"
        self.alias = "FAD"
        self.tools = [FAD]


class FAD(object):
    def __init__(self):
        self.label = "FAD"
        self.VERSION = PLUGIN_VERSION
        self.description = ("Foreground Area Density fragmentation analysis - "
                            "plugin version " + PLUGIN_VERSION)
        self.canRunInBackground = False
        self.plugin_dir = os.path.dirname(__file__)
        self.install_info = arcpy.GetInstallInfo()

    def getParameterInfo(self):
        inputRaster = arcpy.Parameter(
            displayName=("Input image - 0 = missing/nodata, 1 = background, "
                         "2 = foreground, 3/4 optional"),
            name="InputImage",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Input")

        window = arcpy.Parameter(
            displayName="Window size (odd, pixels)",
            name="WindowSize",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        window.value = 27

        savePath = arcpy.Parameter(
            displayName="Output folder",
            name="SavePath",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        return [inputRaster, window, savePath]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        messages.AddMessage("FAD ArcGIS plugin %s (pyGuidos 2.6.5 reference)"
                            % PLUGIN_VERSION)
        check_for_update(messages)

        filepath = parameters[0].valueAsText
        if not filepath:
            messages.AddErrorMessage("Please select an input image.")
            sys.exit(0)

        try:
            window = int(parameters[1].value)
        except Exception:
            messages.AddErrorMessage("Please enter an odd window size >= 3.")
            sys.exit(0)
        if window < 3 or window % 2 == 0:
            messages.AddErrorMessage(
                "The window size must be an odd number >= 3.")
            sys.exit(0)

        savepath = parameters[2].valueAsText
        if not savepath or not os.path.isdir(savepath):
            messages.AddErrorMessage("Please select a valid output folder.")
            sys.exit(0)

        dataset = arcpy.Raster(filepath)
        if dataset.bandCount != 1:
            messages.AddErrorMessage(
                "The image is not a single-band image.")
            sys.exit(0)
        if dataset.pixelType != "U8":
            messages.AddErrorMessage(
                "The image is not an 8-bit (Byte) image.")
            sys.exit(0)

        array = arcpy.RasterToNumPyArray(filepath)
        if hasattr(array, "mask"):
            array = array.filled(0)
        array = np.asarray(array)
        if array.dtype != np.uint8:
            array = array.astype(np.uint8)
        maximum = int(array.max())
        if maximum > 4:
            messages.AddErrorMessage(
                "The image contains value %d; FAD accepts only 0, 1, 2, "
                "3 and 4." % maximum)
            sys.exit(0)

        messages.AddMessage("Computing FAD (window %d) ..." % window)
        result = compute_fad(array, window)
        stats = compute_statistics(result)
        palette = read_palette()

        stem = os.path.splitext(os.path.basename(filepath))[0]
        out_name = "%s_frag_fad_%d.tif" % (stem, window)
        target = os.path.join(savepath, out_name)

        desc = arcpy.Describe(filepath)
        extent = desc.extent
        cell_x = desc.meanCellWidth
        cell_y = desc.meanCellHeight
        spatial_ref = desc.spatialReference

        if os.path.isfile(target):
            messages.AddWarningMessage("Overwriting: " + target)
            try:
                os.remove(target)
            except Exception as exc:
                messages.AddErrorMessage(
                    "The existing file could not be replaced: " + str(exc))
                sys.exit(0)

        tmp_raster = arcpy.NumPyArrayToRaster(
            result, arcpy.Point(extent.XMin, extent.YMin), cell_x, cell_y)
        old_srs = arcpy.env.outputCoordinateSystem
        try:
            if spatial_ref and spatial_ref.name != "Unknown":
                arcpy.env.outputCoordinateSystem = spatial_ref
            arcpy.CopyRaster_management(tmp_raster, target)
        finally:
            arcpy.env.outputCoordinateSystem = old_srs
            try:
                arcpy.Delete_management(tmp_raster)
            except Exception:
                pass

        # Colour table
        clr = os.path.join(tempfile.mkdtemp(prefix="fad_clr_"), "fad.clr")
        try:
            write_clr(clr, palette)
            arcpy.AddColormap_management(target, "", clr)
        except Exception as exc:
            messages.AddWarningMessage(
                "The FAD palette could not be applied: " + str(exc))

        # Projection (CopyRaster usually assigns it; make sure)
        try:
            if spatial_ref and spatial_ref.name != "Unknown":
                arcpy.DefineProjection_management(target, spatial_ref)
        except Exception as exc:
            messages.AddWarningMessage(
                "The coordinate system could not be written: " + str(exc))

        # GTB metadata tags without GDAL
        pixel_size = abs(cell_x) if cell_x else 1.0
        tag = ("GTB_FOS, <Binary,-1,4,FAD_5,%s,%d>, %s"
               % (pixel_size, window, GTB_LINK))
        try:
            write_tiff_tags(target, {
                270: tag,
                305: "FAD-plugins " + PLUGIN_VERSION,
                306: strftime("%Y:%m:%d %H:%M:%S"),
            })
        except Exception as exc:
            messages.AddWarningMessage(
                "The GTB metadata could not be written: " + str(exc))

        # Statistics files
        stat_stem = os.path.splitext(target)[0]
        try:
            write_report(stat_stem + ".txt", stats, filepath, target, window,
                         pixel_size, PLUGIN_VERSION)
            write_csv(stat_stem + ".csv", stats)
            write_histogram(stat_stem + ".png", stats, palette)
        except Exception as exc:
            messages.AddWarningMessage(
                "The statistics files could not be written: " + str(exc))

        messages.AddMessage(
            "FAD finished: %s (FAD_av %.6f, AVcon %.6f)"
            % (target, stats["fad_av"], stats["avcon"]))

        try:
            layer = arcpy.MakeRasterLayer_management(
                target, os.path.splitext(out_name)[0]).getOutput(0)
            if self.install_info['ProductName'] == 'Desktop':
                document = arcpy.mapping.MapDocument("CURRENT")
                dataframe = arcpy.mapping.ListDataFrames(document)[0]
                arcpy.mapping.AddLayer(dataframe, layer, "TOP")
            else:
                project = arcpy.mp.ArcGISProject("current")
                project.listMaps()[0].addLayer(layer, "TOP")
        except Exception as exc:
            messages.AddWarningMessage(
                "The result was written but could not be added to the map: "
                + str(exc))
