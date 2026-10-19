#!/usr/bin/env python3
"""Check the page layout of a built report as Microsoft Word renders it.

Why: Word decides where pages break, and no Python library reproduces its
layout. A cover whose bottom block spills onto a second page passes every XML
check and is only visible when the document is opened. This script has Word
export the document to PDF and checks the pages:

  1. the cover is exactly one page: the date and the whole title are on page 1,
     and the page after the cover is the logo ("Prepared for") page;
  2. when the table of contents is included, it follows the logo page;
  3. when it is excluded, the body starts right after the logo page.

It needs macOS with Microsoft Word. Elsewhere, or if Word does not respond, it
says so and exits with code 2 (not checked) rather than 1 (layout problem), so
render.py can tell the two apart.

Safety: all files are written under a dedicated folder inside Word's sandbox
container, with names unique to this run. Only the two files this run created
are removed afterwards, by explicit path; nothing is deleted by pattern.

Usage:  python3 verify_layout.py <report.docx> --date "15 October 2026" [--no-toc]
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
APPLESCRIPT = HERE / "word_export_pdf.applescript"
WORD_APP = Path("/Applications/Microsoft Word.app")
# Word is sandboxed: it can read and write its own container without prompting.
CONTAINER = Path.home() / "Library/Containers/com.microsoft.Word/Data/causal_report_verify"
TIMEOUT_S = 120

OK, LAYOUT_PROBLEM, NOT_CHECKED = 0, 1, 2
# The contents page is recognised by its heading, in capitals as in the front
# matter; body text that merely mentions a table of contents does not match.
TOC_HEADING = "TABLE OF CONTENTS"


def word_available() -> bool:
    return sys.platform == "darwin" and WORD_APP.exists()


def copy_without_field_prompt(src: Path, dst: Path) -> None:
    """Copy the .docx, dropping <w:updateFields>.

    The build sets updateFields so the table of contents refreshes when a person
    opens the file. Word then asks "update fields?", and that dialog would block
    an unattended export. The delivered file is not changed.
    """
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/settings.xml":
                data = re.sub(rb"<w:updateFields[^>]*/>", b"", data)
            zout.writestr(item, data)


def export_pdf(docx: Path) -> tuple[Path | None, str]:
    CONTAINER.mkdir(parents=True, exist_ok=True)
    stamp = f"{time.strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"
    tmp_docx = CONTAINER / f"verify_{stamp}.docx"
    tmp_pdf = CONTAINER / f"verify_{stamp}.pdf"
    copy_without_field_prompt(docx, tmp_docx)
    try:
        proc = subprocess.run(["osascript", str(APPLESCRIPT), str(tmp_docx), str(tmp_pdf)],
                              capture_output=True, text=True, timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return None, (f"Word did not finish within {TIMEOUT_S} s; a dialog may be open in Word "
                      f"(close it and re-run)")
    finally:
        if tmp_docx.exists():
            tmp_docx.unlink()
    if proc.returncode != 0 or not tmp_pdf.exists():
        return None, f"Word could not export the PDF: {proc.stderr.strip() or 'no output'}"
    return tmp_pdf, ""


def page_texts(pdf: Path) -> list[str]:
    from pypdf import PdfReader
    return [(p.extract_text() or "") for p in PdfReader(str(pdf)).pages]


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def check(pages: list[str], date: str, toc: bool, title: str | None = None) -> list[str]:
    problems = []
    if len(pages) < 3:
        return [f"only {len(pages)} pages; expected a cover, a logo page and a body"]
    p1, p2, p3 = (norm(p) for p in pages[:3])
    if norm(date) not in p1:
        problems.append("the cover's date is not on page 1: the cover does not fit on one page")
    if title:
        # The title row has a fixed height; a title too long for it is cut off.
        missing = [w for w in norm(title).split() if w not in p1]
        if missing:
            problems.append(f"part of the title is not visible on the cover ({' '.join(missing[:5])}): "
                            "shorten the title")
    if "prepared for" not in p2:
        where = next((i + 1 for i, p in enumerate(pages) if "prepared for" in norm(p)), None)
        problems.append(f"the logo page should be page 2 but is page {where}: "
                        "the cover spills onto an extra page")
    # A page past the logo page with almost no text is blank apart from its
    # running header ("Title | CAUSAL DESIGN | 3"): a stray page break.
    # The contents page is exempt: its field is filled in when a person opens
    # the file, but not in this unattended export, so it holds only a few words.
    for i, page in enumerate(pages[2:], start=3):
        if TOC_HEADING in page:
            continue
        if len(norm(page).split()) < 8:
            problems.append(f"page {i} is blank apart from its header or footer")
    has_toc = TOC_HEADING in pages[2]
    if toc and not has_toc:
        problems.append("the table of contents should follow the logo page")
    if not toc and has_toc:
        problems.append("the table of contents was excluded but is still in the document")
    return problems


def verify(docx: Path, date: str, toc: bool = True, title: str | None = None) -> tuple[int, str]:
    if not word_available():
        return NOT_CHECKED, "layout not checked: needs macOS with Microsoft Word"
    pdf, err = export_pdf(docx)
    if pdf is None:
        return NOT_CHECKED, f"layout not checked: {err}"
    try:
        pages = page_texts(pdf)
    finally:
        pdf.unlink()
    problems = check(pages, date, toc, title)
    if problems:
        return LAYOUT_PROBLEM, "layout problem:\n  " + "\n  ".join(problems)
    return OK, f"layout checked in Word: {len(pages)} pages; cover fits on page 1"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docx", type=Path)
    ap.add_argument("--date", required=True, help="the cover date, as in the spec")
    ap.add_argument("--no-toc", action="store_true", help="the build excluded the table of contents")
    ap.add_argument("--title", help="the cover title, to check that none of it is cut off")
    args = ap.parse_args()
    code, msg = verify(args.docx.resolve(), args.date, toc=not args.no_toc, title=args.title)
    print(msg)
    sys.exit(code)


if __name__ == "__main__":
    main()
