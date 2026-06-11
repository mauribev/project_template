# Workstream Entry Template

*Instructions for Claude: This is the shape of a single section in `01_progress_logs/WORKSTREAMS.md`. WORKSTREAMS.md is the topic-indexed **synthesis** layer — an index over the chronological session logs, the decision ledger, and the PENDING queue. It is NOT a diary: synthesize the current state in a few lines and link out to the detailed records instead of restating them.*

*When to update: only when a workstream's **state** meaningfully changes (a phase completes, a decision lands, a blocker appears/clears). When you log a session milestone or a `decision_log.md` entry that advances a workstream, reflect the new state in the matching WORKSTREAMS.md section in the same pass.*

*Status values: 🔴 Not started · 🟡 In progress · 🟢 Done / stable · ⏸️ Paused / blocked.*

---

## [emoji] [Workstream Name]
**Status:** [🔴 / 🟡 / 🟢 / ⏸️]
**Current State:** [One short paragraph — the *now*. What phase is this workstream in, what's the headline status, what (if anything) blocks it. Synthesize; do not paste narrative.]
**Advances:**
- `[YYYY-MM-DD]` [What concretely moved on this date.] — *see `YYYY-MM-DD_session.md`*
- `[YYYY-MM-DD]` […]
**Key Decisions:** [Link to the relevant `decision_log.md → [Decision Title]` entries, or "none yet".]
**Open Items:** [Link to the relevant `PENDING.md → [item title]` entries, or "none".]

---

### Notes on use
- **Link, don't duplicate.** Point to `YYYY-MM-DD_session.md`, `decision_log.md`, and `PENDING.md` rather than copying their content.
- **Keep Advances pruned.** A few recent, meaningful bullets — not every micro-step. The session logs hold the full chronicle.
- **Add/rename/remove workstreams** to fit the project. The starter set in WORKSTREAMS.md (Lit Review, Survey Design, Sampling & Weights, Cleaning, Construction, Analysis, Reporting, Dissemination, AI/Tooling) is a default, not a fixed schema.
