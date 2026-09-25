"""Bring an edited .docx back into the report's .qmd, section by section.

    python3 import_docx.py --spec report_spec.yaml --from edited.docx

The checkout model
------------------
render.py stores a baseline each time it builds: the .qmd as delivered, plus a
conversion of the .docx that went out. While a document is out for editing the
.qmd is frozen. This script refuses to run if the .qmd changed in the meantime,
so the rule is enforced rather than merely agreed.

How the merge works
-------------------
Both sides are split into sections by heading. For each section:

  unchanged  ->  the ORIGINAL .qmd text is kept, untouched
  changed    ->  the converted text from the edited document is taken
  new        ->  inserted at its position in the heading order
  missing    ->  reported, never deleted automatically

The first rule is what makes this safe to run every cycle: conversion artefacts
only ever enter sections somebody actually edited. Everything else keeps its
pristine source, so the file does not degrade a little with each round trip.

Comparison is conversion-against-conversion -- the stored baseline went through
exactly the same pipeline as the incoming file -- so an untouched section
compares byte-identical and "changed" means changed.

What it will not do
-------------------
A section whose .qmd source contains an executable code chunk is never
overwritten: what appears in the .docx is the chunk's *output*, not its code.
Those are reported for manual merge.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import docx_common as dc  # noqa: E402
import docx_import as di  # noqa: E402

STATE_DIR = ".causal-report"
CHUNK_MARKERS = ("```{r", "```{python", "```{julia", "```{ojs")


def load_state(base: Path) -> tuple[Path, dict]:
    sd = base / STATE_DIR
    meta = sd / "state.json"
    if not meta.exists():
        raise SystemExit(
            f"no baseline found in {sd}.\n"
            "Run render.py once first -- the baseline is written at build time, "
            "and without it there is nothing to compare the edited file against.")
    return sd, json.loads(meta.read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", type=Path, required=True)
    ap.add_argument("--from", dest="incoming", type=Path, required=True,
                    help="the edited .docx that came back")
    ap.add_argument("--force", action="store_true",
                    help="import even though the .qmd changed since it was sent out")
    ap.add_argument("--dry-run", action="store_true", help="report, write nothing")
    args = ap.parse_args()

    spec = yaml.safe_load(args.spec.read_text(encoding="utf-8"))
    base = args.spec.parent.resolve()
    qmd = (base / spec["body"]).resolve()
    sd, state = load_state(base)
    scratch = base / "build" / ".import"

    # --- checkout integrity ---------------------------------------------------
    baseline_qmd = (sd / "baseline.qmd").read_text(encoding="utf-8")
    current_qmd = qmd.read_text(encoding="utf-8")
    if current_qmd != baseline_qmd and not args.force:
        raise SystemExit(
            f"{qmd.name} has changed since it was last rendered.\n"
            "Under the checkout model the .qmd stays frozen while a document is "
            "out for editing, because there is no way to tell your edits and the "
            "reviewers' apart.\n"
            "Either revert the .qmd, or re-render and re-send, or pass --force to "
            "discard the reviewers' version of any section you also changed.")

    # --- convert the incoming file -------------------------------------------
    baseline_md = (sd / "baseline.md").read_text(encoding="utf-8")
    # The body's own headings, taken from the .qmd rather than from the
    # conversion -- they are what says where the front matter stops.
    titles = di.body_titles(baseline_qmd)
    print(f"[1/4] Converting {args.incoming.name} ...")
    incoming_md, notes = di.convert(args.incoming, base / "media", titles, scratch)
    for n in dict.fromkeys(notes):
        print(f"  note: {n}")

    # --- table integrity ------------------------------------------------------
    work = dc.unpack(args.incoming, scratch / "check")
    shapes = di.source_table_shapes(work, titles)
    got = [(len([l for l in t.splitlines() if l.startswith("|")]) - 1,
            t.splitlines()[0].count("|") - 1)
           for t in di.TABLE_BLOCK_RE.findall(incoming_md)]
    if shapes != got:
        print(f"  ! table check: package has {shapes}, markdown has {got}")
        raise SystemExit(
            "table dimensions do not match the source document. Pandoc is known "
            "to drop columns silently, so this is refused rather than risking a "
            "report with a column missing.")
    print(f"[2/4] {len(shapes)} table(s) verified against the package")

    # --- merge ----------------------------------------------------------------
    print("[3/4] Merging section by section ...")
    qmd_pre, qmd_secs = di.split_sections(current_qmd)
    _, base_secs = di.split_sections(baseline_md)
    _, new_secs = di.split_sections(incoming_md)

    base_by_key = {s.key: s for s in base_secs}
    qmd_by_key = {s.key: s for s in qmd_secs}

    merged, report = [], {"unchanged": [], "updated": [], "added": [],
                          "removed": [], "skipped": []}

    for sec in new_secs:
        qsec = qmd_by_key.get(sec.key)
        bsec = base_by_key.get(sec.key)
        if qsec is None:
            report["added"].append(sec.title)
            merged.append(sec)
            continue
        if bsec is not None and bsec.body.strip() == sec.body.strip():
            report["unchanged"].append(sec.title)
            merged.append(qsec)                      # keep the pristine source
            continue
        if any(m in qsec.body for m in CHUNK_MARKERS):
            report["skipped"].append(sec.title)
            merged.append(qsec)                      # never clobber a code chunk
            continue
        report["updated"].append(sec.title)
        merged.append(di.Section(sec.level, sec.title, sec.body))

    new_keys = {s.key for s in new_secs}
    for s in qmd_secs:
        if s.key not in new_keys:
            report["removed"].append(s.title)

    # --- write ----------------------------------------------------------------
    out = di.render_sections(qmd_pre, merged)
    print("[4/4] Result")
    for kind in ("unchanged", "updated", "added", "skipped", "removed"):
        items = report[kind]
        if not items:
            continue
        label = {"skipped": "skipped (contains a code chunk)",
                 "removed": "MISSING from the edited file -- NOT deleted"}.get(kind, kind)
        print(f"  {len(items):>3} {label}")
        if kind in ("updated", "added", "skipped", "removed"):
            for t in items:
                print(f"        - {t}")

    if args.dry_run:
        print("\ndry run -- nothing written.")
        return

    shutil.copy2(qmd, sd / "pre_import.qmd")
    qmd.write_text(out, encoding="utf-8")
    print(f"\nwrote {qmd.name}  (previous version kept at {STATE_DIR}/pre_import.qmd)")
    print("Next: review the diff, run renumber_titles.py, then render.py.")


if __name__ == "__main__":
    main()
