# Skills Backlog

Candidate repetitive, tedious tasks that could be automated into a Claude Code skill (a reusable `/slash-command` pipeline). When we hit the same multi-step chore 2–3 times, capture it here; promote the strongest candidates into `.claude/skills/<name>/` per the versioning discipline in `CLAUDE.md` §7.

## How to add a candidate

Each entry: **Name (proposed).** What the task is → why it's painful by hand → rough sketch of the pipeline (inputs → steps → output). Tag with a status: `idea` · `scoped` · `building` · `shipped`.

---

## Candidates

_(none yet)_

Example shape (delete once you add a real one):
- **`xlsform-diff` `idea`.** Compare two XLSForm versions and report added/removed/renamed questions and choice-list changes. *Painful by hand:* manual cell-by-cell diff across sheets. *Sketch:* read both `.xlsx` (survey + choices sheets) → align on `name` → emit a markdown change table to `06_workspace/`.

---

## Shipped (now live under `.claude/skills/`)

- **`doc-to-md`** — convert PDF/Word documents to clean Markdown.
- **`doc-review`** — thorough, stand-alone review of converted Markdown documents.
