---
name: doc-review
version: 1.2
description: Produces a thorough, stand-alone review of one or more already-converted Markdown documents. Uses structural (heading-based) chunking and a sequential Refine pattern to preserve cross-section coherence and prevent context degradation. When multiple documents are provided, reviews them one at a time. Requires a pre-existing .md file — use the doc-to-md skill first if starting from a PDF or Word document.
context: fork
---

# Document Review Pipeline

You are executing a rigorous document review pipeline. Read this file in full before taking any action.

> **Why this pipeline is designed the way it is:** LLMs suffer from a "Lost in the Middle" attention bias (Liu et al., 2024 — content in the middle of a long context is systematically underweighted), context rot (attention quality degrades as the context window fills), and hallucination under pressure (fabricated details when content is partially lost). This pipeline addresses all three by: (1) processing one section at a time so every section is at the beginning of its own inference call, (2) using the output file as running memory rather than carrying raw document text forward, and (3) applying the Refine pattern so every section is processed with full awareness of what was read before. See `KNOWLEDGE_BASE.md` in this skill folder for the full research rationale.

---

## Orchestrator Handoff Protocol

> **⛔ THIS SECTION IS FOR THE ORCHESTRATOR (parent agent), NOT the forked skill agent.**
>
> This skill uses `context: fork`. The forked agent cannot talk to the user directly — its output is relayed by the orchestrator. To prevent information loss at the handoff boundary:
>
> 1. **RELAY VERBATIM:** When the forked agent returns output containing a chunk plan table, confirmation questions, or any content marked with `⛔ RELAY VERBATIM`, the orchestrator MUST show it to the user **as-is**. Do not summarize, compress, or paraphrase.
> 2. **USE SendMessage:** After the user confirms the chunk plan, the orchestrator MUST use `SendMessage` to continue the **same forked agent** (using its returned agent ID). Do NOT launch a new general-purpose agent. The forked agent has the SKILL.md context, the chunk plan, and the user's decisions — a new agent has none of these.
> 3. **PLAN FILE AS SAFETY NET:** If SendMessage fails for any reason, the forked agent will have written a plan file to disk. A new agent can recover by reading the plan file + this SKILL.md. But this is a fallback — SendMessage is the preferred path.

---

## Inputs

Confirm the following before proceeding:

1. **Target file(s):** One or more `.md` file paths provided by the user. These must already exist — this skill does not convert documents. If the `.md` file does not exist, stop and tell the user to run the `doc-to-md` skill first.
2. **Output directory:** The base review directory. Default: `06_workspace/03_document_review/`. The skill creates artifact-type subfolders inside this directory automatically (see Folder Structure below). Use the default unless the user specifies otherwise.
3. **Focus area (optional):** What to extract from each document. If the user does not specify, use the **default comprehensive focus**:
   > *Purpose & Context → Methodology & Design → Key Variables & Indicators → Data Sources & Sampling → Main Findings → Limitations → Open Questions & Decisions*

   The focus area is an **analytical lens** — it guides what to pay attention to while reading, not the structure of the output. Tell the user upfront: *"I will use the default comprehensive focus unless you specify a different angle (e.g., 'sampling strategy only' or 'indicator construction')."*

4. **Review structure (optional):** The user may specify a section outline or reference a template file for the final `_review` document. This is asked actively during Phase 0. If no structure is given, the review is organized thematically by content.

5. **Evidence extraction (optional):** Whether to extract key verbatim quotes into a separate `_evidence.md` file. This is asked actively during Phase 0. If yes, quotes are extracted during Phase 2 and verified programmatically in Phase 2.5.

---

## Folder Structure

All artifacts are organized by type inside the base review directory. **The skill must create these subdirectories if they do not exist.**

```
<base_review_dir>/
├── 01_sources/          # Converted .md files (created by doc-to-md)
├── 02_plans/            # Chunk plans (YAML)
├── 03_notes/            # Section-by-section notes + evidence files (if enabled)
├── 04_reviews/          # Thematic synthesis reviews
├── 05_synthesis/        # Cross-document analysis (by theme, not by doc)
└── registry.csv         # Master index: doc → all artifacts + status
```

> **Why artifact-type folders:** This is the dominant model across systematic review tools (Covidence, EPPI-Reviewer), research data management standards (NIH, UK Data Service, ICPSR), QDA software (NVivo, ATLAS.ti), and LLM pipelines (LangChain, LlamaIndex). It enables batch operations, cross-document comparison, and scales to 100+ documents. Per-document folders are rejected by every professional-grade review tool for analytical work. See KNOWLEDGE_BASE.md for full research basis.

---

## Naming Convention

**This rule is mandatory and must never be overridden.**

All output filenames share the **same stem** derived from the source filename, with an **artifact-type suffix**:

```
<source_stem>_plan.yaml       → 02_plans/
<source_stem>_notes.md        → 03_notes/
<source_stem>_review.md       → 04_reviews/
<source_stem>_evidence.md     → 03_notes/   (lives alongside the notes)
```

Where `<source_stem>` = the source filename **without its extension**, with **spaces replaced by underscores**. No abbreviation. No sequential prefix.

**Example:**
- Source: `01_sources/BRCiS III Baseline Report_final_shared_2024.07.22.md`
- Plan: `02_plans/BRCiS_III_Baseline_Report_final_shared_2024.07.22_plan.yaml`
- Notes: `03_notes/BRCiS_III_Baseline_Report_final_shared_2024.07.22_notes.md`
- Evidence: `03_notes/BRCiS_III_Baseline_Report_final_shared_2024.07.22_evidence.md`
- Review: `04_reviews/BRCiS_III_Baseline_Report_final_shared_2024.07.22_review.md`

> **Why suffix, not prefix:** Sorting by filename groups all artifacts for the same document together. `ls *Baseline*` shows everything related to one document across folders. The suffix distinguishes artifact type while the stem provides traceability.

---

## Multi-Document Rule

When the user provides more than one document:

1. **List all target files** explicitly and confirm the order before starting.
2. **Complete the full pipeline for document 1** before touching document 2. Never process documents in parallel.
3. After all reviews are complete, present a summary table of all output files created.
4. **Update the registry** after each completed document.

> **Why sequential:** Parallel agents cause write-permission conflicts even across different output files (confirmed from project experience). Sequential processing also allows learnings from one document to inform how the next is read.

---

## Pipeline

### Phase 0 — Intake, TOC Extraction & Confirmation

1. **Create folder structure** if it does not exist:
   ```bash
   mkdir -p "<base_dir>/01_sources" "<base_dir>/02_plans" "<base_dir>/03_notes" "<base_dir>/04_reviews" "<base_dir>/05_synthesis"
   ```

2. Run `wc -l` on the target `.md` file to get the total line count.

3. Extract the heading structure:
   ```bash
   grep -n "^#" "<path_to_md_file>"
   ```

4. Build a **chunk plan** — a table showing every top-level section with its start line, end line, and line count. End line of section N = start line of section N+1 minus 1 (last section ends at total line count).

5. Apply the following rules silently, then flag them to the user:
   - **Sections > 500 lines (~8–10 pages):** Flag as LONG. Propose using the section's own sub-headings as chunk boundaries. Do not subdivide silently.
   - **Sections < 80 lines (~1–2 pages):** Flag as SHORT. Propose grouping with the adjacent section. Do not group silently.
   - **Structural sections** (e.g., "Acronyms", "References", "Table of Contents"): Propose skipping unless the user wants them included.

6. Present the chunk plan to the user. **This output must be relayed verbatim by the orchestrator.**

   ```
   ⛔ RELAY VERBATIM — The following chunk plan must be shown to the user as-is.

   Document: <filename>
   Total lines: <N>
   Detected focus: <focus area>

   | # | Section heading | Start | End | Lines | Flag |
   |---|----------------|-------|-----|-------|------|
   | 1 | Introduction   | 12    | 96  | 85    |      |
   | 2 | Methodology    | 97    | 508 | 412   |      |
   | 3 | Annex I        | 509   | 1131| 623   | ⚠️ LONG — suggest sub-headings |
   | 4 | References     | 1132  | 1176| 45    | ⏭️ Structural — skip? |
   ```

7. **Ask about review structure and evidence extraction** alongside the chunk plan:

   > *"Before I begin:*
   > *1. Do you want the final review to follow a specific structure or template? If yes, paste the section outline or reference a template file. If no, I'll organize it thematically based on the content.*
   > *2. Do you want me to extract key verbatim quotes into a separate evidence file? (Quotes will be programmatically verified against the source for accuracy.)"*

8. **Wait for user confirmation** of the chunk plan, review structure, and evidence preference before proceeding. Adjust the plan based on the user's response.

---

### Phase 1 — Plan File & Output Initialization

Once confirmed:

1. Derive `<source_stem>` from the source filename (strip extension, spaces → underscores).

2. **Write the plan file** (`02_plans/<source_stem>_plan.yaml`). This is the structural contract — it captures all decisions so any agent can resume from it:

   ```yaml
   # Doc-Review Plan File — do not edit manually
   source_file: "<path to source .md>"
   source_stem: "<derived stem>"
   base_dir: "<base review directory>"
   focus_area: "<focus area>"
   review_structure: "<user-specified structure or 'thematic — content-driven'>"
   evidence_extraction: true/false
   date_created: "YYYY-MM-DD"

   chunks:
     - id: 1
       heading: "Introduction"
       start_line: 12
       end_line: 96
       lines: 85
       status: pending
     - id: 2
       heading: "Methodology"
       start_line: 97
       end_line: 508
       lines: 412
       status: pending
     # ...

   skipped_sections:
     - heading: "References"
       reason: "Structural — user confirmed skip"

   output_files:
     notes: "03_notes/<stem>_notes.md"
     review: "04_reviews/<stem>_review.md"
     evidence: "03_notes/<stem>_evidence.md"  # only if evidence_extraction: true
   ```

3. **Initialize the notes file** (`03_notes/<source_stem>_notes.md`):

   ```markdown
   ---
   title: "Section Notes: <Document Title>"
   source_file: "<filename>.md"
   date_reviewed: "<YYYY-MM-DD>"
   analyst: "Claude Code (doc-review skill v1.2)"
   focus_area: "<focus area>"
   total_chunks: <N>
   ---

   ## Chunk Plan

   | # | Section heading | Start | End | Lines | Status |
   |---|----------------|-------|-----|-------|--------|
   | 1 | Introduction   | 12    | 96  | 85    | pending|
   | ...                                               |

   ---
   ```

4. **Initialize the evidence file** (only if evidence extraction = yes) (`03_notes/<source_stem>_evidence.md`):

   ```markdown
   ---
   title: "Evidence File: <Document Title>"
   source_file: "<filename>.md"
   date_reviewed: "<YYYY-MM-DD>"
   analyst: "Claude Code (doc-review skill v1.2)"
   total_quotes: 0
   verified: false
   ---
   ```

5. **Initialize the review file** (`04_reviews/<source_stem>_review.md`):

   ```markdown
   ---
   title: "Document Review: <Document Title>"
   source_file: "<filename>.md"
   date_reviewed: "<YYYY-MM-DD>"
   analyst: "Claude Code (doc-review skill v1.2)"
   focus_area: "<focus area>"
   review_structure: "<user-specified or 'thematic — content-driven'>"
   total_chunks: <N>
   ---

   <!-- Review content will be written in Phase 3 after all notes are complete -->
   ```

6. Notify the user that processing is beginning.

---

### Phase 2 — Sequential Section Notes (Refine Pattern)

Process each chunk in order, writing **to the notes file** (and optionally the evidence file). For **every section**:

#### Step A — Prepare carry-forward context

- If the accumulated **notes file is under ~500 lines** (~4,000–7,000 tokens): Read it in full and use it as carry-forward context.
- If the accumulated **notes file exceeds ~500 lines**: Apply tiered context:
  1. Read the last 2 sections' notes verbatim from the notes file.
  2. Mentally distill a compact "Key Threads" block from all earlier sections (~300–500 tokens): defined terms, major methodology decisions, key figures established so far, open questions. You do not write this to file — it is your internal working context.
- If this is **section 1:** No prior context. Start fresh.

> **Why size-based, not count-based:** A document with 20 tiny sections might have only 200 lines of notes by section 10 — easily fits in context. A document with 3 massive sections might already have 1,000+ lines by section 4. The trigger for tiered context is the accumulated content size, not the section number. 500 lines is roughly where reading prior context starts competing with attention to the current section.

#### Step B — Read the section

Use the Read tool with `offset` and `limit` matching the section's start and end lines from the chunk plan. Do not read beyond the section boundaries.

#### Step C — Synthesize and append to the notes file

Use the focus area as an **analytical lens** — it tells you what to look for, not what headings to write. Extract what is actually present in the section. Do not create a sub-heading for a focus dimension if the section has nothing relevant to say about it.

- Write **free-form notes** organized by what is actually present in the section.
- For specific figures (sample sizes, weights, indicator values, dates): **quote verbatim** rather than paraphrase. Fabrication risk is highest for precise numerical values.
- Note explicit connections to content from earlier sections (e.g., "Confirms the sampling approach from Section 2").
- Flag inconsistencies or ambiguities using `> ⚠️ FLAG:` callouts.
- Flag open methodological questions using `> ❓ OPEN QUESTION:` callouts.

Append to the **notes file**:

```markdown
## [Section Number]. [Section Heading]
*Lines [start]–[end] | [N] lines*

[Free-form notes — organized by what is present, not by a fixed sub-heading template]

---
```

**Write immediately after processing each section.** Do not batch writes. If something fails mid-review, the partial notes are preserved.

#### Step C.1 — Extract quotes to evidence file (if enabled)

If evidence extraction is enabled, extract **key quotes** from the section:

- Extract quotes that meet any of these criteria:
  - Definitions or technical terms introduced
  - Methodological decisions and their stated rationale
  - Key statistics, baseline values, or thresholds
  - Surprising or counterintuitive findings
  - Caveats, limitations, or acknowledged weaknesses
  - Contradictions with earlier sections or other documents
  - Statements that directly address the focus area
- Extract as many as the section warrants — not every paragraph, but every passage that meets the criteria above. Some sections may yield many quotes; others may yield none.
- Copy the text **exactly as it appears** in the source. Do not clean up typos, formatting, or grammar.
- Append each quote to the **evidence file** using this format:

```markdown
### E[NNN]
- **Section:** [Section Number]. [Section Heading]
- **Lines:** [start]–[end]
- **Quote:** "[exact verbatim text from source]"
- **Tag:** [1–3 thematic tags, comma-separated]
- **Note:** [Brief analyst note — why this quote matters]
- **Verified:** (pending — filled by verify_quotes.py)
```

Quote numbering (`E001`, `E002`, ...) is sequential across the entire document, not per section.

> **Why a separate evidence file:** Quotes serve as verifiable anchors between the notes/review and the source document. They are also reusable across projects (e.g., extracting all quotes tagged "sampling" across 30 documents). Keeping them separate follows JBI SUMARI and Cochrane best practice for evidence tables.

#### Step D — Update plan file and progress

After processing each section:
1. Update the chunk's `status` from `pending` to `complete` in the plan file.
2. Update the chunk plan table at the top of the notes file.
3. Briefly confirm to the user: *"Section [N/Total] complete: [Section Heading]. Continuing..."* — one line only.

---

### Phase 2.5 — Quote Verification (if evidence extraction is enabled)

After all sections are processed and before writing the review:

1. Run the verification script:
   ```bash
   python3 .claude/skills/doc-review/scripts/verify_quotes.py \
     "<base_dir>/03_notes/<stem>_evidence.md" \
     "<source_file_path>"
   ```
2. The script updates the evidence file in-place with verification results (`✅ PASS`, `⚠️ FLAG`, `❌ FAIL`) and prints a summary report.
3. Report the verification summary to the user. If any quotes FAIL, flag them explicitly.

---

### Phase 3 — Synthesis Review

After all sections are processed (and quotes verified, if applicable):

1. Read the **complete notes file**.
2. If evidence extraction is enabled, also read the **evidence file** for verified quotes.
3. Write the **`_review` file** as a coherent, standalone analytical document:
   - If the user specified a structure or template: apply it exactly.
   - If no structure was specified: organize thematically based on what the content actually warrants. Do not impose the focus area list as section headings — let the content drive the structure.
   - The review should read as a self-contained synthesis. A reader who has not seen the notes or evidence file should fully understand the document.
   - For all specific figures, weights, and dates: quote verbatim.
   - Carry over all substantive `⚠️ FLAG` and `❓ OPEN QUESTION` callouts from the notes.

4. **Update the registry** (see below).

5. Notify the user with:
   - Full paths to all output files (plan, notes, evidence if applicable, review)
   - Total sections reviewed
   - Count of `⚠️ FLAG` and `❓ OPEN QUESTION` items
   - Quote verification summary (if applicable)

---

## Registry

The registry is a CSV file at `<base_dir>/registry.csv` that maps each document to all its artifacts. **The skill must create the registry if it does not exist, and append to it after each completed review.**

```csv
source_stem,source_file,date_reviewed,focus_area,plan,notes,evidence,review,total_chunks,flags,open_questions,quotes_total,quotes_passed,quotes_flagged,quotes_failed,status
BRCiS_III_Baseline_Report_final_shared_2024.07.22,01_sources/BRCiS III Baseline Report_final_shared_2024.07.22.md,2026-04-07,comprehensive,02_plans/...yaml,03_notes/...notes.md,03_notes/...evidence.md,04_reviews/...review.md,14,3,6,42,40,2,0,complete
```

> **Why a registry:** This is the single most consistent recommendation across NIH, ICPSR, LLM pipelines, and QDA tools for projects with many documents. It provides a single lookup for "what was reviewed, when, and where are the artifacts" without opening any files.

---

## Anti-Patterns

The following are explicitly prohibited in this pipeline:

| Anti-Pattern | Why It Fails |
|---|---|
| Reading the entire `.md` file at once before chunking | Causes "Lost in the Middle" — middle sections will be underweighted or missed |
| Carrying forward the raw source text between sections | Causes context rot — the model attends thinly to early content as context grows |
| Writing the notes file only at the end | All work is lost if the process fails mid-way |
| Processing two documents in parallel | Write-permission conflicts; incoherent cross-document context |
| Splitting a section mid-table or mid-paragraph | Produces garbled analysis; always honour structural boundaries |
| Paraphrasing specific numbers, weights, or dates | Highest hallucination risk; always quote verbatim |
| Silently applying thresholds or groupings | User must confirm the chunk plan before processing begins |
| Skipping the TOC step to "save time" | Removes the user's only checkpoint before a potentially long, unrecoverable run |
| Abbreviating or reordering the source filename in output names | Breaks the naming convention; causes ambiguity when multiple reviews exist |
| Applying focus-area dimensions as mandatory sub-headings in every chunk | Produces thin, empty sub-headings for sections where those dimensions are not present |
| Asking about review structure or evidence after processing begins | Both must be known before Phase 2; retrofitting is disruptive |
| Launching a new agent instead of continuing via SendMessage | Loses SKILL.md context, chunk plan, and user decisions — produces spec-divergent output |
| Cleaning up, paraphrasing, or "fixing" verbatim quotes | Defeats the purpose of verbatim extraction; the verification script will flag non-matches |

---

## Continuous Improvement (Self-Healing)

If this pipeline fails, produces poor output, or you discover a better approach:

1. Stop, diagnose, and resolve the issue.
2. **Update Learnings:** Append the finding to the **Learnings** section at the bottom of this file. If the finding suggests the core pipeline instructions should be changed, **do NOT modify them unilaterally** — present the proposed change to the user and wait for approval before editing.
3. **Update the Log:** Append to `.claude/skills/doc-review/CHANGELOG.md` with: date, issue, and exact resolution.
4. **Version discipline:** If the Learnings section exceeds **8 entries**, propose a version cut to the user: promote mature/recurrent learnings into the core pipeline instructions, clear them from the Learnings section, bump the version in frontmatter and CHANGELOG, and archive the old `SKILL.md` as `SKILL_vN.md`. Learnings are candidates for pipeline promotion, not a permanent log.
5. **Global Sync:** Promote the upgrade to the global profile:
   ```bash
   mkdir -p ~/.claude/skills/
   cp -R .claude/skills/doc-review ~/.claude/skills/
   ```
6. Notify the user of the upgrade, then resume.

---

## Output File Format Reference

### Notes file (`03_notes/<stem>_notes.md`)

```markdown
---
title: "Section Notes: [Document Title]"
source_file: "[filename].md"
date_reviewed: "YYYY-MM-DD"
analyst: "Claude Code (doc-review skill v1.2)"
focus_area: "[focus area]"
total_chunks: N
---

## Chunk Plan

| # | Section heading | Start | End | Lines | Status    |
|---|----------------|-------|-----|-------|-----------|
| 1 | Introduction   | 12    | 96  | 85    | complete  |
| 2 | Methodology    | 97    | 508 | 412   | pending   |

---

## 1. [Section Heading]
*Lines [start]–[end] | [N] lines*

[Free-form notes — organized by what is actually present in the section.
 Focus areas are lenses, not mandatory sub-headings.
 Verbatim quotes for all numbers, weights, dates.]

> ⚠️ FLAG: [Any inconsistency or ambiguity for human review]
> ❓ OPEN QUESTION: [Any unresolved methodological question]

---

## 2. [Next Section Heading]
...
```

### Evidence file (`03_notes/<stem>_evidence.md`)

```markdown
---
title: "Evidence File: [Document Title]"
source_file: "[filename].md"
date_reviewed: "YYYY-MM-DD"
analyst: "Claude Code (doc-review skill v1.2)"
total_quotes: N
verified: true/false
---

### E001
- **Section:** 1. Introduction
- **Lines:** 45–48
- **Quote:** "[exact verbatim text from source document]"
- **Tag:** sampling, methodology
- **Note:** Key design decision — must be replicated at midline.
- **Verified:** ✅ PASS (100%)

### E002
- **Section:** 3. Findings
- **Lines:** 312–315
- **Quote:** "[exact verbatim text]"
- **Tag:** food_security, FCS
- **Note:** Baseline FCS value for midline comparison.
- **Verified:** ⚠️ FLAG (91%)

---
```

### Review file (`04_reviews/<stem>_review.md`)

```markdown
---
title: "Document Review: [Document Title]"
source_file: "[filename].md"
date_reviewed: "YYYY-MM-DD"
analyst: "Claude Code (doc-review skill v1.2)"
focus_area: "[focus area]"
review_structure: "[user-specified structure, or 'thematic — content-driven']"
total_chunks: N
---

[Coherent thematic synthesis — structure driven by content or user-specified template.
 Self-contained: readable without the notes or evidence file.
 Substantive ⚠️ FLAG and ❓ OPEN QUESTION callouts carried over from notes.]
```

### Plan file (`02_plans/<stem>_plan.yaml`)

See Phase 1, step 2 for full format.

---

## Learnings

*(Append discoveries here — do not modify the pipeline instructions above without user approval.)*

- **2026-04-07 — Design basis:** This skill implements the Refine pattern (sequential accumulation) rather than Map-Reduce. Rationale: evaluation reports have cross-section narrative coherence that Map-Reduce destroys. See `KNOWLEDGE_BASE.md` for full research basis (Liu et al. 2024, LangChain pattern taxonomy, Google Cloud summarization guide).
- **2026-04-07 — Thresholds:** 500-line flag for long sections ≈ 8–10 Word pages ≈ 4,000–7,000 tokens (Pandoc output). 80-line floor for short sections ≈ 1–2 pages. Based on empirical observation of Pandoc-converted BRCiS documents: ~50–70 lines per Word page.
- **2026-04-07 — context:fork:** This skill uses `context: fork` to isolate execution from the main conversation. All necessary context (file path, focus area, output directory, review structure, evidence preference) must be passed through the skill invocation — do not rely on conversation history.
- **2026-04-07 — Output file as memory:** The notes file is the running synthesis. Read it back before each section rather than maintaining a separate memory object. For 20+ section documents, apply tiered context: verbatim last 2 sections + distilled Key Threads block from earlier sections.
- **2026-04-07 — Artifact-type folder structure:** Based on convergent evidence from Covidence, EPPI-Reviewer, NIH, UK Data Service, ICPSR, NVivo, ATLAS.ti, LangChain, and LlamaIndex. Artifact-type separation scales to 100+ documents; per-document folders are rejected by every professional-grade review tool.
- **2026-04-07 — Quote verification:** Verbatim quotes are verified programmatically using `rapidfuzz` (tiered: ≥95% PASS, 85–94% FLAG, <85% FAIL). Thresholds derived from convergent legal (95–100%), academic (90–95%), and systematic review (90–95%) standards. Even the best legal AI tools hallucinate 17%+ (Magesh et al. 2024, Stanford RegLab).
