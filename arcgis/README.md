# FAD for ArcGIS

A native **FAD** (Foreground Area Density) toolbox for ArcGIS Pro and ArcGIS
Desktop 10.x, based on the pyGuidos 2.6.5 FAD implementation.

No pyGuidos, GDAL, extra Python packages or administrator rights are needed;
the computation uses the numpy that ships with ArcGIS.

| | |
|---|---|
| **Plugin version** | 1.0.2 |
| **Reference** | pyGuidos 2.6.5 (FAD, binary) |
| **Host** | ArcGIS Pro and ArcGIS Desktop 10.3–10.9 |

## Installation

1. Download `FAD-ArcGIS-1.0.2.zip` from the
   [ArcGIS release](https://github.com/vogtpet/FAD-plugins/releases/tag/arcgis-v1.0.2)
   and verify it against `SHA256SUMS` if you wish.
2. Extract the archive to a permanent folder, for example
   `C:\Users\<user>\Documents\ArcGIS\FAD-ArcGIS`.
3. **ArcGIS Pro:** open the **Catalog** pane, **Favorites → Add Item →
   Toolbox**, and select `...\FAD-ArcGIS\FAD.pyt`. The **FAD Tools** toolbox
   is then available in the project.
4. **ArcGIS Desktop 10.x:** open the **ArcToolbox** window, right-click
   **ArcToolbox → Add Toolbox…**, and select `...\FAD-ArcGIS\FAD.pyt`.

If an earlier version is installed, remove the old toolbox entry first.

## Usage

Run the **FAD** tool:

* **Input image** – single-band 8-bit TIFF/GeoTIFF with GTB values
  0 = missing, 1 = background, 2 = foreground, optional 3/4. The parameter
  accepts a raster layer: drag it from the Contents pane or browse for it.
* **Window size** – odd number ≥ 3 (default 27).
* **Output folder**.

The result is written as `<input>_frag_fad_<W>.tif` and added to the current
map/data frame. Next to it, `.txt`, `.csv` and `.png` statistics are written.

## Input and output

See [`../shared/spec/FAD.md`](../shared/spec/FAD.md). The window is clipped at
the raster border; FAD ignores connectivity. Output values are 0–100 (FAD
percentage), 101 (background), 102 (missing/invalid), 105 and 106 (special
background classes).

The result uses the GTB fragmentation palette and the metadata tag

```
GTB_FOS, <Binary,-1,4,FAD_5,<resX>,<W>>, https://forest.jrc.ec.europa.eu/en/activities/lpa/gtb/
```

Plain TIFFs without a coordinate reference system are accepted; the result is
then unreferenced.

## Statistics

`<result>.txt`, `.csv` and `.png` contain the class counts and percentages,
`FAD_av`, `AVcon` and the foreground histogram. The PNG uses matplotlib when
it is available in the ArcGIS Python environment and a plain bar chart
otherwise.

## Updates

The toolbox checks `arcgis/VERSION` in the FAD-plugins repository each time it
runs and warns when a newer plugin version is available.

## Development

```sh
cd arcgis
./scripts/build-release.sh   # dist/FAD-ArcGIS-<version>.zip + SHA256SUMS
```

The shared fixtures in [`../shared/fixtures`](../shared/fixtures) contain
pyGuidos reference outputs for windows 3, 9 and 25.

## License

GPL-3.0-or-later. See [../LICENSE](../LICENSE). The algorithm follows pyGuidos
(GPL-3.0-or-later) by Giovanni Caudullo, Peter Vogt and Pierre Soille.
