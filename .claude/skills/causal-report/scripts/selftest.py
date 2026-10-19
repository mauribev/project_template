#!/usr/bin/env python3
"""Build the example report in every front-matter configuration and check each in Word.

Run this after any change to the skill (scripts, profile or front matter):

    python3 <skill>/scripts/selftest.py

Each case renders examples/01_elements.qmd through render.py, which ends with
the Word layout check (verify_layout.py, via --check-layout). It opens Word
repeatedly in the background, so run it only when nobody is working in Word. The cases cover what has broken
before or could: a long two-line title, a client line long enough to need the
automatic font reduction, and each combination of the table of contents and
acronyms switches. A case passes only if render.py exits cleanly and the layout
check ran in Word and found no problem.

Everything is written to a new folder under the system temp directory, printed
at the end. Nothing is deleted.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

SKILL = Path(__file__).resolve().parents[1]
BODY = SKILL / "examples" / "01_elements.qmd"

SHORT = {"TITLE": "Causal Design Report Template", "SUBTITLE": "Style Reference",
         "CLIENT": "Causal Design", "COUNTRY": "Example", "DATE": "1 January 2027"}
LONG = {"TITLE": "Impact Evaluation of the Example Livelihood Programme\nFinancial Proposal",
        "SUBTITLE": "Financial Proposal", "CLIENT": "Sample Fund",
        "COUNTRY": "Northland and Southland", "DATE": "15 October 2026"}
VERY_LONG_CLIENT = {**LONG, "CLIENT": "Ministry of Agriculture, Livestock and Food",
                    "COUNTRY": "Northland, Southland and East Coast"}

CASES = [
    ("full front matter, short values", SHORT, {}),
    ("full front matter, two-line title", LONG, {}),
    ("no TOC, acronyms kept", LONG, {"toc": False}),
    ("TOC kept, no acronyms", LONG, {"acronyms": False}),
    ("neither, two-line title", LONG, {"toc": False, "acronyms": False}),
    ("neither, very long client line", VERY_LONG_CLIENT, {"toc": False, "acronyms": False}),
]


def main() -> None:
    root = Path(tempfile.mkdtemp(prefix="causal_report_selftest_"))
    results = []
    for i, (name, values, include) in enumerate(CASES, 1):
        case = root / f"case{i}"
        case.mkdir()
        shutil.copy2(BODY, case / BODY.name)
        spec = {"profile": "long_report", "body": BODY.name, "out": f"case{i}.docx", "values": values}
        if include:
            spec["include"] = include
        if include.get("acronyms", True):
            spec["acronyms"] = {"CD": "Causal Design", "GPS": "Global Positioning System",
                                "MDE": "minimum detectable effect"}
        (case / "report_spec.yaml").write_text(yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
        proc = subprocess.run([sys.executable, str(SKILL / "scripts" / "render.py"),
                               "--spec", str(case / "report_spec.yaml"), "--check-layout"],
                              cwd=case, capture_output=True, text=True)
        lines = (proc.stdout + proc.stderr).splitlines()
        layout = [ln.strip() for ln in lines if ln.strip().startswith(("layout", "the ", "part of", "page "))]
        notes = [ln.strip() for ln in lines if "cover line of" in ln or "left out:" in ln]
        checked = any(ln.startswith("layout checked in Word") for ln in layout)
        ok = proc.returncode == 0 and checked
        results.append(ok)
        print(f"[{'PASS' if ok else 'FAIL'}] {i}. {name}")
        for ln in notes + layout:
            print(f"        {ln}")
        if proc.returncode != 0 and not layout:
            print("        " + "\n        ".join(lines[-8:]))
    print(f"\n{sum(results)}/{len(results)} cases passed. Builds in {root}")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
