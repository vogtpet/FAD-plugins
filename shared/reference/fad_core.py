# -*- coding: utf-8 -*-
"""Reference FAD implementation used to generate and verify the fixtures.

This is intentionally simple (full integral images) and not the production
implementation used by the plugins. It follows shared/spec/FAD.md.
"""

import numpy as np

FOREGROUND = 2
BACKGROUND = 1
BACKGR_SP3 = 3
BACKGR_SP4 = 4


def compute_fad(data, window_size):
    """Return the FAD raster for a 2-D uint8 array."""
    data = np.asarray(data, dtype=np.uint8)
    if window_size < 3 or window_size % 2 == 0:
        raise ValueError("window_size must be odd and >= 3")
    height, width = data.shape
    radius = window_size // 2

    fg = (data == FOREGROUND).astype(np.int64)
    valid = ((data != 0) & (data != BACKGR_SP4)).astype(np.int64)

    def integral(array):
        return np.pad(array.cumsum(0).cumsum(1), ((1, 0), (1, 0)))

    fg_sum = integral(fg)
    valid_sum = integral(valid)

    rows = np.arange(height)
    cols = np.arange(width)
    r0 = np.maximum(0, rows - radius)[:, None]
    r1 = np.minimum(height, rows + radius + 1)[:, None]
    c0 = np.maximum(0, cols - radius)[None, :]
    c1 = np.minimum(width, cols + radius + 1)[None, :]

    def window_sum(table):
        return (table[r1, c1] - table[r0, c1]
                - table[r1, c0] + table[r0, c0])

    a = window_sum(fg_sum)
    b = window_sum(valid_sum)

    out = np.full((height, width), 102, dtype=np.uint8)
    out[data == BACKGROUND] = 101
    out[data == BACKGR_SP3] = 105
    out[data == BACKGR_SP4] = 106

    foreground = data == FOREGROUND
    with np.errstate(divide="ignore", invalid="ignore"):
        values = np.where(b > 0, (200 * a + b) // (2 * b), 102)
    values = np.clip(values, 0, 100).astype(np.uint8)
    out[foreground] = values[foreground]
    return out


def statistics(output):
    """Compute the statistics defined in FAD.md from a FAD raster."""
    freq = np.bincount(np.asarray(output, dtype=np.uint8).ravel(), minlength=256)
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

    def pct(value):
        return value / foreground * 100.0 if foreground else 0.0

    return {
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
        "class_pct": {
            "rare": pct(rare),
            "patchy": pct(patchy),
            "transitional": pct(transitional),
            "dominant": pct(dominant),
            "interior": pct(interior),
        },
        "frequency": [int(v) for v in freq[:101]],
    }
