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

output_file <- file.path(base_dir, "NHT2602_data_all_by_colnum.csv")

# 1-based column ranges from the source CSV layouts.
common_range <- c(1, 3637)
main_ranges <- list(
  A = c(3638, 9971),
  B = c(3638, 7182),
  C = c(3638, 9168),
  D = c(3638, 7256)
)
v_ranges <- list(
  A = c(9972, 10233),
  B = c(7183, 7444),
  C = c(9169, 9430),
  D = c(7257, 7518)
)
a_tail_range <- c(10234, 10362)

seq_range <- function(x) {
  x[1]:x[2]
}

range_length <- function(x) {
  x[2] - x[1] + 1
}

read_header <- function(path) {
  names(read.csv(path, nrows = 0, check.names = FALSE, fileEncoding = "UTF-8-BOM"))
}

headers <- lapply(files, read_header)

output_header <- headers$A[seq_range(common_range)]
output_header[1] <- "SAMPLENUMBER"

for (category in c("A", "B", "C", "D")) {
  output_header <- c(output_header, headers[[category]][seq_range(main_ranges[[category]])])
}

output_header <- c(
  output_header,
  headers$A[seq_range(v_ranges$A)],
  headers$A[seq_range(a_tail_range)]
)

main_offsets <- list()
cursor <- common_range[2] + 1
for (category in c("A", "B", "C", "D")) {
  main_offsets[[category]] <- cursor
  cursor <- cursor + range_length(main_ranges[[category]])
}

v_offset <- cursor
cursor <- cursor + range_length(v_ranges$A)
a_tail_offset <- cursor

merged <- setNames(data.frame(matrix(ncol = length(output_header), nrow = 0)), output_header)

for (category in names(files)) {
  data <- read.csv(files[[category]], check.names = FALSE, colClasses = "character", fileEncoding = "UTF-8-BOM")

  src_indexes <- c(
    seq_range(common_range),
    seq_range(main_ranges[[category]]),
    seq_range(v_ranges[[category]])
  )

  dst_indexes <- c(
    seq_len(common_range[2]),
    main_offsets[[category]]:(main_offsets[[category]] + range_length(main_ranges[[category]]) - 1),
    v_offset:(v_offset + range_length(v_ranges[[category]]) - 1)
  )

  if (category == "A") {
    src_indexes <- c(src_indexes, seq_range(a_tail_range))
    dst_indexes <- c(dst_indexes, a_tail_offset:(a_tail_offset + range_length(a_tail_range) - 1))
  }

  out <- setNames(data.frame(matrix("", nrow = nrow(data), ncol = length(output_header))), output_header)

  for (i in seq_along(src_indexes)) {
    out[[dst_indexes[i]]] <- data[[src_indexes[i]]]
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
