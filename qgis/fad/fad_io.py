# -*- coding: utf-8 -*-
"""GDAL input/output helpers for the FAD plugin."""

import os

import numpy as np
from osgeo import gdal

from .fad_core import MAX_INPUT

GTB_LINK = "https://forest.jrc.ec.europa.eu/en/activities/lpa/gtb/"
DEFAULT_TRANSFORM = (0.0, 1.0, 0.0, 0.0, 0.0, 1.0)


def read_input(path):
    """Read and validate a FAD input raster."""
    dataset = gdal.Open(path, gdal.GA_ReadOnly)
    if dataset is None:
        raise ValueError("The image could not be opened.")

    if dataset.RasterCount != 1:
        raise ValueError("The image is not a single-band image.")
    band = dataset.GetRasterBand(1)
    if gdal.GetDataTypeName(band.DataType) != "Byte":
        raise ValueError("The image is not an 8-bit (Byte) image.")

    data = band.ReadAsArray()
    if data is None:
        raise ValueError("The pixel values could not be read.")
    maximum = int(data.max())
    if maximum > MAX_INPUT:
        raise ValueError(
            "The image contains value %d; FAD accepts only 0 (missing), "
            "1 (background), 2 (foreground), 3 and 4." % maximum)

    projection = dataset.GetProjection()
    gcps = dataset.GetGCPs()
    gcp_projection = dataset.GetGCPProjection()
    if not projection:
        projection = gcp_projection
    transform = dataset.GetGeoTransform()
    has_transform = (transform is not None
                     and tuple(transform) != DEFAULT_TRANSFORM)

    return {
        "data": data,
        "projection": projection,
        "geotransform": transform if has_transform else None,
        "gcps": gcps,
        "gcp_projection": gcp_projection,
        "width": dataset.RasterXSize,
        "height": dataset.RasterYSize,
        "pixel_size": abs(transform[1]) if has_transform else 1.0,
        "path": path,
    }


def color_table(palette):
    table = gdal.ColorTable()
    for value in range(256):
        table.SetColorEntry(value, palette.get(value, (255, 255, 255, 255)))
    return table


def write_output(path, data, info, window_size, palette, version):
    """Write the palette GeoTIFF with georeferencing and GTB metadata."""
    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(
        path, info["width"], info["height"], 1, gdal.GDT_Byte,
        options=["COMPRESS=LZW", "PREDICTOR=2", "TILED=YES",
                 "BLOCKXSIZE=256", "BLOCKYSIZE=256"])
    if dataset is None:
        raise RuntimeError("The result file could not be created.")

    band = dataset.GetRasterBand(1)
    band.SetColorTable(color_table(palette))
    band.SetColorInterpretation(gdal.GCI_PaletteIndex)
    band.WriteArray(data)

    if info["projection"]:
        dataset.SetProjection(info["projection"])
    if info["gcps"]:
        dataset.SetGCPs(info["gcps"], info["gcp_projection"])
    elif info["geotransform"] is not None:
        dataset.SetGeoTransform(info["geotransform"])

    tag = ("GTB_FOS, <Binary,-1,4,FAD_5,%s,%d>, %s"
           % (info["pixel_size"], int(window_size), GTB_LINK))
    dataset.SetMetadataItem("TIFFTAG_IMAGEDESCRIPTION", tag)
    dataset.SetMetadataItem("TIFFTAG_SOFTWARE", "FAD-plugins " + version)
    dataset.FlushCache()
    dataset = None


def output_path(input_path, window_size, outdir=None):
    directory = outdir or os.path.dirname(os.path.abspath(input_path))
    stem = os.path.splitext(os.path.basename(input_path))[0]
    return os.path.join(directory,
                        "%s_frag_fad_%d.tif" % (stem, int(window_size)))
