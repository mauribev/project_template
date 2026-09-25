---
paths:
  - "**/*.R"
  - "**/*.Rmd"
  - "**/*.qmd"
---

# R conventions

- **Order at the top of every script:** 1) `source(here::here("04_scripts", "00_setup_paths.R"))`, 2) one grouped `pacman::p_load(...)` call (installs anything missing, then loads), 3) `set.seed()` with the seed recorded in the README, if the script uses randomness.
- **Data manipulation:** `data.table` by default (memory efficiency on survey-sized data). Use `dplyr` / base R where they fit better — notably spatial data with `sf`.
- **Paths:** `here::here()` for files inside the repository; the `DATA_*` variables from the paths file for anything on Google Drive. Never `setwd()`, never `source("../...")`.
- **Quarto / R Markdown:** the first chunk sources the paths file. A production notebook loads pre-cleaned data and only presents it (tables, figures, text); heavy logic belongs in the paired `.R` script. Diagnostic reports follow `08_ai_management/03_system_templates/qmd_template.qmd` (fixed intro → dynamic chunk → optional AI-commentary callout).
