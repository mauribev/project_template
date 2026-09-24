#!/bin/sh
# ==============================================================================
# check_large_files.sh — Claude Code hook: confirm large files before Claude commits
# ==============================================================================
# WHAT THIS IS
#   A Claude Code hook (registered in .claude/settings.json under "PreToolUse").
#   Claude Code runs it just BEFORE Claude executes a git command in Bash, and
#   passes the planned command to it as JSON on stdin.
#
#   It reuses the list from the git hook (.githooks/pre-commit --list), so the
#   size limits live in one place only.
#
# WHAT IT RETURNS
#   - Nothing large staged -> prints nothing, exits 0: Claude Code carries on
#     with its normal permission rules.
#   - Large files staged   -> prints a JSON "ask" decision: Claude Code shows
#     you the list and waits for Yes / No (even in auto mode). It also writes an
#     approval note (.git/large_files_approved) so the git hook, which cannot
#     ask Claude anything, knows you already confirmed this exact list.
# ==============================================================================

input=$(cat)

# 1. Only act on commits ------------------------------------------------------
# settings.json already limits this hook to git commands ("if": "Bash(git *)");
# here we keep only the ones that commit. jq reads the command out of the JSON
# when installed; otherwise the raw JSON text is searched instead.
if command -v jq >/dev/null 2>&1; then
  cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty')
else
  cmd=$input
fi
case "$cmd" in
  *commit*) ;;
  *) exit 0 ;;
esac

# 2. Ask the git hook which staged files are too large --------------------------
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
[ -f .githooks/pre-commit ] || exit 0
flagged=$(sh .githooks/pre-commit --list)
approval_file="$(git rev-parse --git-dir)/large_files_approved"

if [ -z "$flagged" ]; then
  rm -f "$approval_file"   # clear any stale note from an earlier, declined prompt
  exit 0
fi

# 3. Leave the approval note, then ask the user -----------------------------------
# If the user answers No, the command never runs and the note is simply
# overwritten or removed on the next commit attempt.
printf '%s\n' "$flagged" > "$approval_file"

data_mb=$(sed -n 's/^DATA_LIMIT_MB=//p' .githooks/pre-commit)
any_mb=$(sed -n 's/^ANY_LIMIT_MB=//p' .githooks/pre-commit)

# JSON strings cannot contain raw newlines or unescaped quotes/backslashes:
# escape \ and ", then join the lines with a literal \n.
to_json() { sed 's/\\/\\\\/g; s/"/\\"/g' | awk '{ printf "%s\\n", $0 }'; }

reason=$(printf 'Large files in this commit (limits: data files %s MB, any file %s MB):\n%s\nReal data normally lives on Google Drive. Commit these anyway?' \
  "$data_mb" "$any_mb" "$flagged" | to_json)
context=$(printf 'The large-file hook asked the user to confirm committing:\n%s' "$flagged" | to_json)

# permissionDecisionReason is shown to the user; additionalContext tells Claude.
printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"%s","additionalContext":"%s"}}\n' \
  "$reason" "$context"
exit 0
