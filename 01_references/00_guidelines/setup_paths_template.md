# The Central Configuration File Templates

**For Human Users:**
* **Why we use this:** Because our team uses different computers (Mac/Windows) and different usernames, absolute paths (like `C:/Users/Maria/...`) will break the code for everyone else. The setup file templates provided below dynamically detects who is running the script and sets the correct paths automatically.
* **How to use this:** 
  1. Copy the code block for your programming language (R, Python, or Stata).
  2. Save it as `00_setup_paths.[extension]` inside the `04_scripts/` folder.
  3. Add your computer's username and your specific local paths to the `if/else` block. 
  4. At the top of all your analysis scripts, you only need to run one line of code to "call" this file.

---
## Templates for the setup file
### R Setup (`00_setup_paths.R`)
```R
# ==============================================================================
# Central Path Configuration
# Run this script at the top of all analysis files to ensure cross-platform compatibility.
# ==============================================================================
library(here)

# 1. Detect User
user <- Sys.info()["user"]

# 2. Define Root Paths
if (user == "maria_p") {
  GITHUB_PATH <- "C:/Users/Maria/github/project_example" 
  GDRIVE_PATH <- "G:/Shared Drives/CD_3_Projects/Active Projects/project_example/03_data"
} else if (user == "juan_r") {
  GITHUB_PATH <- "/Users/juan/github/project_example" 
  GDRIVE_PATH <- "/Volumes/GoogleDrive/Shared Drives/CD_3_Projects/Active Projects/project_example/03_data"
} else {
  stop("User not recognized. Please add your paths to 04_scripts/00_setup_paths.R")
}

# 3. Build Standardized Sub-Paths
# This ensures Claude and human users always point to the exact same folders.
DATA_RAW   <- file.path(GDRIVE_PATH, "01_raw_data")
DATA_TEMP  <- file.path(GDRIVE_PATH, "02_temp_data")
DATA_CLEAN <- file.path(GDRIVE_PATH, "03_clean_data")
```

### Python Setup (00_setup_paths.py)
```Python
# ==============================================================================
# Central Path Configuration
# Run this script at the top of all analysis files to ensure cross-platform compatibility.
# ==============================================================================
import os
from pathlib import Path
import getpass

# 1. Detect User
user = getpass.getuser()

# 2. Define Root Paths
if user == "maria_p":
    GITHUB_PATH = Path("C:/Users/Maria/github/project_example")
    GDRIVE_PATH = Path("G:/Shared Drives/CD_3_Projects/Active Projects/project_example/03_data")
elif user == "juan_r":
    GITHUB_PATH = Path("/Users/juan/github/project_example")
    GDRIVE_PATH = Path("/Volumes/GoogleDrive/Shared Drives/CD_3_Projects/Active Projects/project_example/03_data")
else:
    raise ValueError("User not recognized. Please add your paths to 04_scripts/00_setup_paths.py")

# 3. Build Standardized Sub-Paths
DATA_RAW   = GDRIVE_PATH / "01_raw_data"
DATA_TEMP  = GDRIVE_PATH / "02_temp_data"
DATA_CLEAN = GDRIVE_PATH / "03_clean_data"
```

### Stata Setup (00_setup_paths.do)
```Stata
* ==============================================================================
* Central Path Configuration
* Run this script at the top of all analysis files to ensure cross-platform compatibility.
* ==============================================================================
clear all
set more off

* 1. Detect User
local user = c(username)

* 2. Define Root Paths
if "`user'" == "maria_p" {
    global GITHUB_PATH "C:/Users/Maria/github/project_example"
    global GDRIVE_PATH "G:/Shared Drives/CD_3_Projects/Active Projects/project_example/03_data"
} 
else if "`user'" == "juan_r" {
    global GITHUB_PATH "/Users/juan/github/project_example"
    global GDRIVE_PATH "/Volumes/GoogleDrive/Shared Drives/CD_3_Projects/Active Projects/project_example/03_data"
} 
else {
    display as error "User not recognized. Please add your paths to 04_scripts/00_setup_paths.do"
    exit 198
}

* 3. Build Standardized Sub-Paths
global DATA_RAW   "$GDRIVE_PATH/01_raw_data"
global DATA_TEMP  "$GDRIVE_PATH/02_temp_data"
global DATA_CLEAN "$GDRIVE_PATH/03_clean_data"
```
---
## How to Call the Setup File
At the absolute top of every new analysis script you write, you must include one line of code to execute the setup file. This ensures your script always knows where the data lives, regardless of where the script itself is saved.

### R
The `here` package searches upwards from your script's location until it finds a `.git` folder or `.Rproj` file, establishing the absolute "root" of your project. This prevents relative path errors.

While opening an `.Rproj` file sets your working directory to the project root, relying solely on this (e.g., using `source("04_scripts/00_setup_paths.R")`) is fragile. If you "Knit" an `.Rmd` file or click "Source" on a script located inside a subfolder, R temporarily changes the working directory to that subfolder, which will break your paths. 
The `here` package solves this by dynamically searching upwards to find the `.git` or `.Rproj` file, establishing an unbreakable absolute path to the root, regardless of how or where the script is run. (See [C-Ran](https://cran.r-project.org/web/packages/here/vignettes/here.html) for more information).

```R
# The 'here' package finds the project root automatically
source(here::here("04_scripts", "00_setup_paths.R"))
```

### Python
Python struggles to import files that start with numbers. The code below uses pyprojroot (a Python equivalent to R's here) to find the project root, reads the setup file as text, and executes it to load the path variables into your script's memory.
*Note: If you need to sequentially run mixed file types like .py, .ipynb, and .qmd, do not use this method. Instead, orchestrate them using a Makefile or a `00_master.py` script utilizing the `subprocess` and `papermill` libraries. See the section on 'How to run sequential files' below*
```Python
# The 'pyprojroot' package finds the project root automatically
from pyprojroot import here
exec(open(here("04_scripts/00_setup_paths.py")).read())
```

### Stata
Stata handles paths differently. Because it lacks a robust project-root locator, do NOT copy and paste the user-detection code into every single .do file. Instead, rely on Stata's global memory.
During Development: At the start of your Stata session, open and run 04_scripts/00_setup_paths.do ONCE. This loads all path variables into Stata's memory. You can then open and interactively run any sub-script (e.g., `02_clean.do`).

For Final Execution: Use a `00_master.do` file located at the project root to run everything sequentially.
---

## How to Run Sequential Files (Master Scripts)

A "Master Script" is a single file that executes all the other scripts in your project in the exact order required to go from raw data to final report. 

**Why is this a best practice?**
According to the [World Bank DIME Analytics Wiki on Master Scripts](https://dimewiki.worldbank.org/Master_Do-files) (see also [DIME Publishing resource](https://dimewiki.worldbank.org/Publishing_Data)) and Gentzkow & Shapiro's [Code and Data for the Social Sciences](https://web.stanford.edu/~gentzkow/research/CodeAndData.pdf), a master script is the ultimate test of reproducibility. If a new team member joins, they should be able to press "run" on one file, walk away, and have the entire project rebuild itself. It removes human error, documents the exact pipeline architecture, and ensures no hidden dependencies are forgotten.

**The Two Approaches for Pathing Execution**
When a master script calls a sub-script, it needs to know exactly where that sub-script lives. There are two standard approaches to achieve this:

The Root Locator Approach (`here::here()` or `pyprojroot`): This dynamically searches your computer for the project's root folder (using the .git folder) every time it runs. It is incredibly robust for R and Python because it requires no prior variables to be loaded.

The Global Variable Approach (`GITHUB_PATH`): If your master script begins by sourcing the 00_setup_paths configuration file, the `$GITHUB_PATH` global variable is loaded into memory. You can then use this variable to build paths to your sub-scripts (e.g., `file.path(GITHUB_PATH, "04_scripts", "01_clean.R")`). This is the mandatory approach for Stata, and perfectly acceptable for R/Python if the team members prefer explicit path construction.

Below are the standard approaches for orchestrating files, ranging from nested scripts to cross-format pipelines, demonstrating both pathing styles.

### Case 1: Running a script inside another sub-script
**Is this good practice?** Generally, no. Sourcing a long data-cleaning script inside an analysis script hides dependencies and makes debugging a nightmare. 
**When it is advisable:** You should only source files within files when loading **Functions** or **Configurations** (like `00_setup_paths`), or if a single step in the pipeline is so massive it needs to be modularized (e.g., `01_clean_baseline.R` calling `01a_clean_demographics.R` and `01b_clean_geography.R`).
* **R:** 
  * Root locator: `source(here::here("04_scripts", "01a_clean_demographics.R"))`
  * Global variable: `source(file.path(GITHUB_PATH, "04_scripts", "01a_clean_demographics.R"))`
* **Python:** 
  * Root locator: `import subprocess; from pyprojroot import here; subprocess.run(["python", here("04_scripts/01a_clean_demographics.py")])`
  * Global variable: `import subprocess; subprocess.run(["python", GITHUB_PATH / "04_scripts" / "01a_clean_demographics.py"])`
* **Stata:** `do "$GITHUB_PATH/04_scripts/01a_clean_demographics.do"`

### Case 2: The Standard Sequential Pipeline
This is the standard approach for a `00_master.R/py/do` file. It sequentially calls the numbered scripts.
**Handling Nested Master Files:** In large projects, subfolders often have their own master files. Your top-level `00_master` can simply call the sub-masters (e.g., calling the master cleaner, then the master analyzer).

* **R (Using `source()`):**
  ```R
  # 1. Setup paths (creates GITHUB_PATH and GDRIVE_PATH)
  source(here::here("04_scripts", "00_setup_paths.R"))

  # 2. Run nested master cleaning file (Using the Global Variable approach)
  source(file.path(GITHUB_PATH, "04_scripts", "01_data_cleaning", "00_master_clean.R"))

  # 3. Run sequential analysis (Using the Root Locator approach)
  source(here::here("04_scripts", "02_analysis", "01_summary_stats.R"))
  source(here::here("04_scripts", "02_analysis", "02_regressions.R"))
  ```

  *Note*: At the very beginning of each script you rely on the package `here` to create the different source paths (e.g. `GITHUB_PATH`). This requires than you have installed the package `here` or your scripts use `pacman::p_load(here)` to install it automatically.
  * **Why we accept this dependency:** The alternative to using `here` is relying on relative paths (e.g., `source("../../00_setup_paths.R")`) or having the right working directory. Relative paths are incredibly fragile because they break if a script is moved up or down a folder. The here package is universally considered the lesser of two evils. It is a tiny, lightweight package maintained by the core RStudio (Posit) team, so the risk of it breaking or becoming obsolete is virtually zero.

* **Python (Using subprocess):**
  (Note on Numbered Folders: Python normally prohibits importing modules that start with numbers. By using `subprocess`, we bypass Python's internal import rules entirely. We are simply telling the operating system's terminal to run the file. Therefore, numbered folders and files are perfectly safe and highly encouraged for organization).

  ```Python
  import subprocess
  from pyprojroot import here

  # 1. Setup paths (creates GITHUB_PATH and GDRIVE_PATH)
  exec(open(here("04_scripts/00_setup_paths.py")).read())

  # 2. Run nested master cleaning file (Using the Global Variable approach)
  subprocess.run(["python", GITHUB_PATH / "04_scripts/01_data_cleaning/00_master_clean.py"], check=True)

  # 3. Run sequential analysis (Using the Root Locator approach)
  subprocess.run(["python", here("04_scripts/02_analysis/01_summary_stats.py")], check=True)


  import subprocess
  from pyprojroot import here

  # Execute scripts using the terminal via subprocess
  subprocess.run(["python", here("04_scripts/01_data_cleaning/00_master_clean.py")], check=True)
  subprocess.run(["python", here("04_scripts/02_analysis/01_summary_stats.py")], check=True)
  ```
  * Note on `exec` vs `subprocess`: Current Memory vs. Isolated Execution
    * Step 1 uses `exec(...)` because we need to INJECT memory.: The `00_setup_paths.py` file does not do anything; it simply defines variables like `GITHUB_PATH` and `GDRIVE_PATH`.
    When you use `exec(open().read())`, you are telling Python to open the setup file, read the text, and execute it inside the master script's own brain. This allows the master script to suddenly know what `GITHUB_PATH` is, so it can use that variable in the lines of code that follow.
    (If you used `subprocess.run(["python", "00_setup_paths.py"])`, Python would open a brand new, invisible terminal, define the variables there, and immediately close it. Your master script would remain completely blind to the paths!)

    * Step 2 uses `subprocess.run(...)` because we want ISOLATED execution.
    When it is time to run the heavy data-cleaning script (`01_master_clean.py`), we do not want to inject it into the master script's brain. If the cleaning script loads 10GB of data into memory, and then the analysis script loads another 10GB, your master script will crash your computer.
    When you use `subprocess.run()`, you are telling the computer: "Open a completely separate, isolated terminal. Run the cleaning script over there. When it finishes and saves the .csv file, close that terminal and free up all the memory. Then, come back and tell the master script to proceed to the next step."


* **Stata (Using do):**

  ```Stata
  * Run setup to load globals
  do "$GITHUB_PATH/04_scripts/00_setup_paths.do"

  * Run nested masters and sequential files
  do "$GITHUB_PATH/04_scripts/01_data_cleaning/00_master_clean.do"
  do "$GITHUB_PATH/04_scripts/02_analysis/01_summary_stats.do"
  ```

### Case 3: Mixed File Types (.Rmd, .ipynb, .qmd)
Master files often need to run standard scripts to clean data, and then render notebooks or Markdown documents to produce the final reports.

* **R (Mixing .R and .Rmd):** Use the rmarkdown or quarto packages.
  ```R
  # Run the backend cleaning script
  source(here::here("04_scripts", "01_clean.R"))

  # Render the frontend report to Word/HTML
  rmarkdown::render(
    input = here::here("04_scripts", "03_report.Rmd"),
    output_dir = here::here("06_outputs", "03_deliverables")
  )
  ```

* **Python (Mixing .py, .ipynb, and .qmd):** Use subprocess to trigger Quarto and Papermill (the standard for executing Jupyter notebooks).

```Python
  import subprocess
  from pyprojroot import here

  # 1. Run a standard .py file
  subprocess.run(["python", here("04_scripts/01_clean.py")], check=True)

  # 2. Execute a Jupyter Notebook using Papermill (requires: pip install papermill)
  subprocess.run(["papermill", here("04_scripts/02_eda.ipynb"), here("05_workspace/02_exploratory/02_eda_executed.ipynb")], check=True)

  # 3. Render a Quarto document
  subprocess.run(["quarto", "render", here("04_scripts/03_report.qmd")], check=True)
```

---

## Appendix 1: Best Practices for Notebooks (.Rmd, .ipynb, .qmd) in a Team Lifecycle
Computational notebooks (like RMarkdown `.Rmd`, Jupyter `.ipynb`, or Quarto `.qmd`) are incredibly popular because they allow data scientists to weave narrative text, executable code, and visualizations into a single dynamic document.

However, if misused in a collaborative environment, giant notebooks become a liability. Merge conflicts in `.ipynb` files are notoriously difficult to resolve, and running a 2,000-line notebook can consume massive amounts of memory.

To solve this, leading practitioners have established formal lifecycles for notebook development. Two essential readings on this topic are Emily Riederer's **[RMarkdown Driven Development (RmdDD)](https://emilyriederer.netlify.app/post/rmarkdown-driven-development/)** and the **[Ten Simple Rules for Reproducible Research in Jupyter Notebooks](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1007007)**.

Here is how you should structure the use of pure scripts (.R / .py) versus notebooks across the project lifecycle.

**1. Project Start (Exploration Phase): The Notebook is King**
At the very beginning of a project, you don't know what the data looks like yet. You are writing quick summaries, plotting histograms, and writing notes to yourself. During this phase, you should absolutely use notebooks. They act as your digital lab notebook. It is entirely acceptable for these files to be messy and exploratory, as they document your initial interactions with the data.

**2. The Transition (Refinement Phase): The "Extraction Rule"**
As the project matures, you will inevitably write chunks of code in your notebook that do heavy lifting—like standardizing 50 variable names, merging datasets, or calculating a complex index. This is the critical inflection point. You must extract this heavy computational logic out of the notebook and place it into a standalone script.

When doing this, you have two structural options for preserving your original notebook without cluttering your pipeline:

* Option A: The Subfolder Separation: You create a `notebooks/` subfolder inside `04_scripts/` (or inside subfolders) to hold your exploratory files, keeping your .R/.py files at the root level. While this separates formats cleanly, it often breaks the chronological numbering (e.g., you lose the visual link between step 1 and step 3).

* Option B: The "Paired Notebook" Pattern (Recommended): You keep the notebook right next to the new script in `04_scripts/` and give them identical names (e.g., `02_clean.Rmd` sitting next to `02_clean.R,` or `03_model.ipynb` next to `03_model.py`). The pure script acts as the automated data-processing engine for the master file, while the paired notebook remains untouched as your rich, human-readable documentation of why the code was written that way. Open-source tools like [Jupytext](https://jupytext.readthedocs.io/en/latest/) (for Python) or `knitr::purl()` (for R) can even automate this syncing process.

**3. Separation of Concerns: The "Backend" and the "Frontend"**
By the middle of the project, your architecture should mimic professional software engineering: a strict separation between the "backend" and the "frontend." 
* **The Backend (`.R` files):** These files do the heavy lifting. They pull from the Google Drive `raw_data/` folder, run the merges and regressions, and output highly compressed, clean data files (e.g., `.rds` or `.parquet`) into the `clean_data/` folder.
* **The Frontend (`.Rmd`, `.ipynb`, `qmd`):** These files act as the presentation layer. A production-ready notebook should perform almost zero data manipulation. The very first chunk should load the pre-cleaned data, and the remaining chunks should strictly generate charts, tables, and narrative text. 

**4. Team Collaboration (Conflict Prevention)**
When you separate the backend and frontend, teamwork becomes seamless. If your teammate needs to fix a bug in the poverty index calculation, they open `01_clean.R`. If you need to fix a typo in the client report and change the color of a graph, you open `03_report.Rmd`. Because you are working in different files, you will never trigger a Git merge conflict. Furthermore, your master execution script will run much faster, as the pure scripts execute silently in the background without the overhead of rendering HTML or Markdown text.

**5. Final Delivery: Parameterized Rendering**
At the end of the project, your master script acts as the conductor. You don't open the notebook and click "Run All" or "Knit" manually. Instead, your `00_master` script uses tools like `rmarkdown::render()`, quarto `render`, or `papermill to execute the report programmatically. This allows for powerful automation: if you need to generate 15 identical reports for 15 different regions, you can write a loop in your master script that passes different region parameters into a single template notebook, generating all 15 reports automatically.