# Changelog

FAD ArcGIS plugin versions follow [Semantic Versioning](https://semver.org/).

## [1.0.3] - 2026-11-26

### Fixed

* Reload `fad_core`, `fad_stats` and `fad_tags` from the current plugin
  folder. ArcGIS keeps them in `sys.modules` for the whole session, so after
  an in-place upgrade the old `write_report` signature could be called
  ("missing 1 required positional argument: 'version'").

### Changed

* Time the update check and the automatic layer addition; the total message
  now includes both. The update-check timeout is 2 s.

## [1.0.2] - 2026-11-26

### Fixed

* A raster layer dragged from the Contents pane is a Layer object; use its
  `catalogPath` for reading instead of passing the object to `arcpy.Raster`,
  which raised "expected a raster or layer name".

## [1.0.1] - 2026-11-26

### Fixed

* ArcGIS Desktop 10 statistics: Python 2 integer division produced 0.0 % for
  all classes and integer-rounded FAD_av/AVcon. All divisions now use floats.
* Removed the pixel-size line from the statistics report.

### Changed

* Disable pyramid and raster-statistics building while writing the output,
  and report per-stage timings (read, compute, write, palette, total).

## [1.0.0] - 2026-11-26

### Added

* ArcGIS Pro and Desktop 10.x toolbox with native numpy FAD matching
  pyGuidos 2.6.5.
* GTB palette output and `GTB_FOS ... FAD_5 ...` metadata tag without GDAL.
* Statistics: class counts, `FAD_av`, `AVcon`, CSV and histogram PNG.
* Plain TIFF inputs without georeferencing.
* Update check against `arcgis/VERSION`.
