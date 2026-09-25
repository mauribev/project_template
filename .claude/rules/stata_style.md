---
paths:
  - "**/*.do"
  - "**/*.ado"
---

# Stata conventions

- **Setup:** Stata's working directory is the repo root (open the project's `.stpr` file or `cd` there). The first command is `do "04_scripts/00_setup_paths.do"` — a relative path, because `$GITHUB_PATH` does not exist until that file has run. After that, build every path from the globals (`$GITHUB_PATH`, `$DATA_RAW`, `$DATA_TEMP`, `$DATA_CLEAN`).
- **Execution:** run do-files in batch mode (`stata -b do file.do`) and check the `.log` it writes; `00_master.do` in `04_scripts/` calls the others with `do "$GITHUB_PATH/04_scripts/..."`.
- Set `version` and `set seed` (seed from the README) at the top of any do-file that uses randomness.
