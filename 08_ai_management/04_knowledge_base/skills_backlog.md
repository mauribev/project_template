# Skills Backlog

Candidate repetitive, tedious tasks that could be automated into a Claude Code skill (a reusable `/slash-command` pipeline). When we hit the same multi-step chore 2–3 times, capture it here; promote the strongest candidates into `.claude/skills/<name>/` per the versioning discipline in `CLAUDE.md` §7.

## How to add a candidate

Each entry: **Name (proposed).** What the task is → why it's painful by hand → rough sketch of the pipeline (inputs → steps → output). Tag with a status: `idea` · `scoped` · `building` · `shipped`.

---

## Candidates

- **`deck-from-template` `scoped`.** Build an on-brand `.pptx` by editing a copy of an existing deck. *Painful by hand:* the same loop every time — dump the base deck's structure, map shape names, write a build script, verify, then fix the same class of bug that was fixed on the last deck. *Sketch:* inputs = base deck + a slide-by-slide content spec (title, bullets as `label — explanation` pairs, figures, notes) → steps = inspect and emit the shape-name map, clone/edit/add slides, delete unused, reorder, then run the verification battery (slide count, no surviving source text, bold only on lead runs, pictures within bounds, no duplicate zip parts) → output = the deck in `07_deliverables/01_decks/` plus a structural dump. The rules this would encode are written up in `_examples/learning_deck_editing.md`; the point of the skill is that they stop being re-derived.
- **`xlsform-diff` `idea`.** Compare two XLSForm versions and report added/removed/renamed questions and choice-list changes. *Painful by hand:* manual cell-by-cell diff across sheets. *Sketch:* read both `.xlsx` (survey + choices sheets) → align on `name` → emit a markdown change table to `06_workspace/`.

---

## Shipped (now live under `.claude/skills/`)

- **`doc-to-md`** — convert PDF/Word documents to clean Markdown.
- **`doc-review`** — thorough, stand-alone review of converted Markdown documents.
- **`causal-report`** — build a Causal Design client report as a formatted Word document. Front matter authored in Word with `{{TOKEN}}` placeholders, body authored in Quarto, the two stitched into one flat `.docx`. All typography, colour and table formatting live in `profiles/<name>/profile.yaml`, so no design decision is left to whoever writes the report. **Known gap:** a standardised *figure* function set — nothing yet enforces a consistent palette, axis treatment or source footnote across a report's charts. See the skill's `CHANGELOG.md`.
