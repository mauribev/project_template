---
paths:
  - ".claude/skills/**"
---

# Creating and changing skills

**Structure.** Each skill lives in `.claude/skills/<skill-name>/` with `SKILL.md` (the active instructions, with `name`, `version` and `description` in the frontmatter), `CHANGELOG.md` (version history and why each change was made), and optionally `KNOWLEDGE_BASE.md` (design rationale for complex skills) and `scripts/`.

**Scope.** Project skills (`.claude/skills/`) work only in this repository; global skills (`~/.claude/skills/`) work everywhere. After changing a project skill that is also used globally, sync it: `cp -R .claude/skills/<name> ~/.claude/skills/`.

**Versioning — candidate → promote → version cut.**
1. New observations go into the `## Learnings` section of `SKILL.md` as candidates.
2. A learning that recurs 2–3 times is promoted into the core instructions, and the entry is archived in `CHANGELOG.md`.
3. When `## Learnings` passes ~8 entries, propose a version cut: fold in mature learnings, clear the section, bump `version`, and archive the old file as `SKILL_vN.md`.
4. Never change a skill's core instructions without proposing the change and getting the user's approval.

**Deprecation.** Don't delete a superseded skill: add a `⚠️ DEPRECATED` notice at the top of `SKILL.md` and in its frontmatter description, record the reason and the replacement in `CHANGELOG.md`, and keep the folder until the user explicitly authorises deletion.
