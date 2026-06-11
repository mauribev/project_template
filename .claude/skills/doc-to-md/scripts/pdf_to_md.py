import sys
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Conversion strategy:
#   .docx / .doc  →  pypandoc  (Pandoc)
#       Pandoc has first-class support for Word's table model, correctly
#       handling row-spanning and column-spanning (merged) cells that cause
#       Docling to collapse multiple rows into a single cell.
#   .pdf (and everything else)  →  Docling
#       IBM Docling is best-in-class for PDF extraction (OCR, layout, tables).
# ---------------------------------------------------------------------------

DOCX_EXTENSIONS = {".docx", ".doc"}


def ensure_pypandoc():
    """Install pypandoc if missing. Pandoc itself must be installed at the OS level."""
    try:
        import pypandoc
    except ImportError:
        print("pypandoc not found. Installing now...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pypandoc"])


def ensure_docling():
    """Install Docling if missing."""
    try:
        import docling
    except ImportError:
        print("Docling library not found. Installing now...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "docling"])


def _resolve_output_path(source: Path, output_dir) -> Path:
    """Return the full output .md path, creating output_dir if needed."""
    if output_dir:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir / source.with_suffix(".md").name
    return source.with_suffix(".md")


def convert_docx_to_md(source: Path, output_path: Path):
    """
    Convert a Word document to Markdown using Pandoc via pypandoc.

    Pandoc correctly handles merged/spanning table cells which are common in
    Word reports. Docling collapses spanned rows into a single cell, producing
    garbled tables. Pandoc treats each logical cell independently.
    """
    ensure_pypandoc()
    import pypandoc

    print(f"Converting {source.name} using Pandoc (via pypandoc) ...")
    output = pypandoc.convert_file(
        str(source),
        to="gfm",          # GitHub-Flavored Markdown — best table support
        format="docx",
        extra_args=["--wrap=none"],  # don't hard-wrap long lines
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)


def convert_pdf_to_md(source: Path, output_path: Path):
    """
    Convert a PDF to Markdown using IBM Docling.

    Docling is best-in-class for PDF extraction: it handles complex layouts,
    multi-column text, and embedded tables via OCR.
    """
    ensure_docling()
    from docling.document_converter import DocumentConverter

    print(f"Converting {source.name} using Docling ...")
    converter = DocumentConverter()
    result = converter.convert(source)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result.document.export_to_markdown())


def convert_to_md(input_path, output_dir=None):
    """
    Convert a PDF or Word file to Markdown and save to output_dir (or
    alongside the source if output_dir is None).

    Args:
        input_path:  Path to the source .pdf, .docx, or .doc file.
        output_dir:  Optional destination directory. Use this whenever the
                     source lives in a read-only directory (e.g. a legacy vault).
    """
    source = Path(input_path)
    if not source.exists():
        print(f"Error: File not found at {input_path}")
        sys.exit(1)

    output_path = _resolve_output_path(source, output_dir)

    if source.suffix.lower() in DOCX_EXTENSIONS:
        convert_docx_to_md(source, output_path)
    else:
        convert_pdf_to_md(source, output_path)

    print(f"Success! Clean Markdown saved to {output_path}")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_md.py <path_to_file> [output_dir]")
        sys.exit(1)
    out_dir = sys.argv[2] if len(sys.argv) >= 3 else None
    convert_to_md(sys.argv[1], output_dir=out_dir)
