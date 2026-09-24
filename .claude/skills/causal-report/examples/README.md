# Examples

## `01_elements` — one of every element

The style reference and the pipeline's smoke test.

```bash
cd examples
python3 ../scripts/render.py --spec report_spec.yaml
```

**Read `01_elements.qmd`** to learn the markup. **Open `01_elements.docx`** to see what it produces. Both are committed, so neither can drift from the other without a rebuild catching it.

It covers: all five heading levels · body text · bulleted and numbered lists · a table with the house title convention · a wider table · a figure title · inline and display mathematics · a block quotation · a footnote · bold, italic and inline code.

If this renders and validates, the pipeline works. It is the first thing to run after changing a profile.

### What to look for when you open it

| | |
|---|---|
| Cover | Title, client and date filled from `report_spec.yaml`, not `{{TOKENS}}` |
| Footer | The subtitle, from a token that Word had split across three runs |
| Headings | H1 19pt blue starting its own page · H2 15pt · H3 13pt · H4 red small caps · H5 black underlined small caps |
| Tables | Blue header row, white bold type, body rows banded white and pale blue — from a plain pipe table with no extra markup |
| Equations | Native Word equations you can click into and edit, not images |
| Table of contents | Empty until you click it and press **F9** — it is a live Word field |

`build/` holds disposable intermediates and is not committed.
