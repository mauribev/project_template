# doc-to-md Skill — Changelog

## 2026-04-07 — v1.1

- **Default output directory changed** from `06_workspace/03_document_review/` to `06_workspace/03_document_review/01_sources/`. Aligns with the `doc-review` skill's v1.2 artifact-type folder structure where `01_sources/` holds all converted source Markdown files.
- **Added `mkdir -p` instruction** to ensure the output directory exists before conversion.
- **Added `version` field** to frontmatter.

---

## 2026-04-07 — Initial creation

**Source:** Extracted from the `hybrid-lit-review` skill. The conversion logic (Phase 1) has been separated into a standalone skill so that document conversion and document review can be invoked independently.

**Script:** `scripts/pdf_to_md.py` copied from `hybrid-lit-review/scripts/pdf_to_md.py` (which already includes two prior patches — see that skill's CHANGELOG for history):

- *Patch 1 (2026-04-06):* Added `output_dir` parameter to prevent writes into read-only source directories.
- *Patch 2 (2026-04-06):* Routing strategy — `.docx`/`.doc` → Pandoc (pypandoc); `.pdf` → Docling. Fixes merged-cell table corruption in Word files.

No changes to script logic in this release.
