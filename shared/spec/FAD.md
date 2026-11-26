# FAD specification (plugin contract)

This document defines the FAD (Foreground Area Density) behaviour shared by the
R, QGIS and ArcGIS plugins in this repository. It follows the binary FAD
implementation in [pyGuidos](https://code.europa.eu/jrc-forest/guidos/pyguidos)
`engine.compute_FAD` (reference version 2.6.5).

## Input

* Single-band, 8-bit (`Byte`, `uint8`) TIFF or GeoTIFF.
* GTB encoding:

  | Value | Meaning |
  |---|---|
  | 0 | NoData / missing |
  | 1 | Background |
  | 2 | Foreground |
  | 3 | Special background class 2 |
  | 4 | Special background class 3 (treated as missing for FAD) |

* Values greater than 4 are invalid.
* A coordinate reference system and geotransform are optional. Plain TIFFs are
  processed in pixel space; the result is then written without georeferencing.
* `W` (window size) is an odd integer, `W >= 3`.

## Algorithm

For every pixel with value 2, a square `W x W` window centred on the pixel is
used. Windows are **clipped** at the raster border (no padding).

```
a = number of pixels with value 2 in the window
b = number of valid pixels in the window
    (value not 0 and not 4; values 1, 2 and 3 are valid)
if b > 0:
    FAD = min(100, (200 * a + b) // (2 * b))
else:
    FAD = 102
```

The integer expression reproduces pyGuidos' rounded percentage:
`round(a / b * 100)` with half-up rounding.

Pixels that are not foreground keep special codes:

| Input value | Output value |
|---|---|
| 1 | 101 |
| 3 | 105 |
| 4 | 106 |
| 0 or anything else | 102 |

Output values `0..100` are the FAD percentage of foreground pixels.

## Output raster

* File name: `<input stem>_frag_fad_<W>.tif`
* 8-bit palette TIFF, LZW compressed; colour table from
  `shared/templates/frag_colormap.txt`.
* Georeferencing and extent are copied from the input when present. Plain
  input TIFFs produce an unreferenced result.
* TIFF metadata:

  ```
  TIFFTAG_IMAGEDESCRIPTION =
    GTB_FOS, <Binary,-1,4,FAD_5,<resX>,<W>>,
    https://forest.jrc.ec.europa.eu/en/activities/lpa/gtb/
  TIFFTAG_SOFTWARE = FAD-plugins <plugin version>
  ```

  `resX` is the absolute input pixel width (`1.0` when there is no
  geotransform); `4` is the constant connectivity field used by pyGuidos for
  FAD; `FAD_5` denotes the five fragmentation classes.

## Statistics

Numbers are computed from the output pixel frequencies `freq[0..255]`.

```
background  = freq[101]
backgr3     = freq[105]
backgr4     = freq[106]
missing     = freq[102]

rare        = sum(freq[0:10])
patchy      = sum(freq[10:40])
transitional= sum(freq[40:60])
dominant    = sum(freq[60:90])
interior    = sum(freq[90:101])

foreground  = rare + patchy + transitional + dominant + interior
reported    = foreground + background + backgr3 + backgr4
sum_product = sum(v * freq[v] for v in 0..100)

FAD_av      = sum_product / foreground      (0 if foreground == 0)
AVcon       = sum_product / reported        (0 if reported == 0)
class_pct   = class_count / foreground * 100 (0 if foreground == 0)
```

## Statistics files

Next to the output TIFF, using the same stem:

* `<stem>.txt` – human-readable report with input/output counts, class counts
  and percentages, `FAD_av` and `AVcon`.
* `<stem>.csv` – header `pixel_value,pixel_count,foreground_proportion` for
  values `0..100`.
* `<stem>.png` – bar chart of foreground proportions for values `0..100`,
  bars coloured from the palette.

## Reference fixtures

`shared/fixtures/input_fad.tif` is a plain 8-bit TIFF using all input classes.
`shared/fixtures/expected/` contains pyGuidos outputs for several window sizes
and the expected statistics. Every plugin must reproduce these byte values
(for the raster) and the computed statistics exactly, as part of its tests.
