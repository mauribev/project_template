---
name: session-start
version: 1.0
description: Restores project context at the start of a work session — reads the latest session log, the relevant WORKSTREAMS.md sections, open PENDING.md items and recent decisions, then checks git against the remote. Use when the user says "pick up where we left off", "where were we", "let's continue", or starts a new session on ongoing project work.
---

# Session Start

Rebuild context from the project's four tracking layers before doing any work. Read, summarise, and stop — do not start the task until the user confirms what to work on.

## Steps

1. **Latest chronicle.** List `08_ai_management/01_progress_logs/` and read the most recent `YYYY-MM-DD_session.md` in full. If its `⏭️ Next Steps` point back to earlier work, also read the one before it.
2. **Board.** Read `08_ai_management/01_progress_logs/WORKSTREAMS.md`. If the user named a task, read that workstream's section closely; otherwise note each workstream's Status line.
3. **Queue.** Read `## Open` in `08_ai_management/01_progress_logs/PENDING.md` and pick out the items relevant to the task (or the oldest / most pressing, if no task was named).
4. **Ledger.** Skim `08_ai_management/02_quality_reports/decision_log.md`: the last few entries, plus any entry that bears on the task.
5. **Git.** Run `git fetch` and `git status`.
   - Behind the remote → tell the user and ask before running `git pull`.
   - Uncommitted changes → list them; they may be unfinished work from last time.
   - Report the current branch.

## Report back (short)

- **Where we left off:** 2–4 bullets from the latest log and board.
- **Open items that matter now:** from PENDING, with their dates.
- **Relevant decisions:** titles only, one line each.
- **Git:** branch, ahead/behind, uncommitted files.
- **Suggested next step** — then ask the user to confirm or redirect.

Don't create today's session log yet; the `log-session` skill creates it at the first milestone.

## Learnings
<!-- Candidate observations go here (see .claude/rules/skills_maintenance.md). -->
