# [Project Name: E.g., Endline Assessment for Project X]

---
    ⚠️ NEW TO GITHUB? If you are a team member or consultant unfamiliar with Git version control, please read @01_references/00_guidelines/git_team_workflow.md before making any changes to this repository.

## 1. Project Overview
* **Principal Investigators / Lead:** [Names/Company]
* **Project Status:** [e.g., Midline Data Collection, Baseline Cleaning, Final Analysis]
* **Objectives:** [Brief summary of the primary goal of this project phase]
* **Research Questions:**
    - 1. [RQ 1]
    - 2. [RQ 2]
* **Methodology & Estimation:** [e.g., Staggered Difference-in-Differences using Callaway & Sant'Anna (2021). Standard errors clustered at the village level. See `@01_references/02_literature/` for specific methodological papers.]
* **Expected Outputs:** [E.g., Inception Report, Midline Clean Dataset, Final Evaluation Deck, Interactive Dashboard]

---

## 2. Data Access & Security
* **Data Security Note:** Raw, personally identifiable (PII), and intermediate datasets are **strictly ignored** in this Git repository to protect beneficiary privacy and maintain repo hygiene.
* **Data Location:** All data (KoboToolbox exports, clean data) is housed on the secure organizational Google Drive at: `[Insert Link to GDrive Folder]`.
* **Pathing Note:** Scripts in this repository are configured to read data directly from the Google Drive synced folder on the local machine (e.g., `~/Google Drive/Shared drives/.../03_data/`). You do not need to move data into this repository manually.
* **Data Sources in Use:**
    [e.g.,
    1. `household_baseline_2025.csv`: Primary Kobo survey data.
    2. `admin_school_enrollment.dta`: Ministry of Education administrative panel.
    3. `spatial_borders.shp`: Regional shapefiles for geo-merging.
    ]

---
## 3. Setup & Dependencies
Before running any code, you must configure your local paths and install the necessary software packages.

**A. Pathing Setup**
1. The markdown file `01_references/00_guidelines/setup_paths_template.md` contains the comprehensive guide and code snippets for different programs (R/Python/Stata).
2. Copy the desired code to a new file `00_setup_paths.[R/py/do]` and store it in `04_scripts/`.
3. Add your local OS username and the absolute paths to your Google Drive (`GDRIVE_PATH`) and this local code repository (`GITHUB_PATH`).
4. This file must be called at the very top of all execution scripts to dynamically set the paths for the rest of the code.

**B. Environment & Packages**
* **Primary Language:** [e.g., R Version 4.3.0 or Python 3.11]
* **Packages:** [e.g., include R packages or reference the user to requirements.txt]
* **Package management:**
    * **Python Users:** Create a virtual environment (`python -m venv venv`), activate it, and install the project dependencies by running `pip install -r requirements.txt` in your terminal.
    * **R Users:** Ensure you have the `pacman` package installed. The scripts will automatically install and load all other necessary packages via `pacman::p_load()` at execution. (Key packages include: [e.g., tidyverse, fixest, modelsummary]).
* **Random Seed:** Set to `[Insert Seed Number, e.g., 20260403]`. All execution scripts must set this seed at the top of the file to ensure exact reproducibility of simulations, bootstrapping, or clustering.

---
## 4. Replication Pipeline
The core analytical pipeline is executed sequentially from the root of the `04_scripts/` directory.

**Execution Conventions:**
* **Master Scripts:** This project uses Master Scripts to orchestrate the execution of all sub-scripts. Please refer to the "How to Run Sequential Files" section in `01_references/00_guidelines/setup_paths_template.md` for exact syntax on running sub-scripts and notebooks across R, Python, and Stata.
* **Numbering:** All main execution scripts and subfolders are sequentially numbered (e.g., `01_cleaning/`, `02_analysis.R`) to enforce a strict chronological flow. Both pure scripts (`.R`, `.py`) and analysis notebooks (`.Rmd`, `.ipynb`) live together here to maintain this order.
* **Living Document:** *Note: As the project advances, the AI Agent or Team members must continuously update the pipeline list below to reflect the true execution order.*

**Current Pipeline:**
1. `04_scripts/00_master.[R/do/py]` - [Executes the entire project pipeline from start to finish]
2. `04_scripts/01_[insert_name].[R/do/py]` - [Brief description of what this sub-script does]
3. `04_scripts/02_[insert_name].[R/do/py]` - [Brief description of what this sub-script does]

---

## 5. Repository Structure
```
[project-name]/
├── CLAUDE.md                     # Core rules and instructions for Claude Code CLI
├── README.md                     # Human-readable project context and methodology
├── .gitignore                    # Prevents Git from tracking local Google Drive data
├── .githooks/pre-commit          # Asks before large data files are committed (activate: git config core.hooksPath .githooks)
├── .claude/                      # skills/ · hooks/ · settings.json (Claude Code permissions and guardrails)
├── 01_references/
│   ├── 00_guidelines/            # Company guidelines (git workflow, path setup)
│   ├── 01_project_documentation/ # SoWs, IRB approvals, Project documentation, MoUs, Data Sharing Agreements
│   ├── 02_literature/            # Academic papers and methodology manuals
│   └── 03_past_examples/         # Historical reports, old tools, and reference materials
├── 02_survey_tools/
│   ├── 01_quant_tools/           # Kobo XLSForms, CSVs of quantitative tools
│   └── 02_qual_tools/            # KII guides, FGD protocols
│   (no 03_data/ here — data lives only on Google Drive: 01_raw_data · 02_temp_data · 03_clean_data)
├── 04_scripts/                   # Main chronologically numbered execution scripts live here
│   ├── 00_resources/             # Code snippets from past projects or general helpful syntax
│   ├── 01_functions/             # User-created functions for complex/repetitive workflows used across scripts
│   └── 99_replication/           # Cross-language translation scripts (e.g. Stata to R) to test robustness
├── 05_outputs/                   # Raw, script-generated artifacts
│   ├── 01_figures/               # e.g., /01_figures/02_analysis/ (maps, charts)
│   └── 02_tables/                # e.g., /02_tables/02_analysis/ (raw regression outputs)
├── 06_workspace/                 # Internal drafting and unstructured work
│   ├── 01_notes/                 # Scratchpads, meeting notes
│   ├── 02_exploratory/           # Quick/dirty EDA, internal sanity-check slides
│   ├── 03_document_review/       # Output folder for the AI doc-review skill
│   └── 04_report_drafts/         # causal-report sources (body .qmd + report_spec.yaml)
├── 07_deliverables/              # Formal, compiled, human-facing products
│   ├── 00_templates/             # Slide/Report templates
│   ├── 01_decks/                 # Polished stakeholder presentations
│   └── 02_output_documents/      # Formal Inception, Midline, Final reports
├── 08_ai_management/
│   ├── 01_progress_logs/         # Session logs (YYYY-MM-DD), PENDING.md queue, WORKSTREAMS.md topic board
│   ├── 02_quality_reports/       # decision_log.md and AI-generated code reviews / audits
│   ├── 03_system_templates/      # Formatting blueprints for AI generation (README, log, decision, learning, workstream, qmd)
│   └── 04_knowledge_base/        # learnings.md, skills_backlog.md, methodology_*.md (see _examples/), transcripts/
└── 09_legacy_vault/              # [READ-ONLY] Unorganized legacy code and data for AI migration
```

**Understanding the Directory Structure**
* **Data Separation:** To ensure reproducibility and security, data is never tracked. It lives only on Google Drive (`GDRIVE_PATH/01_raw_data`, `02_temp_data`, `03_clean_data`), and scripts reach it through the `DATA_RAW` / `DATA_TEMP` / `DATA_CLEAN` variables set in `04_scripts/00_setup_paths`. A pre-commit hook asks for confirmation before any large data file is committed (see `.githooks/pre-commit`).
* **Script Modularity:** The main pipeline runs at the root of `04_scripts/`. Any custom algorithms or repetitive tasks (like formatting specific tables) are written once in `04_scripts/01_functions/` and sourced by the main scripts. `00_resources/` is purely for reference (borrowed code from old projects).
* **Output Organization:** As you create and run individual scripts you might want to store figures and tables. All script-generated figures/tables go in `05_outputs/` (split into `01_figures` and `02_tables`). To improve organization, create a subfolder for each script/folder inside `04_scripts`.
* **Deliverables:** Final, human-facing products (formal slide decks, Word/PDF reports for clients) belong strictly in `07_deliverables/`.
* **Robustness & Replication:** `04_scripts/99_replication/` acts as a sandbox. Because we may utilize AI assistance, this folder is used to recreate specific analytical pipelines in a different programming language to ensure results are robust and free of language-specific artifacts or AI hallucinations.
* **Migration & Refactoring:** `09_legacy_vault/` is a strictly read-only directory containing old, unorganized project files. It is used as a "ground truth" reference for the AI to read from when migrating and refactoring code into the new, standardized `04_scripts/` pipeline. Scripts in this folder should never be executed or modified.

---
## 6. How We Work — AI Assistance & Project Tracking
*Note: This project utilizes the Claude Code CLI to assist with code generation, cross-language replication, automated reporting, and documentation. The conventions below are for **both** human team members and the AI agent.*

* **Core Instructions:** Agent rules, data-pathing guardrails, and workflow constraints are strictly defined in `CLAUDE.md`.

### The four tracking layers
Project progress is tracked through four complementary files. They answer different questions — keep them in sync, don't collapse one into another:

| Layer | File | Organized by | Answers |
|-------|------|--------------|---------|
| **Chronicle** | `08_ai_management/01_progress_logs/YYYY-MM-DD_session.md` | date | *What did we do that day?* — daily milestones, dead ends, next steps. Append-only. |
| **Queue** | `08_ai_management/01_progress_logs/PENDING.md` | flat open-items list | *What is still open?* — cross-session to-dos, recently done, cancelled. |
| **Ledger** | `08_ai_management/02_quality_reports/decision_log.md` | date | *Why did we choose X, and when?* — methodological / econometric / data-sourcing decisions and rejected alternatives. |
| **Board** | `08_ai_management/01_progress_logs/WORKSTREAMS.md` | topic / workstream | *Where do we stand on each topic?* — a status board with one section per workstream (Lit Review, Survey Design, Sampling & Weights, Cleaning, Construction, Analysis, Reporting, Dissemination…), each linking out to the chronicle, ledger, and queue. |

**How to read them together:** the session logs are *what happened*; the decision log is *why*; PENDING is *what's queued*; WORKSTREAMS is *where each topic stands now*. If you want the history of a topic, start at its `WORKSTREAMS.md` section and follow the pointers into the dated logs and decision entries.

### Knowledge capture
* **Learnings (`04_knowledge_base/learnings.md`):** reusable analytical / coding lessons, tagged with a standard taxonomy.
* **Deep methodology references (`04_knowledge_base/methodology_*.md`):** full course-note-style write-ups for non-trivial methods (math, derivations, procedure). See `04_knowledge_base/_examples/` for the expected depth.
* **Skills backlog (`04_knowledge_base/skills_backlog.md`):** candidate repetitive tasks to automate into Claude Code skills.
* **AI skills (`.claude/skills/`):** reusable slash-command pipelines (e.g. `/doc-to-md`, `/doc-review`). See `CLAUDE.md` §7 for the versioning discipline.
