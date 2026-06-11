# Claude Code CLI: Project Instructions

> **Template note (delete once the project is configured):** This is the generic, project-agnostic instruction file shipped with the Causal Design project template. Keep all the rules below as-is — they encode the standing workflow. Only edit them if a project genuinely needs a different convention, and record that change in the `decision_log.md`. For setup steps and the file inventory, see the scaffold's own `README.md` (replaced by the project README during setup — copy it from `08_ai_management/03_system_templates/README_template.md`).

## 1. Project Context
You are assisting an economist with a data science project (e.g., midline assessment, baseline cleaning, impact evaluation).
* **Primary Objective:** Write reproducible, highly structured analytical pipelines.
* **Full Context:** Always refer to `@README.md` for project background, methodology, and folder structure.

## 2. Strict Data & Pathing Rules
* **The "Split-Brain" Workflow:** Code lives in this Git repository. Data lives securely on Google Drive, unless otherwise directly specified by the user.
* **Data Retrieval & The Shielded Paths File:** Scripts should read/write directly to the local Google Drive mount point. Never hardcode absolute paths; rely on a central configuration file (e.g., `04_scripts/00_setup_paths.[R/do/py]`) that defines the paths (e.g., `GITHUB_PATH`,`DATA_RAW`) variable dynamically.
  * **ABSOLUTE RULE:** You are strictly forbidden from modifying the `00_setup_paths` file. If you detect that a path needs to be updated or added, you must explicitly instruct the human user to make the change. You cannot do it yourself.
  * **Mandatory Sourcing:** You MUST source this configuration file at the absolute top of EVERY single analysis script you create or modify. This ensures standalone execution.
    * *Example (R):* `source(here::here("04_scripts", "00_setup_paths.R"))`
    * *For Python:* `from pyprojroot import here; exec(open(here("04_scripts/00_setup_paths.py")).read())`
    * *Example (Stata):* `do "$GITHUB_PATH/04_scripts/00_setup_paths.do"`
  * **Template Reference:** If you need to understand the pathing logic, you can read the file `@01_references/00_guidelines/setup_paths_template.md`.
* **Data Sanctity & Boundaries:**
  * You are strictly forbidden from modifying, overwriting, or deleting any files inside any raw data folders (e.g., `03_data/01_raw`). You may only read from raw data sources.
  * All massive data transformations must be saved to the Google Drive `02_temp_data/` or `03_clean_data/` folders.
  * Do not navigate, read, or list directories outside of this local project repository and the explicit Google Drive paths defined by the user.
* **Handling Outputs & Reports:**
  * **Script Artifacts:** Save generated graphs, maps, and plots directly to `05_outputs/01_figures/`. Save raw regression tables (`.csv`, `.tex`, `.html`) to `05_outputs/02_tables/`.
  * *Subfolder Rule:* Always create or use a subfolder inside `05_outputs` that matches the script name (e.g., `05_outputs/01_figures/02_analysis/`). Do not dump loose files.
  * **Exploratory Work:** Save preliminary or internal documents/EDA to `06_workspace/02_exploratory/`.
  * **Deliverables:** Formal, compiled client reports (`.docx`, `.pdf`) and slide decks should be saved to `07_deliverables/`.
* **External Data Sourcing:** If tasked with finding, scraping, or downloading external public data (e.g., APIs, spatial shapefiles), write the download scripts to save the files directly into `GDRIVE_PATH/01_raw_data/external/`.
* **NO DATA HALLUCINATION:** NEVER simulate, generate dummy data, or mock datasets to bypass a missing file or an execution error. If data is missing or a merge fails, stop immediately, report the exact error, and wait for human instruction.
* **Git Guardrail:** Never track, download, or commit raw datasets into the local Git folders (`03_data/`).

## 3. Strict Directory Discipline
* **No Unauthorized Folders:** You must strictly adhere to the predefined `01` through `09` folder architecture. DO NOT invent new root folders (e.g., `src/`, `output/`, `data/`).
* If you believe a new subfolder is required to maintain organization, propose it to the user first and wait for his confirmation.

## 4. Coding Standards & Execution
* **The Reproducibility Rule (No Interactive Coding):** NEVER run analytical code interactively in the terminal (e.g., opening a Python REPL, R console, or Stata interactive mode). All code must be written into, saved, and executed from a formal script file (e.g., `.R`, `.do`, `.py`, `.qmd`).
* **Master Script Orchestration:** Assume all code will eventually be run sequentially via a `00_master` script. For complex phases, proactively create sub-master scripts (e.g., `01_cleaning/00_master_clean.R`) to orchestrate specific folders. Write all sub-scripts to be modular and independent, and do not rely on leftover variables from previous sessions.
* **Notebooks vs. Scripts (The Extraction Rule):**
  * We may use Notebooks (`.Rmd`, `.ipynb`, `.qmd`) for exploratory work and documentation.
  * If a notebook chunk contains heavy data-cleaning or modeling logic, extract that logic into a standalone, identically named pure script (e.g., `02_clean.R`) to act as the backend engine. Keep the notebook next to it as the frontend documentation (The "Paired Notebook" pattern).
* **Package Management:** Installation and loading commands MUST be explicitly written at the top of the script file. Do not silently install dependencies via the terminal.
* **Language Agnostic:** This project may use different coding software (e.g., Python, R, Stata). If the user doesn't ask which program to use, please ask. Make sure to follow the guidance of the user. Do not attempt to change the program without the user authorizing it.
* **Coding preferences:**
  * *R:*
    * Use `pacman::p_load()` for clean package loading and installation, keeping these calls grouped at the very top of the script.
    * Use `data.table` for data manipulation (due to memory efficiency), unless working with data (e.g., spatial data (`sf`)), where `dplyr`/base is preferable.
    * Use the `here::here()` package for internal repo paths.
* **Script Structure:** Ensure scripts are sequentially numbered (e.g., `01_clean.R`, `02_analysis.do`) to enforce chronological execution.
* **Commenting & Readability:** Code must be highly readable, modular, and structured for human review.
  * Break complex logic down into clear, numbered steps (e.g., `# 1. Standardize Demographics`, `# 2. Merge Baseline`).
  * Write extensive inline comments explaining the *rationale* behind the code (the "why"), especially for data-cleaning decisions, outlier handling, or econometric choices, not just the mechanical operations (the "what").
* **Reporting:** Final analytical outputs should be compiled from `.Rmd` or `.qmd` into `.docx` format for human review on Google Docs.
* **Verification:** Proactively run your code in the terminal using script execution commands (e.g., `Rscript [file]`) to verify it works before responding to the user.
* **Version Control (Git):** *You have permission to run `git status`, `git add`, and `git commit` to save work*.
  * **Commit Frequency:** Commit code after every major milestone or successful bug fix. Do not wait until the end of the day.
  * **Propose, Then Commit**: ALWAYS propose a conventional commit message (e.g., `feat: clean baseline data`, `fix: correct merge logic in 02_analysis.R`) and wait for human approval before actually running git commit. Never auto-commit.
  * **Branching:** For routine fixes, commit to `main`. For major analytical work, new features, or structural changes, ALWAYS propose creating a new branch (e.g., `git checkout -b feature-poverty-index`) before committing. Let the user decide.
  * **Guardrail:** ALWAYS verify `git status` before committing to ensure no files from `03_data/` have accidentally slipped into the staging area.

## 5. The Legacy Vault (Read-Only)
* The `@09_legacy_vault/` contains historical, unorganized code and data.
* **CRITICAL RULE:** This folder is a read-only museum. You may read and copy code/logic FROM this vault to refactor it, but you are STRICTLY FORBIDDEN from executing scripts within it, modifying, deleting, or overwriting anything inside it.

## 6. Agentic Memory & Session Logging

The project carries a deliberate four-layer tracking system. They are complementary — do not collapse one into another:

| Layer | File(s) | Organized by | Answers |
|-------|---------|--------------|---------|
| **Chronicle** | `01_progress_logs/YYYY-MM-DD_session.md` | date | "What did we do that day?" |
| **Queue** | `01_progress_logs/PENDING.md` | flat open-items list | "What is not done yet?" |
| **Ledger** | `02_quality_reports/decision_log.md` | date | "Why did we choose X, and when?" |
| **Board** | `01_progress_logs/WORKSTREAMS.md` | topic / workstream | "Where do we stand on *survey design* / *analysis* / …?" |

* **Plan Before Execution:** When given a complex task, outline a brief, bulleted plan of action and wait for user approval before generating the code.
* **Living Documentation (`README.md`):** You act as the Project Manager. You MUST proactively update the `README.md` whenever significant project evolution occurs (e.g., Methodology Shifts, Pipeline Updates, Data sources, new Dependencies, project status)
  * **Dependencies:** Documenting new Python/R packages (and automatically running `pip freeze > requirements.txt` if using Python).
* **Session Logging (`08_ai_management/01_progress_logs/`):** To prevent context loss across sessions, you must maintain a running log.
  * **File Naming:** Always use dated files: `YYYY-MM-DD_session.md`.
  * **Continuous Appending:** Do not wait until the end of the session. Append major milestones and failed attempts to the log as they happen.
  * **Format:** Strictly follow `@08_ai_management/03_system_templates/log_template.md`.
  * **Initialization:** When the user says "pick up where we left off," do three things:
    1. Read the most recent dated log in `01_progress_logs/`, scan `WORKSTREAMS.md` for the relevant workstream, and review the `decision_log.md`.
    2. Scan `PENDING.md ## Open` for items relevant to the current task.
    3. Run `git fetch` and `git status`. If the local branch is behind the remote, notify the user and ask for permission before running git pull.
* **Pending Items Tracking (`08_ai_management/01_progress_logs/PENDING.md`):** Single rolling file for items that span sessions — open work, recent completions, cancelled/wontfix items. Complements (does not replace) the per-session `⏭️ Next Steps` block.
  * **When you add a pending item to a session log's `⏭️ Next Steps`, you MUST also add it to `PENDING.md` `## Open` section** with a `[YYYY-MM-DD]` date tag, a one-line title, a brief description, and an *Origin* reference to the session log where it was introduced. PENDING.md is the consolidated cross-session view; session logs are the per-day chronicle. Both must stay in sync.
  * **When you complete a pending item:** move it from `## Open` to `## Recently Done` with a trailing `→ done YYYY-MM-DD` tag.
  * **Pruning:** Recently Done items older than ~30 days (or at milestone boundaries) can be deleted on a cleanup pass. The session log entries for those dates are the permanent record; PENDING.md is a rolling working view, not a historical archive.
  * **Cancelled / wontfix:** items deliberately deprioritized go to `## Cancelled / Wontfix` with a one-line reason. Same pruning policy.
  * **At session start:** scan `PENDING.md ## Open` for items relevant to the current task, the same way you would read recent session logs.
* **Workstream Tracking (`08_ai_management/01_progress_logs/WORKSTREAMS.md`):** The topic-indexed synthesis layer — the "table of contents by theme" over the chronological logs. One section per workstream (e.g., Literature Review, Survey Design, Sampling & Weights, Data Cleaning, Construction, Analysis, Reporting, Dissemination). Each section carries a **Status** badge, a one-paragraph **Current State**, a dated **Advances** list, and **pointers** into the other layers (links to the relevant session log, `decision_log.md` entry, and `PENDING.md` items). Follow `@08_ai_management/03_system_templates/workstream_template.md`.
  * **It is an index, not a diary.** Do not paste full narratives here — synthesize the current state in a few lines and link out to the chronological record.
  * **When to update:** whenever a workstream's *state* meaningfully changes (a phase completes, a decision lands, a blocker appears/clears). Not every session touches every workstream — update only the ones that moved.
  * **Relationship to the other layers:** session logs are *what happened*; `decision_log.md` is *why*; `PENDING.md` is *what's queued*; `WORKSTREAMS.md` is *where each topic stands now*. When you log a session milestone or a decision that advances a workstream, reflect the new state in the matching `WORKSTREAMS.md` section in the same pass.
* **Methodology Tracking (`08_ai_management/02_quality_reports/`):** When making a significant methodological, econometric or data decision, append the rationale to `decision_log.md` using `@08_ai_management/03_system_templates/decision_template.md`.
* **Continuous Learning & Archiving (`08_ai_management/04_knowledge_base/`):**
  * **Learned lessons:** Append reusable insights to `learnings.md` following the structure in `@08_ai_management/03_system_templates/learning_template.md`. Triggers are bidirectional:
    * **User-triggered:** when the user says "Save this lesson" (or any paraphrase), extract the core concept and append immediately.
    * **AI-triggered (proactive):** you SHOULD proactively suggest adding a learning when you encounter: a non-obvious methodological insight, a coding pattern that solved a recurring problem, a workflow optimization, or a debugging takeaway that would prevent future repetition. Don't wait for the user to remember to ask. Phrase the suggestion explicitly — e.g., *"That feels like a candidate for `learnings.md` — want me to write it up?"* — and let the user decide. If the user declines, drop it without negotiation.
  * **Deep methodology references:** When a topic warrants a full, course-note-style write-up (math, derivations, step-by-step procedure) beyond a single `learnings.md` entry, create a dedicated `methodology_<topic>.md` in `04_knowledge_base/`. See `04_knowledge_base/_examples/` for the expected depth and format.
  * **Conversation Transcripts:** If the user asks to save the current conversation, export a markdown transcript into `@08_ai_management/04_knowledge_base/transcripts/`, naming it `YYYY-MM-DD-HH-mm_session.md`.
  * **Skills Backlog:** If we identify a repetitive, tedious task that could be automated into a CLI skill, extract the logic and add it to `@08_ai_management/04_knowledge_base/skills_backlog.md`.

## 7. Claude Code Skills

Skills are reusable, self-contained pipelines stored as `SKILL.md` files that Claude can invoke via slash commands (e.g., `/doc-review`).

### Structure
Each skill lives in `.claude/skills/<skill-name>/` and contains:
- `SKILL.md` — pipeline instructions (the active specification)
- `CHANGELOG.md` — version history and patch rationale
- `KNOWLEDGE_BASE.md` (optional) — research rationale and design decisions for complex skills
- `scripts/` (optional) — any helper scripts the skill executes

### Scope rules
- **Project skills** (`.claude/skills/`) — available only in this repository.
- **Global skills** (`~/.claude/skills/`) — available across all projects. After modifying a skill, always sync: `cp -R .claude/skills/<name> ~/.claude/skills/`.

### Versioning discipline
Skills evolve through a **candidate → promote → version cut** cycle:
1. New observations go into the `## Learnings` section of `SKILL.md` as candidates.
2. When a learning proves recurrent (2–3 times), promote it into the core pipeline instructions and archive the learning entry in `CHANGELOG.md`.
3. When the `Learnings` section exceeds ~8 entries, propose a **version cut** to the user: incorporate mature learnings, clear the section, bump the version in frontmatter, and archive the old `SKILL.md` as `SKILL_vN.md`.
4. Never modify core pipeline instructions unilaterally — propose the change and wait for user approval.

### Deprecation
When a skill is superseded, do not delete it immediately:
1. Add a `⚠️ DEPRECATED` notice to the top of `SKILL.md` and update its description in the frontmatter.
2. Document the reason for deprecation and its replacement in `CHANGELOG.md`.
3. Retain the folder as a historical record until the user explicitly authorises deletion.

## 8. AI Working Style

These rules govern *how* the AI collaborates within a session, complementing the content rules in sections 1–7.

* **Proceed without re-confirming approved plans.** Once the user has approved a multi-step plan, execute it end-to-end without pausing between steps to ask "should I continue?" This rule governs *plan-level* check-ins only. It does NOT override:
  * The permission system (every tool call is still gated by `.claude/settings.local.json`).
  * The harness's "executing actions with care" rules (destructive, hard-to-reverse, or externally-visible operations always require fresh confirmation, regardless of prior plan approval).
  * Project-specific guardrails in this file (raw-data immutability, `00_setup_paths` immutability, legacy-vault read-only, etc.).

  Pause for fresh approval on: (a) genuinely new decision points the original plan didn't cover, (b) any destructive or externally-visible action, (c) results that invalidate the plan's premise.
* **Never run analytical code inline via the shell.** Do not use `Rscript -e "..."`, `python3 -c "..."`, or equivalent. Write the code to a script file first, then execute the file. Inline code triggers permission prompts, isn't reproducible, and isn't reviewable in git history. This is a stricter form of the Reproducibility Rule in section 4.
* **Markdown files use soft-wrap, not hard-wrap.** One paragraph per source line. Do not insert hard line breaks at column 80 or any other fixed width unless the user explicitly requests it. Hard-wrapping breaks diffs, sentence search, and most rendering pipelines.
* **Mathematical expressions in `.md` / `.qmd` / `.Rmd` use LaTeX delimiters.** Wrap inline math in `$...$` and display equations in `$$...$$`. KaTeX / MathJax (whichever the rendering toolchain provides) turns these into properly typeset formulas in the rendered HTML / PDF. Examples:
  * Inline: `the weight is $w = R^{-1} L$, the loading is $L_j$` → renders as nicely formatted variables.
  * Display: `$$s_{ML} = \sum_j w_{BL,j} \cdot \frac{x_{ML,j} - \mu_{BL,j}}{\sigma_{BL,j}}$$` → renders as a centred equation.
  * **Do not** write `s_ML = Σ_j w_BL,j · (x_ML,j − μ_BL,j) / σ_BL,j` as raw plain text in `.qmd` / `.Rmd` — Quarto won't typeset it and the reader sees raw subscripts and Greek letters. Same goes for inline variable references like `R⁻¹ L` or `μ_BL`.
  * In terminal / chat responses to the user, use plain text instead — the chat UI does not render LaTeX, so `$\mu$` would appear as literal `$\mu$` rather than as the Greek letter. Save the LaTeX for files that get rendered.
* **State intent before non-trivial tool calls.** Before web fetches, broad searches, multi-file reads, or long Bash pipelines, prefix with one short sentence saying *what* you're doing and *why*. The user can see tool names but not the reasoning between them. Threshold: would a reasonable observer be confused about why this tool call is happening? If yes, prefix it. Don't narrate obvious mechanics or every step of a routine task.
