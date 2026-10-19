# ==============================================================================
# log_output(): record which code produced a saved data file
# Load it after the paths file, then call it right after each save:
#   exec(open(here("04_scripts/01_functions/log_output.py")).read())
#   panel.to_parquet(DATA_CLEAN / "panel.parquet")
#   log_output(DATA_CLEAN / "panel.parquet")
# It appends one row to _output_log.csv in the same folder, so the last row for a
# file says who wrote it, when, and from which commit. The git details come from
# part 4 of 00_setup_paths.py, which must have run first.
# ==============================================================================
import csv
from datetime import datetime
from pathlib import Path


def log_output(path):
    # 1. Fail early if 00_setup_paths.py has no part 4 (projects set up before October 2026)
    needed = ["user", "GIT_COMMIT", "CODE_ON_GITHUB", "OFFICIAL_RUN"]
    missing = [name for name in needed if name not in globals()]
    if missing:
        raise NameError(
            f"log_output() needs {', '.join(missing)} from part 4 of 04_scripts/00_setup_paths.py. "
            "See 01_references/00_guidelines/setup_paths_template.md."
        )

    # 2. One row per save; an empty commit means git was not found when the run started.
    #    TRUE/FALSE as text, so rows written from R, Python and Stata read the same.
    path = Path(path)
    row = {
        "file": path.name,
        "written": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "by": user,
        "commit": GIT_COMMIT or "",
        "code_on_github": "TRUE" if CODE_ON_GITHUB else "FALSE",
        "official": "TRUE" if OFFICIAL_RUN else "FALSE",
    }

    # 3. Append, writing the header only when the log is new
    log_file = path.parent / "_output_log.csv"
    new_log = not log_file.exists()
    with open(log_file, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row))
        if new_log:
            writer.writeheader()
        writer.writerow(row)
    return row
