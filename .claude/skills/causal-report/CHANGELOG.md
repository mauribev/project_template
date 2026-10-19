# Changelog — causal-report

## [1.3.0] — 2026-10-15

Found on the Matthew 6:3 financial proposal: the cover's client line wrapped and pushed the date onto a second cover page, and nothing in the build could see it. The skill now checks the layout as Word renders it, and the front matter adapts to short documents.

### Added

- **Layout check in Word (build step 6, `verify_layout.py`), opt-in with `--check-layout`.** It ran on every build at first; it was made opt-in the same day because it takes over Word for a moment and interrupted the user reading a document. Word exports the built report to PDF and the pages are checked: the cover is one page with its date and whole title, the logo page follows it, there is no blank page, and the contents pages match the spec. A problem fails the build with a plain message. Without macOS and Word, the step reports that the layout was not checked. The export runs on a copy without `updateFields`, whose "update fields?" prompt would otherwise block Word; it writes only to its own folder in Word's sandbox and deletes only the files it created, by explicit path.
- **`include:` in the spec** switches off the table of contents, the acronyms page, or both (default: both on, so existing specs build as before). Blocks are located by structure, not by position.
- **Line breaks in spec values**: `\n` in a value becomes a Word line break, e.g. a two-line title.
- **Automatic size for the client line** (`cover_fit` in the profile): a "CLIENT, COUNTRY" line longer than about 38 characters is set smaller, down to 9 pt, so it never overflows the cover.
- **Table page breaks controlled** (`keep_together_max_rows` in the profile): no table row is ever split across pages. Keeping whole tables of up to 30 rows on one page was tried first and turned off the same day because it left white space; see *New page-flow defaults* below.
- **`acronyms:` in the spec** fills the acronyms table (sorted, placeholder highlight removed). When the acronyms page is included the list is required, and the build refuses any document that still contains the `###` placeholders.
- **New page-flow defaults, to avoid white space** (user, 2026-10-15): Heading 1 no longer starts a new page and gets 24 pt of space above instead; tables may start on one page and continue on the next, with no row ever cut in two and the title line and header row kept with the first body row. Both are profile settings (`Heading1`, `table: keep_together_max_rows`); SKILL.md, *Page flow defaults*, says how to change them.
- **`selftest.py`** builds the example in six configurations and checks each in Word. Run it after any change to the skill.

### Fixed

- **Cover spilling onto a second page.** The client line sat in a 2.7-inch cell and wrapped to three lines; the row grew and the date moved to page 2. The bottom row now spans the full width, both cover rows have an exact height, and the empty paragraphs around the cover table are 2 pt. Patch kept in `profiles/long_report/patches/2026-10-15_cover_fit.py`; the original front matter is `frontmatter_source_v1.docx`.
- **Blank page before the body.** An empty paragraph after the front matter's last section break sat alone on a page, because the body's first heading starts a new page; a redundant manual page break sat in the same place. Both are removed at build time.

### Evidence

`selftest.py`: 6/6 configurations pass in Word, including a two-line title and an 80-character client line (set at 9 pt). The Matthew 6:3 financial proposal went from 16 pages (one of them a spilled cover page, one blank) to 12, every table on the page of its title. The layout check fails, as it should, on the proposal built with version 1.2.1.

### Ported to the scaffold (2026-10-19)

Copied from the Matthew 6:3 project into `project_template`. Project names in the example acronyms (`SKILL.md`, `templates/report_spec.yaml`) and in the `selftest.py` test values were replaced with neutral ones of the same length, so the client line still tests below and above the 38-character limit; `selftest.py` passed 6/6 in Word with the new values. `examples/README.md` no longer says Heading 1 starts its own page.

---

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
