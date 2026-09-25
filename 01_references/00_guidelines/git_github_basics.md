# Git & GitHub — The Basics, Explained Simply

This guide explains *how* Git and GitHub work, so that the team routine in `git_team_workflow.md` makes sense. It follows one small example from start to finish. Read it once top to bottom; afterwards, the cheat sheet (Section 13), the FAQ (Section 14) and the glossary (Section 15) are there for quick reference.

**Two kinds of boxes appear in this guide:**
- **Command output** — exactly what Git prints when you run the command shown after `$`. These were produced by running the commands on a real (small) repository; a few repeated hint lines were trimmed for readability. The commit IDs (like `1e9b60c`) will be different on your computer.
- **Diagram** — a drawing to explain an idea. Git does not print these.

---

## 1. The example used throughout

Maria works on a midline evaluation. The project repository contains, among other things, a cleaning script and the README:

```
04_scripts/02_clean.R     ← merges the baseline and midline surveys
README.md                 ← project documentation, with a "Changes" list
```

The data itself (`baseline.rds`, `midline.rds`, …) is **not** in the repository — it lives on Google Drive and the script reads it from there (Section 9 explains why that matters).

Maria has found a bug: households are merged on `hh_id` alone, but `hh_id` repeats across villages, so the merge must use `hh_id` **and** `village_id`. She will fix the script and add a line to the README.

At the start, everything is up to date: her computer and GitHub hold exactly the same version of the project.

---

## 2. The four places your work lives

Every change travels through up to four places. Understanding them is 80% of understanding Git.

**Diagram:**
```
 1. YOUR FOLDER        2. STAGING AREA         3. HISTORY              4. GITHUB
 the files you see     the "basket": changes   commits saved on        the shared copy
 and edit in RStudio   chosen for the NEXT     YOUR computer           in the cloud
                       commit

   edit a file  ──git add──►  in the basket  ──git commit──►  a commit  ──git push──►  on GitHub
                                                                        ◄──git pull───
```

1. **Your folder.** When Maria edits `02_clean.R` in RStudio, the change is in her folder. Git *notices* it, but nothing is saved in Git yet.
2. **The staging area ("basket").** `git add` puts a change in the basket: "this goes into my next save". Nothing is saved yet; she can still take it out (`git restore --staged <file>`).
3. **History.** `git commit` saves whatever is in the basket as a permanent snapshot — a **commit** — on her computer only.
4. **GitHub.** `git push` uploads her commits so the team can see them; `git pull` downloads the team's commits to her computer.

**Why a basket at all?** So you choose what goes into each save. Maria can commit the script fix on its own, the README note separately, and leave a half-finished experiment out entirely. Think of **add** as *putting things in a box* and **commit** as *sealing and labelling the box*.

> **Important:** until you commit, a change belongs to **no branch**. It just sits in your folder (or basket). Branches are explained in Section 4; keep this sentence in mind.

---

## 3. Seeing what changed: `git status`, `git diff`, `git diff --staged`

Before saving anything, you want to *look* at what you are about to save — to catch mistakes, stray files, or data that should not be there. Three commands do this. Each one answers a different question:

| Command | Question it answers | Compares |
|---|---|---|
| `git status` | *Which files* changed, and which are in the basket? | — (a list, no content) |
| `git diff` | What exactly did I change that is **not in the basket yet**? | your folder ↔ the basket |
| `git diff --staged` | What exactly **will my next commit contain**? | the basket ↔ your last commit |

Add `--stat` to either diff for a one-line-per-file summary instead of the full content.

### Seeing it on the example

Maria has edited both files but not added anything yet.

**Command output:**
```
$ git status
On branch fix/merge-key
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   04_scripts/02_clean.R
	modified:   README.md

no changes added to commit (use "git add" and/or "git commit -a")
```
Both files are *"not staged"*: changed in her folder, not in the basket. (In a terminal with colours they appear in red.)

`git diff` would now show the changes in both files, and `git diff --staged` shows **nothing at all** — not because nothing was committed, but because **the basket is empty**, so it is identical to the last commit.

Now she puts only the script into the basket:

**Command output:**
```
$ git add 04_scripts/02_clean.R

$ git status
On branch fix/merge-key
Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
	modified:   04_scripts/02_clean.R

Changes not staged for commit:
	modified:   README.md

$ git diff --stat
 README.md | 1 +
 1 file changed, 1 insertion(+)

$ git diff --staged --stat
 04_scripts/02_clean.R | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)
```
The two diffs have split the work between them: `git diff` shows only the README (changed, not in the basket); `git diff --staged` shows only the script (in the basket — this is what the next commit will contain).

| File | In the folder | In the basket | Shown by |
|---|---|---|---|
| `02_clean.R` | changed | ✔ added | `git diff --staged` |
| `README.md` | changed | ✘ not added | `git diff` |

One more thing: **a brand-new file is invisible to `git diff`** — Git only compares files it already knows. After `git add`, a new file shows up in `git diff --staged` (entirely as added lines).

### How to read a diff

This is the full `git diff` for the script, before it was added:

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

Line by line:
- `diff --git a/… b/…` — which file. **`a/` is the version before your change, `b/` the version after.**
- `index b7d85ab..fac1921 100644` — Git's internal IDs for the two versions. Ignore it.
- `--- a/…` and `+++ b/…` — a legend: lines marked `-` come from the *before* version, lines marked `+` from the *after* version.
- `@@ -2,8 +2,8 @@` — a **hunk header**: "this excerpt starts at line 2 and covers 8 lines, before (`-2,8`) and after (`+2,8`)". A file with changes in several places has several hunks.
- Lines starting with a **space** are unchanged, shown only as context so you can see *where* the change is.
- Lines starting with **`-`** were removed (red on screen); lines starting with **`+`** were added (green).

So this diff says: *"in `02_clean.R`, the comment and the merge line were replaced; everything else is unchanged."* Note that Git works **line by line**: Maria changed a few words on each line, but Git shows the whole line removed and the whole new line added.

**In practice** most people read diffs in a visual tool rather than the terminal: GitHub Desktop (click a file in the *Changes* tab), RStudio's Git pane (*Diff* button), VS Code (*Source Control*), or a pull request's *Files changed* tab on GitHub. They show the same information, side by side and coloured.

---

## 4. Commits and branches

### A commit is a snapshot
Each commit is a saved snapshot of the whole project with a short ID (like `1e9b60c`), the author, the date and a message. Every commit remembers the one before it, so the history is a **chain**.

**Diagram** (in the diagrams, commits are drawn as letters — `A`, `B`, `C` — instead of long IDs; the arrow points from a commit back to the one before it):
```
A ◄── B ◄── C
(oldest)    (newest)
```

### A branch is a label on a commit
This is the part that confuses most people: **a branch is not a copy of your files.** It is a *label* (a sticky note with a name) attached to one commit.

- `main` is simply the label of the version everyone trusts.
- When you commit while you are "on" a branch, **that label moves forward** to the new commit. All other labels stay where they were.
- Creating a new branch just attaches a new label to the commit you are on. **Nothing is copied and no file changes.**
- Two labels can sit on the **same commit** — two names for the same point in history. They only separate when someone commits on one of them.

**Why use branches?** So that unfinished work doesn't touch `main`. Maria can make several commits on `fix/merge-key` while `main` — the version her colleagues pull — stays exactly as it was, until the fix is finished and reviewed (Section 6).

### Seeing the labels: `git log --oneline --graph --all --decorate`
You use this command when you want to know **where you are**: which branches exist, which one you are on, and whether your computer is ahead of or behind GitHub. It is the Git equivalent of a map with a "you are here" marker.

- `--oneline`: one line per commit (ID + message)
- `--graph`: draw the lines connecting commits when branches split and join
- `--all`: show every branch, not just the current one
- `--decorate`: print the labels (branch names) next to the commits they sit on

Here is Maria's map right after she created her branch and made her first commit (Section 5 shows how she got there):

**Command output:**
```
$ git log --oneline --graph --all --decorate
* 1e9b60c (HEAD -> fix/merge-key) fix: merge on hh_id + village_id
* 730e8a7 (origin/main, main) chore: start project
```
- Each `*` is a commit, newest at the top.
- The names in brackets are the labels sitting on that commit.
- **`HEAD -> fix/merge-key`** — `HEAD` means "**you are here**": Maria is on the branch `fix/merge-key`, so her next commit will move that label.
- **`main`** — her own `main` label is still on the older commit `730e8a7`: the fix is not in `main`.
- **`origin/main`** — `origin` is Git's nickname for the GitHub copy of the project. `origin/main` shows where `main` is **on GitHub** (as of the last time her computer talked to GitHub). Since `main` and `origin/main` sit on the same commit, her computer and GitHub agree about `main`.

`--all` shows every branch on your computer plus the known GitHub positions (`origin/...`). Branches are not "open" or "closed" — they are labels that exist until someone deletes them.

---

## 5. Step by step: saving work on a branch (the recommended way)

This follows Maria's fix from start to finish. Each step says **why**, the **command**, what **GitHub Desktop** shows, and **what actually happens**.

### Step 0 — Start from the latest `main`
**Why:** colleagues may have added work since yesterday; you want to build on top of it.

**Command output:**
```
$ git switch main
Already on 'main'
Your branch is up to date with 'origin/main'.

$ git pull
Already up to date.
```
*GitHub Desktop:* set *Current Branch* to `main`, click **Fetch origin**, then **Pull origin** if it is offered.

**What `git pull` does when you are behind:** it downloads the new commits from GitHub and **updates the files in your folder** to the latest version — yes, the files change on disk (only files in the repository; your data on Google Drive is untouched). Your own uncommitted edits are kept; if an incoming change would overwrite one of them, Git refuses and tells you which file, rather than losing your work. Section 8 shows a pull that brings in a colleague's work.

**Diagram — the situation now:**
```
A  ◄── main, origin/main  (HEAD: Maria is on main)        folder: no changes
```

### Step 1 — Create a branch for the task
**Why:** to keep the fix away from `main` until it is finished. Do this **before you start editing** — it is the first step of a task. (If you forget, nothing is lost: uncommitted edits belong to no branch, so create the branch before your first commit and the edits come along.)

**Command output:**
```
$ git switch -c fix/merge-key
Switched to a new branch 'fix/merge-key'

$ git status
On branch fix/merge-key
nothing to commit, working tree clean
```
`switch -c` means "create (`-c`) a branch with this name and switch to it". *GitHub Desktop:* **Current Branch → New Branch**.

**Diagram:**
```
A  ◄── main, origin/main, fix/merge-key  (HEAD: Maria is on fix/merge-key)
```
A new label on the same commit. No file changed.

### Step 2 — Do the work
Maria edits `02_clean.R` and `README.md` in RStudio as usual. `git status` lists both as *"not staged"*, `git diff` shows the changes, `git diff --staged` is empty (Section 3).

### Step 3 — Put the script fix in the basket
**Why:** she wants the fix saved as one clear commit, separately from the README note.

`git add 04_scripts/02_clean.R` — and `git diff --staged` now shows exactly what will be committed (Section 3).
*GitHub Desktop:* the checkboxes next to each file in the *Changes* tab **are** the basket: tick `02_clean.R` only.

### Step 4 — Commit
**Command output:**
```
$ git commit -m "fix: merge on hh_id + village_id"
[fix/merge-key 1e9b60c] fix: merge on hh_id + village_id
 1 file changed, 2 insertions(+), 2 deletions(-)
```
Git confirms which branch received the commit (`fix/merge-key`) and its ID (`1e9b60c`). *GitHub Desktop:* type the summary and click **Commit to fix/merge-key** — the button always names the branch you are on.

**Diagram — only the label she is on moved:**
```
A ◄── B
▲     ▲
main  fix/merge-key (HEAD)
origin/main
```

### Step 5 — Commit the README note too
`git add README.md`, then `git commit -m "docs: note merge-key fix"`. Several small commits on a branch are normal and useful.

**Command output:**
```
$ git log --oneline --graph --all --decorate
* ca685c5 (HEAD -> fix/merge-key) docs: note merge-key fix
* 1e9b60c fix: merge on hh_id + village_id
* 730e8a7 (origin/main, main) chore: start project
```
Two new commits on her branch; `main` has not moved. **So far everything is only on Maria's computer.**

### Step 6 — Push the branch to GitHub
**Why:** to back the work up and make it visible to the team — without touching `main`.

**Command output:**
```
$ git push -u origin fix/merge-key
To https://github.com/your-team/midline-project.git
 * [new branch]      fix/merge-key -> fix/merge-key
branch 'fix/merge-key' set up to track 'origin/fix/merge-key'.
```
- `git push` — upload commits.
- `origin` — *where to*: the GitHub copy.
- `fix/merge-key` — *which* branch.
- `-u` — "remember this pairing", so from now on a plain `git push` / `git pull` on this branch needs no extra words. Only needed the first time. *GitHub Desktop:* **Publish branch** does the same.

**Command output:**
```
$ git log --oneline --graph --all --decorate
* ca685c5 (HEAD -> fix/merge-key, origin/fix/merge-key) docs: note merge-key fix
* 1e9b60c fix: merge on hh_id + village_id
* 730e8a7 (origin/main, main) chore: start project
```
The new label `origin/fix/merge-key` shows the branch now exists on GitHub too. `origin/main` has not moved: **`main` on GitHub is untouched.**

### Step 7 — Open a pull request, review, merge (on github.com)
This happens in the browser and is explained in detail in Section 6. In short: Maria asks GitHub to merge `fix/merge-key` into `main`, looks over the changes once more (or a colleague does), and clicks **Merge**. From that moment `main` **on GitHub** contains the fix.

### Step 8 — Bring your computer up to date and tidy up
**Why:** the merge happened on GitHub, so Maria's computer doesn't know about it yet — her own `main` label is still on the old commit.

**Command output:**
```
$ git switch main
Switched to branch 'main'

$ git pull
Updating 730e8a7..ba1315e
Fast-forward
 04_scripts/02_clean.R | 4 ++--
 README.md             | 1 +
 2 files changed, 3 insertions(+), 2 deletions(-)

$ git branch -d fix/merge-key
Deleted branch fix/merge-key (was ca685c5).
```
`git pull` downloaded the merged work and updated the two files in her folder (*Fast-forward* means her `main` label simply moved forward to the new commit). `git branch -d` deleted the branch label, which is no longer needed. **Deleting a branch deletes only the label; its commits are now part of `main` forever.** (Also click **Delete branch** on the pull-request page to remove GitHub's copy of the label.)

**Command output — the final map:**
```
$ git log --oneline --graph --all --decorate
*   ba1315e (HEAD -> main, origin/main) Merge pull request #1 from fix/merge-key
|\
| * ca685c5 docs: note merge-key fix
| * 1e9b60c fix: merge on hh_id + village_id
|/
* 730e8a7 chore: start project
```
Read the lines on the left as a road map: the history split at `730e8a7`, the two commits happened on the side road (the branch), and they joined `main` again at the **merge commit** `ba1315e`. Maria is back where she started — everything up to date — ready for the next task.

### The alternative: committing straight to `main`
Same start, but she skips Step 1 and commits on `main` directly. The saving commands are **exactly the same** (`status → diff → add → diff --staged → commit`); the only difference is that the `main` label moves:

**Command output:**
```
$ git status
On branch main
Your branch is ahead of 'origin/main' by 1 commit.
  (use "git push" to publish your local commits)

$ git push
To https://github.com/your-team/midline-project.git
   ba1315e..5892250  main -> main
```
*"Ahead by 1 commit"* means her computer has a commit GitHub doesn't. After `git push`, GitHub's `main` includes it — immediately, with no review and no pull request.

**The catch:** if a colleague pushed to `main` since Maria's last pull, GitHub **rejects** her push (*"rejected — fetch first"*). She must `git pull` first (Git combines their commits with hers), then push again — and if they both edited the same lines, resolve a conflict (Section 8).

| Straight to `main` is fine for… | Use a branch + pull request for… |
|---|---|
| a typo, a comment, a one-line documentation fix | anything analytical: cleaning, indicators, models |
| trivial changes when working alone | structural changes, anything a colleague should see |
| | anything you want reviewed, recorded, or linked to an issue |

**The one thing to remember:** both ways use the same commands to save work. **The branch only decides which label moves when you commit** — and therefore whether `main` changes *now* (straight to `main`) or *later, after a review* (branch + pull request).

---

## 6. Pull requests, step by step

A **pull request (PR)** is a page on GitHub that says: *"I propose to merge branch X into `main`; here is what changes and why."* It shows the full diff, lets people comment on individual lines, and has the **Merge** button. It is how work gets from a branch into `main`.

**Why bother when working alone?** Two reasons. It is a last look at *everything* that is about to enter `main`, in one place, before it does. And it leaves a permanent, readable record: months later, *"PR #14 — merge on hh_id + village_id"* tells you what changed, why, and exactly which lines — much more than a list of commits.

### Opening one (on github.com)
1. **Push your branch** (Section 5, Step 6).
2. Open the repository on github.com. A yellow banner appears: *"fix/merge-key had recent pushes — **Compare & pull request**"*. Click it. (No banner? Go to the **Pull requests** tab → **New pull request**, choose *base:* `main` and *compare:* your branch. In GitHub Desktop, **Create Pull Request** opens this same page.)
3. Check the two boxes at the top: **base: `main` ← compare: `fix/merge-key`** — "merge *compare* into *base*".
4. **Title:** what the change does, e.g. *Merge baseline and midline on hh_id + village_id*.
5. **Description:** a few lines — *what* changed, *why*, *how you checked it* (e.g. "re-ran `02_clean.R`; panel now has 4,812 households, no duplicates"). If the work relates to an issue, write `Closes #12` — the issue will close automatically when the PR is merged.
6. Click **Create pull request**.

### Reviewing it
- **Files changed** tab: the complete diff of the branch against `main`, file by file, coloured. Read it top to bottom. Tick **Viewed** on each file as you go.
- To comment on a line, hover over it and click the **+** that appears. Useful for colleagues ("why `all.x = TRUE` here?") — and for notes to yourself.
- **Conversation** tab: the description, comments, and — if configured — automatic checks.
- A reviewer can **Approve** or **Request changes** (*Review changes* button). If changes are needed, the author simply commits and pushes to the same branch; the PR updates by itself.

### Merging it
1. At the bottom of the *Conversation* tab, click **Merge pull request** → **Confirm merge**. (The arrow next to the button offers *Squash and merge* — all the branch's commits become one — or *Rebase and merge*. The default, *Create a merge commit*, is fine and is what this guide shows.)
2. Click **Delete branch** on the same page — the branch has done its job.
3. On your computer: `git switch main`, `git pull`, `git branch -d <branch>` (Section 5, Step 8).

If GitHub shows *"This branch has conflicts that must be resolved"* instead of a green merge button, see Section 8.

---

## 7. Working as a team

### Everyone works the same way
Each person opens pull requests **for their own branches**. It is not one person's job to open PRs — the question is only who *reviews* and *merges* them, which the team decides (below).

**Diagram — two people, two branches, one `main`:**
```
main ──●──────────────────●──────────●──────►
        \                /          /
         ●──●──●  fix/merge-key    /          (Maria)
          \                       /
           ●──●──●──●  feat/fies-index        (Juan)
```
Each branch grows separately and joins `main` through its own pull request when it is ready.

### Maria's day with Claude Code
1. **Morning:** `git switch main`, `git pull` — bring in anything colleagues merged. (The `session-start` skill checks this for you.)
2. **Start or resume the task's branch:** new task → `git switch -c feat/fies-index` (from the fresh `main`); continuing → `git switch feat/fies-index`.
3. **Work with Claude.** At each milestone ("the index script runs"), Claude adds the relevant files and proposes a commit message; Claude Code asks before committing. Maria's part: glance at the list of files (no data, nothing unexpected) and approve.
4. **End of the day:** `git push` — backed up on GitHub, visible to the team, `main` untouched.
5. **When the task is finished** (today or next week): open a pull request, review, merge (Section 6).

### A colleague's work
Juan does the same on his branch. His daily commits and pushes **do not affect Maria at all** — they stay on his branch until merged. **Nobody reviews daily work.** Maria looks once, when Juan opens a pull request to say "this is ready". The next morning, her `git pull` on `main` brings his merged work to her computer.

- **To look at Juan's unfinished branch** (e.g. to help him): `git fetch` (download news from GitHub without changing anything), then `git switch feat/fies-index`. Switch back to your own branch when done.

### How much review? (a team policy, not a Git rule)
Git does not require review; the team decides. A light policy suited to small development-economics teams:
- **Scripts that produce numbers for a report** (cleaning, indicators, estimation): the lead or data manager reviews the PR before merging — 10–15 minutes: read the description, scan *Files changed*, check the outputs look plausible.
- **Documentation, notes, small fixes:** the author merges their own PR.

Larger or longer projects usually go further: a *branch protection* rule so nothing reaches `main` without a PR, one required approval, and automatic checks. Compared with editing files directly on Google Drive: Drive has no review *and* no history. With Git, even a self-merged PR records who changed what, when and why — and any change can be undone.

### Branches or straight to `main` in a team?
**Branches, for everything except trivial fixes.** When several people push straight to `main`, their pushes collide (rejected pushes, surprise conflicts) and half-finished work lands in the version everyone pulls.

### What counts as "one task"
A branch is a piece of work you would review and merge as a unit: *clean baseline module B*, *construct the FIES index*, *draft report chapter 3*, *fix the sampling weights*. **Not** one branch per day, per person or per file. More work on the same task tomorrow → keep the same branch. A new, unrelated task → back to `main`, pull, new branch.

---

## 8. When two people change the same lines: conflicts

### When it happens
Git combines work automatically whenever people changed **different files, or different parts of the same file**. A **conflict** happens only when two people changed **the same lines of the same file** — Git cannot know which version is right, so it asks a human.

### An example
While Maria worked on a branch that adds suffixes to the merged variables, Juan fixed the same merge line (to keep baseline households missing at midline). Juan's PR was merged first. Maria now brings the new `main` into her branch:

**Command output:**
```
$ git pull origin main
Auto-merging 04_scripts/02_clean.R
CONFLICT (content): Merge conflict in 04_scripts/02_clean.R
Automatic merge failed; fix conflicts and then commit the result.

$ git status
On branch feat/panel-weights
You have unmerged paths.
  (fix conflicts and run "git commit")
  (use "git merge --abort" to abort the merge)

Unmerged paths:
	both modified:   04_scripts/02_clean.R
```
Git has written **both versions** into the file, between markers:

**Command output — the file `02_clean.R` now contains:**
```
# 2. Merge baseline and midline (hh_id repeats across villages)
<<<<<<< HEAD
hh <- merge(baseline, midline, by = c("hh_id", "village_id"), suffixes = c("_bl", "_ml"))
=======
hh <- merge(baseline, midline, by = c("hh_id", "village_id"), all.x = TRUE)
>>>>>>> 74003280d9e78f56c9fc8cda36695273effa4f56
```
- Between `<<<<<<< HEAD` and `=======`: **Maria's** version (HEAD = where she is).
- Between `=======` and `>>>>>>> …`: the **incoming** version (Juan's, now in `main`).

### What to do
1. **Open the file and decide** what the line should be. Often it is a combination — here, both changes are wanted:
   `hh <- merge(baseline, midline, by = c("hh_id", "village_id"), all.x = TRUE, suffixes = c("_bl", "_ml"))`
2. **Delete the three marker lines** (`<<<<<<<`, `=======`, `>>>>>>>`), leaving only the final code.
3. **Re-run the script** to check it works.
4. `git add 04_scripts/02_clean.R` (marks the conflict as resolved), then `git commit` (Git suggests a message), then `git push`.

If you get lost: `git merge --abort` puts everything back to how it was before the pull. When in doubt, ask the colleague whose change it was — a conflict is a conversation, not an error. RStudio, VS Code and GitHub Desktop all highlight the conflicting blocks and offer buttons to pick one side.

A conflict can also show up on the pull-request page (*"This branch has conflicts that must be resolved"*). The fix is the same: on your computer, on your branch, `git pull origin main`, resolve as above, commit, push — the PR updates itself.

### How to avoid most conflicts
- **Pull `main` every morning**, and branch from a fresh `main`.
- **Keep branches short**: merge within days. The longer a branch lives, the more `main` moves under it.
- **Divide work by file**: one person per script. The numbered-scripts structure (`01_clean_baseline.R`, `02_clean_midline.R`, …) already encourages this.
- **Say when you are touching a shared file** (the master script, the paths file, the README): a one-line message to the team avoids most surprises.
- **Merge small PRs often** rather than one enormous PR at the end.

---

## 9. Code on GitHub, data on Google Drive — what that means for branches

Git keeps **one version of the code per branch**: `main` has the old merge line, `fix/merge-key` the new one, and switching branch swaps the files. **Google Drive has only one copy of each data file** — it knows nothing about branches.

### The problem
When Maria runs `02_clean.R` **from her unmerged branch**, it writes `panel.rds` to the shared `03_clean_data` folder on Drive — **overwriting the file everyone uses** with output from code that is not in `main` yet, and may never be. Juan, running the analysis from `main`, now silently reads a panel built with a merge rule his code doesn't contain. Nobody notices until the numbers stop matching.

### Good practices
1. **Raw data is read-only for everyone** (already a rule in this template). Branches can only ever break *derived* files, which can be regenerated.
2. **Branch work writes somewhere else.** While testing a branch, write outputs to a personal or per-branch folder, e.g. `02_temp_data/sandbox/<your-name>/`, not to `03_clean_data`. One simple way is to have the paths file choose the folder from the current branch — a person (not the AI) can add to `00_setup_paths.R`:
   ```r
   branch <- system("git branch --show-current", intern = TRUE)
   if (branch != "main") DATA_CLEAN <- file.path(DATA_TEMP, "branches", branch)
   ```
   so any script run from a branch writes to its own folder automatically.
3. **Only `main` produces the official data.** After a PR is merged, re-run the relevant scripts (or the master script) from `main` to regenerate the shared files in `03_clean_data`.
4. **Record which code produced a file.** Save the commit ID with important outputs (e.g. `git rev-parse --short HEAD` written into the log or the file's metadata), so you can always tell which version of the code built it.
5. **Tell the team when shared data is regenerated** — and log significant data changes in `decision_log.md`.

---

## 10. Stacked branches (a branch on top of a branch)

Normally every branch starts from `main`. Sometimes, though, a second task **depends on work that is not merged yet**: task 2 needs the changes from task 1, but task 1's pull request hasn't been merged. Starting task 2 from `main` would mean working without those changes, so people start it **from task 1's branch** instead — a *stacked* branch.

**Diagram:**
```
main ──A
        \
         B  task-1            ← not merged yet
          \
           C  task-2          ← started from task-1, so it contains B as well
```

**What follows from this:**
- **Merge in order.** Task 1's PR goes first. Until then, task 2's PR would show task 1's changes too, which is confusing to review.
- **After task 1 is merged,** task 2's PR (base `main`) shows only its own changes, and merges normally.
- If task 1 changes during review, task 2 may need to pull those changes in (`git pull origin task-1` while on task-2).

**Should you avoid it?** When you can, yes — it is simpler to **merge task 1 first**, then pull `main` and start task 2 from there. Stacking is a reasonable choice when you can't wait (task 1 is in review and you need to continue), but keep it to two levels and merge promptly.

---

## 11. GitHub features beyond commit and push

| Feature | What it is | Why it helps |
|---|---|---|
| **Issue** | A numbered ticket (`#12`) for a bug, task or question; can be labelled and assigned to someone. | A shared to-do list attached to the code. `Closes #12` in a PR description closes the issue automatically when the PR is merged, linking the problem to the exact change that fixed it. |
| **Pull request** | A page proposing to merge a branch, with the full diff and comments (Section 6). | A final review before `main` changes, and a readable record of what changed and why. |
| **Tag / Release** | A permanent name for one commit (`v1.1`, `midline-report-sent-2026-10-02`), optionally with notes. | You can always go back to exactly the code that produced what the client received. |
| **Branch protection** | A repository setting that forces changes to `main` to go through a PR (optionally with an approval). | Nobody — human or AI — pushes to `main` by accident. |
| **PR / issue templates** | Pre-filled text in a `.github/` folder that appears in every new PR or issue. | A checklist on every PR: "☐ no data files ☐ runs from `00_master` ☐ outputs regenerated from `main`". |
| **Actions** | Automatic checks that GitHub runs on every PR. | E.g. repeat the large-file check on GitHub's side, even for people who never activated the local hook. |

**Issues and `PENDING.md`:** they overlap, so give them different jobs. Use **issues** for anything other people should see, discuss or be assigned. Keep **`PENDING.md`** as the short working queue Claude reads each session, referring to issue numbers (*"finish #12"*) rather than repeating them.

---

## 12. Hooks: Git hooks vs Claude Code hooks

A **hook** is a small script that a program runs automatically at a certain moment. Two different programs in this template have them, which is easy to mix up:

| | Git hook — `.githooks/pre-commit` | Claude Code hook — `.claude/hooks/check_large_files.sh` |
|---|---|---|
| Run by | Git | Claude Code |
| When | Just before *any* commit — from the terminal, GitHub Desktop, RStudio or Claude | Just before *Claude* runs a git command |
| Answers with | An exit code: `0` = go ahead, anything else = stop the commit | A short JSON message: `ask`, `deny` or `allow` |
| Switched on by | `git config core.hooksPath .githooks` — once per person, per clone | Its registration in `.claude/settings.json` — automatic |
| Can it ask you a question? | Only in a terminal window | Always — Claude Code shows the prompt |

In this template they work together to protect the rule *"data lives on Drive"*: both list any data file over 5 MB (or any file over 25 MB) in a commit and let you decide whether it really belongs in the repository. More in the *Safety net* section of the scaffold `README.md`.

---

## 13. Cheat sheet

### Looking (safe — these never change anything)
| Command | Use it when… |
|---|---|
| `git status` | Always, first. Shows the branch you're on, which files changed, what's in the basket, and whether you're ahead of / behind GitHub. |
| `git diff` | You want to see the exact lines you changed that are **not yet added**. |
| `git diff --staged` | Right before committing: shows exactly what the commit will contain. |
| `git diff --stat` / `git diff --staged --stat` | You want the summary (files + number of lines) rather than every line. |
| `git log --oneline --graph --all --decorate` | You want the map: which branches exist, where you are (`HEAD`), and where GitHub is (`origin/...`). |
| `git show <commit-id>` | You want to see what one past commit changed (IDs come from `git log`). |
| `git diff main..my-branch --stat` | You want to know everything your branch changes compared with `main` (what its PR will show). |
| `git branch --show-current` | You just want to know which branch you're on. |

### Saving
| Command | What it does |
|---|---|
| `git add <file>` | Put one file's changes in the basket. |
| `git add -A` | Put **all** changes in the basket, including new and deleted files. Check with `git diff --staged --stat` afterwards. |
| `git restore --staged <file>` | Take a file back out of the basket. **Your edits are kept** in the folder. |
| `git commit -m "message"` | Save the basket as a commit on the current branch. Message style: `fix: …`, `feat: …`, `docs: …`. |

### Branches
| Command | What it does |
|---|---|
| `git switch -c <name>` | Create a new branch on the commit you're on and switch to it. Do it from a fresh `main`. |
| `git switch <name>` | Switch to an existing branch. The files in your folder change to that branch's version. |
| `git branch` | List your local branches (`*` marks the current one). |
| `git branch -d <name>` | Delete a branch label after its work has been merged. Refuses if the work isn't merged — a safety check. |

### Syncing with GitHub
| Command | What it does |
|---|---|
| `git pull` | Download new commits for the current branch **and update your files**. Do it on `main` every morning. |
| `git fetch` | Only *check* GitHub for news (updates the `origin/...` labels); your files don't change. |
| `git push -u origin <branch>` | First upload of a new branch; `-u` remembers the pairing. |
| `git push` | Later uploads of the same branch. |
| `git pull origin main` | While on your branch: bring the latest `main` into it (to get colleagues' work or resolve a conflict). |

### Undoing
| Command | What it does |
|---|---|
| `git restore <file>` | **Discard** your uncommitted edits to a file — it goes back to the last commit. Cannot be undone. |
| `git merge --abort` | Cancel a merge that produced conflicts; everything goes back to before the pull. |
| `git revert <commit-id>` | Undo a commit that is already pushed, safely: adds a new commit that reverses it. History stays intact. |

*Older guides use `git checkout` for switching branches and discarding edits; `git switch` and `git restore` are the newer, clearer names for the same things.*

---

## 14. Frequently asked questions

**Why is `git diff --staged` empty before I `git add` anything?**
It compares the basket with the last commit. An empty basket means "no difference yet" — it has nothing to do with whether you have committed. After `git add` it shows what you added; right after `git commit` it is empty again, because the basket was emptied into the commit.

**Do I have to `git add` before every commit?**
Yes — `git commit` saves only what is in the basket. Shortcuts: `git add -A` stages everything; `git commit -am "message"` stages and commits all *modified* files in one go (but skips brand-new files).

**Do I have to add files one by one when working with Claude?**
No. Claude runs `git add` and `git commit` at milestones, and Claude Code asks you before each commit. Your part is to check the file list it shows (no data, nothing unexpected) and approve. You can also just say "commit this" at a good point.

**When should I add and commit?**
At logical checkpoints — whenever a piece works ("the merge runs", "the table renders"), usually several times per task. Add and commit together, one right after the other. One giant commit at the end of a week makes the history useless and mistakes harder to undo.

**Should I create the branch before I start working, or just before committing?**
Before you start — it's the first step of a task and prevents accidental commits to `main`. If you forget, create it before your first commit; your uncommitted edits come along.

**If I'm far behind, does `git pull` change my files?**
Yes: it updates the files in your folder to the latest version of the branch (only files in the repository — never your data on Drive). Your uncommitted edits are kept; if an incoming change would overwrite one, Git stops and tells you which file.

**Do I need to review my colleagues' branches every day?**
No. Look at their work once, when they open a pull request. How thorough the review is, is a team decision (Section 7).

**Does only the lead open pull requests?**
No — everyone opens PRs for their own branches. The team decides who reviews and merges them. Conflicts are avoided by short branches, dividing work by file and pulling `main` often — not by limiting who opens PRs (Section 8).

**Can two people work on the same branch?**
Yes, but then they are effectively sharing a mini-`main`: both must `git pull` before starting and push often. Usually simpler to give each person their own branch.

---

## 15. Glossary

- **Repository (repo):** the project folder plus its complete history (kept in the hidden `.git` folder).
- **Commit:** a saved snapshot of the project, with an ID, author, date and message.
- **Staging area ("basket"):** the changes chosen for the next commit.
- **Branch:** a movable label pointing at a commit; it moves forward when you commit on it.
- **`main`:** the main branch — the version everyone trusts and pulls from.
- **HEAD:** "you are here" — the branch you are currently on.
- **Remote / `origin`:** the GitHub copy of the repository; `origin` is its standard nickname.
- **`origin/main`:** where `main` is on GitHub, as of your last fetch or pull.
- **Push / pull / fetch:** upload your commits / download commits and update your files / only check for new commits.
- **Merge:** combine one branch's commits into another.
- **Merge commit:** the commit that joins a branch back into `main`.
- **Fast-forward:** a pull or merge where your label simply moves forward, because there is nothing to combine.
- **Pull request (PR):** a GitHub page proposing, reviewing and performing a merge.
- **Conflict:** two changes to the same lines that Git cannot combine by itself.
- **Issue:** a numbered ticket for a task, bug or question.
- **Tag / release:** a permanent name (and notes) for one specific commit.
- **Stacked branch:** a branch started from another unmerged branch rather than from `main`.
- **Hook:** a script run automatically at a certain moment (Section 12).
