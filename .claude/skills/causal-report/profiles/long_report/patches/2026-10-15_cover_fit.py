#!/usr/bin/env python3
"""One-time patch to frontmatter_source.docx: make the cover always fit on one page.

Problem (found 2026-10-15 on the Matthew 6:3 financial proposal and EA): the
cover's bottom block ("CLIENT, COUNTRY" and the date) sat in a 2.7-inch cell at
14.5 pt, so "Matthew 6:3, Guatemala and Honduras" wrapped to three lines. The
row was only a minimum height, so it grew, and the date spilled onto a second
cover page. Word renders this; no XML check sees it.

Changes, all to the cover (section 1):
  1. Bottom row: the empty left cell is removed and the text cell spans the full
     width, so the client line has room for about 40 characters.
  2. Both rows get an EXACT height (the title row 10,700 twips, the bottom row
     1,450), so no content can make the table taller than its design. The bottom
     row holds the spacer line plus up to two client lines and the date.
  3. The empty paragraph before the table and the one holding the section break
     after it are shrunk to 2 pt, so they no longer take a full line each.

The original file is kept as frontmatter_source_v1.docx. Run once, from the
skill directory:  python3 profiles/long_report/patches/2026-10-15_cover_fit.py
"""
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROFILE = HERE.parent
sys.path.insert(0, str(PROFILE.parents[1] / "scripts"))
import docx_common as dc  # noqa: E402
from lxml import etree  # noqa: E402

SRC = PROFILE / "frontmatter_source.docx"
ARCHIVE = PROFILE / "frontmatter_source_v1.docx"
TITLE_ROW_TWIPS = "10700"
BOTTOM_ROW_TWIPS = "1450"
q = dc.q

if ARCHIVE.exists():
    raise SystemExit(f"{ARCHIVE.name} already exists: the patch has been applied")
shutil.copy2(SRC, ARCHIVE)

work = dc.unpack(SRC, Path("/tmp") / "cdr_patch_cover")
doc = work / "word" / "document.xml"
tree = dc.parse(doc)
body = tree.getroot().find(q("body"))
children = list(body)

table = children[1]
assert table.tag == q("tbl") and "{{TITLE}}" in "".join(table.itertext()), "cover table not where expected"
rows = table.findall(q("tr"))
assert len(rows) == 2, "cover table should have two rows"

# 1 and 2: exact row heights
for row, height in zip(rows, (TITLE_ROW_TWIPS, BOTTOM_ROW_TWIPS)):
    tr_h = row.find(f"{q('trPr')}/{q('trHeight')}")
    tr_h.set(q("val"), height)
    tr_h.set(q("hRule"), "exact")

# 1: bottom row -- drop the empty left cell, let the text cell span both columns
cells = rows[1].findall(q("tc"))
assert len(cells) == 2 and not "".join(cells[0].itertext()).strip(), "unexpected bottom row"
rows[1].remove(cells[0])
tc_pr = cells[1].find(q("tcPr"))
tc_pr.find(q("tcW")).set(q("w"), "10422")
span = etree.SubElement(tc_pr, q("gridSpan"))
span.set(q("val"), "2")
tc_pr.remove(span)
tc_pr.insert(1, span)          # schema order: tcW, gridSpan, ..., vAlign

# 3: shrink the paragraph before the table and the section-break paragraph after it
def shrink(p):
    p_pr = p.find(q("pPr"))
    if p_pr is None:
        p_pr = etree.SubElement(p, q("pPr"))
        p.remove(p_pr)
        p.insert(0, p_pr)
    for old in p_pr.findall(q("spacing")):
        p_pr.remove(old)
    spacing = etree.Element(q("spacing"))
    for k, v in (("before", "0"), ("after", "0"), ("line", "40"), ("lineRule", "exact")):
        spacing.set(q(k), v)
    # Schema order: pStyle, keepNext..., spacing comes before ind/jc/rPr/sectPr.
    anchor = next((c for c in p_pr if etree.QName(c).localname in
                   ("ind", "contextualSpacing", "jc", "rPr", "sectPr")), None)
    if anchor is not None:
        anchor.addprevious(spacing)
    else:
        p_pr.append(spacing)
    r_pr = p_pr.find(q("rPr"))
    if r_pr is None:
        r_pr = etree.Element(q("rPr"))
        sect = p_pr.find(q("sectPr"))
        if sect is not None:
            sect.addprevious(r_pr)
        else:
            p_pr.append(r_pr)
    for tag in ("sz", "szCs"):
        for old in r_pr.findall(q(tag)):
            r_pr.remove(old)
        el = etree.SubElement(r_pr, q(tag))
        el.set(q("val"), "4")

assert children[0].tag == q("p") and children[2].tag == q("p")
assert children[2].find(f".//{q('sectPr')}") is not None
shrink(children[0])
shrink(children[2])

dc.save(tree, doc)
problems = dc.validate_package(work)
if problems:
    shutil.copy2(ARCHIVE, SRC)
    ARCHIVE.unlink()
    raise SystemExit("patched file failed validation, original restored:\n  " + "\n  ".join(problems))
dc.repack(work, SRC)
print(f"patched {SRC.name}; original kept as {ARCHIVE.name}")
