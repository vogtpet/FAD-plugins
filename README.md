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

| Plugin | Folder | Version | Host |
|---|---|---|---|
| QGIS 3 & 4 | [`qgis/`](qgis/) | planned | QGIS 3.16+ and QGIS 4 |
| R / RStudio | [`r/`](r/) | planned | R ≥ 4.0 (Shiny) |
| ArcGIS | [`arcgis/`](arcgis/) | planned | ArcGIS Pro and Desktop 10.x |

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
