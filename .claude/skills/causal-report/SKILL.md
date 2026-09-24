---
name: causal-report
version: 1.2.1
description: Produces a Causal Design client report as a Word document — cover, logo page, table of contents and acronyms from a hand-authored Word front matter, body authored in Quarto, the two stitched into one flat .docx. All typography, colour and table formatting come from a profile YAML, so no design decision is left to whoever is writing. Use when a report, assessment or memo has to be delivered as a formatted .docx.
---

# Causal Design Report Pipeline

You are producing a Word deliverable. Read this file in full before acting.

> **The one idea behind this pipeline.** `profile.yaml` is authoritative for everything expressible as a value — fonts, sizes, colours, the table look, page geometry. The `.docx` is authoritative only for what YAML cannot express: cover layout, graphics, and the live table-of-contents field. You never choose a font or a colour; you choose a profile name. See `KNOWLEDGE_BASE.md` for why each piece is built the way it is.

---

## Inputs

| | |
|---|---|
| **profile** | A directory under `profiles/`. Ships with `long_report`. |
| **report spec** | `report_spec.yaml` — this report's title, client, date, paths. Copy from `templates/`. |
| **body** | A `.qmd` holding the report text. Copy from `templates/report.qmd`. |

## Produce the report

One command. There are no flags to get wrong, and every check runs every time.

```bash
python3 <skill>/scripts/render.py --spec report_spec.yaml
```

Then open the file in Word, click the table of contents and press **F9** to fill in page numbers. The TOC is a live Word field and cannot be populated at build time.

---

## Pipeline

### Phase 0 — Set up (once per report)

1. Create the report directory. Copy `templates/report_spec.yaml` and `templates/report.qmd` into it, renaming the `.qmd` as you like.
2. Discover what the front matter needs filled in:
   ```bash
   python3 <skill>/scripts/make_templates.py --profile long_report --list-tokens
   ```
3. Fill every listed token into the spec's `values:` block, and set `body:` and `out:`.

**Do not** edit `profile.yaml` for a single report. It describes the house style, not this document.

Everything about the document's appearance is in that file: all twelve styles pandoc emits for a report body — `Normal`, `BodyText`, `FirstParagraph`, `Compact` (list items and table cells), `BlockText` (block quotations), `ImageCaption`, `TableCaption` and `Heading1`–`Heading5` — plus the table look and the page geometry. Anything a style is not given there is **cleared**, so formatting that happens to sit in the Word file does not leak into the build.

### Phase 1 — Write the body

Write in the `.qmd`. The four rules in **House Rules** below are not stylistic preferences — three of them are enforced by a lint pass that refuses to build.

### Phase 2 — Build

```bash
python3 <skill>/scripts/renumber_titles.py <body>.qmd   # if figures/tables moved
python3 <skill>/scripts/render.py --spec report_spec.yaml
```

`render.py` builds the templates, lints the source, renders the body, stitches it onto the front matter, and validates the result. **If validation fails it deletes the output rather than hand over a file Word might refuse to open.**

### Phase 3 — Check

Report to the user:
- the output path and size;
- that they must press F9 in Word to populate the TOC;
- anything the lint pass or the build printed as a note.

---

## Round trip: bringing an edited document back

The `.docx` goes out, people edit it in Word or Google Docs, and their work comes back into the `.qmd`.

```bash
python3 <skill>/scripts/import_docx.py --spec report_spec.yaml --from edited.docx
```

**The checkout model.** `render.py` stores a baseline each time it builds. While a document is out for editing the `.qmd` is **frozen** — the importer refuses to run if it changed in the meantime, so the rule is enforced rather than merely agreed.

**The merge is section by section**, keyed on headings:

| | |
|---|---|
| unchanged | the original `.qmd` text is kept, untouched |
| changed | the converted text from the edited document is taken |
| new | inserted at its position in the heading order |
| missing | reported, **never deleted automatically** |

The first rule is what makes this safe to run every cycle: conversion artefacts only enter sections somebody actually edited, so the file does not degrade a little with each round trip. Comparison is conversion-against-conversion — the baseline went through the identical pipeline — so an untouched section compares byte-identical.

**Incoming structure is normalised to house convention**, not preserved as found. A caption styled as a heading becomes a bold caption line; an image styled as a heading becomes a plain image. Whatever habits the editor had, what lands in the `.qmd` looks like something this skill would have produced.

**Tables are read from the XML, never from pandoc.** Pandoc's docx table reader silently dropped two of three columns from a well-formed table in a real Google Docs export, with no warning. Table dimensions are checked against the package afterwards and the import **fails** on any mismatch.

**Sections containing a code chunk are never overwritten** — what appears in the `.docx` is the chunk's *output*, not its code. They are reported for manual merge.

After importing: review the diff, run `renumber_titles.py`, then `render.py`.

### What to tell reviewers

- Use **Heading 1–5** for section titles. A title typed as bold body text is invisible to the merge.
- Don't renumber sections by hand.
- Tracked changes are accepted automatically on import; resolve anything contentious before sending it back.

### Verifying the loop

`render.py` → `import_docx.py` on the **unedited** output must report every section unchanged and write nothing. If it does not, the round trip is lossy and something needs fixing before it is trusted with a real report.

---

## House Rules

**1. Section numbers are typed into the heading text.**
`# 2.0 METHODOLOGY`, `## 2.1 Sampling`. Quarto's `number-sections` is off, because the front matter's table of contents is a Word field that reads heading text.

**2. Figure and table titles are a bold line above the element, numbered by hand.**
```markdown
**Table 1. Household composition at baseline and midline**

| Indicator | BL | ML |
|---|---|---|
```
Keep them sequential with `renumber_titles.py`. Figures and tables are two independent sequences.

**3. Never use Quarto cross-reference anchors.**
`{#fig-…}` and `{#tbl-…}` make Quarto emit two `w:pPr` elements inside the caption, which the OOXML schema forbids and Word may offer to "repair". **Enforced by lint.**

**4. Never cite a figure or table by number in the prose.**
Write "the table below", or cite the section. Numbers are reassigned whenever content moves; inline references to them go stale silently. **Enforced by lint.**

---

## Anti-Patterns

- **Restyling headings in Word.** The next build overwrites you. Change `profile.yaml`.
- **Editing the rendered `.docx` and shipping that.** The `.qmd` is the source of truth. Edits made in Word are legitimate — that is what a review cycle is — but they have to come back through `import_docx.py`, or the next render discards them.
- **Editing the `.qmd` while a document is out for review.** The importer cannot tell your changes from the reviewers' and will refuse to run. Wait for the file to come back.
- **Adding manual page breaks before top-level sections.** `page_break_before` is set on the Heading 1 style.
- **Hand-formatting a table** — shading cells, bolding the header row. The build stamps the house look onto every table from `profile.yaml`; a plain pipe table comes out right.
- **Running `quarto render` directly and shipping that.** It produces the body with no front matter. Only `render.py` produces the deliverable.
- **Putting design values in the `.qmd` YAML.** They belong in `profile.yaml`, or every report drifts.
- **Adding a table of contents to the body.** It is already in the front matter.
- **Passing `--skip-lint` to get a build through.** Fix the source.

---

## Adding a profile

1. `mkdir profiles/<name>`; author the front matter in Word with `{{TOKEN}}` placeholders where values go.
2. Copy `profiles/long_report/profile.yaml` and edit the values.
3. Structure the Word file as: cover → any logo/notice pages → table of contents → **one empty final section** for the body. Set `frontmatter_sections` to the count before the body.
4. Do **not** embed fonts (File → Options → Save). They are stripped anyway, and they were 4.9 MB of one 5.4 MB example.
5. Verify with `--list-tokens`, then render `examples/01_elements.qmd` against the new profile as a smoke test.

---

## Files

| Path | Role |
|---|---|
| `profiles/<name>/profile.yaml` | **All** typography, colour, table and page values. |
| `profiles/<name>/frontmatter_source.docx` | Hand-authored cover, logo page, TOC, acronyms, with `{{TOKENS}}`. |
| `profiles/<name>/style_specimen.docx` | Reference specimen. Not used by the pipeline — open it to see the intended look. |
| `templates/report_spec.yaml` | Copy per report. |
| `templates/report.qmd` | Copy per report. |
| `examples/01_elements.qmd` + `.docx` | One of every element. The style reference and the smoke test. |
| `scripts/render.py` | **The only supported way to build.** |
| `scripts/make_templates.py` | Tokens + styles → `frontmatter.docx` and `bodyref.docx`. Also `--list-tokens`. |
| `scripts/import_docx.py` | Brings an edited `.docx` back into the `.qmd`, section by section. |
| `scripts/docx_import.py` | Conversion and normalisation, shared by render (baseline) and import. |
| `scripts/renumber_titles.py` | Resequences `**Figure N.**` / `**Table N.**`. |
| `scripts/docx_common.py` | Shared Word-package helpers. |

Build artifacts land in `build/` next to the spec and are disposable. The baseline for the next import lives in `.causal-report/` and **is** committed — without it the round trip has nothing to compare against.

## Requirements

`quarto`, `pandoc`, `python3` with `lxml`, `pyyaml`, `docxcompose` (`pip3 install docxcompose`). The profile font should be installed locally or previews will substitute.

---

## Learnings

*Candidates for promotion into the pipeline above. Per `CLAUDE.md` §7, promote when one recurs two or three times.*

- `2026-09-22` Word silently splits a typed token across runs — `{{subtitle}}` was stored as `{{` + `subtitle` + `}}`. Substitution joins paragraph text before matching and writes back surgically, so fields such as `PAGE` survive. Any future token-based template needs the same treatment.
- `2026-09-22` A hand-authored Word file carries formatting the profile never asked for (small caps on H1 and H3). Style application therefore clears emphasis before setting it, or the profile is not really authoritative.
- `2026-09-22` Quarto writes its output next to the source, which collides with the final output when a report is named after its body. The body is staged into `build/` before stitching.
- `2026-09-22` The same clear-then-set lesson recurred for **indentation**: `Heading1` carried `<w:ind w:left="720"/>` from the hand-authored file and rendered indented. Third instance of "the Word file carries formatting the profile never asked for" — emphasis, then indentation, then spacing. Any pPr or rPr property the profile controls has to be cleared first, not merely overwritten. **Recurrent: promote to the pipeline description at the next version cut.**
- `2026-09-23` A skill has to be tested from `~/.claude/skills/` in an unrelated directory, not only from the repo it was written in. That test found the lint failing on the skill's own template, which every first-time user would have hit.
- `2026-09-22` Order of operations in the importer was the whole game: normalising and trimming the front matter had to happen BEFORE splicing tables, or the acronyms table lines up against the body's first table and shifts every table by one. Found by the idempotency test, not by reading the code.
- `2026-09-22` `\s*` in a table-matching regex swallowed the blank line after a table, because `\s` matches newlines. Use `[ \t]*` when matching to end of line.
- `2026-09-22` Word did not apply a table style's conditional formatting (`firstRow`, `band1Horz`, `band2Horz`) even with correct `tblLook` flags and an intact style definition. Resolved by stamping shading and run properties directly onto rows and cells. Relying on a renderer to interpret a style is a bet; writing the result is not.
