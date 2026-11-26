# -*- coding: utf-8 -*-
"""Native FAD computation and statistics (host-independent)."""

import numpy as np

MISSING = 0
BACKGROUND = 1
FOREGROUND = 2
BACKGR_SP3 = 3
BACKGR_SP4 = 4
MAX_INPUT = 4


def validate_window(window_size):
    window_size = int(window_size)
    if window_size < 3 or window_size % 2 == 0:
        raise ValueError("The window size must be an odd number >= 3.")
    return window_size


def compute_fad(data, window_size, progress=None):
    """Return the FAD raster for a 2-D uint8 array.

    The window is clipped at the raster border, matching pyGuidos. The
    computation uses moving column sums, so memory is O(width) besides the
    input and output arrays.
    """
    data = np.asarray(data, dtype=np.uint8)
    if data.ndim != 2:
        raise ValueError("The input must be a single-band raster.")
    window_size = validate_window(window_size)
    height, width = data.shape
    radius = window_size // 2

    out = np.full((height, width), 102, dtype=np.uint8)
    out[data == BACKGROUND] = 101
    out[data == BACKGR_SP3] = 105
    out[data == BACKGR_SP4] = 106

    columns = np.arange(width)
    col0 = np.maximum(0, columns - radius)
    col1 = np.minimum(width, columns + radius + 1)

    fg_sums = np.zeros(width, dtype=np.int64)
    valid_sums = np.zeros(width, dtype=np.int64)

    def add_row(row, sign):
        values = data[row]
        fg_sums[:] += sign * (values == FOREGROUND)
        valid_sums[:] += sign * ((values != MISSING) & (values != BACKGR_SP4))

    for row in range(min(height, radius + 1)):
        add_row(row, 1)

    prefix_fg = np.empty(width + 1, dtype=np.int64)
    prefix_valid = np.empty(width + 1, dtype=np.int64)
    prefix_fg[0] = 0
    prefix_valid[0] = 0

    for row in range(height):
        if row:
            entering = row + radius
            if entering < height:
                add_row(entering, 1)
            leaving = row - radius - 1
            if leaving >= 0:
                add_row(leaving, -1)

        np.cumsum(fg_sums, out=prefix_fg[1:])
        np.cumsum(valid_sums, out=prefix_valid[1:])
        num = prefix_fg[col1] - prefix_fg[col0]
        den = prefix_valid[col1] - prefix_valid[col0]

        values = np.full(width, 102, dtype=np.uint8)
        valid = den > 0
        values[valid] = np.minimum(
            100, (200 * num[valid] + den[valid]) // (2 * den[valid]))

        foreground = data[row] == FOREGROUND
        out[row, foreground] = values[foreground]

        if progress is not None and (row % 64 == 0 or row == height - 1):
            progress(row + 1, height)

    return out


def compute_statistics(output):
    """Return the statistics dictionary from a FAD output raster."""
    freq = np.bincount(np.asarray(output, dtype=np.uint8).ravel(),
                       minlength=256)
    background = int(freq[101])
    backgr3 = int(freq[105])
    backgr4 = int(freq[106])
    missing = int(freq[102])

    rare = int(freq[0:10].sum())
    patchy = int(freq[10:40].sum())
    transitional = int(freq[40:60].sum())
    dominant = int(freq[60:90].sum())
    interior = int(freq[90:101].sum())
    foreground = rare + patchy + transitional + dominant + interior
    reported = foreground + background + backgr3 + backgr4
    sum_product = int((np.arange(101) * freq[:101]).sum())

    def percent(value):
        return value / foreground * 100.0 if foreground else 0.0

    return {
        "frequency": [int(v) for v in freq[:256]],
        "background": background,
        "backgr3": backgr3,
        "backgr4": backgr4,
        "missing": missing,
        "rare": rare,
        "patchy": patchy,
        "transitional": transitional,
        "dominant": dominant,
        "interior": interior,
        "foreground": foreground,
        "reported": reported,
        "fad_av": sum_product / foreground if foreground else 0.0,
        "avcon": sum_product / reported if reported else 0.0,
        "percent": {
            "rare": percent(rare),
            "patchy": percent(patchy),
            "transitional": percent(transitional),
            "dominant": percent(dominant),
            "interior": percent(interior),
        },
    }
