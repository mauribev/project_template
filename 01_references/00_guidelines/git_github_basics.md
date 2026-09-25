# Git & GitHub — The Basics, Explained Simply

This guide explains *how* Git and GitHub work, so that the team routine in `git_team_workflow.md` makes sense. **Section 0 is all you need day to day.** The rest explains it with one small, real example — read it once, then come back to the cheat sheet (Section 11) and FAQ (Section 12) when needed.

Two kinds of boxes appear below:
- **Command output** — exactly what Git prints for the command after `$`, produced on a real (small) repository. A few repeated hint lines are trimmed; your commit IDs (like `1e9b60c`) will differ.
- **Diagram** — a drawing to explain an idea. Git never prints these.

---

## 0. The everyday loop on one screen

```
# Start a task
git switch main                      # go to main                          (Section 5, Step 0)
git pull                             # get the latest from GitHub
git switch -c fix/short-name         # a new branch for this task          (Step 1)

# While working — at every milestone
git status                           # which files changed?                (Section 3)
git diff                             # what exactly changed?
git add -A                           # put the changes in the "basket"     (Section 2)
git diff --staged --stat             # check what will be saved
git commit -m "fix: what you did"    # save                                (Step 4)

# Share
git push -u origin fix/short-name    # upload the branch (later just: git push)   (Step 6)
#   → on github.com: open a pull request, review, merge                          (Section 6)

# Tidy up after the merge
git switch main
git pull                             # your main catches up with GitHub     (Step 8)
git branch -d fix/short-name         # delete the finished branch
git fetch --prune                    # forget branches deleted on GitHub
```

**Where to type these commands:**
- a **terminal** opened in the project folder (Terminal on Mac; *Git Bash* on Windows; or the *Terminal* tab in RStudio / VS Code);
- inside **Claude Code**, by starting the line with `!` (e.g. `! git status`) — the output appears in the conversation, so Claude can explain it;
- or use **GitHub Desktop**, which has a button for each step (named in Section 5).

---

## 1. The example used throughout

Maria works on a midline evaluation. Her repository contains, among other things:

```
04_scripts/02_clean.R     ← merges the baseline and midline surveys
README.md                 ← project documentation, with a "Changes" list
```

The data itself is **not** in the repository — it lives on Google Drive, and the script reads it from there (Section 9 explains why that matters).

Maria has found a bug: households are merged on `hh_id` alone, but `hh_id` repeats across villages, so the merge must use `hh_id` **and** `village_id`. She will fix the script and add a line to the README. At the start, her computer and GitHub hold exactly the same version of the project.

---

## 2. The four places your work lives

**Diagram:**
```
 1. YOUR FOLDER        2. STAGING AREA         3. HISTORY              4. GITHUB
 the files you see     the "basket": changes   commits saved on        the shared copy
 and edit in RStudio   chosen for the NEXT     YOUR computer           in the cloud
                       commit

   edit a file  ──git add──►  in the basket  ──git commit──►  a commit  ──git push──►  on GitHub
                                                                        ◄──git pull───
```

1. **Your folder.** When Maria edits `02_clean.R`, the change is in her folder. Git *notices* it but has saved nothing.
2. **The basket.** `git add` puts a change in the basket: "this goes into my next save". She can still take it out (`git restore --staged <file>`).
3. **History.** `git commit` saves whatever is in the basket as a permanent snapshot — a **commit** — on her computer only.
4. **GitHub.** `git push` uploads her commits; `git pull` downloads her colleagues' commits.

**Why a basket?** So you choose what goes into each save: the script fix in one commit, the README note in another, a half-finished experiment in none. Think of **add** as *putting things in a box* and **commit** as *sealing and labelling it*. With Claude Code you rarely type `git add` yourself: Claude adds and commits at milestones and asks you first.

> **Keep in mind:** until you commit, a change belongs to **no branch** — it just sits in your folder.

---

## 3. Seeing what changed: `git status`, `git diff`, `git diff --staged`

Before saving, *look* at what you are saving — to catch mistakes, stray files, or data that doesn't belong. Each command answers a different question:

| Command | Question it answers | Compares |
|---|---|---|
| `git status` | *Which files* changed, and which are in the basket? | — (a list, no content) |
| `git diff` | What did I change that is **not in the basket yet**? | your folder ↔ the basket |
| `git diff --staged` | What **will my next commit contain**? | the basket ↔ your last commit |

Add `--stat` to either diff for a one-line-per-file summary.

### On the example
Maria has edited both files and added nothing yet:

**Command output:**
```
$ git status
On branch fix/merge-key
Changes not staged for commit:
	modified:   04_scripts/02_clean.R
	modified:   README.md
```
Both files are changed in her folder, not in the basket. `git diff` shows both changes; `git diff --staged` shows **nothing** — not because nothing was committed, but because **the basket is empty**.

She puts only the script in the basket:

**Command output:**
```
$ git add 04_scripts/02_clean.R

$ git status
On branch fix/merge-key
Changes to be committed:
	modified:   04_scripts/02_clean.R
Changes not staged for commit:
	modified:   README.md

$ git diff --stat
 README.md | 1 +

$ git diff --staged --stat
 04_scripts/02_clean.R | 4 ++--
```

| File | Changed in folder | In the basket | Shown by |
|---|---|---|---|
| `02_clean.R` | ✔ | ✔ | `git diff --staged` (will be committed) |
| `README.md` | ✔ | ✘ | `git diff` (will not) |

A **brand-new file** is invisible to `git diff` — Git only compares files it already knows. After `git add` it appears in `git diff --staged`.

### How to read a diff

**Command output:**
```
$ git diff 04_scripts/02_clean.R
diff --git a/04_scripts/02_clean.R b/04_scripts/02_clean.R
index b7d85ab..fac1921 100644
--- a/04_scripts/02_clean.R
+++ b/04_scripts/02_clean.R
@@ -2,8 +2,8 @@
 baseline <- readRDS(file.path(DATA_CLEAN, "baseline.rds"))
 midline  <- readRDS(file.path(DATA_CLEAN, "midline.rds"))
 
-# 2. Merge baseline and midline
-hh <- merge(baseline, midline, by = "hh_id")
+# 2. Merge baseline and midline (hh_id repeats across villages)
+hh <- merge(baseline, midline, by = c("hh_id", "village_id"))
 
 # 3. Save
 saveRDS(hh, file.path(DATA_CLEAN, "panel.rds"))
```
- `diff --git a/… b/…` — which file; **`a/` = before your change, `b/` = after**. The `index` line is internal — ignore it.
- `@@ -2,8 +2,8 @@` — this excerpt starts at line 2 and covers 8 lines, before and after. A file changed in several places has several such blocks.
- Lines starting with a **space** are unchanged context; **`-`** lines were removed (red on screen), **`+`** lines added (green).

So: *"the comment and the merge line were replaced; everything else is unchanged."* Git works **line by line** — changing one word shows the whole line removed and re-added. That is also why an edited line counts as 1 deletion + 1 insertion in `--stat`.

Most people read diffs in a visual tool: GitHub Desktop (click a file), RStudio's Git pane (*Diff*), VS Code (*Source Control*), or a pull request's *Files changed* tab.

---

## 4. Commits, branches, and where you are

### A commit is a snapshot; a branch is a label
Each **commit** is a saved snapshot of the whole project with a short ID, an author, a date and a message. Each commit remembers the one before it, so history is a chain. **Diagram** (commits drawn as letters; arrows point back in time):
```
A ◄── B ◄── C
```
A **branch is not a copy of your files.** It is a *label* on one commit.
- `main` is the label of the version everyone trusts.
- When you commit while "on" a branch, **that label moves forward** to the new commit; all other labels stay put.
- Creating a branch attaches a new label to the commit you are on — nothing is copied, no file changes.
- Two labels can sit on the same commit; they separate when someone commits on one of them.

**Why branches?** So unfinished work doesn't touch `main`: Maria can make several commits on `fix/merge-key` while the `main` her colleagues pull stays unchanged — until the fix is reviewed and merged (Section 6).

### The map: `git log --oneline --graph --all --decorate`
Use it when you want to know **where you are**: which branches exist, which one you are on, and whether you are ahead of or behind GitHub. (`--oneline`: one line per commit; `--graph`: draw the lanes; `--all`: every branch; `--decorate`: show the labels.)

**Command output** — Maria after her first commit on her branch:
```
$ git log --oneline --graph --all --decorate
* 1e9b60c (HEAD -> fix/merge-key) fix: merge on hh_id + village_id
* 730e8a7 (origin/main, main) chore: start project
```
- Each `*` is a commit, newest on top; the names in brackets are the labels on it.
- **`HEAD -> fix/merge-key`** — `HEAD` means **"you are here"**: her next commit will move this label.
- **`main`** — her own `main` is still on the older commit: the fix is not in `main`.
- **`origin/main`** — `origin` is Git's nickname for GitHub; `origin/main` is where `main` is **on GitHub** (see below).

### GitHub and your computer: four things to keep apart
Most confusion comes from mixing up *where* a version lives. There are four separate things — one in the cloud, three on your computer:

| # | Where | What it is | Changes when… |
|---|---|---|---|
| 1 | **GitHub** | The shared repository in the cloud | someone pushes, or merges a pull request on the website |
| 2 | **`origin/main`** (your computer) | Your computer's **last known photo** of GitHub's `main` | your computer talks to GitHub: `git fetch`, `git pull`, `git push` |
| 3 | **`main`** (your computer) | *Your own* `main` label, in your local history | *you* commit on it or pull into it |
| 4 | **Your folder** | The files you see | you switch branch or pull — it shows **whichever branch you are on** |

**GitHub never changes anything on your computer by itself.** Your computer only learns what happened when you ask.

**Worked through** — Maria is on her branch when her pull request is merged on the website:

| Moment | 1. GitHub `main` | 2. Photo `origin/main` | 3. Maria's `main` | 4. Folder shows |
|---|---|---|---|---|
| Before the merge | `730e8a7` | `730e8a7` | `730e8a7` | her branch |
| **Merge** clicked on GitHub | **`ba1315e`** | `730e8a7` (old photo) | `730e8a7` | her branch |
| `git fetch` | `ba1315e` | **`ba1315e`** | `730e8a7` | her branch |
| `git switch main` | `ba1315e` | `ba1315e` | `730e8a7` | `main` — the **old** version |
| `git pull` | `ba1315e` | `ba1315e` | **`ba1315e`** | `main` — the **new** version |

Each command brings one more column up to date; when all four agree, you are in sync.

- **`git fetch`** — *"GitHub, what's new?"* Updates the photo (`origin/...` labels) only. Your branches and files don't change. Always safe.
- **`git pull`** — a fetch **plus** moving your current branch forward **plus** updating your files.

**Command output** — what a fetch reports after a merge on GitHub:
```
$ git fetch
From https://github.com/your-team/midline-project
   730e8a7..ba1315e  main       -> origin/main
```
*"`main` on GitHub moved from `730e8a7` to `ba1315e`; your photo is updated."*

> **"Behind by N commits" can be out of date.** `git status` compares your branch with the *photo*, not with GitHub itself. If you haven't fetched since the last merge, the number is too small. `git fetch` (or `git pull`) first, then trust it.

---

## 5. Step by step: saving work on a branch

Each step: **why**, the **command**, the **GitHub Desktop** equivalent, and what **actually happens**.

**Step 0 — Start from the latest `main`.** *Why:* build on your colleagues' latest work.
```
$ git switch main
$ git pull
Already up to date.
```
*Desktop:* Current Branch = `main` → **Fetch origin** → **Pull origin** if offered.
If you are behind, `git pull` downloads the new commits **and updates the files in your folder** (never your data on Drive). Your uncommitted edits are kept — if an incoming change would overwrite one, Git stops and names the file.

**Step 1 — Create a branch for the task.** *Why:* keep the work away from `main` until it is finished. Do it **before** editing (if you forget, create it before your first commit — uncommitted edits come along).
```
$ git switch -c fix/merge-key
Switched to a new branch 'fix/merge-key'
```
*Desktop:* **Current Branch → New Branch**. A new label on the same commit; no file changes.

**Step 2 — Work.** Maria edits both files in RStudio. `git status` / `git diff` show the changes (Section 3).

**Step 3 — Add.** `git add 04_scripts/02_clean.R`, then `git diff --staged` to check. *Desktop:* the checkboxes in the *Changes* tab **are** the basket.

**Step 4 — Commit.**
```
$ git commit -m "fix: merge on hh_id + village_id"
[fix/merge-key 1e9b60c] fix: merge on hh_id + village_id
 1 file changed, 2 insertions(+), 2 deletions(-)
```
Git confirms the branch that received the commit and its ID. *Desktop:* **Commit to fix/merge-key** (the button always names your branch). Only the label you are on moves — **Diagram:**
```
A ◄── B
▲     ▲
main  fix/merge-key (HEAD)
```

**Step 5 — Commit the README too** (`git add README.md`, `git commit -m "docs: note merge-key fix"`). Several small commits per task are normal.
```
$ git log --oneline --graph --all --decorate
* ca685c5 (HEAD -> fix/merge-key) docs: note merge-key fix
* 1e9b60c fix: merge on hh_id + village_id
* 730e8a7 (origin/main, main) chore: start project
```
**So far everything is only on Maria's computer.**

**Step 6 — Push the branch.** *Why:* back it up and make it visible — without touching `main`.
```
$ git push -u origin fix/merge-key
remote: Create a pull request for 'fix/merge-key' on GitHub by visiting:
remote:      https://github.com/your-team/midline-project/pull/new/fix/merge-key
To https://github.com/your-team/midline-project.git
 * [new branch]      fix/merge-key -> fix/merge-key
branch 'fix/merge-key' set up to track 'origin/fix/merge-key'.
```
`origin` = to GitHub; `fix/merge-key` = which branch; `-u` = remember the pairing, so next time a plain `git push` works. Lines starting with `remote:` are messages *from GitHub* — here, a shortcut link to open the pull request. *Desktop:* **Publish branch**.

**Step 7 — Pull request, review, merge — on github.com** (Section 6). From the moment of the merge, `main` **on GitHub** contains the fix.

**Step 8 — Catch up and tidy up.** *Why:* the merge happened on GitHub; your computer doesn't know yet (Section 4, the four-column table).
```
$ git switch main
Your branch is up to date with 'origin/main'.      ← the photo is old: nothing fetched yet

$ git pull
Updating 730e8a7..ba1315e
Fast-forward
 04_scripts/02_clean.R | 4 ++--
 README.md             | 1 +

$ git branch -d fix/merge-key
Deleted branch fix/merge-key (was ca685c5).

$ git fetch --prune
 - [deleted]         (none)     -> origin/fix/merge-key
```
- `git pull` downloaded the merged work and updated the files; **Fast-forward** means her `main` label simply moved forward.
- `git branch -d` deletes the label — **only the label; the commits are now part of `main` for good.** (Lowercase `-d` refuses if the work isn't merged yet — a safety check.)
- `git fetch --prune` removes the photo of the branch that was deleted on GitHub.

**The final map:**
```
$ git log --oneline --graph --all --decorate
*   ba1315e (HEAD -> main, origin/main) Merge pull request #1 from fix/merge-key
|\
| * ca685c5 docs: note merge-key fix
| * 1e9b60c fix: merge on hh_id + village_id
|/
* 730e8a7 chore: start project
```
Read the lanes as a road map: history split at `730e8a7`, the two commits happened on the side road, and they joined `main` at the **merge commit** `ba1315e`.

### The shortcut: committing straight to `main`
Skip Step 1. The saving commands are **identical**; the commit simply lands on `main`:
```
$ git status
Your branch is ahead of 'origin/main' by 1 commit.

$ git push
   ba1315e..5892250  main -> main
```
No pull request, no review. If a colleague pushed in the meantime, GitHub **rejects** the push (*"fetch first"*): `git pull`, then `git push` again.

| Straight to `main` | Branch + pull request |
|---|---|
| typos, comments, one-line doc fixes | anything analytical: cleaning, indicators, models |
| trivial changes when working alone | structural changes; anything a colleague should see or review |

**Both ways save work with the same commands. The branch only decides *which label moves* — and whether `main` changes now or after a review.**

---

## 6. Pull requests

A **pull request (PR)** is a page on GitHub saying *"I propose to merge branch X into `main`"*, with the full diff, comments, and the **Merge** button. Even when working alone it is worth it: a last look at everything entering `main`, and a permanent record — *"PR #14: merge on hh_id + village_id"* — of what changed and why.

**Opening one** (after pushing the branch), any of:
- the **link** printed by `git push` (the `remote:` lines);
- the yellow banner on the repository page, *"… had recent pushes — **Compare & pull request**"* (shown for about an hour);
- **Pull requests** tab → **New pull request** → choose *base* `main` and *compare* your branch — works any time;
- *GitHub Desktop:* **Create Pull Request** (opens the same page).

**Filling it in:**
1. Check the top bar reads **base: `main` ← compare: `your-branch`** ("merge *compare* into *base*").
2. **Title** — what the change does. GitHub pre-fills it from the commit message if the branch has one commit, or from the **branch name** if it has several (*"Fix/merge key"*) — edit it; the title ends up in `main`'s history.
3. **Description** — *what* changed, *why*, *how you checked it* ("re-ran `02_clean.R`: 4,812 households, no duplicates"). `Closes #12` closes that issue automatically on merge.
4. **Create pull request.**

**Reviewing:** the **Files changed** tab shows the whole diff; tick **Viewed** per file. To comment on a line, hover over it and click the **+** (choose *Add single comment*; *Start a review* keeps comments hidden until you *Submit review*). The **Commits** tab lists the branch's commits. If changes are needed, the author commits and pushes to the same branch — the PR updates itself.

**Merging:** at the bottom of the *Conversation* tab, **Merge pull request → Confirm merge** (the default, *Create a merge commit*, is fine), then **Delete branch**. Then on your computer: Section 5, Step 8.

If GitHub says *"This branch has conflicts"* instead, see Section 8.

---

## 7. Working as a team

Everyone works the same way: **each person opens pull requests for their own branches.** The team only decides who *reviews* and *merges* them.

**Diagram:**
```
main ──●──────────────────●──────────●──────►
        \                /          /
         ●──●──●  fix/merge-key    /          (Maria)
          \                       /
           ●──●──●──●  feat/fies-index        (Juan)
```

**Maria's day with Claude Code:**
1. Morning: `git switch main`, `git pull` (the `session-start` skill checks this).
2. New task → `git switch -c feat/fies-index`; continuing → `git switch feat/fies-index`.
3. Work with Claude. At each milestone Claude commits — Claude Code asks first; Maria checks the file list (no data, nothing unexpected).
4. End of day: `git push` — backed up and visible; `main` untouched.
5. Task finished (today or next week): pull request → review → merge.

**Juan's work doesn't affect Maria** until it is merged: his pushes stay on his branch. **Nobody reviews daily work** — Maria looks once, when Juan's PR says "ready". Her next morning pull brings his merged work. (To peek at his unfinished branch: `git fetch`, `git switch feat/fies-index`, and back.)

**How much review** is a team choice, not a Git rule. A light policy for small teams: scripts that produce numbers for a report get a 10–15-minute review by the lead (description, *Files changed*, plausible outputs); documentation and small fixes are merged by their author. Larger projects add branch protection (nothing reaches `main` without a PR) and required approvals. Even a self-merged PR records who changed what, when and why — which editing files on Drive never did.

**One branch = one task** — something you'd review and merge as a unit (*clean baseline module B*, *construct the FIES index*). Not one branch per day, person or file. More work on the same task → same branch; a new task → back to `main`, pull, new branch.

> **Stacked branches.** Starting a branch from *another unmerged branch* (because task 2 needs task 1's changes) works, but the PRs must then be merged **in order**, and task 2's PR shows task 1's changes until task 1 is merged. Simpler: **merge task 1 first**, pull `main`, then start task 2.

---

## 8. Conflicts: two people change the same lines

Git combines work automatically when people changed **different files or different parts of a file**. A **conflict** happens only when two people changed **the same lines** — Git asks a human to choose.

**Example.** Juan fixed the merge line (keeping baseline households missing at midline) and his PR was merged. Maria, on her branch, changed the same line. She brings the new `main` into her branch:

**Command output:**
```
$ git pull origin main
CONFLICT (content): Merge conflict in 04_scripts/02_clean.R
Automatic merge failed; fix conflicts and then commit the result.
```
Git writes **both versions** into the file:
```
<<<<<<< HEAD
hh <- merge(baseline, midline, by = c("hh_id", "village_id"), suffixes = c("_bl", "_ml"))
=======
hh <- merge(baseline, midline, by = c("hh_id", "village_id"), all.x = TRUE)
>>>>>>> 74003280d9e78f56c9fc8cda36695273effa4f56
```
Top part: **her** version (HEAD); bottom part: the **incoming** one (Juan's, from `main`).

**To resolve:**
1. Edit the file to what it should be — often a combination: `…, all.x = TRUE, suffixes = c("_bl", "_ml"))`.
2. Delete the three marker lines (`<<<<<<<`, `=======`, `>>>>>>>`).
3. Re-run the script.
4. `git add 04_scripts/02_clean.R`, `git commit`, `git push`.

Lost? `git merge --abort` returns everything to before the pull. RStudio, VS Code and GitHub Desktop highlight conflicts and offer buttons to pick a side. A conflict shown on a PR page is fixed the same way, on your computer.

**Avoiding most conflicts:** pull `main` every morning and branch from it; keep branches short (days, not weeks); one person per script; announce when you touch shared files (master script, paths file, README); merge small PRs often.

---

## 9. Code on GitHub, data on Google Drive

Git keeps **one version of the code per branch**; Google Drive keeps **one copy of each data file**, and knows nothing about branches.

**The problem** — and it exists with or without branches: when Maria runs her *modified, unmerged* `02_clean.R`, it overwrites `panel.rds` in the shared `03_clean_data`. Juan, running the analysis from `main`, silently reads a panel built with code he doesn't have.

**The rule:** *work in progress writes to `02_temp_data`; only the finished code in `main` writes to `03_clean_data`.* In practice:
1. **Raw data is read-only** for everyone — so only derived files can ever be affected, and those can be regenerated.
2. **Branch runs write elsewhere** — a personal or per-branch folder under `02_temp_data`. This can be automatic: a person (not the AI) can add to `00_setup_paths.R`
   ```r
   branch <- system("git branch --show-current", intern = TRUE)
   if (branch != "main") DATA_CLEAN <- file.path(DATA_TEMP, "branches", branch)
   ```
3. **After a merge, regenerate** the shared files by running the scripts (or the master script) from `main`.
4. **Record which code produced a file** — e.g. write `git rev-parse --short HEAD` into the log.
5. **Tell the team** when shared data is regenerated; log significant changes in `decision_log.md`.

Data-engineering teams solve the same problem with separate *environments*: each developer's work writes to a private area, and only the official pipeline, run from `main`, writes the shared data.

---

## 10. More GitHub features

| Feature | What it is | Why it helps |
|---|---|---|
| **Issue** | A numbered ticket for a bug, task or question; can be labelled and assigned. | A to-do list attached to the code. `Closes #12` in a PR closes it on merge, linking the problem to its fix. |
| **Tag / Release** | A permanent name for one commit (`v1.1`, `midline-report-sent-2026-10-02`). | You can always return to exactly what the client received. |
| **Branch protection** | A setting that forces changes to `main` through a PR. | Nobody — human or AI — pushes to `main` by accident. |
| **PR / issue templates** | Pre-filled text from a `.github/` folder. | A checklist on every PR: "☐ no data ☐ runs from `00_master`". |
| **Actions** | Automatic checks on every PR. | E.g. repeat the large-file check on GitHub's side. |

- **Issues and pull requests share one numbering:** if PRs #1 and #2 exist, the next issue is #3.
- **Issues vs `PENDING.md`:** issues for anything others should see, discuss or be assigned; `PENDING.md` as the short queue Claude reads each session, pointing to issue numbers (*"finish #12"*).
- **Hooks** (scripts run automatically before a commit) protect this template's rule that data stays on Drive: they list large data files and ask before committing them. See the *Safety net* section of the scaffold `README.md`.

---

## 11. Cheat sheet

**Looking** (safe — never changes anything)
| Command | Use it when… |
|---|---|
| `git status` | Always first: your branch, changed files, the basket, ahead/behind. |
| `git diff` / `git diff --staged` | You want the exact lines changed — not added yet / about to be committed. |
| `… --stat` | You want a summary rather than every line. |
| `git log --oneline --graph --all --decorate` | You want the map: branches, where you are, where GitHub is. |
| `git show <id>` | You want to see what one past commit changed. |
| `git diff main..my-branch --stat` | You want what your branch changes compared with `main` (what its PR will show). |

**Saving**
| Command | What it does |
|---|---|
| `git add <file>` / `git add -A` | One file / everything (new and deleted files too) into the basket. |
| `git restore --staged <file>` | Take a file out of the basket — your edits are kept. |
| `git commit -m "message"` | Save the basket as a commit (`fix: …`, `feat: …`, `docs: …`). |

**Branches**
| Command | What it does |
|---|---|
| `git switch -c <name>` | Create a branch here and switch to it. |
| `git switch <name>` | Switch branch — your folder changes to that branch's version. |
| `git branch` | List your branches (`*` = current). |
| `git branch -d <name>` | Delete a merged branch's label (refuses if not merged). |

**Syncing with GitHub**
| Command | What it does |
|---|---|
| `git pull` | Get new commits for this branch **and update your files**. |
| `git fetch` / `git fetch --prune` | Only check GitHub (updates the photo) / and forget branches deleted there. |
| `git push -u origin <branch>` / `git push` | First upload of a branch / later uploads. |
| `git pull origin main` | While on your branch: bring the latest `main` into it. |

**Undoing**
| Command | What it does |
|---|---|
| `git restore <file>` | **Discard** uncommitted edits to a file. Cannot be undone. |
| `git merge --abort` | Cancel a merge that produced conflicts. |
| `git revert <id>` | Safely undo a pushed commit (adds a reversing commit). |

*Older guides use `git checkout` for switching branches and discarding edits; `git switch` / `git restore` are the newer names.*

---

## 12. FAQ

**Why is `git diff --staged` empty before I add anything?** It compares the basket with the last commit; an empty basket means no difference. Right after a commit it is empty again.

**Do I need to add files one by one when working with Claude?** No — Claude adds and commits at milestones and Claude Code asks you first. Check the file list and approve. Without Claude, `git add -A` stages everything; check with `git diff --staged --stat`.

**When should I commit?** Whenever a piece works ("the merge runs", "the table renders") — several times per task, not once a week.

**Does `git pull` change my files?** Yes — it updates repository files in your folder to the latest version (never your data on Drive). Uncommitted edits are kept; if one would be overwritten, Git stops and tells you.

**I stopped tracking some files (`git rm --cached`) — are they safe?** On *your* computer, yes. But the commit records them as **deleted**, so anyone who pulls it — including you, on another machine or after switching away and back — loses their local copy. They remain in history (`git restore --source=<older-commit> -- <path>` brings them back).

**Do I need to review colleagues' branches every day?** No — once, when they open a pull request.

**Does only the lead open pull requests?** No — everyone, for their own branches. Conflicts are avoided by short branches, one person per script and pulling `main` often (Section 8).

**Can two people share a branch?** Yes, but both must pull before starting and push often — like a mini-`main`. Usually simpler to have one branch each.

---

## 13. Glossary

- **Repository (repo):** the project folder plus its full history (in the hidden `.git` folder).
- **Commit:** a saved snapshot, with ID, author, date and message.
- **Staging area ("basket"):** the changes chosen for the next commit.
- **Branch:** a movable label on a commit; moves forward when you commit on it.
- **`main`:** the trusted branch everyone pulls from.
- **HEAD:** "you are here" — your current branch.
- **`origin`:** the GitHub copy; **`origin/main`:** your last known photo of GitHub's `main`.
- **Push / pull / fetch:** upload / download and update your files / only check.
- **Merge / merge commit:** combine a branch into another / the commit that joins them.
- **Fast-forward:** your label simply moves forward; nothing to combine.
- **Pull request (PR):** a GitHub page proposing, reviewing and performing a merge.
- **Conflict:** two changes to the same lines that Git can't combine by itself.
- **Issue:** a numbered ticket for a task, bug or question.
- **Tag / release:** a permanent name for one commit.
