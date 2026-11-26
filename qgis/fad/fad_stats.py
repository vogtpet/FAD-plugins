# -*- coding: utf-8 -*-
"""FAD palette and statistics writers."""

import csv
import os

PALETTE_FILE = os.path.join(os.path.dirname(__file__), "frag_colormap.txt")


def read_palette(path=PALETTE_FILE):
    """Return {value: (r, g, b, a)} from the GTB fragmentation palette."""
    palette = {}
    with open(path, "r") as handle:
        for line in handle:
            parts = line.split()
            if len(parts) >= 4:
                value = int(parts[0])
                palette[value] = (int(parts[1]), int(parts[2]),
                                  int(parts[3]), 255)
    return palette


def write_csv(path, stats):
    foreground = stats["foreground"]
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["pixel_value", "pixel_count",
                         "foreground_proportion"])
        for value in range(101):
            count = stats["frequency"][value]
            pct = count / foreground * 100.0 if foreground else 0.0
            writer.writerow([value, count, "%.6f" % pct])


def write_report(path, stats, input_path, output_path, window_size,
                 version):
    lines = [
        "FAD - Foreground Area Density",
        "=============================",
        "",
        "Input file      : " + os.path.basename(input_path),
        "Output file     : " + os.path.basename(output_path),
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
    with open(path, "w") as handle:
        handle.write("\n".join(lines) + "\n")
