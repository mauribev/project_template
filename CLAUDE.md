<!--
TEMPLATE NOTE (for humans — HTML comments are stripped before Claude reads this file, so this note costs no context):
This is the generic instruction file shipped with the Causal Design project template. Keep the rules as they are; change one only if the project genuinely needs a different convention, and record the change in decision_log.md.
Design: this file holds only what Claude needs in EVERY session. Language-specific style lives in .claude/rules/ (loaded when matching files are read); triggered workflows live in skills (/session-start, /log-session, /save-lesson, /save-transcript); hard guardrails are enforced by .claude/settings.json and the git pre-commit hook.
Keep it under ~200 lines (Anthropic's guidance). Before adding a line, ask: "Would removing this cause Claude to make mistakes?"
Per project: fill in the Commands section below.
-->

# Project Instructions

You are assisting an economist with a data-science / impact-evaluation project (baseline cleaning, midline assessment, impact evaluation). The goal is reproducible, well-structured analytical pipelines.

Project background, methodology, data sources, language and pipeline: @README.md

## Commands
<!-- Fill in per project, e.g. the master script and how to run one step. -->
- Full pipeline: `Rscript 04_scripts/00_master.R` *(adapt to the project's language)*
- One script: `Rscript 04_scripts/<NN_name>.R` · `python 04_scripts/<NN_name>.py` · `stata -b do 04_scripts/<NN_name>.do`
- Client report (.docx): `python3 .claude/skills/causal-report/scripts/render.py --spec <report_spec.yaml>` — see the `causal-report` skill; never ship a plain `quarto render`.

## Data and paths
- **Split-brain:** code lives in this repository; data lives on Google Drive and is read at runtime. Never copy data into the repository.
- **Paths come only from `04_scripts/00_setup_paths.[R/py/do]`.** Never hardcode absolute paths; use `GITHUB_PATH`, `GDRIVE_PATH`, `DATA_RAW`, `DATA_TEMP`, `DATA_CLEAN`. You may not edit this file (blocked in settings): if a path must change, tell the user exactly what to change.
- **Source the paths file first in every analysis script you create or modify**, so each script runs on its own:
  - R: `source(here::here("04_scripts", "00_setup_paths.R"))`
  - Python: `from pyprojroot import here; exec(open(here("04_scripts/00_setup_paths.py")).read())`
  - Stata: `do "04_scripts/00_setup_paths.do"` — relative path, working directory at the repo root; `$GITHUB_PATH` only exists after this runs.
  - Full pathing and master-script guide: `01_references/00_guidelines/setup_paths_template.md`.
- **Raw data is read-only.** Never modify, overwrite or delete anything in `DATA_RAW` (`GDRIVE_PATH/01_raw_data/`). Write transformations to `DATA_TEMP` or `DATA_CLEAN`. Downloaded external data goes to `GDRIVE_PATH/01_raw_data/external/`, via a download script.
- **IMPORTANT — no invented data.** Never simulate, mock or generate dummy data to get past a missing file or an error. If data is missing or a merge fails, stop, report the exact error, and wait for instructions.
- Do not read or list directories outside this repository and the Google Drive paths defined in the paths file.

## Where things go
- The `01_`–`09_` root folders are fixed. Never create new root folders; propose any new subfolder and wait for the user's confirmation.
- Figures → `05_outputs/01_figures/<script_name>/`; tables (`.csv`, `.tex`, `.html`) → `05_outputs/02_tables/<script_name>/`. No loose files.
- Exploratory / internal work → `06_workspace/02_exploratory/`.
- Client reports are authored in `06_workspace/04_report_drafts/<report_name>/` (body `.qmd` + `report_spec.yaml`) and rendered into `07_deliverables/02_output_documents/`. The `build/` folder beside a spec is disposable; the `.causal-report/` baseline is tracked (the `.docx` round trip needs it).
- Other deliverables (decks, compiled `.docx` / `.pdf` for review on Google Docs) → `07_deliverables/`.
- `09_legacy_vault/` is a read-only museum: read and copy logic from it, but never execute its scripts (editing is blocked in settings).

## Coding standards
- **Scripts, not consoles.** All analytical code lives in a saved file (`.R`, `.py`, `.do`, `.qmd`) and runs as a file (`Rscript file.R`, `python file.py`, `stata -b do file.do`, `quarto render file.qmd`). Never use an interactive console or inline code (`Rscript -e`, `python -c` are blocked). After writing or changing a script, run it to verify it works before reporting back.
- **Pipeline shape.** Number scripts in execution order (`01_clean.R`, `02_analysis.R`). Everything must run from a `00_master` script; complex phases get a sub-master (`01_cleaning/00_master_clean.R`). Scripts are independent: no reliance on objects left over from another script or session.
- **Paired notebooks.** Notebooks (`.qmd`, `.Rmd`, `.ipynb`) are for exploration and documentation. Move heavy cleaning or modelling logic into an identically named script (`02_clean.R` beside `02_clean.qmd`) and keep the notebook as the documentation.
- **Packages** are installed and loaded explicitly at the top of the script, directly after sourcing the paths file — never installed silently from the terminal. Language-specific conventions load automatically from `.claude/rules/`.
- **Language.** Use the language recorded in the README (Setup & Dependencies). If none is recorded, ask once and suggest recording it. Never switch language without the user's approval.
- **Comments explain the why.** Break logic into numbered steps (`# 1. Standardize demographics`) and comment the rationale behind cleaning decisions, outlier handling and econometric choices — not just what the code does.

## Git
- You may run `git status`, `git add` and `git commit`. Commit after each milestone or successful fix.
- Always propose a conventional commit message (`feat: …`, `fix: …`) and wait for approval before committing (Claude Code also asks before every commit and push).
- Routine fixes go to `main`. For major analytical work, new features or structural changes, propose a new branch first and let the user decide.
- Before committing, check `git status` for data files. The pre-commit hook lists large data files; if it stops a commit, show the user the list and let them decide.

## Working style
- **Plan, then run.** For a complex task, outline a short bulleted plan and wait for approval. Once approved, carry it out end to end without asking "should I continue?". Stop for fresh approval only on (a) a decision the plan didn't cover, (b) anything destructive or externally visible, (c) results that undermine the plan.
- **Say why before non-obvious tool calls** (web fetches, broad searches, multi-file reads, long pipelines): one short sentence of intent.
- **Markdown is soft-wrapped:** one paragraph per line, no hard line breaks at a fixed width.
- **Math:** in `.md` / `.qmd` / `.Rmd` files use LaTeX (`$...$` inline, `$$...$$` display), never Unicode pseudo-math like `μ_BL` or `R⁻¹`. In chat replies use plain text (the terminal doesn't render LaTeX).
- **README is a living document.** You act as project manager: update `README.md` when the methodology, pipeline, data sources, dependencies or project status change.
- When compacting context, preserve the list of files changed, open decisions, and pending items.

## Project memory (four layers — keep them in sync, never merge them)
| Layer | File | Answers |
|---|---|---|
| Chronicle | `08_ai_management/01_progress_logs/YYYY-MM-DD_session.md` | What did we do that day? |
| Queue | `08_ai_management/01_progress_logs/PENDING.md` | What is still open? |
| Ledger | `08_ai_management/02_quality_reports/decision_log.md` | Why did we choose X, and when? |
| Board | `08_ai_management/01_progress_logs/WORKSTREAMS.md` | Where does each topic stand? |

- **"Pick up where we left off"** (or a new session on ongoing work) → run the `session-start` skill.
- **Record milestones, failed attempts, next steps and decisions as they happen** — not at the end of the session → `log-session` skill. It keeps all four layers in sync.
- **Lessons:** when the user says "save this lesson", or you spot a non-obvious insight, reusable pattern or debugging takeaway (then ask first: *"That feels like a candidate for `learnings.md` — want me to write it up?"*; drop it if declined) → `save-lesson` skill. Topics that need a full write-up (math, derivations, procedure) get their own `08_ai_management/04_knowledge_base/methodology_<topic>.md`; see `_examples/` for depth.
- **Saving the conversation** on request → `save-transcript` skill.
- **Repetitive chores** worth automating → add a candidate to `08_ai_management/04_knowledge_base/skills_backlog.md`. Rules for creating or changing skills load from `.claude/rules/skills_maintenance.md` when you work in `.claude/skills/`.
