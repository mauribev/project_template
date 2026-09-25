# causal-report — why the pipeline is built this way

Rationale behind the design decisions in `SKILL.md`. Everything here was verified by rendering and inspecting the resulting XML, not inferred from documentation — there is no LibreOffice on the build machine, so structural inspection is the only check available short of opening the file in Word.

---

## 1. Why front matter is a separate Word file rather than generated

Quarto produces **uniform single-section documents**. A report's first pages are a multi-section Word layout: a full-page cover with graphics, a logo page, a table-of-contents page. Asked to produce that, Quarto repeats the cover graphic on every page.

So the front matter is authored in Word, where that kind of layout belongs, and kept as a static `.docx`. The body is authored in Quarto. A stitch step merges them.

The merge uses `docxcompose`, which produces a **flat** document — one that opens correctly in Google Docs as well as Word. That matters because `CLAUDE.md` specifies Word output "for human review on Google Docs".

## 2. Why two artifacts are built from one source

`make_templates.py` emits both `frontmatter.docx` (the stitch master) and `bodyref.docx` (Quarto's `--reference-doc`).

The reason is a pandoc behaviour that is easy to get wrong: **pandoc copies the first `sectPr` it finds in a reference document.** Handed the front matter as-is, it takes the *cover* section's headers and footers and applies them to every page of the body. `bodyref.docx` is therefore a stripped twin — same styles, but its body is emptied down to a single section carrying the *running* chrome.

Building both in one pass from one source is what stops them disagreeing about styling.

## 3. Why styles are grafted from pandoc's own reference document

**Pandoc does not synthesise missing styles.** Its docx writer references roughly fifty style ids; a hand-authored Word file typically defines twenty or thirty. The rest — `BodyText`, `FirstParagraph`, `Compact`, `ImageCaption`, `TableCaption`, `Hyperlink`, `FootnoteText` and others — end up referenced but undefined.

Word does not error on this. It silently falls back through the theme, in practice to Cambria. The symptom is a report whose headings are correct and whose body text is quietly the wrong font.

So the build takes `pandoc --print-default-data-file reference.docx` as a style donor and copies in everything the front matter lacks, rewriting the donor's theme-driven font attributes (`w:asciiTheme="minorHAnsi"` and friends) to name the profile font directly. The theme's own Latin fonts are set as well, belt and braces.

## 4. Why embedded fonts are stripped

Word can embed fonts so a document renders identically anywhere. Two reasons the pipeline removes them:

**They break the package.** Pandoc copies embedded font parts but regenerates `[Content_Types].xml` from a fixed template. Where the embedded parts are `.ttf`, that template declares no `ttf` default and the parts end up with no content type at all — an invalid OPC package, which Word responds to by offering to repair the file.

**They dominate the file size.** One example front matter was 5.4 MB, of which 4.9 MB was seven `.odttf` font parts. The document itself was under 500 KB.

The font is named explicitly instead, with an `altName` to steer substitution where it is not installed.

## 5. Why tables need no markup

The house table look — blue header row with white bold type, body rows banded white and pale blue, borderless — is defined **once** as a Word table style called `Table`, using `tblStylePr` conditional formatting for `firstRow`, `band1Horz` and `band2Horz`.

`Table` is precisely the style id pandoc assigns to every table it writes, and pandoc also emits:

```xml
<w:tblLook w:firstRow="1" w:lastRow="0" w:firstColumn="0"
           w:lastColumn="0" w:noHBand="0" w:noVBand="0" w:val="0020"/>
```

`firstRow="1"` and `noHBand="0"` are exactly the flags that tell Word to apply the `firstRow` and horizontal-band rules from the style. So an ordinary pipe table in the `.qmd` acquires the full house look with nothing added.

This replaces what would otherwise be a table-construction function library. The specimen table that defined the look was originally built in R; none of that machinery is needed to reproduce it.

## 5a. Why the table look is stamped onto cells as well as defined as a style

Section 5 is how it *should* work, and the style is still defined that way. It did not hold up in Word: the header row rendered black instead of white, and no banding appeared at all. The style definition was intact in the output and the `tblLook` flags were right, so the conditional-format engine simply was not applying it — the style's base `rPr` colour won for the header text.

Chasing that down without a renderer to test against is guesswork. So `stamp_table_formatting()` writes the formatting **directly onto every row and cell**: a `w:shd` fill per cell, and run properties on every header run. Deterministic, renderer-independent, and verifiable by inspecting the output.

The values still come from `profile.yaml`, so nothing becomes less pre-specified — it is applied rather than requested and hoped for. The style definition is kept too (now `basedOn` `TableNormal`, with explicit band sizes), so the table still reads correctly to anyone who inspects or restyles it in Word's UI.

## 5b. Why the profile lists every style, not just headings

The first version specified `Normal` and `Heading1`–`Heading5`. That left everything else — paragraphs, list items, block quotations, captions — to whatever the grafted pandoc defaults happened to be, which meant part of the document's appearance was outside the profile's control and invisible in it.

The profile now names all twelve styles pandoc actually emits for a report body: `Normal`, `BodyText`, `FirstParagraph`, `Compact`, `BlockText`, `ImageCaption`, `TableCaption` and the five headings. That is the complete set, not a sample, so "everything is in the YAML" is literally true.

One deliberate omission: `Compact` gets no `indent`. List indentation comes from `numbering.xml` via each item's `numPr`, and a paragraph-level indent on `Compact` would override it and flatten every list.

## 6. Why figure and table numbers are manual

Quarto's cross-reference anchors (`{#fig-…}`, `{#tbl-…}`) are unusable in `.docx`. A cross-referenced caption comes out as:

```xml
<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:pPr> … <w:pStyle w:val="ImageCaption"/> </w:pPr> …
```

Two `w:pPr` elements in one paragraph. `CT_P` permits at most one, and `w:pStyle` is not first in the second. Reproduced with stock Quarto 1.9.36 and **no** reference document, so it is not a template problem and no template change addresses it. Plain captions render clean.

Automatic numbering is not worth the risk of Word offering to repair a funder deliverable, so titles are manual bold lines and `renumber_titles.py` resequences them.

The editorial rule that makes renumbering safe — **never cite a figure or table by number in the prose** — is enforced by `render.py`'s lint pass rather than left to discipline. Without it, renumbering silently desyncs every inline reference.

## 7. Why token substitution is surgical rather than a string replace

Word splits typed text across runs for reasons of its own — spell-check state, formatting history, revision tracking. A token typed as `{{subtitle}}` was found stored as **three separate runs**: `{{`, `subtitle`, `}}`. A regex over the raw XML finds nothing, replaces nothing, and reports success.

So substitution works on the **joined text of each paragraph**. A token contained in one run is replaced in place; a token spanning several has its replacement written into the first and only its own characters removed from the rest. Other runs, and any field codes such as `PAGE`, are untouched.

The build then asserts that **no `{{` survives anywhere in the package**. A document cannot reach a client with `{{TITLE}}` on its cover.

## 8. Why the profile clears formatting before setting it

A hand-authored Word file carries formatting nobody asked for — the specimen had small caps on Heading 1 and Heading 3, which the profile never specified. If style application only *adds* attributes, the YAML is not really authoritative and the document quietly keeps whatever Word happened to hold.

So emphasis (`b`, `i`, `smallCaps`, `caps`, `u`, `strike`) and `pageBreakBefore` are removed before the profile's own values are written. The consequence, stated in `SKILL.md`: restyling a heading in Word does not survive the next build.

## 9. What validation actually checks

With no renderer available, structural checks are the real guarantee. `validate_package()` verifies that every part has a declared content type, every non-external relationship resolves to a file that exists, every XML part parses, every style the document references is defined, and no paragraph carries two `w:pPr` elements.

`render.py` **deletes its output** if validation fails, rather than leaving a plausible-looking file that Word might reject.

---

## Sources

- The pipeline's split-document architecture derives from the BRCiS III midline long-report build (`00_make_frontmatter.py` / `02_render.py` / `renumber_titles.py`), which proved it on a 1,311-line body with 144 headings.
- Pandoc and Quarto behaviours above were verified against pandoc 3.9.0.2 and Quarto 1.9.36 on 2026-09-21/22.
