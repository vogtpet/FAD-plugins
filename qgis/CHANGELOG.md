# Changelog

FAD QGIS plugin versions follow [Semantic Versioning](https://semver.org/).

## [1.0.1] - 2026-11-26

### Changed

* Removed the pixel-size line from the statistics report; it does not affect
  the statistics.

## [1.0.0] - 2026-11-26

### Added

* Native FAD implementation for single-band 8-bit TIFF/GeoTIFF with the GTB
  encoding (0, 1, 2 and optional 3/4), matching pyGuidos 2.6.5 FAD.
* Odd window size, border-clipped windows, palette output with
  `frag_colormap.txt`, and the `GTB_FOS ... FAD_5 ...` metadata tag.
* Statistics: class counts and percentages, `FAD_av`, `AVcon`, CSV and
  histogram PNG.
* Plain TIFF inputs without georeferencing.
* QGIS 3/QGIS 4 Qt5/Qt6 compatibility; Linux file picker without GTK theme
  icons.
* Update check against `qgis/VERSION`.
