---
name: log-session
version: 1.0
description: Records work as it happens across the project's four tracking layers — appends a timestamped entry to today's session log and keeps PENDING.md, decision_log.md and WORKSTREAMS.md in sync. Use after each milestone, failed attempt, significant decision or new next step (do not wait for the end of the session), and whenever the user asks to log progress.
---

# Log Session

The four layers answer different questions and must not be merged: the **session log** is what happened, **PENDING.md** is what's still open, **decision_log.md** is why, **WORKSTREAMS.md** is where each topic stands. One logging pass updates every layer the event touched.

## 1. Session log (always)

- File: `08_ai_management/01_progress_logs/YYYY-MM-DD_session.md` for today (`date +%F`). If it doesn't exist, create it with the heading `# Session Log — YYYY-MM-DD`.
- **Append** a block using `08_ai_management/03_system_templates/log_template.md`, headed with the current time (`## HH:MM - Session Update`, from `date +%H:%M`). Never rewrite or delete earlier blocks.
- Fill **Goal**, **Completed / Milestones** (scripts touched, outputs produced, skills changed with version), **Dead Ends / Failed Attempts** (what broke and why it was abandoned — this prevents repeating mistakes), **⏭️ Next Steps**.

## 2. PENDING.md (whenever next steps or completions appear)

- Every new item in `⏭️ Next Steps` is also added under `## Open`:
  `` - `[YYYY-MM-DD]` **Short title.** One-line description. *Origin: YYYY-MM-DD_session.md.* ``
- A finished item moves from `## Open` to `## Recently Done`, with `` `→ done YYYY-MM-DD` `` appended.
- A deliberately dropped item moves to `## Cancelled / Wontfix` with a one-line reason.
- On a cleanup pass, Recently Done / Cancelled items older than ~30 days may be deleted (the session logs keep the permanent record).

## 3. decision_log.md (whenever a significant choice was made)

For methodological, econometric, data-sourcing, survey-design, indicator or AI-tooling decisions: append an entry **at the bottom** using `08_ai_management/03_system_templates/decision_template.md` — context and source (with URL / citation for external data), the decision, and the alternatives rejected with reasons.

## 4. WORKSTREAMS.md (only if a workstream's state changed)

A phase completed, a decision landed, a blocker appeared or cleared. Otherwise skip it. For each workstream that moved, following `08_ai_management/03_system_templates/workstream_template.md`:
- update **Status** (🔴 / 🟡 / 🟢 / ⏸️) and rewrite **Current State** in a few lines;
- add a dated **Advances** bullet pointing to the session log;
- link new entries under **Key Decisions** (decision_log) and **Open Items** (PENDING).

It is an index, not a diary: synthesise and link; never paste narrative.

## 5. README (if the project itself changed)

A new dependency, data source, pipeline step, or a methodology or status change → update the matching `README.md` section.

## Report back

One or two lines: which files were updated and what was added.

## Learnings
<!-- Candidate observations go here (see .claude/rules/skills_maintenance.md). -->
