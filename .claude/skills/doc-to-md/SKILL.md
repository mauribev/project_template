---
name: doc-to-md
version: 1.1
description: Converts one or more PDF or Word (.docx/.doc) documents to clean Markdown files. Saves output to a specified directory. Does not summarize or analyze content — use the doc-review skill for that.
---

# Document-to-Markdown Conversion Pipeline

You are executing a document conversion pipeline. Your **only** job here is to convert source files to clean Markdown. Do not summarize, analyze, or annotate the content.

---

## Inputs

1. **Target File(s):** One or more `.pdf`, `.docx`, or `.doc` files specified by the user.
2. **Output Directory (Optional):** Where to save the resulting `.md` files. If not specified by the user, default to `06_workspace/03_document_review/`.

---

## Conversion Logic

The script at `.claude/skills/doc-to-md/scripts/pdf_to_md.py` uses a routing strategy:

| File type | Tool | Reason |
|-----------|------|--------|
| `.docx` / `.doc` | **Pandoc** (via pypandoc) | First-class Word table model; correctly handles merged/spanning cells |
| `.pdf` (and all others) | **Docling** (IBM) | Best-in-class PDF extraction: OCR, multi-column layout, embedded tables |

**System requirements:**
- Pandoc must be installed at the OS level: `brew install pandoc` (macOS)
- pypandoc and docling are installed automatically on first run if missing

---

## Single-File Procedure

1. Run the conversion script:
   ```
   python3 .claude/skills/doc-to-md/scripts/pdf_to_md.py "<path_to_file>" "<output_dir>"
   ```
2. Confirm the `.md` file was written to the output directory.
3. Report the output file path and its line count (`wc -l`) to the user.

---

## Multi-File Procedure

When the user provides more than one file:

1. **List all target files** explicitly before starting.
2. Run Phase 1 for each file **in sequence** — do not skip any.
3. After all conversions complete, report a summary table:

   | Source file | Output `.md` | Line count |
   |-------------|-------------|------------|
   | ... | ... | ... |

4. Remind the user they can now run the `doc-review` skill on any of the resulting `.md` files.

---

## Output Directory

Unless the user specifies otherwise, save all `.md` files to `06_workspace/03_document_review/01_sources/`.

**Create the directory if it does not exist:**
```bash
mkdir -p "06_workspace/03_document_review/01_sources"
```

This aligns with the `doc-review` skill's artifact-type folder structure, where `01_sources/` holds all converted source Markdown files.

**CRITICAL:** Never write output files into a read-only directory (e.g., `09_legacy_vault/`). Always pass an explicit `output_dir` to the script.

---

## Continuous Improvement (Self-Healing)

If `pdf_to_md.py` fails for any reason, or if you discover a more efficient workflow:

1. Stop and debug the code to handle the edge case.
2. Overwrite `pdf_to_md.py` with your fixed code.
3. **Update the Log:** Append to `.claude/skills/doc-to-md/CHANGELOG.md` with: date, error, and exact fix applied.
4. **Update Learnings:** Append findings to the **Learnings** section at the bottom of this file. If the finding suggests the core pipeline instructions should be changed, do NOT modify them unilaterally — present the proposed change to the user and wait for approval before editing.
5. **Version discipline:** If the Learnings section exceeds **8 entries**, propose a version cut to the user: promote mature/recurrent learnings into the core pipeline instructions, clear them from the Learnings section, bump the version in the frontmatter and CHANGELOG, and archive the old SKILL.md as `SKILL_vN.md`. Learnings are candidates for pipeline promotion, not a permanent log.
6. **Global Sync:** Promote upgrades to the global profile:
   ```
   mkdir -p ~/.claude/skills/
   cp -R .claude/skills/doc-to-md ~/.claude/skills/
   ```
6. Notify the user of the upgrade, then resume.

---

## Learnings

*(Append discoveries here — do not modify the pipeline instructions above.)*

- **2026-04-07 — Routing strategy:** `.docx`/`.doc` files route through Pandoc (pypandoc); `.pdf` files route through Docling. Pandoc correctly handles merged/spanning table cells that Docling collapses. Requires OS-level Pandoc installation (`brew install pandoc`).
- **2026-04-07 — Output directory:** Always pass an explicit output directory to avoid writing into read-only source folders (e.g., `09_legacy_vault/`). Default output: `06_workspace/03_document_review/`.
- **2026-04-07 — Line counts:** Pandoc-converted `.docx` files are line-sparse (many blank lines, inline HTML for merged tables). A 30-page Word report typically produces 500–2,500 lines of Markdown depending on table density.
