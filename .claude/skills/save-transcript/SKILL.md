---
name: save-transcript
version: 1.0
description: Exports the current conversation as a Markdown transcript to 08_ai_management/04_knowledge_base/transcripts/. Use only when the user asks to save, export or archive the conversation.
---

# Save Transcript

## Steps

1. **File name:** `08_ai_management/04_knowledge_base/transcripts/YYYY-MM-DD-HH-mm_session.md`, using the current local time (`date +%F-%H-%M`).
2. **Header:** date, project, branch (`git branch --show-current`), and a 3–5 bullet summary of what the conversation covered.
3. **Body:** the exchange in order —
   - `### User` — the user's messages, verbatim;
   - `### Claude` — Claude's replies, verbatim for substance; tool calls condensed to one line each (e.g. *ran `Rscript 04_scripts/02_clean.R` — succeeded*), never raw file dumps or long command output.
4. **Be honest about gaps:** if earlier parts of the conversation were compacted or summarised, say so at the top and mark where the verbatim record begins. Don't reconstruct text you no longer have.
5. **Never include data:** no data rows, personal information or credentials, even if they appeared in tool output.
6. Tell the user the path of the saved file.

## Learnings
<!-- Candidate observations go here (see .claude/rules/skills_maintenance.md). -->
