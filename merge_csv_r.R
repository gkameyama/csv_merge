args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)

if (length(file_arg) > 0) {
  script_path <- sub("^--file=", "", file_arg[1])
  base_dir <- dirname(normalizePath(script_path))
} else {
  base_dir <- getwd()
}

files <- list(
  A = file.path(base_dir, "NHT2602_A0.csv"),
  B = file.path(base_dir, "NHT2602_B0.csv"),
  C = file.path(base_dir, "NHT2602_C0.csv"),
  D = file.path(base_dir, "NHT2602_D0.csv")
)

output_file <- file.path(base_dir, "NHT2602_data_all.csv")

read_header <- function(path) {
  names(read.csv(path, nrows = 0, check.names = FALSE, fileEncoding = "UTF-8-BOM"))
}

column_range <- function(header, start, end) {
  start_index <- match(start, header)
  end_index <- match(end, header)

  if (is.na(start_index) || is.na(end_index)) {
    stop(sprintf("Column range not found: %s -> %s", start, end))
  }
  if (start_index > end_index) {
    stop(sprintf("Invalid range: %s appears after %s", start, end))
  }

  header[start_index:end_index]
}

build_layout <- function(headers) {
  common <- column_range(headers$A, "l_userid", "SC22.22")
  common[1] <- "SAMPLENUMBER"

  c(
    common,
    column_range(headers$A, "A1.1", "E2.15"),
    column_range(headers$B, "AA1.1", "F4.7"),
    column_range(headers$C, "AAA1.101", "G5.10"),
    column_range(headers$D, "AAAA0", "H5.5"),
    column_range(headers$A, "V1_1", "V11.42"),
    column_range(headers$A, "P1", "R4_14")
  )
}

source_columns <- function(category, headers) {
  header <- headers[[category]]
  columns <- column_range(header, "l_userid", "SC22.22")

  if (category == "A") {
    columns <- c(columns, column_range(header, "A1.1", "E2.15"))
  } else if (category == "B") {
    columns <- c(columns, column_range(header, "AA1.1", "F4.7"))
  } else if (category == "C") {
    columns <- c(columns, column_range(header, "AAA1.101", "G5.10"))
  } else if (category == "D") {
    columns <- c(columns, column_range(header, "AAAA0", "H5.5"))
  } else {
    stop(sprintf("Unknown category: %s", category))
  }

  columns <- c(columns, column_range(header, "V1_1", "V11.42"))

  if (category == "A") {
    columns <- c(columns, column_range(header, "P1", "R4_14"))
  }

  columns
}

headers <- lapply(files, read_header)
output_header <- build_layout(headers)
merged <- setNames(data.frame(matrix(ncol = length(output_header), nrow = 0)), output_header)

for (category in names(files)) {
  data <- read.csv(files[[category]], check.names = FALSE, colClasses = "character", fileEncoding = "UTF-8-BOM")
  columns <- source_columns(category, headers)

  out <- setNames(data.frame(matrix("", nrow = nrow(data), ncol = length(output_header))), output_header)
  output_columns <- columns
  output_columns[output_columns == "l_userid"] <- "SAMPLENUMBER"

  for (i in seq_along(columns)) {
    out[[output_columns[i]]] <- data[[columns[i]]]
  }

  merged <- rbind(merged, out)
}

samplenumber_numeric <- suppressWarnings(as.numeric(merged[["SAMPLENUMBER"]]))
samplenumber_text <- merged[["SAMPLENUMBER"]]
samplenumber_numeric_order <- samplenumber_numeric
samplenumber_numeric_order[is.na(samplenumber_numeric_order)] <- Inf
merged <- merged[order(is.na(samplenumber_numeric), samplenumber_numeric_order, samplenumber_text), ]

write.table(
  merged,
  output_file,
  sep = ",",
  row.names = FALSE,
  col.names = TRUE,
  na = "",
  quote = FALSE,
  fileEncoding = "UTF-8"
)
cat(sprintf("created: %s\n", output_file))
