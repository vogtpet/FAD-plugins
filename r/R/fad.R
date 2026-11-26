## ---------------------------------------------------------------------------
## FAD core: native Foreground Area Density on a terra SpatRaster
## ---------------------------------------------------------------------------

FAD_MAX_INPUT <- 4

fad_read_palette <- function(path) {
  lines <- readLines(path, warn = FALSE)
  parts <- strsplit(trimws(lines), "[[:space:]]+")
  parts <- parts[lengths(parts) >= 4L]
  data.frame(
    value = as.integer(vapply(parts, `[`, "", 1)),
    red = as.integer(vapply(parts, `[`, "", 2)),
    green = as.integer(vapply(parts, `[`, "", 3)),
    blue = as.integer(vapply(parts, `[`, "", 4)),
    alpha = 255L,
    stringsAsFactors = FALSE
  )
}

fad_check_window <- function(window_size) {
  window_size <- as.integer(window_size)
  if (length(window_size) != 1L || is.na(window_size) ||
      window_size < 3L || window_size %% 2L == 0L) {
    stop("The window size must be an odd number >= 3.", call. = FALSE)
  }
  window_size
}

fad_check_raster <- function(r) {
  if (terra::nlyr(r) != 1L) {
    stop("The image is not a single-band image.", call. = FALSE)
  }
  if (!terra::datatype(r) %in% c("INT1U")) {
    stop("The image is not an 8-bit (Byte) image.", call. = FALSE)
  }
  freq <- terra::freq(r)
  values <- freq$value[!is.na(freq$value)]
  if (length(values) > 0L && max(values) > FAD_MAX_INPUT) {
    stop(sprintf(paste0("The image contains value %d; FAD accepts only ",
                        "0 (missing), 1 (background), 2 (foreground), ",
                        "3 and 4."), max(values)), call. = FALSE)
  }
  invisible(TRUE)
}

## Returns a list(raster = SpatRaster, stats = list)
fad_compute <- function(input, window_size = 27L) {
  window_size <- fad_check_window(window_size)
  r <- if (inherits(input, "SpatRaster")) input else terra::rast(input)
  fad_check_raster(r)

  fg <- terra::ifel(r == 2, 1, 0)
  valid <- terra::ifel(r == 0 | r == 4, 0, 1)

  a <- terra::focal(fg, w = window_size, fun = "sum", fillvalue = 0)
  b <- terra::focal(valid, w = window_size, fun = "sum", fillvalue = 0)

  fad <- terra::ifel(
    b > 0,
    terra::ifel((200 * a + b) %/% (2 * b) > 100, 100,
                (200 * a + b) %/% (2 * b)),
    102)

  out <- terra::ifel(
    r == 1, 101,
    terra::ifel(r == 3, 105,
                terra::ifel(r == 4, 106,
                            terra::ifel(r == 2, fad, 102))))

  list(raster = out, stats = fad_statistics(out))
}

fad_statistics <- function(out) {
  values <- as.integer(terra::values(out, mat = FALSE))
  values <- values[!is.na(values)]
  freq <- tabulate(values + 1L, nbins = 256L)
  background <- freq[102]
  backgr3 <- freq[106]
  backgr4 <- freq[107]
  missing <- freq[103]

  rare <- sum(freq[1:10])
  patchy <- sum(freq[11:40])
  transitional <- sum(freq[41:60])
  dominant <- sum(freq[61:90])
  interior <- sum(freq[91:101])
  foreground <- rare + patchy + transitional + dominant + interior
  reported <- foreground + background + backgr3 + backgr4
  sum_product <- sum((0:100) * freq[1:101])

  pct <- function(value) if (foreground > 0) value / foreground * 100 else 0

  list(
    frequency = freq[1:256],
    background = background, backgr3 = backgr3, backgr4 = backgr4,
    missing = missing,
    rare = rare, patchy = patchy, transitional = transitional,
    dominant = dominant, interior = interior,
    foreground = foreground, reported = reported,
    fad_av = if (foreground > 0) sum_product / foreground else 0,
    avcon = if (reported > 0) sum_product / reported else 0,
    percent = list(
      rare = pct(rare), patchy = pct(patchy),
      transitional = pct(transitional), dominant = pct(dominant),
      interior = pct(interior)
    )
  )
}

fad_write_stats <- function(stats, stem, palette, input_name, window_size,
                            pixel_size, version) {
  foreground <- stats$foreground
  proportions <- if (foreground > 0) stats$frequency[1:101] / foreground * 100 else rep(0, 101)

  csv <- data.frame(
    pixel_value = 0:100,
    pixel_count = stats$frequency[1:101],
    foreground_proportion = sprintf("%.6f", proportions)
  )
  utils::write.csv(csv, paste0(stem, ".csv"), row.names = FALSE,
                   quote = FALSE)

  lines <- c(
    "FAD - Foreground Area Density",
    "=============================",
    "",
    paste("Input file      :", input_name),
    paste("Output file     :", basename(stem), ".tif"),
    paste("Plugin version  :", version),
    paste("Window size     :", window_size, "x", window_size, "pixels"),
    paste("Pixel size      :", pixel_size),
    "Reference       : pyGuidos 2.6.5 FAD (binary)",
    "",
    "Input pixels",
    "------------",
    sprintf("Foreground      : %d", foreground),
    sprintf("Background      : %d", stats$background),
    sprintf("Missing         : %d", stats$missing),
    sprintf("Background 3    : %d", stats$backgr3),
    sprintf("Background 4    : %d", stats$backgr4),
    "",
    "Fragmentation classes (foreground pixels)",
    "-----------------------------------------",
    sprintf("Rare            : %10d  %8.3f %%", stats$rare, stats$percent$rare),
    sprintf("Patchy          : %10d  %8.3f %%", stats$patchy, stats$percent$patchy),
    sprintf("Transitional    : %10d  %8.3f %%", stats$transitional, stats$percent$transitional),
    sprintf("Dominant        : %10d  %8.3f %%", stats$dominant, stats$percent$dominant),
    sprintf("Interior        : %10d  %8.3f %%", stats$interior, stats$percent$interior),
    "",
    "Indices",
    "-------",
    sprintf("FAD_av          : %.6f", stats$fad_av),
    sprintf("AVcon           : %.6f", stats$avcon),
    "",
    "Classes: 0-9 rare, 10-39 patchy, 40-59 transitional, 60-89 dominant, 90-100 interior."
  )
  writeLines(lines, paste0(stem, ".txt"))

  colors <- grDevices::rgb(
    palette$red[1:101], palette$green[1:101], palette$blue[1:101],
    maxColorValue = 255)
  grDevices::png(paste0(stem, ".png"), width = 900, height = 520, res = 110)
  graphics::barplot(
    proportions, col = colors, border = NA,
    xlab = "FAD", ylab = "Frequency [%]",
    main = "Foreground pixel histogram",
    names.arg = ifelse((0:100) %% 20 == 0, 0:100, ""),
    cex.names = 0.8)
  grDevices::dev.off()
}

fad_write_output <- function(out, path, palette, window_size, pixel_size,
                             version) {
  out <- out
  terra::coltab(out) <- palette[, c("value", "red", "green", "blue", "alpha")]
  tag <- sprintf(
    "GTB_FOS, <Binary,-1,4,FAD_5,%s,%d>, https://forest.jrc.ec.europa.eu/en/activities/lpa/gtb/",
    format(pixel_size, scientific = FALSE, trim = TRUE),
    as.integer(window_size))
  terra::metags(out) <- c(
    TIFFTAG_IMAGEDESCRIPTION = tag,
    TIFFTAG_SOFTWARE = paste("FAD-plugins", version))
  terra::writeRaster(out, path, datatype = "INT1U", overwrite = TRUE,
                     gdal = c("COMPRESS=LZW", "PREDICTOR=2"))
  invisible(path)
}
