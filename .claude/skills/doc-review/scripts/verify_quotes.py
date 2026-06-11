#!/usr/bin/env python3
"""
verify_quotes.py — Verbatim quote verification for the doc-review skill.

Reads an evidence file (_evidence.md) and its corresponding source Markdown file,
then checks every extracted quote against the source text using tiered fuzzy matching.

Usage:
    python3 verify_quotes.py <evidence_file> <source_file> [--threshold-pass 95] [--threshold-flag 85]

Output:
    - Updates the evidence file in-place with verification results.
    - Prints a summary report to stdout.

Dependencies:
    - rapidfuzz (auto-installed if missing)

Thresholds (configurable):
    >=95%  → PASS  (accepted as verbatim)
    85-94% → FLAG  (near-match, likely minor formatting — human review)
    <85%   → FAIL  (not found in source — possible hallucination)

References:
    - Magesh et al. (2024), "Hallucination-Free? Assessing the Reliability of
      Leading AI Legal Research Tools," Stanford RegLab.
    - Thresholds derived from convergent evidence across legal (95-100%),
      academic (90-95%), and systematic review (90-95%) domains.
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path

# ---------------------------------------------------------------------------
# Auto-install rapidfuzz if missing
# ---------------------------------------------------------------------------
try:
    from rapidfuzz import fuzz
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rapidfuzz", "-q"])
    from rapidfuzz import fuzz


# ---------------------------------------------------------------------------
# Text normalisation
# ---------------------------------------------------------------------------
def normalise(text: str) -> str:
    """Lowercase, normalise unicode, collapse whitespace."""
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Parse the evidence file
# ---------------------------------------------------------------------------
def parse_evidence(evidence_path: Path) -> list[dict]:
    """
    Parse an _evidence.md file into a list of quote records.

    Expected format per entry:
        ### E001
        - **Section:** ...
        - **Lines:** 245–248
        - **Quote:** "The exact quoted text..."
        - **Tag:** ...
        - **Note:** ...
        - **Verified:** (filled by this script)
    """
    content = evidence_path.read_text(encoding="utf-8")
    entries = re.split(r"(?=^### E\d+)", content, flags=re.MULTILINE)

    records = []
    for entry in entries:
        entry = entry.strip()
        if not entry.startswith("### E"):
            continue

        record = {"raw": entry}

        # Extract entry ID
        id_match = re.match(r"### (E\d+)", entry)
        record["id"] = id_match.group(1) if id_match else "UNKNOWN"

        # Extract quote text (between outermost quotes on the Quote line)
        quote_match = re.search(
            r"\*\*Quote:\*\*\s*[\"\"](.*?)[\"\"]",
            entry,
            re.DOTALL,
        )
        if not quote_match:
            # Fallback: try without smart quotes
            quote_match = re.search(
                r'\*\*Quote:\*\*\s*"(.*?)"',
                entry,
                re.DOTALL,
            )
        record["quote"] = quote_match.group(1).strip() if quote_match else ""

        # Extract source lines (for reporting)
        lines_match = re.search(r"\*\*Lines:\*\*\s*(.+)", entry)
        record["lines"] = lines_match.group(1).strip() if lines_match else ""

        records.append(record)

    return records


# ---------------------------------------------------------------------------
# Verify a single quote against source text
# ---------------------------------------------------------------------------
def verify_quote(
    quote: str,
    source_text: str,
    source_normalised: str,
    threshold_pass: int = 95,
    threshold_flag: int = 85,
) -> dict:
    """
    Verify a quote against the source text.

    Returns dict with: score, verdict, method.
    """
    if not quote:
        return {"score": 0, "verdict": "FAIL", "method": "empty_quote"}

    quote_norm = normalise(quote)

    # --- Tier 1: Exact substring match ---
    if quote_norm in source_normalised:
        return {"score": 100, "verdict": "PASS", "method": "exact_substring"}

    # --- Tier 2: Fuzzy partial match (best matching substring) ---
    score = fuzz.partial_ratio(quote_norm, source_normalised)

    if score >= threshold_pass:
        verdict = "PASS"
    elif score >= threshold_flag:
        verdict = "FLAG"
    else:
        verdict = "FAIL"

    return {"score": round(score, 1), "verdict": verdict, "method": "partial_ratio"}


# ---------------------------------------------------------------------------
# Update the evidence file with verification results
# ---------------------------------------------------------------------------
def update_evidence_file(
    evidence_path: Path,
    records: list[dict],
    results: list[dict],
) -> None:
    """Rewrite the evidence file with verification results injected."""
    content = evidence_path.read_text(encoding="utf-8")

    for record, result in zip(records, results):
        entry_id = record["id"]
        score = result["score"]
        verdict = result["verdict"]

        if verdict == "PASS":
            icon = "\u2705"  # ✅
        elif verdict == "FLAG":
            icon = "\u26a0\ufe0f"  # ⚠️
        else:
            icon = "\u274c"  # ❌

        verification_line = f"{icon} {verdict} ({score}%)"

        # Replace or insert the Verified line for this entry
        # Pattern: find the entry block and update/add Verified line
        entry_pattern = re.compile(
            rf"(### {re.escape(entry_id)}.*?)(\n### E|\Z)",
            re.DOTALL,
        )
        match = entry_pattern.search(content)
        if not match:
            continue

        block = match.group(1)

        # Remove existing Verified line if present
        block_updated = re.sub(
            r"- \*\*Verified:\*\*.*\n?", "", block
        )
        # Append new Verified line
        block_updated = block_updated.rstrip() + f"\n- **Verified:** {verification_line}\n"

        content = content[: match.start(1)] + block_updated + content[match.start(2) :]

    evidence_path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Print summary report
# ---------------------------------------------------------------------------
def print_report(records: list[dict], results: list[dict]) -> None:
    """Print a summary verification report to stdout."""
    total = len(results)
    passed = sum(1 for r in results if r["verdict"] == "PASS")
    flagged = sum(1 for r in results if r["verdict"] == "FLAG")
    failed = sum(1 for r in results if r["verdict"] == "FAIL")

    print("\n" + "=" * 60)
    print("QUOTE VERIFICATION REPORT")
    print("=" * 60)
    print(f"Total quotes:  {total}")
    print(f"  \u2705 PASS:      {passed}")
    print(f"  \u26a0\ufe0f  FLAG:      {flagged}")
    print(f"  \u274c FAIL:      {failed}")
    print("-" * 60)

    # Detail for flagged and failed quotes
    for record, result in zip(records, results):
        if result["verdict"] in ("FLAG", "FAIL"):
            icon = "\u26a0\ufe0f" if result["verdict"] == "FLAG" else "\u274c"
            print(f"\n{icon} {record['id']} (score: {result['score']}%, "
                  f"method: {result['method']}, lines: {record['lines']})")
            quote_preview = record["quote"][:120]
            if len(record["quote"]) > 120:
                quote_preview += "..."
            print(f"   Quote: \"{quote_preview}\"")

    print("\n" + "=" * 60)

    if failed > 0:
        print(f"\n\u274c {failed} quote(s) could not be verified. "
              "Review these manually before trusting the evidence file.")
    elif flagged > 0:
        print(f"\n\u26a0\ufe0f All quotes passed or near-matched. "
              f"{flagged} quote(s) flagged for human review (minor differences).")
    else:
        print("\n\u2705 All quotes verified as verbatim.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Verify verbatim quotes in a doc-review evidence file."
    )
    parser.add_argument("evidence_file", help="Path to the _evidence.md file")
    parser.add_argument("source_file", help="Path to the source .md file")
    parser.add_argument(
        "--threshold-pass", type=int, default=95,
        help="Minimum score to auto-accept as verbatim (default: 95)"
    )
    parser.add_argument(
        "--threshold-flag", type=int, default=85,
        help="Minimum score to flag for review instead of failing (default: 85)"
    )
    args = parser.parse_args()

    evidence_path = Path(args.evidence_file)
    source_path = Path(args.source_file)

    if not evidence_path.exists():
        print(f"Error: Evidence file not found: {evidence_path}", file=sys.stderr)
        sys.exit(1)
    if not source_path.exists():
        print(f"Error: Source file not found: {source_path}", file=sys.stderr)
        sys.exit(1)

    # Read and normalise source text
    source_text = source_path.read_text(encoding="utf-8")
    source_normalised = normalise(source_text)

    # Parse evidence file
    records = parse_evidence(evidence_path)
    if not records:
        print("No quote entries found in evidence file.")
        sys.exit(0)

    # Verify each quote
    results = []
    for record in records:
        result = verify_quote(
            record["quote"],
            source_text,
            source_normalised,
            threshold_pass=args.threshold_pass,
            threshold_flag=args.threshold_flag,
        )
        results.append(result)

    # Update evidence file with results
    update_evidence_file(evidence_path, records, results)

    # Print report
    print_report(records, results)


if __name__ == "__main__":
    main()
