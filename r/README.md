# FAD for R and RStudio

A Shiny application for **FAD** (Foreground Area Density), the fragmentation
analysis of [pyGuidos](https://code.europa.eu/jrc-forest/guidos/pyguidos) and
[GuidosToolbox](https://forest.jrc.ec.europa.eu/en/activities/lpa/gtb/).

FAD is implemented natively with **terra**; pyGuidos is not required.

| | |
|---|---|
| **Plugin version** | 1.0.1 |
| **Reference** | pyGuidos 2.6.5 (FAD, binary) |
| **Host** | R ≥ 4.0, RStudio recommended |

## Installation

1. Download `FAD-R-1.0.1.zip` from the
   [R release](https://github.com/vogtpet/FAD-plugins/releases/tag/r-v1.0.1).
2. Extract it. You get a folder `FAD` with `app.R`, `R/`, `VERSION` and this
   README.
3. Open `app.R` in RStudio and click **Run App**, or run
   `shiny::runApp("path/to/FAD")`.
4. Install the required packages if they are missing:
   `install.packages(c("shiny", "terra"))`.

## Usage

1. Select a single-band 8-bit TIFF/GeoTIFF with the GTB encoding
   (0 = missing, 1 = background, 2 = foreground, optional 3/4).
2. Choose the odd window size `W` (default 27).
3. Choose the output folder.
4. Click **Run FAD**.

The result is `<input>_frag_fad_<W>.tif` with the GTB palette and metadata,
plus `.txt`, `.csv` and `.png` statistics.

## Input and output

See [`../shared/spec/FAD.md`](../shared/spec/FAD.md). Plain TIFFs without
georeferencing are accepted; the result is then unreferenced.

The output classes are FAD values 0–100 plus 101 (background), 102
(missing/invalid), 105 and 106 (special background classes). The window is
clipped at the raster border.

## Statistics

* Rare 0–9, patchy 10–39, transitional 40–59, dominant 60–89, interior 90–100.
* `FAD_av` = sum(value × count) / foreground pixels.
* `AVcon` = sum(value × count) / reported area.
* `.txt` report, `.csv` per-value counts, `.png` histogram.

## Development

```sh
cd r
./scripts/build-release.sh   # dist/FAD-R-<version>.zip + SHA256SUMS
```

The native implementation must reproduce the shared fixtures in
[`../shared/fixtures`](../shared/fixtures).

## License

GPL-3.0-or-later. See [../LICENSE](../LICENSE). The algorithm follows pyGuidos
(GPL-3.0-or-later) by Giovanni Caudullo, Peter Vogt and Pierre Soille.
