# Changelog

FAD R plugin versions follow [Semantic Versioning](https://semver.org/).

## [1.0.3] - 2026-11-26

### Changed

* Removed the pixel-size line from the statistics report; it does not affect
  the statistics.

## [1.0.2] - 2026-11-26

### Added

* If the result TIFF already exists, the app asks for confirmation before
  overwriting the raster and its statistics files.

## [1.0.1] - 2026-11-26

### Fixed

* An invalid input image no longer crashes the Shiny app. Validation and
  processing errors are shown in a modal dialog and the app stays usable.

## [1.0.0] - 2026-11-26

### Added

* Shiny application with native terra implementation of FAD, matching
  pyGuidos 2.6.5 (0/1/2 input, optional 3/4).
* GTB palette output with `GTB_FOS ... FAD_5 ...` metadata and preserved
  extent/CRS.
* Statistics: class counts and percentages, `FAD_av`, `AVcon`, CSV and
  histogram PNG.
* Plain TIFF inputs without georeferencing.
