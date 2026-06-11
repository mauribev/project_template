# Knowledge Base: LLM Analysis of Long Documents
### Problems, Patterns, Best Practices, and Skill Design Decisions

*Compiled for the `doc-review` skill. Last updated: 2026-04-07.*

---

## 1. Core Problems When Using LLMs on Long Documents

### 1.1 Lost in the Middle

**Source:** Liu et al. (2023/2024), *[Lost in the Middle: How Language Models Use Long Contexts](https://aclanthology.org/2024.tacl-1.9/)*, published in *Transactions of the Association for Computational Linguistics*.

LLMs exhibit a systematic U-shaped attention bias: they attend most reliably to content at the **beginning** and **end** of the context window, and perform significantly worse on content in the **middle** — even when the context window is technically large enough to hold the entire document.

Key finding: on multi-document question answering tasks, performance degraded substantially when relevant information was placed in the middle of the input, regardless of model size or advertised context length.

**Implication for document review:** Feeding an entire large document as a single prompt is not reliable. Critical details in the middle sections will be underweighted or missed. Processing one section at a time ensures every part of the document receives primacy-of-position attention within its own inference call — it is always at the beginning of that call's context.

---

### 1.2 Context Rot (Context Degradation)

As a context window fills up, the quality of attention across the full history degrades. This happens for two reasons:

1. **Attention diffusion:** With more tokens in context, the model distributes attention more thinly. Early content gets diluted.
2. **Positional encoding strain:** Transformer models encode position mathematically. Very long sequences push tokens into ranges that are less well-represented in training data.

**Implication:** Even with a 200K-token context window (Claude), dumping a 400-page report as a single prompt is not equivalent to reading it carefully. The model loses coherence and tends to produce generic, surface-level summaries for material late in the document.

---

### 1.3 Hallucination Under Pressure

When a model is asked to summarize content it has partially lost track of (due to the above problems), it tends to fill gaps with plausible-sounding but fabricated detail — especially for specific numbers, names, and methodological steps. This is particularly dangerous for technical evaluation reports where precise figures matter.

**Implication:** Shorter, focused inference calls with explicit scope ("extract content from this section only") reduce the pressure to confabulate. When extracting specific figures (sample sizes, indicator values, weights), quote verbatim from the source text rather than paraphrasing.

---

## 2. Summarization Architectures

Three canonical patterns exist, popularized by LangChain but applicable to any LLM pipeline. See: *[Scaling Document Summarization: Stuffing, Map-Reduce, and Refine](https://medium.com/@sonimegha1602/scaling-document-summarization-with-llms-stuffing-map-reduce-and-refine-a8a468d479c3)* and *[Google Cloud: Long Document Summarization](https://cloud.google.com/blog/products/ai-machine-learning/long-document-summarization-with-workflows-and-gemini-models)*.

### 2.1 Stuff (Single-Pass)

The entire document is passed to the LLM in one prompt.

- **When it works:** Documents that comfortably fit within ~50K tokens with no complexity.
- **When it fails:** Anything longer, or documents with detailed tables, methodology sections, and numerical data that must be faithfully reproduced.
- **Risk:** Directly subject to Lost in the Middle and context rot.

### 2.2 Map-Reduce

The document is split into chunks. Each chunk is independently summarized (the *map* step). All chunk summaries are then combined into a final synthesis (the *reduce* step).

- **Advantage:** Highly parallelizable — each map step is independent.
- **Disadvantage:** Each chunk is processed in isolation with no awareness of what came before or after. Cross-chunk themes, arguments that span sections, and cumulative reasoning are lost.
- **Best for:** Very large corpora where speed matters more than nuance, or when chunks are genuinely self-contained (e.g., independent news articles).
- **Not ideal for:** Technical reports with a narrative arc, where later sections refer back to earlier ones.

### 2.3 Refine (Iterative Accumulation) ← our chosen pattern

The document is split into chunks. The first chunk is summarized. For each subsequent chunk, the LLM receives both the new chunk **and** the running synthesis from all previous chunks, and is asked to refine/extend the summary.

- **Advantage:** Produces coherent, narrative-aware summaries. Each inference call is aware of what came before. Cross-section themes are naturally preserved.
- **Disadvantage:** Sequential — cannot be parallelized. Slower than Map-Reduce.
- **Best for:** Technical evaluation reports, academic papers, policy documents — anything with a logical flow where later sections build on earlier ones.

### 2.4 Summary of Summaries (Hierarchical)

A variant of Map-Reduce where the reduce step is itself recursive: chunk summaries are grouped and re-summarized in multiple rounds until a single synthesis emerges. Useful for extremely large document collections (hundreds of documents), but adds complexity. Relevant for future use if we ever need to synthesize across dozens of reports.

---

## 3. Chunking Strategies

### 3.1 Fixed-Size Chunking

Split by a fixed number of tokens, characters, or lines.

- **Pros:** Simple, deterministic.
- **Cons:** Ignores document structure entirely. Chunks can cut mid-sentence, mid-paragraph, or mid-table.
- **Verdict:** Acceptable as a fallback only. Should not be the primary strategy for structured documents.

### 3.2 Structural Chunking (Section-Based) ← our chosen strategy

Split at natural document boundaries — headings, sections, subsections — rather than at arbitrary counts.

- **Pros:** Each chunk is semantically coherent. Tables within a section are not split. The model can be told explicitly what section it is reading. Markdown files make this trivially easy — headings are explicit `#`/`##`/`###` markers.
- **Cons:** Chunk sizes become variable. Very long sections may still need subdivision. Very short sections may need grouping.
- **Verdict:** The correct default for any well-structured document. The `doc-review` skill uses top-level headings as primary chunk boundaries, and only descends to sub-headings when a section exceeds the size threshold (see Section 4).

### 3.3 Semantic Chunking

Split at points of semantic shift using embedding similarity to detect topic boundaries.

- **Pros:** Captures thematic coherence even in poorly structured documents.
- **Cons:** Computationally expensive. 2024 research (Vectara) found that semantic chunking's advantage largely disappeared on normal, well-structured text.
- **Verdict:** Overkill for structured evaluation reports. Reserve for unstructured text (e.g., raw interview transcripts with no headings).

See: *[Pinecone: Chunking Strategies for LLM Applications](https://www.pinecone.io/learn/chunking-strategies/)* and *[Firecrawl: Best Chunking Strategies for RAG in 2026](https://www.firecrawl.dev/blog/best-chunking-strategies-rag)*.

---

## 4. Section Size Thresholds: Tradeoffs and Guidance

### How long is "400 lines" of Pandoc Markdown?

Pandoc-converted Word documents are line-sparse: many lines are blank separators, inline HTML fragments, or short bullet items. Empirically (from this project's converted documents):

| Lines of Pandoc Markdown | Approximate Word pages | Approximate tokens |
|---|---|---|
| 100 lines | 1–2 pages | ~800–1,200 |
| 300 lines | 4–6 pages | ~2,500–4,000 |
| 400 lines | 6–8 pages | ~3,500–5,500 |
| 600 lines | 10–14 pages | ~5,000–8,000 |
| 800 lines | 14–20 pages | ~7,000–11,000 |

*Rule of thumb: 1 Word page ≈ 50–70 lines of Pandoc Markdown. Actual ratio depends on table density and list structure.*

### The core tradeoff

| | Small sections (< 200 lines / ~3 pages) | Medium sections (200–500 lines / ~4–8 pages) | Large sections (> 600 lines / ~10+ pages) |
|---|---|---|---|
| Lost-in-Middle risk | Very low | Low | High |
| Inference calls needed | Many | Moderate | Few |
| Context carry-forward load | High (many iterations) | Moderate | Light |
| Structural coherence | Risk of over-splitting a logical unit | ✅ Ideal | Risk of under-splitting |
| Table integrity | ✅ Easy to preserve | ✅ Easy to preserve | ⚠️ Large tables may cause issues |

### Recommended thresholds for `doc-review`

- **Flag for subdivision:** Sections exceeding **500 lines** (~8–10 pages). Suggest to user that the section's own sub-headings be used as chunk boundaries.
- **Group short sections:** Sections under **80 lines** (~1–2 pages) should be merged with the adjacent section unless they are stand-alone (e.g., a "Glossary" or "Acronyms" section).
- **Ideal chunk target:** 150–400 lines (~3–7 pages). This falls in the sweet spot: long enough to be coherent, short enough to avoid attention degradation.

These thresholds should be surfaced to the user at the TOC step, not applied silently.

**Why not token-count thresholds?** Token counts require running a tokenizer, which is an extra dependency. Line counts are a practical proxy. The structural approach (headings) naturally produces coherent chunks; line count is only a secondary safeguard for pathologically long sections.

---

## 5. Sequential vs. Parallel Processing

| Dimension | Sequential (Refine) | Parallel (Map-Reduce) |
|---|---|---|
| Cross-section awareness | ✅ Full — each step sees prior synthesis | ❌ None — chunks processed in isolation |
| Summary coherence | ✅ High — narrative preserved | ⚠️ Medium — depends on reduce quality |
| Speed | ❌ Slower | ✅ Faster |
| Agent complexity | ✅ Simple — one agent, one context | ⚠️ Higher — requires orchestration |
| File write permissions | ✅ No conflict — single writer | ❌ Risk of race conditions with multiple agents |
| Best for | Technical reports, evaluation docs | Large independent document collections |

**For evaluation reports (our use case): sequential is strictly better.** Midline/baseline inception reports have explicit cross-references between sections. A parallel agent has no access to this context.

**On parallel agents and write permissions:** Confirmed by direct experience in this project. Multiple agents running concurrently — even targeting different output files — can produce permission conflicts in Claude Code. Sequential processing eliminates this entirely.

**Multiple documents:** When the user provides more than one document, process them fully one-by-one in sequence before starting the next. Never launch parallel agents per document.

---

## 6. Context Window Management

### 6.1 The Output File as Running Memory

The most robust carry-forward mechanism is to use **the review file itself as the running synthesis**. Since sections are appended incrementally to the output file, the already-written content is always available. Before processing each new section, read back the accumulated review file as context.

- This scales naturally — the review file is already compressed (it's structured notes, not raw document text).
- No separate memory object to maintain.
- If processing fails mid-way, the partial review is preserved.

### 6.2 Tiered Context for Very Long Documents (20+ sections)

For very long documents, the accumulated review file may itself grow large. Apply a tiered approach:

1. **Full detail for the last 1–2 sections** (most recent context, carried verbatim).
2. **Compressed "key threads" block** distilled from all earlier sections (~300–500 tokens). This captures: defined terms, major methodology decisions, established facts, and open questions identified so far.

The distillation step should happen every ~5 sections to keep carry-forward cost bounded.

### 6.3 Compaction as Recovery Mechanism

If the conversation context approaches its limit during a long review, summarize the accumulated context and reinitiate with the summary as the new base. This is a recovery mechanism, not standard operating procedure. Notify the user when this happens.

---

## 7. `context: fork` — Skill Isolation Feature

**Source:** [Claude Code docs](https://code.claude.com/docs/en/skills), [ClaudeLog: What is Context Fork](https://claudelog.com/faqs/what-is-context-fork-in-claude-code/), added in Claude Code 2.1.

The `context: fork` frontmatter field runs a skill in an isolated sub-agent context with independent conversation history, keeping the main conversation clean.

```yaml
---
name: doc-review
description: ...
context: fork
---
```

**What it does:**
- The skill executes in a forked subagent — it has access to the file system and tools, but does not inherit the main conversation history.
- Output from the skill does not pollute the main conversation context.
- Ideal for heavy, multi-step tasks that generate a lot of intermediate output (exactly what document review is).

**Tradeoff:** The subagent does not have access to any project-specific context from the ongoing conversation (e.g., if the user explained something earlier in the session, the forked agent won't know). The SKILL.md instructions must be fully self-contained.

**Decision for `doc-review`:** Use `context: fork` to keep reviews clean and prevent context blowout in the main session. All necessary context (document path, focus area, output path) must be passed through the skill invocation, not assumed from conversation history.

---

## 8. Survey of Related Skills in the Wild

Reviewing existing skills helps identify patterns to adopt or avoid — not to replicate, but to inform our design.

### 8.1 `academic-paper-reviewer` (Imbad0202/academic-research-skills)

**What it does:** Simulates a full academic peer review panel — Editor-in-Chief + 3 specialist reviewers + a Devil's Advocate — each reading the paper from a different angle, then a synthesizer agent combines the reports.

**Architecture:**
- Phase 0: A `field_analyst_agent` reads the full paper, identifies the discipline, and configures 5 dynamic reviewer personas. Presents a Reviewer Configuration Card to the user for approval before proceeding.
- Phase 1: 5 reviewer agents run **in parallel**, each focused on a non-overlapping dimension (methodology, domain expertise, cross-disciplinary, EIC fit, core argument challenge).
- Phase 2: A `editorial_synthesizer_agent` consolidates all reports into an Editorial Decision + Revision Roadmap.

**Key design lessons:**
- The "presenter configuration to user for approval" step (analogous to our TOC presentation) is explicitly baked into the workflow — not an afterthought.
- 29 anti-patterns are explicitly documented in the SKILL.md (what not to do, and why). This is excellent defensive design.
- Uses parallel agents deliberately, but only because each reviewer is truly independent (non-overlapping scope). This would not work for our refine-style sequential summarization.
- Targeted at critiquing/evaluating papers, not extracting and summarizing content. Different use case — but the multi-phase orchestration pattern is instructive.

### 8.2 `rag-architect` (alirezarezvani/claude-skills)

**What it does:** A knowledge-heavy skill that advises on designing RAG pipelines — chunking strategies, embedding model selection, vector database choice, retrieval strategies.

**Key design lessons:**
- Covers all chunking strategies with explicit pros/cons tables — the same framework we use in this knowledge base.
- Recommends document-aware chunking (PDF pages, Word sections, HTML elements) as best for multi-format document collections — directly supports our structural chunking approach.
- Notes that 10–20% chunk overlap helps maintain context continuity at boundaries — this is less relevant for our section-based approach (we carry the full synthesis forward), but worth knowing for fallback fixed-size chunking.

### 8.3 `self-improving-agent` (alirezarezvani/claude-skills)

**What it does:** Monitors patterns across conversations. When a pattern recurs 2–3 times, it flags it for review, and approved patterns graduate from memory to CLAUDE.md as enforced rules.

**Key design lesson:** The idea of graduating learnings from "observed pattern" → "proposed rule" → "user-approved rule" is the same principle behind our Learnings section + "propose before editing pipeline" rule. Confirms this is a robust approach to skill evolution.

### 8.4 `repomix` (yamadashy/repomix)

**What it does:** Packs an entire codebase into a single structured file (XML/Markdown/JSON) for AI analysis. Designed specifically to give LLMs a coherent, single-pass view of a large codebase.

**Key design lesson:** Repomix solves a different version of the same problem — how to give an LLM access to more content than fits in context. Its solution (pack everything into one structured file with a good index) works for code because code is highly cross-referenced and benefits from a global view. For documents, our approach (process section-by-section with running synthesis) is better because document content is more linearly ordered and sections are more independent.

### 8.5 What's missing in the existing ecosystem

After reviewing available skills, no existing public skill combines:
- Structural (heading-based) chunking of already-converted Markdown
- Refine-pattern sequential processing with output-file-as-memory
- TOC presentation + user confirmation before processing
- Project-specific output conventions (frontmatter, sequential naming, executive summary)

The `doc-review` skill fills a genuine gap.

---

## 9. Design Decisions for `doc-review` — Summary

| Decision | Choice | Rationale |
|---|---|---|
| Skill isolation | `context: fork` | Prevents context blowout in main session |
| Multiple documents | Sequential, fully one at a time | Avoids agent/write-permission conflicts; maintains coherence |
| Single document chunking | Section-based (top-level `##` headings) | Semantic coherence; Markdown structure is explicit |
| Sub-chunking long sections | Flag to user (>500 lines), use sub-headings | Keeps user informed; avoids silent arbitrary splits |
| Short sections | Group with adjacent section (<80 lines) | Avoids trivial inference calls |
| Processing pattern | Refine (sequential accumulation) | Cross-section awareness; narrative coherence |
| Carry-forward context | Output file itself (+ tiered distillation for 20+ sections) | Scales naturally; no separate memory object |
| Parallel agents | Never — not even across documents | Write conflicts; coherence loss |
| TOC presentation | Yes — headings + line counts, user confirms | Best practice; lets user flag priorities |
| Focus area | Comprehensive default, user-overridable | Flexible without being vague |
| Default focus | Purpose & Context → Methodology → Indicators → Data Sources → Findings → Limitations → Open Questions | Covers full evaluation report lifecycle |
| Incremental writing | Append after each section, not batch at end | Preserves work on failure; aligns with Refine pattern |
| Numbers & figures | Quote verbatim, flag ambiguities | Guards against hallucination on precise values |

---

## 10. External Resources

- [Lost in the Middle — Liu et al. (ACL 2024)](https://aclanthology.org/2024.tacl-1.9/)
- [LangChain: 5 Levels of Summarization](https://github.com/gkamradt/langchain-tutorials/blob/main/data_generation/5%20Levels%20Of%20Summarization%20-%20Novice%20To%20Expert.ipynb)
- [Google Cloud: Map-Reduce and Refine for Long Documents](https://cloud.google.com/blog/products/ai-machine-learning/long-document-summarization-with-workflows-and-gemini-models)
- [Pinecone: Chunking Strategies for LLM Applications](https://www.pinecone.io/learn/chunking-strategies/)
- [Firecrawl: Best Chunking Strategies for RAG in 2026](https://www.firecrawl.dev/blog/best-chunking-strategies-rag)
- [Anthropic: Prompt Caching](https://www.anthropic.com/news/prompt-caching)
- [Anthropic: Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)
- [Anthropic: Effective Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [ClaudeLog: What is Context Fork in Claude Code](https://claudelog.com/faqs/what-is-context-fork-in-claude-code/)
- [Claude Code Skill Authoring Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [alirezarezvani/claude-skills — RAG Architect](https://github.com/alirezarezvani/claude-skills/blob/main/engineering/rag-architect/SKILL.md)
- [Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills)
- [StackAI: Sequential, Parallel, and Hierarchical Agent Architectures](https://www.stackai.com/insights/ai-agent-architecture-patterns-sequential-parallel-and-hierarchical-workflows)
