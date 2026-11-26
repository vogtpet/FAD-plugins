# FAD for QGIS 3 and 4

A native **FAD** (Foreground Area Density) plugin for QGIS 3.16+ and QGIS 4.
FAD is the fragmentation analysis of
[pyGuidos](https://code.europa.eu/jrc-forest/guidos/pyguidos) and
[GuidosToolbox](https://forest.jrc.ec.europa.eu/en/activities/lpa/gtb/).

The computation is implemented in Python/numpy inside the plugin. pyGuidos is
**not** required and no native binaries are bundled. The result is a
GTB-compatible palette TIFF with the same `GTB_FOS ... FAD_5 ...` metadata tag
as pyGuidos, plus statistics.

| | |
|---|---|
| **Plugin version** | 1.0.0 |
| **Reference** | pyGuidos 2.6.5 (FAD, binary) |
| **Host** | QGIS 3.16 or newer, and QGIS 4 |

## Installation

1. Download `FAD-QGIS-1.0.0.zip` from the
   [QGIS release](https://github.com/vogtpet/FAD-plugins/releases/tag/qgis-v1.0.0).
2. In QGIS open **Plugins → Manage and Install Plugins…**.
3. Select **Install from ZIP**, choose the file and click **Install Plugin**.
4. Enable **FAD** in the **Installed** tab.
5. The plugin appears as **FAD** in the **Plugins** menu and toolbar.

## Usage

1. Open **Plugins → FAD → FAD**.
2. Select the input TIFF/GeoTIFF.
3. Choose the odd window size `W` (default 27).
4. Optionally choose an output folder; the default is next to the input.
5. Click **Start FAD**.

The result is written as `<input>_frag_fad_<W>.tif` and added to the map.
Next to it, three statistics files are written:

* `.txt` – class counts and percentages, `FAD_av`, `AVcon`;
* `.csv` – pixel counts and foreground proportions for values 0–100;
* `.png` – foreground pixel histogram.

## Input

Single-band, 8-bit TIFF or GeoTIFF using the GTB encoding:

| Value | Meaning |
|---|---|
| 0 | Missing / NoData |
| 1 | Background |
| 2 | Foreground |
| 3 | Special background class 2 (optional) |
| 4 | Special background class 3 (optional; treated as missing for FAD) |

Values > 4 are rejected. Plain TIFFs without georeferencing are accepted; the
result is then unreferenced as well.

## Output values

| Value | Meaning |
|---|---|
| 0–100 | FAD percentage of foreground in the `W × W` window |
| 101 | Background |
| 102 | Missing / invalid |
| 105 | Special background class 3 |
| 106 | Special background class 4 |

The window is clipped at the raster border. FAD ignores connectivity; only
`W` is configurable. The algorithm is documented in
[`../shared/spec/FAD.md`](../shared/spec/FAD.md).

## Statistics

```
Rare            0–9
Patchy         10–39
Transitional   40–59
Dominant       60–89
Interior       90–100

FAD_av = sum(value × count) / foreground pixels
AVcon  = sum(value × count) / reported area
```

## Supported platforms

QGIS 3 and QGIS 4 on Windows, Linux (x86_64 and aarch64) and macOS Apple
Silicon. The plugin has no compiled components; the Linux file picker is a
plain Qt dialog to avoid GTK icon-theme crashes.

## Updates

The plugin checks `qgis/VERSION` in the FAD-plugins repository when it is
opened and shows a message if a newer plugin version is available.

## Development

```sh
cd qgis
./scripts/build-release.sh   # dist/FAD-QGIS-<version>.zip + SHA256SUMS
```

`VERSION`, `fad/metadata.txt` and `PLUGIN_VERSION` in `fad/fad.py` must match.
The shared FAD fixtures are in [`../shared/fixtures`](../shared/fixtures) and
must reproduce the pyGuidos reference rasters exactly.

## License

GPL-3.0-or-later. See [../LICENSE](../LICENSE). The algorithm follows pyGuidos
(GPL-3.0-or-later) by Giovanni Caudullo, Peter Vogt and Pierre Soille.
