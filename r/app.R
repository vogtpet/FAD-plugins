## ---------------------------------------------------------------------------
## FAD - Foreground Area Density for R/RStudio
## ---------------------------------------------------------------------------

app_dir <- local({
  option_dir <- getOption("fad.app_dir", "")
  if (is.character(option_dir) && length(option_dir) == 1L &&
      nzchar(option_dir)) {
    return(normalizePath(option_dir, mustWork = FALSE))
  }
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- sub("^--file=", "", grep("^--file=", args, value = TRUE))
  if (length(file_arg) == 1L && nzchar(file_arg)) {
    return(normalizePath(dirname(file_arg), mustWork = FALSE))
  }
  if (file.exists(file.path(getwd(), "app.R"))) {
    return(normalizePath(getwd(), mustWork = FALSE))
  }
  normalizePath(getwd(), mustWork = FALSE)
})

source(file.path(app_dir, "R", "fad.R"), local = FALSE)
plugin_version <- readLines(file.path(app_dir, "VERSION"), warn = FALSE)[1]

required_packages <- c("shiny", "terra")
missing_packages <- required_packages[!vapply(required_packages,
                                              requireNamespace,
                                              logical(1), quietly = TRUE)]
if (length(missing_packages) > 0L) {
  message("FAD: installing required R packages: ",
          paste(missing_packages, collapse = ", "))
  repos <- getOption("repos")
  if (is.null(repos) || length(repos) == 0L ||
      identical(unname(repos["CRAN"]), "@CRAN@")) {
    repos <- c(CRAN = "https://cloud.r-project.org")
  }
  utils::install.packages(missing_packages, repos = repos)
}

library(shiny)

palette <- fad_read_palette(file.path(app_dir, "R", "frag_colormap.txt"))
palette_colors <- grDevices::rgb(
  palette$red[1:101], palette$green[1:101], palette$blue[1:101],
  maxColorValue = 255)

ui <- fluidPage(
  titlePanel(sprintf("FAD - Foreground Area Density %s", plugin_version)),
  sidebarLayout(
    sidebarPanel(
      fileInput("input", "Input TIFF/GeoTIFF",
                accept = c(".tif", ".tiff", "image/tiff")),
      numericInput("window", "Window size (odd, pixels)", 27,
                   min = 3, step = 2),
      textInput("outdir", "Output folder", getwd()),
      actionButton("run", "Run FAD"),
      tags$p(tags$small(
        paste("Input: single-band 8-bit TIFF with GTB values",
              "0=missing, 1=background, 2=foreground, 3/4 optional."))),
      width = 4
    ),
    mainPanel(
      verbatimTextOutput("log"),
      tableOutput("stats"),
      plotOutput("hist", height = "420px"),
      width = 8
    )
  )
)

server <- function(input, output, session) {
  state <- reactiveValues(log = "Select an input image and click Run FAD.",
                          stats = NULL, paths = NULL)

  fad_error <- function(message) {
    message <- as.character(message)
    state$log <- paste("FAD error:", message)
    state$stats <- NULL
    state$paths <- NULL
    showModal(modalDialog(
      title = "FAD error",
      message,
      easyClose = TRUE,
      footer = modalButton("Close")))
  }

  observeEvent(input$run, {
    req(input$input)
    window <- as.integer(input$window)
    if (is.na(window) || window < 3L || window %% 2L == 0L) {
      fad_error("The window size must be an odd number >= 3.")
      return()
    }
    outdir <- trimws(input$outdir)
    if (!dir.exists(outdir)) {
      fad_error(paste("Output folder does not exist:", outdir))
      return()
    }

    name <- input$input$name
    stem <- tools::file_path_sans_ext(basename(name))
    out_tif <- file.path(outdir, sprintf("%s_frag_fad_%d.tif", stem, window))

    tryCatch({
      withProgress(message = "Computing FAD...", value = 0, {
        incProgress(0.1, detail = "Reading input")
        r <- terra::rast(input$input$datapath)
        incProgress(0.2, detail = "Moving window")
        result <- fad_compute(r, window)
        incProgress(0.5, detail = "Writing result")
        resolution <- terra::res(result$raster)
        pixel_size <- if (length(resolution) > 0L) abs(resolution[1]) else 1
        fad_write_output(result$raster, out_tif, palette, window, pixel_size,
                         plugin_version)
        out_stem <- tools::file_path_sans_ext(out_tif)
        fad_write_stats(result$stats, out_stem, palette, basename(name), window,
                        pixel_size, plugin_version)
        incProgress(0.4, detail = "Done")
      })

      state$stats <- result$stats
      state$paths <- c(
        tif = out_tif,
        txt = paste0(tools::file_path_sans_ext(out_tif), ".txt"),
        csv = paste0(tools::file_path_sans_ext(out_tif), ".csv"),
        png = paste0(tools::file_path_sans_ext(out_tif), ".png")
      )
      state$log <- paste(
        "FAD finished",
        paste("Window:", window, "x", window),
        paste("Result:", out_tif),
        paste("Statistics:", state$paths[["txt"]], state$paths[["csv"]],
              state$paths[["png"]]),
        sep = "\n")
    }, error = function(e) {
      fad_error(conditionMessage(e))
    })
  })

  output$log <- renderText(state$log)

  output$stats <- renderTable({
    req(state$stats)
    s <- state$stats
    data.frame(
      Class = c("Rare", "Patchy", "Transitional", "Dominant", "Interior",
                "FAD_av", "AVcon"),
      Value = c(s$rare, s$patchy, s$transitional, s$dominant, s$interior,
                sprintf("%.6f", s$fad_av), sprintf("%.6f", s$avcon)),
      Percent = c(sprintf("%.3f", s$percent$rare),
                  sprintf("%.3f", s$percent$patchy),
                  sprintf("%.3f", s$percent$transitional),
                  sprintf("%.3f", s$percent$dominant),
                  sprintf("%.3f", s$percent$interior), "", "")
    )
  }, striped = TRUE, bordered = TRUE)

  output$hist <- renderPlot({
    req(state$stats)
    s <- state$stats
    proportions <- if (s$foreground > 0) s$frequency[1:101] / s$foreground * 100 else rep(0, 101)
    graphics::barplot(
      proportions, col = palette_colors, border = NA,
      xlab = "FAD", ylab = "Frequency [%]",
      main = "Foreground pixel histogram",
      names.arg = ifelse((0:100) %% 20 == 0, 0:100, ""),
      cex.names = 0.8)
  })
}

shinyApp(ui, server)
