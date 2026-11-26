# FAD plugins

Application-specific wrappers for **FAD** (Foreground Area Density), the
fragmentation analysis of
[pyGuidos](https://code.europa.eu/jrc-forest/guidos/pyguidos) and
[GuidosToolbox](https://forest.jrc.ec.europa.eu/en/activities/lpa/gtb/), for
QGIS 3/4, ArcGIS and R/RStudio.

FAD classifies the proportion of foreground pixels in a moving window of
`W × W` pixels. This repository implements FAD natively in each host:

* no pyGuidos installation is required,
* no native binaries or Python packages are bundled,
* the result is a GTB-compatible palette TIFF with the same
  `GTB_FOS ... FAD_5 ...` metadata tag as pyGuidos,
* statistics (`FAD_av`, `AVcon`, class counts, CSV and histogram PNG) are
  written next to the result.

The reference behaviour and test fixtures are in [`shared/`](shared/):
[`shared/spec/FAD.md`](shared/spec/FAD.md) is the contract implemented by all
plugins. Reference version: **pyGuidos 2.6.5**.

| Plugin | Folder | Version | Host | Download |
|---|---|---|---|---|
| QGIS 3 & 4 | [`qgis/`](qgis/) | 1.0.1 | QGIS 3.16+ and QGIS 4 | [FAD-QGIS-1.0.1.zip](https://github.com/vogtpet/FAD-plugins/releases/download/qgis-v1.0.1/FAD-QGIS-1.0.1.zip) |
| R / RStudio | [`r/`](r/) | 1.0.3 | R ≥ 4.0 (Shiny) | [FAD-R-1.0.3.zip](https://github.com/vogtpet/FAD-plugins/releases/download/r-v1.0.3/FAD-R-1.0.3.zip) |
| ArcGIS | [`arcgis/`](arcgis/) | 1.0.1 | ArcGIS Pro and Desktop 10.x | [FAD-ArcGIS-1.0.1.zip](https://github.com/vogtpet/FAD-plugins/releases/download/arcgis-v1.0.1/FAD-ArcGIS-1.0.1.zip) |

## Repository layout

```
FAD-plugins/
├── shared/     FAD specification, palette, reference implementation, fixtures
├── qgis/       QGIS 3/4 plugin
├── r/          R/RStudio plugin
├── arcgis/     ArcGIS toolbox
└── .github/    release workflows
```

## Input and output

Input: single-band 8-bit TIFF/GeoTIFF with GTB values `0` NoData,
`1` background, `2` foreground (optionally `3`/`4` special background).
Output: `<input>_frag_fad_<W>.tif` plus `.txt`, `.csv` and `.png` statistics.

FAD ignores connectivity; only the odd window size `W` is configurable.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE). The algorithm follows pyGuidos
(GPL-3.0-or-later) by Giovanni Caudullo, Peter Vogt and Pierre Soille; see
[`shared/spec/FAD.md`](shared/spec/FAD.md).
