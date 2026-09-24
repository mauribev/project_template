# Changelog — causal-report

## [1.2.1] — 2026-09-23

### Fixed

- **The lint failed on the skill's own `templates/report.qmd`.** Its comment block explains the two forbidden patterns by naming them — `{#fig-…}` and "Table 1" — and the lint read them as violations, so copying the template and building produced an immediate failure on unmodified boilerplate. HTML comments are now stripped before linting, which is correct on the merits: a comment never reaches the output. Found by running the skill from `~/.claude/skills/` in a directory outside any project.

---

## [1.2] — 2026-09-22

The round trip. An edited `.docx` can now be brought back into the `.qmd`.

### Added

- **`import_docx.py`** — section-anchored merge under a checkout model. Unchanged sections keep their original `.qmd` text; changed sections take the converted text; new sections are inserted; missing sections are reported and never deleted. Refuses to run if the `.qmd` changed while the document was out.
- **`docx_import.py`** — conversion and normalisation, used by *both* `render.py` (to store the baseline) and `import_docx.py` (to read the returned file). Identical settings on both sides is what makes an untouched section compare byte-identical.
- **Baseline state in `.causal-report/`** — the `.qmd` as delivered, plus a conversion of the `.docx` that went out. Committed; without it the round trip has nothing to compare against.
- **Tables read from the XML, not from pandoc**, with dimensions verified against the package afterwards. The import fails on any mismatch.
- **Normalisation to house convention** on the way in: caption headings become bold caption lines, image-headings become plain images. Incoming documents are made to look like something this skill produced, rather than having their habits preserved.
- **Code-chunk protection** — a section whose source contains an executable chunk is never overwritten, because the `.docx` holds the chunk's output, not its code.

### Evidence

Tested against a real 67-heading Google Docs export. Google Docs writes standard `Heading1`–`Heading6`, and all 67 headings recovered with level and text intact; lists, block quotes, footnotes and mathematics (OMML back to LaTeX) all survive.

**Pandoc's docx table reader silently dropped two of three columns** from a well-formed 11×3 table in that document — no warning, content simply gone. Direct XML extraction recovered all 11×3. This is why tables never go through pandoc.

Idempotency verified: render → import on the unedited output reports 12 sections unchanged and writes nothing. A simulated reviewer edit (one prose change, one table cell) was detected as exactly two changed sections, with the other ten untouched.

### Fixed during development, all found by the idempotency test

- Splicing tables **before** trimming the front matter lined the acronyms table up against the body's first table and shifted every table by one.
- `\s*` in the table regex swallowed the blank line after a table, because `\s` matches newlines. Now `[ \t]*`.
- The `---` → em dash substitution corrupted pipe-table separator rows. Now skips lines starting with `|`.
- Body-start detection used the converted baseline's headings rather than the `.qmd`'s, so the front matter's acronyms section leaked into the body.

---


## [1.1] — 2026-09-22

Fixes from the first visual review of `examples/01_elements.docx`.

### Fixed

- **Heading 1 rendered indented.** The hand-authored front matter carried `<w:ind w:left="720"/>` on the style, and the build only cleared `pageBreakBefore` from the paragraph properties. Indentation and spacing are now profile-controlled and cleared before being set.
- **Table header text rendered black, and body rows were not banded.** The `Table` style's conditional formatting (`firstRow`, `band1Horz`, `band2Horz`) was defined correctly and the `tblLook` flags were right, but Word did not apply it — the style's base `rPr` colour won for the header. The build now **stamps the look directly onto every row and cell** (`stamp_table_formatting`), which is deterministic and verifiable without a renderer. The style definition is kept as well, now `basedOn` `TableNormal` with explicit band sizes, so the table still reads correctly in Word's UI.

### Added

- **Every style pandoc emits is now in `profile.yaml`.** Previously only `Normal` and the headings were specified, leaving paragraphs, lists, quotations and captions to whatever the grafted pandoc defaults happened to be. The profile now names all twelve: `Normal`, `BodyText`, `FirstParagraph`, `Compact` (list items and table cells), `BlockText` (quotations), `ImageCaption`, `TableCaption`, `Heading1`–`Heading5`.
- **`indent`, `indent_right`, `first_line`, `space_before`, `space_after` and `italic`** as per-style profile keys.
- **Schema-ordered element insertion.** `rPr`, `pPr` and `tcPr` children are inserted at their correct position rather than appended. Word tolerates disorder; validators do not, and a file that trips a validator is a file that may prompt "Word found unreadable content".

### Note

`Compact` deliberately has no `indent`. List indentation comes from `numbering.xml` via each item's `numPr`, and a paragraph-level indent would override it and flatten every list.

---


## [1.0] — 2026-09-22

First version. Produces a Causal Design long-form client report as a flat Word document.

### Added

- **`long_report` profile.** Front matter authored in Word (cover, logo page, table of contents, acronyms) with `{{TOKEN}}` placeholders; all typography, colour, table formatting and page geometry in `profile.yaml`.
- **`render.py`** — the single supported build command. Builds templates, lints the source, renders the body, stitches, validates, and deletes its output rather than hand over a file Word might refuse to open.
- **`make_templates.py`** — token substitution and style injection. `--list-tokens` reports what a front matter expects.
- **`renumber_titles.py`** — resequences `**Figure N.**` / `**Table N.**` titles.
- **`docx_common.py`** — shared Word-package helpers.
- **`examples/01_elements.qmd` + rendered `.docx`** — one of every element. Doubles as the style reference and the pipeline's smoke test.
- **Source lint** enforcing the two rules that otherwise fail silently: no Quarto cross-reference anchors, no figure or table numbers cited in prose.

### Design decisions

Recorded with evidence in `KNOWLEDGE_BASE.md`. In brief: front matter stays a Word file because Quarto cannot produce multi-section layouts; two artifacts are built from one source because pandoc copies the first `sectPr` it finds; pandoc's missing styles are grafted in because it does not synthesise them and body text otherwise falls back to Cambria; embedded fonts are stripped because they invalidate the package and dominate its size; tables need no markup because the `Table` style plus pandoc's own `tblLook` flags do the work; figure and table numbers are manual because Quarto's cross-reference anchors emit schema-invalid captions.

### Origin

The split front-matter/body/stitch architecture comes from the BRCiS III midline long-report build, which proved it on a 1,311-line body with 144 headings. Generalised here: branding moved out of the `.docx` and into a profile, tokens made substitutable, validation added, and the editorial rules turned into an enforced lint rather than a convention in a README.

---

## Known gaps / planned work

- **`report_viz.R` — a standardised figure and table function set.** The BRCiS pipeline used one (`fig_bar_compare`, `fig_hist`, `fig_bar_single`, `fig_delta`, `tbl_compare`, `tbl_angled`; every figure returning `list(plot, data)`), which kept the look consistent across a long report and stopped figures being hand-styled. It was judged overkill for v1, and the table half of it is now largely unnecessary — the Word table style reproduces the house look from a plain pipe table, which is what that machinery was mostly doing. **The figure half is still a real gap:** there is currently nothing enforcing a consistent palette, axis treatment or "Based on N households" footnote across a report's charts. Worth building when the first report with a substantial number of figures arrives. Source to lift from: `04_scripts/00_setup/01_functions/report_viz.R` in the BRCiS project.
- **Acronyms are filled by hand** in the front-matter Word file. A `{{ACRONYMS}}` marker that the build expands into a table from a list in the spec would be more automatic, at the cost of the only real table-construction machinery in the pipeline. Revisit if hand-filling proves error-prone.
- **Only one profile.** `long_report` covers the long-form client report. Shorter formats — a memo, a two-page brief — would each need their own front matter and profile.
- **No visual verification.** LibreOffice is not installed, so every check is structural. A rendered report has to be opened in Word by a person at least once per profile change.
