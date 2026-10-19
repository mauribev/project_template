# ==============================================================================
# log_output(): record which code produced a saved data file
# Call it right after each save:
#   saveRDS(panel, file.path(DATA_CLEAN, "panel.rds"))
#   log_output(file.path(DATA_CLEAN, "panel.rds"))
# It appends one row to _output_log.csv in the same folder, so the last row for a
# file says who wrote it, when, and from which commit. The git details come from
# part 4 of 00_setup_paths.R, which must have run first.
# ==============================================================================

log_output <- function(path) {
  # 1. Fail early if 00_setup_paths.R has no part 4 (projects set up before October 2026)
  needed  <- c("user", "GIT_COMMIT", "CODE_ON_GITHUB", "OFFICIAL_RUN")
  missing <- needed[!vapply(needed, exists, logical(1), envir = globalenv())]
  if (length(missing) > 0) {
    stop("log_output() needs ", paste(missing, collapse = ", "),
         " from part 4 of 04_scripts/00_setup_paths.R. ",
         "See 01_references/00_guidelines/setup_paths_template.md.")
  }

  # 2. One row per save; NA commit means git was not found when the run started
  row <- data.frame(
    file           = basename(path),
    written        = format(Sys.time(), "%Y-%m-%d %H:%M:%S"),
    by             = unname(user),
    commit         = if (length(GIT_COMMIT) == 1) GIT_COMMIT else NA_character_,
    code_on_github = CODE_ON_GITHUB,
    official       = OFFICIAL_RUN
  )

  # 3. Append, writing the header only when the log is new
  log_file <- file.path(dirname(path), "_output_log.csv")
  new_log  <- !file.exists(log_file)
  write.table(row, log_file, sep = ",", row.names = FALSE,
              col.names = new_log, append = !new_log, qmethod = "double")
  invisible(row)
}
