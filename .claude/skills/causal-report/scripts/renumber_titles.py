"""Renumber the manual figure and table titles in a report body.

    python3 renumber_titles.py <body.qmd>            # renumber in place
    python3 renumber_titles.py <body.qmd> --check    # report only, exit 1 if stale

Figures and tables are titled with a bold paragraph ABOVE the element:

    **Table 3. Household composition at baseline and midline**

Two independent running sequences, numbered in document order. Inserting a new
section shifts every downstream number, so this rewalks the file top to bottom
and reassigns Figure 1..K and Table 1..M.

Why titles are manual rather than Quarto cross-references: Quarto emits two
<w:pPr> elements inside a cross-referenced caption, which the OOXML schema
forbids. See SKILL.md.

Why renumbering is safe: house style forbids citing figure or table NUMBERS in
the prose -- write "the table below", or cite the section. render.py enforces
that with a lint pass, so renumbering can never desync an inline reference.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TITLE_RE = re.compile(r"^(\*\*(Figure|Table) )(\d+)(\.)")


def renumber(path: Path, check: bool) -> int:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    counters = {"Figure": 0, "Table": 0}
    changes, out = [], []

    for line in lines:
        m = TITLE_RE.match(line)
        if m:
            kind = m.group(2)
            counters[kind] += 1
            old, new = int(m.group(3)), counters[kind]
            if old != new:
                changes.append((kind, old, new, line.strip()[:64]))
            line = TITLE_RE.sub(lambda mm: f"{mm.group(1)}{counters[kind]}{mm.group(4)}",
                                line, count=1)
        out.append(line)

    print(f"Figures: {counters['Figure']}   Tables: {counters['Table']}   "
          f"renumbered: {len(changes)}")
    for kind, old, new, txt in changes[:40]:
        print(f"  {kind} {old:>3} -> {new:>3}   {txt}")
    if len(changes) > 40:
        print(f"  ... and {len(changes) - 40} more")

    if check:
        return 1 if changes else 0
    if changes:
        path.write_text("".join(out), encoding="utf-8")
        print("written.")
    else:
        print("no changes.")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("qmd", type=Path)
    ap.add_argument("--check", action="store_true",
                    help="report only; do not write. Exit 1 if numbering is stale.")
    args = ap.parse_args()
    if not args.qmd.exists():
        raise SystemExit(f"not found: {args.qmd}")
    sys.exit(renumber(args.qmd, args.check))


if __name__ == "__main__":
    main()
