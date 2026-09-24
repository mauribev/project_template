"""Convert a .docx back into house-convention Markdown.

Used in two places, with identical settings in both, which is the point:

* render.py    -- converts the report it just produced, and stores the result as
                  the comparison baseline.
* import_docx.py -- converts the edited copy that came back.

Because both sides go through the same pipeline, a section nobody touched comes
out byte-identical on both, and "changed" means changed rather than "converted
slightly differently this time".

Two things this does that a plain pandoc call does not:

1. **Tables are read from the XML, not from pandoc.** Pandoc's docx table reader
   silently dropped two of three columns from a well-formed table in a real
   Google Docs export -- an 11x3 table came back 11x1, with the other columns
   gone and no warning. Tables are therefore extracted directly and spliced over
   pandoc's versions. The counts are checked afterwards.

2. **Incoming structure is normalised to house convention**, not preserved as
   found. A caption styled as a heading becomes a bold caption line; an image
   styled as a heading becomes a plain image. What comes back looks like
   something this skill would have produced, whatever habits the editor had.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

import docx_common as dc

# Kept identical in both directions. grid/simple/multiline are disabled so that
# pandoc cannot emit a table shape we do not round-trip; ours are spliced in
# afterwards regardless.
PANDOC_TO = "markdown+pipe_tables-simple_tables-multiline_tables-grid_tables"
PANDOC_ARGS = ["--track-changes=accept", "--wrap=none", "--columns=999"]

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
CAPTION_HEADING_RE = re.compile(r"^#{1,6}\s+((?:Figure|Table)\s+\d+)\s*[.:]\s*(.+?)\s*$", re.I)
IMAGE_HEADING_RE = re.compile(r"^#{1,6}\s+(!\[.*)$")
# [ \t]* rather than \s* on purpose: \s matches newlines, so the greedy form
# swallowed the blank line after a table and welded it to the next paragraph.
TABLE_BLOCK_RE = re.compile(r"(?:^\|.*\|[ \t]*$\n)+", re.M)


# --------------------------------------------------------------------------- #
# Tables, read straight from the package
# --------------------------------------------------------------------------- #
def _cell_text(tc) -> str:
    """Flatten a cell to one line. Pipe tables cannot hold block content."""
    parts = ["".join(t.text or "" for t in p.iter(dc.q("t")))
             for p in tc.iter(dc.q("p"))]
    return " ".join(" ".join(parts).split())


def _as_pipe_table(rows: list[list[str]]) -> str:
    width = [max(len(r[i]) if i < len(r) else 0 for r in rows)
             for i in range(max(len(r) for r in rows))]
    width = [max(w, 3) for w in width]

    def line(cells):
        cells = list(cells) + [""] * (len(width) - len(cells))
        return "| " + " | ".join(c.ljust(width[i]) for i, c in enumerate(cells)) + " |"

    out = [line(rows[0]), "|" + "|".join("-" * (w + 2) for w in width) + "|"]
    out += [line(r) for r in rows[1:]]
    return "\n".join(out)


def extract_body_tables(workdir: Path, body_titles: set[str]) -> list[str]:
    """Every table that sits after the body starts, as a pipe table.

    Front-matter tables -- the cover block, the acronyms list -- are skipped, so
    the order here matches the order of tables in the converted body.
    """
    tree = dc.parse(workdir / "word" / "document.xml")
    body = tree.getroot().find(dc.q("body"))
    started, tables = not body_titles, []

    for el in body.iter():
        if el.tag == dc.q("p") and not started:
            style = el.find(f"{dc.q('pPr')}/{dc.q('pStyle')}")
            if style is not None and style.get(dc.q("val"), "").startswith("Heading"):
                text = _norm_title("".join(t.text or "" for t in el.iter(dc.q("t"))))
                if text in body_titles:
                    started = True
        elif el.tag == dc.q("tbl") and started:
            rows = [[_cell_text(tc) for tc in tr.findall(dc.q("tc"))]
                    for tr in el.findall(dc.q("tr"))]
            rows = [r for r in rows if any(c for c in r)]
            if rows:
                tables.append(_as_pipe_table(rows))
    return tables


def source_table_shapes(workdir: Path, body_titles: set[str]) -> list[tuple[int, int]]:
    """(rows, cols) for each body table, for checking nothing was lost."""
    shapes = []
    for t in extract_body_tables(workdir, body_titles):
        lines = [ln for ln in t.splitlines() if ln.startswith("|")]
        shapes.append((len(lines) - 1, lines[0].count("|") - 1))
    return shapes


# --------------------------------------------------------------------------- #
# Conversion + normalisation
# --------------------------------------------------------------------------- #
def _norm_title(s: str) -> str:
    return " ".join(s.split()).strip().lower()


def normalise(md: str) -> str:
    """Rewrite incoming structure into the conventions this skill produces."""
    out, notes = [], []
    for line in md.splitlines():
        cap = CAPTION_HEADING_RE.match(line)
        if cap:
            # A caption styled as a heading becomes a bold caption line.
            out.append(f"**{cap.group(1).title()}. {cap.group(2)}**")
            notes.append(f"caption heading normalised: {cap.group(1)}")
            continue
        img = IMAGE_HEADING_RE.match(line)
        if img:
            out.append(img.group(1))
            notes.append("image styled as a heading turned into a plain image")
            continue
        out.append(line)

    # Conversion artefacts: pandoc's backslash escapes, and --- for an em dash.
    # The dash substitution has to skip table rows, whose separator lines are
    # made of hyphens -- rewriting those would destroy the table.
    fixed = []
    for line in out:
        line = re.sub(r"\\([%$#&_~^])", r"\1", line)
        if not line.lstrip().startswith("|"):
            line = line.replace("---", "—")
        fixed.append(line.replace(" ", " "))

    text = re.sub(r"\n{3,}", "\n\n", "\n".join(fixed))
    normalise.notes = notes
    return text.strip() + "\n"


def trim_to_body(md: str, body_titles: set[str]) -> str:
    """Drop the front matter -- cover, table of contents, acronyms.

    A stitched report converts back as one document, so everything the front
    matter contributed arrives too. The body begins at the first heading the
    .qmd itself declares; anything before that came from the front matter and
    is not ours to merge.
    """
    lines = md.splitlines()
    for i, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if m and _norm_title(m.group(2)) in body_titles:
            return "\n".join(lines[i:]).strip() + "\n"
    return md


def convert(docx: Path, media_dir: Path, body_titles: set[str],
            scratch: Path) -> tuple[str, list[str]]:
    """docx -> house-convention Markdown. Returns (markdown, notes)."""
    scratch.mkdir(parents=True, exist_ok=True)
    md_path = scratch / (docx.stem + ".raw.md")
    subprocess.run(["pandoc", str(docx), "-t", PANDOC_TO, *PANDOC_ARGS,
                    f"--extract-media={media_dir}", "-o", str(md_path)], check=True)
    md = md_path.read_text(encoding="utf-8")
    notes: list[str] = []

    # Order matters. Normalise and trim to the body FIRST, so that the tables
    # left in the markdown are the body's own. Splicing before the trim lines
    # the front matter's acronyms table up against the body's first table and
    # shifts every table by one.
    md = trim_to_body(normalise(md), body_titles)
    notes += getattr(normalise, "notes", [])

    # Now replace pandoc's tables with ones read from the XML, in order.
    work = dc.unpack(docx, scratch / (docx.stem + ".unz"))
    good = extract_body_tables(work, body_titles)
    found = TABLE_BLOCK_RE.findall(md)
    if len(found) != len(good):
        notes.append(f"pandoc produced {len(found)} body table(s), the package "
                     f"holds {len(good)} -- splicing by position")
    it = iter(good)
    md = TABLE_BLOCK_RE.sub(lambda m: (next(it, m.group(0)).rstrip() + "\n"), md)
    return md, notes


# --------------------------------------------------------------------------- #
# Sections
# --------------------------------------------------------------------------- #
@dataclass
class Section:
    level: int
    title: str
    body: str = ""
    raw: str = ""
    children: list = field(default_factory=list)

    @property
    def key(self) -> str:
        return f"{self.level}:{_norm_title(self.title)}"


def split_sections(md: str) -> tuple[str, list[Section]]:
    """Return (preamble, sections). Preamble is everything before heading one."""
    lines = md.splitlines()
    first = next((i for i, l in enumerate(lines) if HEADING_RE.match(l)), len(lines))
    preamble = "\n".join(lines[:first]).rstrip()

    sections, cur = [], None
    for line in lines[first:]:
        m = HEADING_RE.match(line)
        if m:
            if cur:
                sections.append(cur)
            cur = Section(level=len(m.group(1)), title=m.group(2), raw=line)
        elif cur:
            cur.body += line + "\n"
    if cur:
        sections.append(cur)
    for s in sections:
        s.body = s.body.strip("\n")
    return preamble, sections


def body_titles(md: str) -> set[str]:
    _, secs = split_sections(md)
    return {_norm_title(s.title) for s in secs}


def render_sections(preamble: str, sections: list[Section]) -> str:
    parts = [preamble] if preamble.strip() else []
    for s in sections:
        parts.append(f"{'#' * s.level} {s.title}")
        if s.body.strip():
            parts.append(s.body.strip("\n"))
    return "\n\n".join(parts).strip() + "\n"
