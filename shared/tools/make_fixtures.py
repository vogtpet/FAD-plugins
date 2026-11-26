"""Create the FAD fixture input and pyGuidos-generated expected outputs."""

import json
import os
import shutil
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SHARED = os.path.dirname(HERE)
FIXTURES = os.path.join(SHARED, "fixtures")
EXPECTED = os.path.join(FIXTURES, "expected")
WINDOWS = (3, 9, 25)


def build_input():
    data = np.ones((96, 96), dtype=np.uint8)

    yy, xx = np.mgrid[0:96, 0:96]
    blobs = [
        (30, 30, 15),
        (70, 64, 11),
        (50, 78, 7),
        (16, 70, 6),
    ]
    for cx, cy, radius in blobs:
        data[(xx - cx) ** 2 + (yy - cy) ** 2 <= radius ** 2] = 2

    # corridors between the blobs
    for x0, y0, x1, y1, width in [
        (30, 30, 70, 64, 4),
        (30, 30, 16, 70, 3),
        (70, 64, 50, 78, 3),
    ]:
        steps = 400
        for t in np.linspace(0.0, 1.0, steps):
            x = int(round(x0 + (x1 - x0) * t))
            y = int(round(y0 + (y1 - y0) * t))
            data[max(0, y - width):y + width + 1,
                 max(0, x - width):x + width + 1] = 2

    # holes inside the large blob
    data[86:96, 0:8] = 1
    data[0:6, 86:96] = 0      # missing
    data[88:96, 40:48] = 3    # special background 3
    data[40:48, 88:96] = 4    # special background 4 (missing for FAD)
    data[0:4, 40:44] = 1

    return data


def main():
    os.makedirs(EXPECTED, exist_ok=True)
    input_path = os.path.join(FIXTURES, "input_fad.tif")
    data = build_input()
    Image.fromarray(data, mode="L").save(input_path, compression="tiff_lzw")
    print("wrote", input_path)

    try:
        from pyguidos.fragmentation import frag
    except Exception as exc:
        sys.exit("pyGuidos is required to generate the expected outputs: %s"
                 % exc)

    for window in WINDOWS:
        stats = frag(input_path, "FAD", window, outdir=EXPECTED,
                     statists=True, stat_files=False, verb=True)
        produced = os.path.join(
            EXPECTED, "input_fad_frag_fad_%d.tif" % window)
        if not os.path.isfile(produced):
            sys.exit("pyGuidos did not write " + produced)
        with open(os.path.join(EXPECTED, "stats_w%d.json" % window),
                  "w") as handle:
            json.dump(stats, handle, indent=2, sort_keys=True)
        print("window", window, "->", produced)

    print("done")


if __name__ == "__main__":
    main()
