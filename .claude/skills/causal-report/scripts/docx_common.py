"""Shared Word-package helpers for the causal-report pipeline.

Nothing here is specific to one report. The three entry-point scripts
(make_templates.py, render.py, renumber_titles.py) import from this module.

The pipeline's guiding rule: profile.yaml is authoritative for everything that
can be expressed as a value, and the .docx is authoritative only for what cannot
-- cover layout, graphics, and the live table-of-contents field.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import zipfile
from pathlib import Path

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"

TOKEN_RE = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")


def q(tag: str, ns: str = W) -> str:
    return f"{{{ns}}}{tag}"


def parse(path: Path) -> etree._ElementTree:
    return etree.parse(str(path))


def save(tree: etree._ElementTree, path: Path) -> None:
    tree.write(str(path), xml_declaration=True, encoding="UTF-8", standalone=True)


# --------------------------------------------------------------------------- #
# Package open / close
# --------------------------------------------------------------------------- #
def unpack(docx: Path, workdir: Path) -> Path:
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)
    with zipfile.ZipFile(docx) as z:
        z.extractall(workdir)
    return workdir


def repack(workdir: Path, out: Path) -> None:
    """Rezip, with [Content_Types].xml first as the OPC spec expects."""
    out.parent.mkdir(parents=True, exist_ok=True)
    names = ["[Content_Types].xml"] + sorted(
        str(p.relative_to(workdir)) for p in workdir.rglob("*")
        if p.is_file() and p.name != "[Content_Types].xml")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name in names:
            z.write(workdir / name, name)


def text_parts(workdir: Path) -> list[Path]:
    """Every part that can hold visible text: body, headers, footers, footnotes."""
    word = workdir / "word"
    out = [word / "document.xml"]
    out += sorted(word.glob("header*.xml"))
    out += sorted(word.glob("footer*.xml"))
    for extra in ("footnotes.xml", "endnotes.xml"):
        if (word / extra).exists():
            out.append(word / extra)
    return [p for p in out if p.exists()]


# --------------------------------------------------------------------------- #
# Token substitution
# --------------------------------------------------------------------------- #
def find_tokens(workdir: Path) -> dict[str, list[str]]:
    """Map token name -> the parts it appears in.

    Works on the *joined* text of each paragraph, because Word routinely splits
    a typed token across runs -- `{{subtitle}}` is commonly stored as three runs,
    `{{` + `subtitle` + `}}`. Scanning raw XML would miss those silently.
    """
    found: dict[str, list[str]] = {}
    for part in text_parts(workdir):
        root = parse(part).getroot()
        for para in root.iter(q("p")):
            joined = "".join(t.text or "" for t in para.iter(q("t")))
            for name in TOKEN_RE.findall(joined):
                found.setdefault(name.upper(), []).append(part.name)
    return found


def _replace_in_paragraph(para, values: dict[str, str]) -> int:
    """Substitute tokens inside one paragraph, surgically.

    A token that sits entirely within one <w:t> is replaced in place. A token
    split across several <w:t> elements has its replacement written into the
    first, and only the token's own characters removed from the rest -- so other
    runs in the paragraph, and any field codes such as PAGE, survive untouched.
    """
    nodes = [t for t in para.iter(q("t"))]
    if not nodes:
        return 0
    texts = [n.text or "" for n in nodes]
    joined = "".join(texts)
    matches = list(TOKEN_RE.finditer(joined))
    if not matches:
        return 0

    # Character offset at which each node's text begins.
    starts, pos = [], 0
    for t in texts:
        starts.append(pos)
        pos += len(t)

    # Work right to left so earlier offsets stay valid.
    for m in reversed(matches):
        name = m.group(1).upper()
        if name not in values:
            continue
        val, s, e = values[name], m.start(), m.end()
        for i in range(len(nodes) - 1, -1, -1):
            ns, ne = starts[i], starts[i] + len(texts[i])
            if ne <= s or ns >= e:
                continue
            local_s, local_e = max(s - ns, 0), min(e - ns, len(texts[i]))
            head = texts[i][:local_s]
            tail = texts[i][local_e:]
            # The replacement goes in the first node the token touches.
            texts[i] = head + (val if ns <= s else "") + tail

    changed = 0
    for node, new in zip(nodes, texts):
        if (node.text or "") != new:
            node.text = new
            changed += 1
        if new != new.strip():
            node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return changed


def replace_tokens(workdir: Path, values: dict[str, str]) -> int:
    values = {k.upper(): ("" if v is None else str(v)) for k, v in values.items()}
    total = 0
    for part in text_parts(workdir):
        tree = parse(part)
        n = sum(_replace_in_paragraph(p, values) for p in tree.getroot().iter(q("p")))
        if n:
            save(tree, part)
            total += n
    return total


def assert_no_tokens_left(workdir: Path) -> None:
    """A document must never reach a client with {{TITLE}} on the cover."""
    left = find_tokens(workdir)
    if left:
        detail = "; ".join(f"{{{{{k}}}}} in {', '.join(sorted(set(v)))}"
                           for k, v in sorted(left.items()))
        raise SystemExit(f"unsubstituted tokens remain: {detail}")


# --------------------------------------------------------------------------- #
# Style injection -- profile.yaml -> Word styles.xml
# --------------------------------------------------------------------------- #
# OOXML is an ordered schema: inside rPr, pPr and tcPr the child elements must
# appear in the sequence the spec defines. Word tolerates a good deal of
# disorder, validators do not, and a file that trips a validator is a file that
# may prompt "Word found unreadable content". So every element we write is
# inserted at its correct position rather than appended.
_ORDER = {
    "rPr": ["rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps",
            "strike", "dstrike", "outline", "shadow", "emboss", "imprint",
            "noProof", "snapToGrid", "vanish", "webHidden", "color", "spacing",
            "w", "kern", "position", "sz", "szCs", "highlight", "u", "effect",
            "bdr", "shd", "fitText", "vertAlign", "rtl", "cs", "em", "lang"],
    "pPr": ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr",
            "widowControl", "numPr", "suppressLineNumbers", "pBdr", "shd",
            "tabs", "suppressAutoHyphens", "kinsoku", "wordWrap",
            "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN",
            "bidi", "adjustRightInd", "snapToGrid", "spacing", "ind",
            "contextualSpacing", "mirrorIndents", "suppressOverlap", "jc",
            "textDirection", "textAlignment", "outlineLvl", "rPr", "sectPr"],
    "tcPr": ["cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders",
             "shd", "noWrap", "tcMar", "textDirection", "tcFitText", "vAlign",
             "hideMark"],
}


def _local(el) -> str:
    return etree.QName(el).localname


def _set(parent, tag, **attrs):
    """Replace (or insert) a child element, keeping the schema's element order."""
    for old in parent.findall(q(tag)):
        parent.remove(old)
    el = etree.Element(q(tag))
    for k, v in attrs.items():
        el.set(q(k), v)

    order = _ORDER.get(_local(parent))
    if order and tag in order:
        rank = order.index(tag)
        for child in parent:
            name = _local(child)
            if name in order and order.index(name) > rank:
                child.addprevious(el)
                return el
    parent.append(el)
    return el


def _rpr(style):
    rpr = style.find(q("rPr"))
    if rpr is None:
        rpr = etree.SubElement(style, q("rPr"))
    return rpr


def _ppr(style):
    """Get or create <w:pPr>, keeping it before <w:rPr> as the schema requires."""
    ppr = style.find(q("pPr"))
    if ppr is None:
        ppr = etree.Element(q("pPr"))
        rpr = style.find(q("rPr"))
        if rpr is not None:
            rpr.addprevious(ppr)
        else:
            style.append(ppr)
    return ppr


# Emphasis the profile controls. Anything not requested is actively REMOVED, so
# profile.yaml stays authoritative even when the hand-authored Word file carries
# formatting of its own -- the source template had smallCaps on H1 and H3, which
# nothing in the profile asks for.
_EMPHASIS = ("b", "bCs", "i", "iCs", "smallCaps", "caps", "u", "strike")


def apply_paragraph_styles(workdir: Path, profile: dict) -> list[str]:
    """Write the profile's font, size, colour and emphasis into styles.xml."""
    path = workdir / "word" / "styles.xml"
    tree = parse(path)
    root = tree.getroot()
    font = profile["fonts"]["body"]
    colors = profile["colors"]
    spec = profile["styles"]

    # Document-wide default: what every unstyled run inherits.
    for rpr in root.findall(f"{q('docDefaults')}/{q('rPrDefault')}/{q('rPr')}"):
        _set(rpr, "rFonts", ascii=font, hAnsi=font, cs=font, eastAsia=font)
        _set(rpr, "sz", val=str(int(spec["Normal"]["size"] * 2)))
        _set(rpr, "szCs", val=str(int(spec["Normal"]["size"] * 2)))

    by_id = {s.get(q("styleId")): s for s in root.findall(q("style"))}
    applied = []
    for sid, cfg in spec.items():
        style = by_id.get(sid)
        if style is None:
            continue
        rpr = _rpr(style)
        ppr = _ppr(style)
        # Clear first, then set. The profile is authoritative, so anything the
        # hand-authored Word file happens to carry -- small caps on a heading,
        # a left indent -- must not survive into the build.
        for tag in _EMPHASIS + ("pageBreakBefore", "ind", "spacing"):
            for old in rpr.findall(q(tag)) + ppr.findall(q(tag)):
                (rpr if old in rpr else ppr).remove(old)

        _set(rpr, "rFonts", ascii=font, hAnsi=font, cs=font, eastAsia=font)
        _set(rpr, "sz", val=str(int(cfg["size"] * 2)))
        _set(rpr, "szCs", val=str(int(cfg["size"] * 2)))
        _set(rpr, "color", val=colors[cfg["color"]])
        if cfg.get("bold"):
            _set(rpr, "b")
            _set(rpr, "bCs")
        if cfg.get("italic"):
            _set(rpr, "i")
            _set(rpr, "iCs")
        if cfg.get("small_caps"):
            _set(rpr, "smallCaps")
        if cfg.get("underline"):
            _set(rpr, "u", val="single")

        # Indentation is in twips (1440 = 1 inch). `indent: 0` means flush left
        # and is worth stating explicitly -- headings in a hand-authored file
        # often carry an inherited left indent nobody intended.
        ind = {}
        if cfg.get("indent") is not None:
            ind["left"] = str(int(cfg["indent"]))
        if cfg.get("indent_right") is not None:
            ind["right"] = str(int(cfg["indent_right"]))
        if cfg.get("first_line") is not None:
            ind["firstLine"] = str(int(cfg["first_line"]))
        if ind:
            _set(ppr, "ind", **ind)

        spacing = {}
        if cfg.get("space_before") is not None:
            spacing["before"] = str(int(cfg["space_before"]))
        if cfg.get("space_after") is not None:
            spacing["after"] = str(int(cfg["space_after"]))
        if spacing:
            _set(ppr, "spacing", **spacing)

        if cfg.get("page_break_before"):
            _set(ppr, "pageBreakBefore")
        applied.append(sid)

    save(tree, path)
    return applied


def apply_table_style(workdir: Path, profile: dict) -> None:
    """Define the `Table` style, including header fill and row banding.

    `Table` is the style id pandoc assigns to every table it writes, and pandoc
    also emits <w:tblLook w:firstRow="1" w:noHBand="0" .../>, which is what tells
    Word to honour the firstRow and band rules below. Net effect: an ordinary
    pipe table in the .qmd comes out with the house look and no extra markup.
    """
    cfg = profile["table"]
    colors = profile["colors"]
    font = profile["fonts"]["body"]
    path = workdir / "word" / "styles.xml"
    tree = parse(path)
    root = tree.getroot()

    sid = cfg["style_id"]
    for s in root.findall(q("style")):
        if s.get(q("styleId")) == sid:
            root.remove(s)

    style = etree.SubElement(root, q("style"))
    style.set(q("type"), "table")
    style.set(q("customStyle"), "1")
    style.set(q("styleId"), sid)
    _set(style, "name", val=sid)
    # Word applies conditional formatting more reliably when a custom table
    # style derives from the built-in one.
    _set(style, "basedOn", val="TableNormal")
    _set(style, "uiPriority", val="99")

    rpr = etree.SubElement(style, q("rPr"))
    _set(rpr, "rFonts", ascii=font, hAnsi=font, cs=font, eastAsia=font)
    _set(rpr, "sz", val=str(int(cfg["body"]["size"] * 2)))
    _set(rpr, "szCs", val=str(int(cfg["body"]["size"] * 2)))
    _set(rpr, "color", val=colors[cfg["body"]["color"]])

    tblpr = etree.SubElement(style, q("tblPr"))
    # One row per band, so colours alternate every row rather than every pair.
    _set(tblpr, "tblStyleRowBandSize", val="1")
    _set(tblpr, "tblStyleColBandSize", val="1")
    borders = etree.SubElement(tblpr, q("tblBorders"))
    edge = "none" if cfg.get("borders") == "none" else "single"
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b = etree.SubElement(borders, q(side))
        b.set(q("val"), edge)
        b.set(q("sz"), "0")
        b.set(q("space"), "0")
        b.set(q("color"), "auto")

    def band(kind: str, fill: str, *, bold=False, color=None, size=None):
        bp = etree.SubElement(style, q("tblStylePr"))
        bp.set(q("type"), kind)
        if bold or color or size:
            brpr = etree.SubElement(bp, q("rPr"))
            _set(brpr, "rFonts", ascii=font, hAnsi=font, cs=font, eastAsia=font)
            if bold:
                _set(brpr, "b")
                _set(brpr, "bCs")
            if color:
                _set(brpr, "color", val=color)
            if size:
                _set(brpr, "sz", val=str(int(size * 2)))
                _set(brpr, "szCs", val=str(int(size * 2)))
        tcpr = etree.SubElement(bp, q("tcPr"))
        shd = etree.SubElement(tcpr, q("shd"))
        shd.set(q("val"), "clear")
        shd.set(q("color"), "auto")
        shd.set(q("fill"), fill)

    h = cfg["header"]
    band("firstRow", h["fill"], bold=h.get("bold", True),
         color=colors[h["color"]], size=h["size"])
    # band1Horz is the first body band, i.e. the row directly after the header.
    band("band1Horz", cfg["bands"]["odd"])
    band("band2Horz", cfg["bands"]["even"])

    save(tree, path)


def stamp_table_formatting(workdir: Path, profile: dict) -> int:
    """Write the house table look directly onto every table's rows and cells.

    The `Table` style defined by apply_table_style() carries the same values as
    conditional formatting (firstRow / band1Horz / band2Horz). In practice Word
    did not apply it: the header row rendered black rather than white, because
    the style's base rPr colour won, and no banding appeared at all.

    Rather than chase why, the formatting is stamped explicitly -- an <w:shd> on
    every cell and run properties on every header run. That is deterministic and
    renderer-independent, which matters here because there is no LibreOffice on
    the build machine and the only way to test Word's behaviour is to ask a
    person to open the file.

    The values still come from profile.yaml, so this is no less "pre-specified";
    it is applied directly instead of being requested and hoped for. The style
    definition is kept as well, so the table still looks right to anyone who
    inspects or edits it in Word's UI.
    """
    cfg = profile["table"]
    colors = profile["colors"]
    font = profile["fonts"]["body"]
    path = workdir / "word" / "document.xml"
    if not path.exists():
        return 0

    tree = parse(path)
    header, bands = cfg["header"], cfg["bands"]
    touched = 0

    for tbl in tree.getroot().iter(q("tbl")):
        style = tbl.find(f"{q('tblPr')}/{q('tblStyle')}")
        if style is None or style.get(q("val")) != cfg["style_id"]:
            continue
        for row_i, tr in enumerate(tbl.findall(q("tr"))):
            is_header = row_i == 0
            if is_header:
                fill = header["fill"]
            else:
                # Body row 1 takes the odd colour, row 2 the even, and so on.
                fill = bands["odd"] if row_i % 2 == 1 else bands["even"]

            for tc in tr.findall(q("tc")):
                tcpr = tc.find(q("tcPr"))
                if tcpr is None:
                    tcpr = etree.Element(q("tcPr"))
                    tc.insert(0, tcpr)
                _set(tcpr, "shd", val="clear", color="auto", fill=fill)

                for run in tc.iter(q("r")):
                    rpr = run.find(q("rPr"))
                    if rpr is None:
                        rpr = etree.Element(q("rPr"))
                        run.insert(0, rpr)
                    spec = header if is_header else cfg["body"]
                    _set(rpr, "rFonts", ascii=font, hAnsi=font, cs=font, eastAsia=font)
                    _set(rpr, "color", val=colors[spec["color"]])
                    _set(rpr, "sz", val=str(int(spec["size"] * 2)))
                    _set(rpr, "szCs", val=str(int(spec["size"] * 2)))
                    if is_header and header.get("bold", True):
                        _set(rpr, "b")
                        _set(rpr, "bCs")
        touched += 1

    if touched:
        save(tree, path)
    return touched


def graft_missing_styles(workdir: Path, donor: Path, font: str) -> list[str]:
    """Copy in every style pandoc emits that this document does not define.

    Pandoc does NOT synthesise missing styles. Its docx writer references about
    fifty style ids; a hand-made Word file typically defines twenty or thirty.
    Anything undefined falls back through the theme -- in practice to Cambria --
    so the body would silently stop being Arial. Theme-driven font attributes in
    the donor are rewritten to name the profile font directly.
    """
    ours = parse(workdir / "word" / "styles.xml")
    theirs = parse(donor / "word" / "styles.xml")
    have = {s.get(q("styleId")) for s in ours.getroot().findall(q("style"))}

    grafted = []
    for style in theirs.getroot().findall(q("style")):
        sid = style.get(q("styleId"))
        if sid in have:
            continue
        style = etree.fromstring(etree.tostring(style))
        style.attrib.pop(q("default"), None)
        for rf in style.iter(q("rFonts")):
            for attr in ("asciiTheme", "hAnsiTheme", "cstheme", "eastAsiaTheme"):
                rf.attrib.pop(q(attr), None)
            for attr in ("ascii", "hAnsi", "cs", "eastAsia"):
                rf.set(q(attr), font)
        ours.getroot().append(style)
        grafted.append(sid)

    save(ours, workdir / "word" / "styles.xml")
    return grafted


def set_theme_fonts(workdir: Path, font: str) -> int:
    """Point the theme's Latin fonts at the profile font.

    Belt and braces: grafted styles may still reference the theme indirectly.
    """
    path = workdir / "word" / "theme" / "theme1.xml"
    if not path.exists():
        return 0
    tree = parse(path)
    n = 0
    for latin in tree.getroot().iter(q("latin", A)):
        latin.set("typeface", font)
        n += 1
    save(tree, path)
    return n


def strip_embedded_fonts(workdir: Path, font: str, fallback: str) -> bool:
    """Remove embedded font parts and name the font instead.

    Pandoc copies embedded .ttf/.odttf parts but regenerates [Content_Types].xml
    from a fixed template, which can leave those parts with no declared content
    type -- an invalid package that makes Word offer to repair the file. Embedded
    fonts are also most of a front matter's size: 4.9 MB of one 5.4 MB example.
    """
    fonts_dir = workdir / "word" / "fonts"
    had = fonts_dir.exists()
    shutil.rmtree(fonts_dir, ignore_errors=True)
    (workdir / "word" / "_rels" / "fontTable.xml.rels").unlink(missing_ok=True)

    ft = workdir / "word" / "fontTable.xml"
    if ft.exists():
        xml = ft.read_text(encoding="utf-8")
        xml = re.sub(r"<w:embed\w+[^/]*/>", "", xml)
        if f'<w:altName w:val="{fallback}"/>' not in xml:
            xml = xml.replace(f'<w:font w:name="{font}">',
                              f'<w:font w:name="{font}"><w:altName w:val="{fallback}"/>')
        ft.write_text(xml, encoding="utf-8")

    ct_path = workdir / "[Content_Types].xml"
    ct = parse(ct_path)
    for node in list(ct.getroot()):
        if node.get("PartName", "").startswith("/word/fonts/"):
            ct.getroot().remove(node)
    save(ct, ct_path)

    settings = workdir / "word" / "settings.xml"
    if settings.exists():
        xml = settings.read_text(encoding="utf-8")
        xml = re.sub(r"<w:embed(TrueType|System)Fonts[^/]*/>", "", xml)
        settings.write_text(xml, encoding="utf-8")
    return had


def enable_field_update(workdir: Path) -> None:
    """Ask Word to offer to refresh the table-of-contents field on open."""
    path = workdir / "word" / "settings.xml"
    if not path.exists():
        return
    tree = parse(path)
    root = tree.getroot()
    if root.find(q("updateFields")) is None:
        etree.SubElement(root, q("updateFields")).set(q("val"), "true")
    save(tree, path)


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
def validate_package(workdir: Path) -> list[str]:
    """Structural checks. With no LibreOffice available this is the real check."""
    problems: list[str] = []
    ct = parse(workdir / "[Content_Types].xml").getroot()
    defaults = {n.get("Extension", "").lower() for n in ct if n.tag == f"{{{CT}}}Default"}
    overrides = {n.get("PartName") for n in ct if n.tag == f"{{{CT}}}Override"}

    for part in workdir.rglob("*"):
        if not part.is_file():
            continue
        rel = "/" + str(part.relative_to(workdir)).replace("\\", "/")
        if rel == "/[Content_Types].xml":
            continue
        # Path(".rels").suffix is "" -- dotfiles have no suffix -- so take the
        # extension off the name or the package root rels looks untyped.
        ext = part.name.rsplit(".", 1)[-1].lower() if "." in part.name else ""
        if rel not in overrides and ext not in defaults:
            problems.append(f"no content type declared: {rel}")
        if ext in ("xml", "rels"):
            try:
                etree.parse(str(part))
            except etree.XMLSyntaxError as exc:
                problems.append(f"malformed XML in {rel}: {exc}")

    for rels in workdir.rglob("*.rels"):
        base = rels.parent.parent
        for node in parse(rels).getroot():
            if node.get("TargetMode") == "External":
                continue
            if not (base / node.get("Target")).exists():
                problems.append(
                    f"dangling relationship {node.get('Id')} -> {node.get('Target')}")

    doc = workdir / "word" / "document.xml"
    if doc.exists():
        raw = doc.read_text(encoding="utf-8", errors="ignore")
        used = set(re.findall(r'<w:(?:pStyle|rStyle|tblStyle) w:val="([^"]+)"', raw))
        defined = set(re.findall(r'w:styleId="([^"]+)"',
                                 (workdir / "word" / "styles.xml").read_text(
                                     encoding="utf-8", errors="ignore")))
        # FigureTable is referenced by pandoc but defined in no reference doc,
        # including pandoc's own. Harmless.
        for sid in sorted(used - defined - {"FigureTable"}):
            problems.append(f"style used but not defined: {sid}")
        if re.search(r"<w:pPr>(?:(?!</w:p>).){0,400}?<w:pPr>", raw, re.S):
            problems.append(
                "a paragraph carries two <w:pPr> elements, which the schema "
                "forbids -- this is what Quarto cross-reference anchors produce; "
                "use plain captions instead")
    return problems


def pandoc_reference(dest: Path) -> Path:
    """Pandoc's own default reference.docx, unpacked -- the style donor."""
    docx = dest / "pandoc_ref.docx"
    if not docx.exists():
        dest.mkdir(parents=True, exist_ok=True)
        with open(docx, "wb") as fh:
            subprocess.run(["pandoc", "--print-default-data-file", "reference.docx"],
                           stdout=fh, check=True)
    out = dest / "pandoc_ref"
    if not out.exists():
        unpack(docx, out)
    return out
