# Deck-Building Learnings

This file captures learnings for producing on-brand PowerPoint decks programmatically with `python-pptx`. Carried into the scaffold as a craft reference: these rules were paid for once and should not have to be re-derived on the next project.

---

## [2026-09-10] — Editing PowerPoint decks in place: donor cloning, and add-before-delete

**Summary::** Decks that inherit a Google-Slides-exported master carry their formatting in run-level XML properties. `python-pptx` will not reproduce any of it if you create shapes or runs from scratch — you get Calibri 18pt black on a Montserrat deck. The working pattern is to edit a *copy of an existing deck* rather than author one, inheriting every styling decision from paragraphs that already exist.

**Tags:** #coding_architecture, #ai_agents, #visualization

---

### The pattern that works

1. **Inspect → edit in place → verify.** Never create shapes or styling from scratch. Every edit either replaces text inside runs that already exist, or rebuilds a text frame from *that frame's own paragraphs*, deep-copied, so font, size, colour and bullet level are inherited exactly. This is "donor-paragraph cloning" and it is the whole trick.

2. **Normalize run-level overrides after cloning.** If the donor paragraph was bold, the clone is bold — including sub-bullets that should not be. Set or strip the `b` attribute per run explicitly. Skipping this produced a visibly wrong slide.

3. **To add a slide, clone a text slide rather than adding a blank one.** `add_slide()` gives empty placeholders with no donor paragraphs, so there is nothing to inherit from. Deep-copying an existing slide's shape tree onto a new slide gives correctly-styled runs to reshape. This works only for text slides — a picture's `r:embed` would dangle. Use `add_picture` on a fresh slide for figures.

4. **⚠️ Add every slide BEFORE deleting any.** `python-pptx` derives a new slide's part name from the current slide count. Delete first and the additions reuse the part names the deletions just freed, writing **duplicate entries into the `.pptx` zip** (`Duplicate name: 'ppt/slides/slide28.xml'`). The file may still save and may still open — this is the failure most likely to reach a client unnoticed.

5. **Reorder by re-appending.** lxml `append` *moves* an existing element, so appending every slide id in the desired sequence rewrites the order. Capture the id list before you start.

### Verification, and one trap

Always run the structural dump **against the built deck**, never the template. On one occasion an inspector silently ignored its CLI argument and dumped the pristine template instead, which made the verification step vacuous while appearing to pass. **Give the inspector no default path.**

Then assert on things that would actually be wrong: expected slide count, zero surviving source-project text, bold only on lead runs, every picture inside the slide bounds, no duplicate zip parts. Treat warnings as failures.

**Validate the permutation.** Making the reorder function reject anything that is not a true permutation of `0..n-1` caught a slide that had been silently orphaned — it would otherwise have shipped in the wrong place, or not at all.

### The durable point

On the project this was written from, the deck pipeline lived in a session scratchpad for five weeks and had to be reconstructed from session transcripts **twice**. Anything reused across sessions belongs in the repo (`04_scripts/01_functions/`), not the scratchpad. The same reasoning is why this file is in the scaffold.

---
