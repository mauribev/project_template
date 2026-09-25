"""Build the two Word artifacts a report render needs, from one Word source.

    python3 make_templates.py --spec <report_spec.yaml>
    python3 make_templates.py --profile long_report --list-tokens

Inputs
------
profiles/<name>/profile.yaml          all typography, colour and table values
profiles/<name>/frontmatter_source.docx   hand-authored cover / logo / TOC / acronyms
<report_spec.yaml>                    this report's title, client, date, ...

Outputs (written next to the report's .qmd, in a build/ directory)
-----------------------------------------------------------------
frontmatter.docx   sections 1..N of the source with tokens filled -- the stitch master
bodyref.docx       same styles, body emptied to a single section carrying the BODY
                   header/footer rather than the cover's -- Quarto's --reference-doc

Why two artifacts from one source: pandoc copies the FIRST sectPr it finds in a
reference doc. Handed the front matter as-is it would give every body page the
cover's chrome. So the reference doc is a stripped twin, built in the same pass
so the two can never disagree about styling.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import docx_common as dc  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent


def load_profile(name: str) -> tuple[dict, Path]:
    pdir = SKILL / "profiles" / name
    cfg = yaml.safe_load((pdir / "profile.yaml").read_text(encoding="utf-8"))
    return cfg, pdir


def style_pass(work: Path, profile: dict, donor: Path) -> None:
    """Everything that makes a Word package match profile.yaml."""
    font = profile["fonts"]["body"]
    dc.strip_embedded_fonts(work, font, profile["fonts"]["fallback"])
    dc.graft_missing_styles(work, donor, font)
    dc.apply_paragraph_styles(work, profile)
    dc.apply_table_style(work, profile)
    dc.set_theme_fonts(work, font)
    dc.enable_field_update(work)


def build_bodyref(work_src: Path, work_dst: Path, profile: dict) -> None:
    """Strip the front matter down to an empty body section.

    Keeps the styles; replaces the body with a single empty paragraph and one
    sectPr carrying the LAST section's header/footer references -- i.e. the
    running chrome, not the cover's.
    """
    import shutil
    if work_dst.exists():
        shutil.rmtree(work_dst)
    shutil.copytree(work_src, work_dst)

    doc = dc.parse(work_dst / "word" / "document.xml")
    body = doc.getroot().find(dc.q("body"))
    final_sect = body.find(dc.q("sectPr"))
    if final_sect is None:
        raise SystemExit("front matter has no final sectPr; cannot derive a body reference")
    keep = dc.etree.fromstring(dc.etree.tostring(final_sect))

    for child in list(body):
        body.remove(child)
    dc.etree.SubElement(body, dc.q("p"))
    body.append(keep)

    page = profile["page"]
    pg = dc._set(keep, "pgSz", w=str(page["width"]), h=str(page["height"]))
    mar = dc._set(keep, "pgMar", **{k: str(v) for k, v in page["margins"].items()})
    del pg, mar
    dc.save(doc, work_dst / "word" / "document.xml")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", type=Path, help="report spec YAML")
    ap.add_argument("--profile", help="profile name (when only listing tokens)")
    ap.add_argument("--list-tokens", action="store_true",
                    help="print every {{TOKEN}} in the front matter and exit")
    args = ap.parse_args()

    if args.list_tokens:
        name = args.profile or (yaml.safe_load(args.spec.read_text())["profile"]
                                if args.spec else "long_report")
        profile, pdir = load_profile(name)
        work = dc.unpack(pdir / profile["sources"]["frontmatter"],
                         Path("/tmp") / f"cdr_tok_{name}")
        found = dc.find_tokens(work)
        print(f"tokens in {profile['sources']['frontmatter']}:")
        for tok, parts in sorted(found.items()):
            print(f"  {{{{{tok}}}}}  ({', '.join(sorted(set(parts)))})")
        if not found:
            print("  (none)")
        return

    if not args.spec:
        ap.error("--spec is required unless --list-tokens is given")

    spec = yaml.safe_load(args.spec.read_text(encoding="utf-8"))
    profile, pdir = load_profile(spec["profile"])
    out_dir = (args.spec.parent / "build").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    scratch = out_dir / ".work"
    donor = dc.pandoc_reference(scratch / "donor")

    # --- front matter --------------------------------------------------------
    work = dc.unpack(pdir / profile["sources"]["frontmatter"], scratch / "front")

    present = set(dc.find_tokens(work))
    values = {k.upper(): v for k, v in (spec.get("values") or {}).items()}
    missing = sorted(present - set(values))
    if missing:
        raise SystemExit(
            "the front matter contains tokens with no value in the spec: "
            + ", ".join(f"{{{{{m}}}}}" for m in missing))
    unused = sorted(set(values) - present)
    for u in unused:
        print(f"  note: spec value '{u}' has no matching token in the front matter")

    n = dc.replace_tokens(work, values)
    dc.assert_no_tokens_left(work)
    print(f"  substituted {n} text runs across {len(present)} tokens")

    style_pass(work, profile, donor)
    problems = dc.validate_package(work)
    if problems:
        raise SystemExit("front matter failed validation:\n  " + "\n  ".join(problems))
    dc.repack(work, out_dir / "frontmatter.docx")
    print(f"  wrote {out_dir.name}/frontmatter.docx")

    # --- body reference ------------------------------------------------------
    ref = scratch / "bodyref"
    build_bodyref(work, ref, profile)
    problems = dc.validate_package(ref)
    if problems:
        raise SystemExit("body reference failed validation:\n  " + "\n  ".join(problems))
    dc.repack(ref, out_dir / "bodyref.docx")
    print(f"  wrote {out_dir.name}/bodyref.docx")


if __name__ == "__main__":
    main()
