# -*- coding: utf-8 -*-
"""FAD statistics files for ArcGIS (Python 2.7 and 3.x)."""

import os
import struct
import sys
import zlib

PALETTE_FILE = os.path.join(os.path.dirname(__file__), "frag_colormap.txt")


def read_palette(path=PALETTE_FILE):
    palette = {}
    handle = open(path, "r")
    try:
        for line in handle:
            parts = line.split()
            if len(parts) >= 4:
                palette[int(parts[0])] = (
                    int(parts[1]), int(parts[2]), int(parts[3]), 255)
    finally:
        handle.close()
    return palette


def write_report(path, stats, input_name, output_name, window_size,
                 version):
    lines = [
        "FAD - Foreground Area Density",
        "=============================",
        "",
        "Input file      : " + os.path.basename(input_name),
        "Output file     : " + os.path.basename(output_name),
        "Plugin version  : " + str(version),
        "Window size     : %d x %d pixels" % (window_size, window_size),
        "Reference       : pyGuidos 2.6.5 FAD (binary)",
        "",
        "Input pixels",
        "------------",
        "Foreground      : %d" % stats["foreground"],
        "Background      : %d" % stats["background"],
        "Missing         : %d" % stats["missing"],
        "Background 3    : %d" % stats["backgr3"],
        "Background 4    : %d" % stats["backgr4"],
        "",
        "Fragmentation classes (foreground pixels)",
        "-----------------------------------------",
        "Rare            : %10d  %8.3f %%" % (
            stats["rare"], stats["percent"]["rare"]),
        "Patchy          : %10d  %8.3f %%" % (
            stats["patchy"], stats["percent"]["patchy"]),
        "Transitional    : %10d  %8.3f %%" % (
            stats["transitional"], stats["percent"]["transitional"]),
        "Dominant        : %10d  %8.3f %%" % (
            stats["dominant"], stats["percent"]["dominant"]),
        "Interior        : %10d  %8.3f %%" % (
            stats["interior"], stats["percent"]["interior"]),
        "",
        "Indices",
        "-------",
        "FAD_av          : %.6f" % stats["fad_av"],
        "AVcon           : %.6f" % stats["avcon"],
        "",
        "Classes: 0-9 rare, 10-39 patchy, 40-59 transitional, "
        "60-89 dominant, 90-100 interior.",
    ]
    handle = open(path, "w")
    try:
        handle.write("\n".join(lines) + "\n")
    finally:
        handle.close()


def write_csv(path, stats):
    foreground = stats["foreground"]
    handle = open(path, "w")
    try:
        handle.write("pixel_value,pixel_count,foreground_proportion\n")
        for value in range(101):
            count = stats["frequency"][value]
            pct = count / float(foreground) * 100.0 if foreground else 0.0
            handle.write("%d,%d,%.6f\n" % (value, count, pct))
    finally:
        handle.close()


def _row_bytes(row):
    if sys.version_info[0] >= 3:
        return bytes(row)
    return "".join(chr(value) for value in row)


def _png_chunk(kind, data):
    block = struct.pack(">I", len(data)) + kind + data
    return block + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)


def _write_bars_png(path, proportions, palette, width=900, height=520):
    """Fallback PNG: bars and axes, no text."""
    white = 255
    pixels = [bytearray([white] * (width * 3)) for _ in range(height)]

    left, right, top, bottom = 80, width - 30, 40, height - 50
    plot_height = bottom - top
    plot_width = right - left
    maximum = max(proportions) if proportions else 0.0
    if maximum <= 0:
        maximum = 1.0

    def put(x, y, rgb):
        if 0 <= x < width and 0 <= y < height:
            row = pixels[y]
            row[3 * x] = rgb[0]
            row[3 * x + 1] = rgb[1]
            row[3 * x + 2] = rgb[2]

    def line(x0, y0, x1, y1, rgb):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        error = dx - dy
        while True:
            put(x0, y0, rgb)
            if x0 == x1 and y0 == y1:
                break
            twice = 2 * error
            if twice > -dy:
                error -= dy
                x0 += sx
            if twice < dx:
                error += dx
                y0 += sy

    axis = (60, 60, 60)
    line(left, top, left, bottom, axis)
    line(left, bottom, right, bottom, axis)

    bar_width = plot_width / 101.0
    for value in range(101):
        height_px = int(round(proportions[value] / maximum * plot_height))
        color = palette.get(value, (255, 255, 255, 255))
        x0 = int(left + value * bar_width)
        x1 = int(left + (value + 1) * bar_width) - 1
        if x1 < x0:
            x1 = x0
        for y in range(bottom - height_px, bottom):
            for x in range(x0, x1 + 1):
                put(x, y, color)

    raw = b""
    for row in pixels:
        raw += b"\x00" + _row_bytes(row)
    png = b"\x89PNG\r\n\x1a\n"
    png += _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height,
                                           8, 2, 0, 0, 0))
    png += _png_chunk(b"IDAT", zlib.compress(raw, 9))
    png += _png_chunk(b"IEND", b"")
    handle = open(path, "wb")
    try:
        handle.write(png)
    finally:
        handle.close()


def write_histogram(path, stats, palette):
    foreground = stats["foreground"]
    proportions = [
        stats["frequency"][value] / float(foreground) * 100.0
        if foreground else 0.0 for value in range(101)]

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        colors = [
            (palette.get(value, (255, 255, 255, 255))[0] / 255.0,
             palette.get(value, (255, 255, 255, 255))[1] / 255.0,
             palette.get(value, (255, 255, 255, 255))[2] / 255.0)
            for value in range(101)]
        figure, axes = plt.subplots(figsize=(9, 5.2), dpi=100)
        axes.bar(range(101), proportions, color=colors, width=1.0,
                 edgecolor="none")
        axes.set_xlabel("FAD")
        axes.set_ylabel("Frequency [%]")
        axes.set_title("Foreground pixel histogram")
        axes.set_xlim(-1, 101)
        figure.tight_layout()
        figure.savefig(path, facecolor="white")
        plt.close(figure)
        return
    except Exception:
        pass

    _write_bars_png(path, proportions, palette)
