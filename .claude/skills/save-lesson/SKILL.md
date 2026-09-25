---
name: save-lesson
version: 1.0
description: Writes a reusable lesson into 08_ai_management/04_knowledge_base/learnings.md in the project's standard format, with taxonomy tags and real references. Use when the user says "save this lesson" (or any paraphrase), or after the user accepts Claude's suggestion to record a non-obvious insight, reusable coding pattern, workflow improvement or debugging takeaway.
---

# Save Lesson

`learnings.md` is written **for the human user** as a durable learning resource, not as notes for Claude.

## Steps

1. **Extract the core concept** from the recent work: the insight itself, not the story of the session.
2. **Tag it** with 1–5 tags from the Standard Taxonomy listed at the top of `learnings.md`. Invent a new tag only for a genuinely niche concept, and only after the user agrees.
3. **Write the entry** using `08_ai_management/03_system_templates/learning_template.md`:
   - **The Core Insight:** a full explanation of the concept, method, dataset or framework.
   - **Application to this Project:** what problem it solved here, and where (scripts, outputs).
   - **Key Takeaways & Nuances:** limitations, caveats, things to remember.
   - **References & Further Reading:** 2–3 real sources with links (seminal papers, textbooks, J-PAL / World Bank / official documentation). Only cite sources you can verify — look them up if a web tool is available. Never invent a citation or URL; if you can't verify one, say so in the entry.
4. **Append** it at the bottom of `08_ai_management/04_knowledge_base/learnings.md`, headed `## [YYYY-MM-DD] - [Lesson: Short title]`.
5. **Too big for one entry?** If the topic needs math, derivations or a step-by-step procedure, propose a dedicated `08_ai_management/04_knowledge_base/methodology_<topic>.md` instead (depth and format: see `_examples/`), and link to it from a short learnings entry.

## Proactive suggestions

When you notice a lesson-worthy moment, ask once: *"That feels like a candidate for `learnings.md` — want me to write it up?"* If the user declines, drop it without further discussion.

## Learnings
<!-- Candidate observations go here (see .claude/rules/skills_maintenance.md). -->
