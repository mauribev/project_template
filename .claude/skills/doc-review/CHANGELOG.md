# doc-review Skill — Changelog

## 2026-04-07 — v1.2

**Major redesign based on user feedback and cross-domain research (systematic review tools, research data management standards, QDA software, LLM pipelines).**

- **Artifact-type folder structure:** Replaced flat output with `01_sources/`, `02_plans/`, `03_notes/`, `04_reviews/`, `05_synthesis/` subfolders. Based on convergent evidence from Covidence, EPPI-Reviewer, NIH, UK Data Service, ICPSR, NVivo, ATLAS.ti, LangChain, LlamaIndex. Scales to 100+ documents.
- **Suffix naming convention:** Changed from `notes_<stem>.md` (prefix) to `<stem>_notes.md` (suffix). All artifacts for the same document share the same stem and sort together. Suffix distinguishes artifact type.
- **Plan file as structural contract:** New YAML plan file (`_plan.yaml`) written in Phase 1, capturing all chunk plan decisions and user preferences. Enables agent recovery if SendMessage fails — any agent can resume by reading the plan file + SKILL.md.
- **Registry file:** New `registry.csv` master index mapping each document to all derived artifacts, status, and metadata. Single most consistent recommendation across all frameworks reviewed.
- **Evidence file (optional):** New `_evidence.md` file for verbatim quote extraction, following JBI SUMARI finding + illustration + credibility model. Quotes are programmatically verified against the source using `rapidfuzz` (Phase 2.5). Tiered thresholds: ≥95% PASS, 85–94% FLAG, <85% FAIL. Based on Magesh et al. (2024) Stanford hallucination study and convergent legal/academic/journalism standards.
- **verify_quotes.py:** New Python script in `scripts/` that reads the evidence file, checks every quote against the source .md using exact substring match + fuzzy partial ratio, and updates the evidence file in-place with verification results.
- **Orchestrator Handoff Protocol:** New top-level section with explicit instructions for the parent agent: relay verbatim, use SendMessage, plan file as fallback. Added `⛔ RELAY VERBATIM` markers to Phase 0 output.
- **Phase 0 active asks:** Now asks about review structure AND evidence extraction during chunk plan confirmation (single confirmation step).
- **Three new anti-patterns:** launching new agents instead of SendMessage, cleaning up verbatim quotes, asking about structure/evidence after processing begins.

---

## 2026-04-07 — v1.1

**Changes from user feedback after first live run on BRCiS III Baseline Report:**

- **Two-output design:** Pipeline now produces two files per document — `notes_<stem>.md` (section-by-section, written incrementally during Phase 2) and `review_<stem>.md` (thematic synthesis, written in Phase 3 from the completed notes file). Prevents information loss when thematic reorganization doesn't map 1:1 to source sections.
- **Strict naming convention:** Output filenames are always `notes_<source_stem>.md` and `review_<source_stem>.md`, where `<source_stem>` is the exact source filename without extension, spaces replaced with underscores. No sequential prefix, no abbreviation, no suffix. Added to a dedicated `## Naming Convention` section and to the Anti-patterns table.
- **Focus areas as lenses:** Removed the instruction to apply focus-area dimensions as mandatory sub-headings on every chunk. Focus areas now guide what to pay attention to while reading; notes are free-form, organized by what is actually present in each section. Added corresponding Anti-pattern entry.
- **Review structure — active ask:** The skill now actively asks the user during Phase 0 (alongside chunk plan confirmation) whether they want a specific structure or template for the `review_` file. If none is specified, the review is organized thematically by content. Added as item 4 in Inputs and step 6 in Phase 0.
- **Anti-patterns table:** Added two new entries (filename abbreviation/reordering; forced focus sub-headings; asking about structure after processing begins).
- **Version field added to frontmatter.**

---

## 2026-04-07 — Initial creation

**Design basis:** Created as a standalone replacement for Phase 2 of the `hybrid-lit-review` skill. The hybrid skill conflated document conversion with document review; separating them allows the review to be re-run with different focus areas without re-converting the source file.

**Key design decisions implemented in v1.0:**

- `context: fork` frontmatter — runs the skill in an isolated subagent to prevent context blowout in the main conversation.
- Structural (heading-based) chunking — uses `##` heading boundaries rather than arbitrary line counts. Line-count thresholds (>500 flag, <80 group) are secondary safeguards, not primary chunk boundaries.
- Refine pattern (sequential accumulation) — each section is processed with full awareness of all prior sections via the output file as running memory. Map-Reduce rejected due to cross-section coherence loss.
- TOC presentation and user confirmation — chunk plan is presented before any processing begins. User can adjust before a long, unrecoverable run starts.
- Incremental writes — output file is appended after each section, not written at the end. Preserves partial work on failure.
- Anti-patterns table — 8 explicitly documented failure modes with rationale.
- Research basis documented in `KNOWLEDGE_BASE.md` (Liu et al. 2024, LangChain patterns, Google Cloud guide, survey of `academic-paper-reviewer`, `rag-architect`, `self-improving-agent`, `repomix`).
