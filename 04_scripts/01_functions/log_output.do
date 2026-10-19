* ==============================================================================
* log_output: record which code produced a saved data file
* Load it once after the paths file, then call it right after each save:
*   do "$GITHUB_PATH/04_scripts/01_functions/log_output.do"
*   save "$DATA_CLEAN/panel.dta", replace
*   log_output "$DATA_CLEAN/panel.dta"
* It appends one row to _output_log.csv in the same folder, so the last row for a
* file says who wrote it, when, and from which commit. The git details come from
* part 4 of 00_setup_paths.do, which must have run first.
* ==============================================================================

capture program drop log_output
program define log_output
    args path

    * 1. Fail early if 00_setup_paths.do has no part 4 (projects set up before October 2026)
    if "$OFFICIAL_RUN" == "" | "$CD_USER" == "" {
        display as error "log_output needs part 4 of 04_scripts/00_setup_paths.do. See 01_references/00_guidelines/setup_paths_template.md."
        exit 198
    }

    * 2. Split the path into folder and file name (either slash, for Mac and Windows)
    local file   = ustrregexra(`"`path'"', "^.*[/\\]", "")
    local folder = ustrregexra(`"`path'"', "[/\\][^/\\]*$", "")
    local log_file "`folder'/_output_log.csv"
    local written = string(date(c(current_date), "DMY"), "%tdCCYY-NN-DD") + " " + c(current_time)
    * TRUE/FALSE as text, so rows written from R, Python and Stata read the same
    local on_github = cond($CODE_ON_GITHUB, "TRUE", "FALSE")
    local official  = cond($OFFICIAL_RUN, "TRUE", "FALSE")

    * 3. Append, writing the header only when the log is new
    tempname fh
    capture confirm file "`log_file'"
    local new_log = (_rc != 0)
    file open `fh' using "`log_file'", write text append
    if `new_log' file write `fh' "file,written,by,commit,code_on_github,official" _n
    file write `fh' `""`file'","`written'","$CD_USER","$GIT_COMMIT",`on_github',`official'"' _n
    file close `fh'
end
