"""Produce the finished report: build templates, render the body, stitch, validate.

    python3 render.py --spec <report_spec.yaml>

This is the ONLY supported way to produce the deliverable. It is one command on
purpose -- there are no flags to get wrong, and every check runs every time.

Steps
-----
1. make_templates.py  -- fill the front matter's tokens, write profile.yaml's
                         styling into the Word styles, emit frontmatter.docx and
                         bodyref.docx into build/
2. quarto render      -- the body .qmd against build/bodyref.docx, so the body
                         is already styled before it is merged
3. strip tblHeader    -- table header rows repeat on every page by default in
                         some table engines; the house style shows them once
4. docxcompose        -- prepend the front matter, producing a FLAT .docx that
                         opens correctly in Word and in Google Docs
5. validate           -- structural checks on the result; the command fails
                         rather than handing over a file Word might refuse

Afterwards: open the file in Word, click the table of contents, press F9 to
populate page numbers. The TOC is a live Word field, so it cannot be filled in
at build time.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import docx_common as dc  # noqa: E402
import import_docx  # noqa: E402
import make_templates as mt  # noqa: E402


def strip_repeat_headers(docx: Path) -> None:
    """Drop <w:tblHeader/> so a table's header row appears once, not per page."""
    tmp = docx.with_suffix(".tmp.docx")
    with zipfile.ZipFile(docx) as zin, \
         zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                data = re.sub(rb"<w:tblHeader\b[^>]*?/>", b"", data)
            zout.writestr(item, data)
    shutil.move(str(tmp), str(docx))


def lint_source(qmd: Path) -> list[str]:
    """Catch the two authoring mistakes that produce a broken or drifting file."""
    text = qmd.read_text(encoding="utf-8")
    # HTML comments never reach the output, and the shipped template explains
    # both forbidden patterns by naming them -- so linting them would fail on
    # unmodified boilerplate. Strip comments before checking.
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    problems = []
    if re.search(r"\{#(fig|tbl)-", text):
        problems.append(
            f"{qmd.name} uses Quarto cross-reference anchors ({{#fig-…}} / {{#tbl-…}}). "
            "Quarto emits two <w:pPr> elements in a cross-referenced caption, which "
            "the OOXML schema forbids and Word may offer to repair. Use a plain "
            "'**Table N. …**' line above the element instead.")
    body = re.sub(r"^\*\*(Figure|Table) \d+\..*$", "", text, flags=re.M)
    hits = sorted(set(re.findall(r"\b(?:Figure|Table)\s+\d+\b", body)))
    if hits:
        problems.append(
            f"{qmd.name} refers to figure or table NUMBERS in the prose ({', '.join(hits[:5])}). "
            "Numbers are reassigned by renumber_titles.py, so inline references go "
            "stale silently. Write 'the table below' or cite the section instead.")
    return problems


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", type=Path, required=True)
    ap.add_argument("--skip-lint", action="store_true",
                    help="render anyway despite source-lint findings (not advised)")
    args = ap.parse_args()

    spec = yaml.safe_load(args.spec.read_text(encoding="utf-8"))
    base = args.spec.parent.resolve()
    body_qmd = (base / spec["body"]).resolve()
    out = (base / spec["out"]).resolve()
    if out.suffix != ".docx":
        out = out.with_suffix(".docx")

    if not body_qmd.exists():
        raise SystemExit(f"body not found: {body_qmd}")

    print("[1/5] Building templates from the profile ...")
    sys.argv = ["make_templates.py", "--spec", str(args.spec)]
    mt.main()

    print("[2/5] Linting the source ...")
    problems = lint_source(body_qmd)
    if problems:
        for p in problems:
            print(f"  ! {p}")
        if not args.skip_lint:
            raise SystemExit("source lint failed; fix the above or pass --skip-lint")
    else:
        print("  clean")

    print("[3/5] Rendering the body ...")
    subprocess.run(["quarto", "render", str(body_qmd), "--to", "docx"], check=True)
    rendered = body_qmd.with_suffix(".docx")
    if not rendered.exists():
        raise SystemExit(f"quarto produced no output at {rendered}")
    # Stage it under build/ before stitching. Quarto writes next to the source,
    # which for a report named after its body collides with the final output --
    # the stitch would then write the deliverable and the cleanup would delete it.
    staged = base / "build" / "_body.docx"
    staged.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(rendered), str(staged))
    strip_repeat_headers(staged)

    # Stamp the house table look onto every table explicitly. The Table style
    # carries the same values, but Word did not apply its conditional formatting
    # -- header text came out black and no banding appeared. See docx_common.
    profile, _ = mt.load_profile(spec["profile"])
    body_work = dc.unpack(staged, base / "build" / ".body")
    n_tables = dc.stamp_table_formatting(body_work, profile)
    dc.repack(body_work, staged)
    shutil.rmtree(body_work, ignore_errors=True)
    print(f"  formatted {n_tables} table(s)")

    print("[4/5] Stitching front matter + body ...")
    try:
        from docx import Document
        from docxcompose.composer import Composer
    except ImportError:
        raise SystemExit("missing dependency -- run: pip3 install docxcompose")
    front = base / "build" / "frontmatter.docx"
    composer = Composer(Document(str(front)))
    composer.append(Document(str(staged)))
    out.parent.mkdir(parents=True, exist_ok=True)
    composer.save(str(out))
    staged.unlink(missing_ok=True)   # the .qmd is the source of truth

    print("[5/5] Validating the result ...")
    work = dc.unpack(out, base / "build" / ".verify")
    issues = dc.validate_package(work)
    leftover = dc.find_tokens(work)
    if leftover:
        issues.append("unsubstituted tokens: "
                      + ", ".join(f"{{{{{k}}}}}" for k in sorted(leftover)))
    if issues:
        out.unlink(missing_ok=True)
        raise SystemExit("the rendered report failed validation:\n  " + "\n  ".join(issues))
    shutil.rmtree(work, ignore_errors=True)

    # Baseline for the next import. Two files: the .qmd exactly as delivered, so
    # untouched sections can be restored from pristine source; and a conversion
    # of the .docx we are sending, so the comparison later is
    # conversion-against-conversion and an unedited section compares equal.
    import docx_import as di
    state = base / import_docx.STATE_DIR
    state.mkdir(parents=True, exist_ok=True)
    shutil.copy2(body_qmd, state / "baseline.qmd")
    titles = di.body_titles(body_qmd.read_text(encoding="utf-8"))
    baseline_md, _ = di.convert(out, base / "build" / ".baseline_media", titles,
                                base / "build" / ".baseline")
    (state / "baseline.md").write_text(baseline_md, encoding="utf-8")
    (state / "state.json").write_text(json.dumps({
        "rendered": datetime.now().isoformat(timespec="seconds"),
        "body": body_qmd.name, "out": out.name, "profile": spec["profile"],
    }, indent=2), encoding="utf-8")
    print(f"  baseline stored in {import_docx.STATE_DIR}/")

    size = out.stat().st_size
    print(f"\nDone -> {out}  ({size:,} bytes)")
    print("Open in Word, click the table of contents, press F9 to fill in page numbers.")
    print("When an edited copy comes back:  import_docx.py --spec <spec> --from <edited>.docx")


if __name__ == "__main__":
    main()
