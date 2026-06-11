# Causal Design — Project Template / Scaffold

This repository is a **reusable scaffold** for Causal Design data-science and impact-evaluation projects (midline assessments, baseline cleaning, impact evaluations, and the like). It is **not a project itself** — it is the starting point you copy whenever you begin a new one.

Its job is to make every new project start the same way: a fixed folder architecture, a tested set of operating rules for the Claude Code agent, document templates, a four-layer progress-tracking system, and a couple of ready-to-use AI skills. Everything here was refined on real engagements (originally extracted from the BRCiS III midline evaluation) so that the conventions, guardrails, and accumulated lessons carry forward instead of being reinvented each time.

> **This is the README *of the template*.** When you spin up a new project (Section 1), the root `README.md` is **replaced** by a project-specific one (from `08_ai_management/03_system_templates/README_template.md`). So this file documents the scaffold; the new project gets its own.

---

## 1. Start a new project from this scaffold

This scaffold lives on GitHub at **`github.com/mauribev/project-template`** as a *template repository*. Each new project is a **fresh copy with its own clean git history** — the scaffold itself stays pristine. Two ways to get one:

**A. "Use this template" (recommended, no terminal).** On the GitHub page, click the green **"Use this template" → "Create a new repository"** button. Name the new repo after your project, then clone it locally:
```bash
git clone https://github.com/mauribev/<your-new-project>.git
cd <your-new-project>
```
You get the full structure with a single clean commit and no inherited history.

**B. Clone and re-initialise (manual).** If you'd rather copy the files directly:
```bash
git clone https://github.com/mauribev/project-template.git my_new_project
cd my_new_project
rm -rf .git && git init          # drop the template's history, start your own
git add -A && git commit -m "chore: scaffold new project"
```

Either way, the first move inside the new project is to tell Claude Code: **"This is a fresh project from the template — help me fill in the blanks."** It will walk the checklist below.

---

## 2. First-session setup checklist

Turning the blank scaffold into a live project:

- [ ] **Install the project README.** `cp 08_ai_management/03_system_templates/README_template.md README.md`, then fill in every `[bracketed placeholder]`: project name, lead, status, objectives, research questions, methodology, GDrive link, data sources, language/packages, random seed, and the pipeline list.
- [ ] **Create your paths file** — *do this before running any script.* Build `04_scripts/00_setup_paths.[R/py/do]` from `01_references/00_guidelines/setup_paths_template.md`, filling in the absolute path to your Google Drive (`GDRIVE_PATH`) and to this repo (`GITHUB_PATH`). Scripts read the data from Google Drive (not from the repo), so without this file nothing can find its inputs. It's the one file the agent may never edit — see Section 5 for the full rationale.
- [ ] **Skim `CLAUDE.md`.** It is generic and ready to use. Delete the "Template note" blockquote at the top once you've read it. Only change a rule if this project genuinely needs a different convention — and if you do, record it in `decision_log.md`.
- [ ] **Trim the workstreams.** Edit `08_ai_management/01_progress_logs/WORKSTREAMS.md` so its sections match the topics this project actually has (rename / add / delete).
- [ ] **Check `.gitignore`.** Already tuned: it ignores `03_data/`, R/Python environments, and Office lock files, and whitelists the shareable `.claude/skills` etc. Adjust only if the project needs it.
- [ ] **Seed the legacy vault (optional).** Drop any prior-project code/data you'll migrate *from* into `09_legacy_vault/` (read-only reference); remove its `.gitkeep` once populated.
- [ ] **Decide on the examples.** `08_ai_management/04_knowledge_base/_examples/` holds format references from a past project — keep them as a depth guide or delete the folder.

---

## 3. The philosophy behind the structure

A handful of principles explain *why* the scaffold is shaped the way it is. They are enforced in detail by `CLAUDE.md`; this is the short version.

- **Split-brain: code and data live apart.** Code lives in this Git repo; raw and intermediate **data never do** — it stays on the secure Google Drive and is read in at runtime. This protects beneficiary PII, keeps the repo lean, and means the same code runs on any teammate's machine. `03_data/` is gitignored as a hard backstop.
- **Reproducibility over convenience.** No interactive console work, no inline one-liners — all logic lives in numbered, sourceable script files, orchestrated by a master script, with fixed random seeds. Anyone can re-run the pipeline top to bottom and get the same numbers.
- **A fixed, predictable home for everything.** The `01_`–`09_` architecture is deliberate and not to be reinvented per project: references, survey tools, data, scripts, outputs, workspace, deliverables, AI management, legacy vault. You always know where a thing goes.
- **Everything leaves a trail.** Sessions, decisions, open items, and per-topic status are all tracked in dedicated files (Section 4), so context survives across days, people, and AI sessions.
- **Knowledge compounds.** Reusable lessons, deep methodology write-ups, and automatable chores are captured (`learnings.md`, `methodology_*.md`, `skills_backlog.md`) — and the strongest patterns are promoted back into *this scaffold* so the next project starts smarter.
- **The AI is a co-pilot, not the captain.** The agent operates inside firm guardrails — raw data is read-only, the paths file is untouchable, the legacy vault is a museum, and every commit is proposed for human approval before it runs.

---

## 4. The four-layer tracking system

The most important convention in the scaffold. Project progress is tracked across **four complementary files**, each answering a different question. They are kept in sync and never collapsed into one — together they let anyone (human or AI) recover full context after any gap.

| Layer | File | Organized by | Answers |
|-------|------|--------------|---------|
| **Chronicle** | `01_progress_logs/YYYY-MM-DD_session.md` | date | *What did we do that day?* |
| **Queue** | `01_progress_logs/PENDING.md` | flat list | *What's still open?* |
| **Ledger** | `02_quality_reports/decision_log.md` | date | *Why did we choose X, and when?* |
| **Board** | `01_progress_logs/WORKSTREAMS.md` | **topic** | *Where do we stand on each topic?* |

How they interlock:

- **Chronicle** — append-only daily logs (Goal / Completed / Dead Ends / Next Steps). The raw narrative of what happened, including failed attempts so they aren't repeated.
- **Queue** — `PENDING.md` lifts every "Next Step" into one cross-session list (Open / Recently Done / Cancelled), so nothing is lost between sessions.
- **Ledger** — `decision_log.md` records *why* each significant methodological, econometric, or data choice was made, and what was rejected. The audit trail for the analysis.
- **Board** — `WORKSTREAMS.md` is the **synthesis layer**: a status page per topic (Lit Review, Survey Design, Sampling & Weights, Cleaning, Construction, Analysis, Reporting, Dissemination…). Each section gives the current state in a few lines and **links out** to the relevant chronicle entries, decisions, and pending items — so "what's the status of the survey workstream?" is a single read, not a scrub through every daily log.

The Board exists precisely because the other three are chronological or flat: they tell you *what happened* and *what's open*, but not *where each topic stands now*. Rule of thumb: the Board is an **index, not a diary** — synthesize and link, never duplicate.

---

## 5. What's in the box

An annotated inventory of the key files. Each has a matching blueprint in `08_ai_management/03_system_templates/` where relevant.

### Operating rules
- **`CLAUDE.md`** — the agent's full operating manual: data/pathing guardrails, directory discipline, coding standards, git discipline, the tracking system, the skills lifecycle, and AI working style. The single source of truth for how Claude Code behaves in the project. *This file is already generic and ready to use — it is its own template, so there is no separate "CLAUDE template" to copy.*

### The pathing system (`00_setup_paths`)
**What it is for:** code lives in the repo, but the data lives on Google Drive (Section 3), and every person mounts that Drive at a *different* absolute path (e.g. yours starts `/Users/mauribev/Library/CloudStorage/GoogleDrive-…`, a colleague's looks nothing like it). If scripts hardcoded a path, they'd break the moment anyone else ran them. `00_setup_paths` solves this: it is a small config file that figures out the correct paths **for whoever is running the code right now** and stores them in named variables.

**How it's used:** the file defines variables like `GITHUB_PATH` (this repo), `GDRIVE_PATH` (the Drive project folder), and derived data paths (`DATA_RAW`, `DATA_CLEAN`, …). **Every analysis script sources it as its very first line**, then refers to data only through those variables — e.g. read from `file.path(DATA_RAW, "household_survey.csv")` instead of a literal `/Users/...` path. The result: any script runs unchanged on any teammate's machine.

- **Create it once per machine** from the recipe in **`01_references/00_guidelines/setup_paths_template.md`** (ready-made R / Python / Stata versions, plus the syntax for running sequential scripts). You only fill in the absolute paths for *your* machine.
- It is the **one file the AI is forbidden to modify** — it encodes machine-specific absolute paths that only you can know. If a path needs changing, the agent tells you and you edit it by hand.

### Tracking files
`PENDING.md`, `WORKSTREAMS.md` (in `01_progress_logs/`), and `decision_log.md` (in `02_quality_reports/`), plus the dated session logs — all described in Section 4. Blueprints: `log_template.md`, `decision_template.md`, `workstream_template.md`.

### Knowledge base (`08_ai_management/04_knowledge_base/`)
- **`learnings.md`** — reusable analytical/coding lessons, each tagged from a standard taxonomy. Blueprint: `learning_template.md`.
- **`methodology_*.md`** — full, course-note-style references (math first, then step-by-step) for non-trivial methods that outgrow a single learning entry. See `_examples/` for the expected depth.
- **`skills_backlog.md`** — candidate repetitive chores worth turning into a Claude Code skill.
- **`transcripts/`** — saved conversation exports, on request.

### System templates (`08_ai_management/03_system_templates/`)
The blueprints the agent copies from when creating new files: `README_template.md` (the project README, installed in Section 2), `log_template.md`, `decision_template.md`, `learning_template.md`, `workstream_template.md`, and **`qmd_template.qmd`** — the three-part diagnostic-report section pattern (fixed intro prose → dynamic R chunk → optional callout) used for reproducible Quarto reports.

### AI skills (`.claude/skills/`)
Reusable `/slash-command` pipelines:
- **`doc-to-md`** — convert PDF / Word documents to clean Markdown.
- **`doc-review`** — produce a thorough, stand-alone review of a Markdown document.

Skills also work globally from `~/.claude/skills/`. After editing a project skill, sync it with `cp -R .claude/skills/<name> ~/.claude/skills/`. The full versioning/deprecation lifecycle is in `CLAUDE.md` §7.

### Guidelines (`01_references/00_guidelines/`)
- **`git_team_workflow.md`** — onboarding for teammates new to Git (the hybrid Git + Google Drive workflow, and the rules that keep data out of the repo).
- **`setup_paths_template.md`** — the pathing recipe described above.

---

## 6. Folder map

```
[project]/
├── CLAUDE.md            # Agent operating rules
├── README.md            # Project context (from README_template.md on setup)
├── .gitignore           # Keeps data + local cruft out of git
├── 01_references/       # 00_guidelines · 01_project_documentation · 02_literature · 03_past_examples
├── 02_survey_tools/     # 01_quant_tools (XLSForms) · 02_qual_tools (KII/FGD guides)
├── 03_data/             # [GITIGNORED — lives on GDrive] 01_raw_data · 02_temp_data · 03_clean_data
├── 04_scripts/          # 00_setup_paths · numbered pipeline · 00_resources · 01_functions · 99_replication
├── 05_outputs/          # 01_figures · 02_tables (subfoldered per script)
├── 06_workspace/        # 01_notes · 02_exploratory · 03_document_review
├── 07_deliverables/     # 00_templates · 01_decks · 02_output_documents
├── 08_ai_management/    # 01_progress_logs · 02_quality_reports · 03_system_templates · 04_knowledge_base
└── 09_legacy_vault/     # [READ-ONLY] old code/data to migrate from
```

The canonical structure with per-folder rationale is documented in full in `README_template.md` §5 (it ships to every project).

---

## 7. Maintaining the scaffold

This template is a living asset — the canonical home for "how Causal Design runs a project." When a project surfaces a genuinely reusable convention, template, or skill, **port it back here** (stripping anything project-specific) and bump the version note below.

**Scaffold version:** v1.0 — extracted from BRCiS III, June 2026. Adds the `WORKSTREAMS.md` board, `skills_backlog.md`, and the consolidated four-layer tracking model on top of the original folder scaffold.
