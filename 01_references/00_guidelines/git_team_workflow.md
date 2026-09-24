# GitHub, AI, & Data Management Protocol
**Version:** 2.0 (Updated for Claude Code CLI integration)
**Author:** Miguel Uribe
**Applies to:** All Research Staff, Assistants, & AI Agents

---

## 1. The Core Philosophy
*We use a Hybrid System to manage our projects. This ensures that our data is secure on Google Drive while our code is safely version-controlled on GitHub.*

### **The 3 Rules**
1. **DATA stays in the Shared Drive:** Never save data (`.dta`, `.csv`, `.xlsx`) in the GitHub folder. Data lives exclusively in the designated Google Drive project folder (e.g., `G:\Shared Drives\...\Project_name\03_data`).
2. **CODE lives on your LOCAL Drive (Updated):** Git and Google Drive are mortal enemies. **Never clone a GitHub repository into your Google Drive sync folder.** It will corrupt the `.git` tracking. Code must live locally (e.g., `~/Documents/GitHub/Project_name/`).
3. **The AI is a Co-Pilot, not the Captain:** If using Claude Code (or another agentic AI), the human analyst is 100% responsible for reviewing the AI's proposed Git commits to ensure no data is accidentally tracked.

---

## 2. Roles and Responsibilities

| Task / Action | Principal Investigator (PI) | Data Manager (DM) | Analyst / Contributor |
| :--- | :--- | :--- | :--- |
| **Phase 0: Project Inititation**  | | | |
| 1. Create New Project (GitHub)  | 🔵 Accountable  | ✅ Executor  | |
| 2. Invite Users & Permissions  | | ✅ Executor  | |
| **Phase 1: Regular routine**  | | | |
| 3. Clone & Setup Paths  | | | ✅ Executor  |
| 4. Daily Work (Pull/Push)  | 🔵 Oversight  | | ✅ Executor  |
| 5. Consult on Major Changes  | ✅ Advisor  | ✅ Advisor  | 🔵 Initiator  |
| 6. Review & Merge Branches  | ✅ Approver  | ✅ Executor  | |
| 7. Weekly Snapshot (Backup)  | | ✅ Executor  | |
| **Phase 2: Project Closure**  | | | |
| 8. Project Closure / Archive  | ✅ Approver  | ✅ Executor  | |

---

## 3. Phase 0: Project Initiation (The "Empty Box" Method)
*This section defines how to set up a brand new project. This is typically done by the Data Manager or Principal Investigator.*

**Step 1: Create the Empty Box (GitHub.com)**
1. Go to GitHub.com -> Click **New Repository**.
2. **Name:** `project-name-code` (e.g., `educ-midline-code`).
3. **Visibility:** Select **Private**.
4. ⚠️ **CRITICAL:** Do NOT check the boxes for "Add a README" or "Add .gitignore". We want a completely empty repository.
5. Click **Create repository**.

**Step 2: Clone to a Safe Local Folder (GitHub Desktop)**
1. Open GitHub Desktop -> **File** -> **Clone Repository**.
2. Select your new repository from the GitHub.com tab.
3. ⚠️ **CRITICAL - THE SAFE FOLDER RULE:** Do not clone this into a folder synced by Google Drive, OneDrive, or iCloud (like Documents or Desktop). It will corrupt the repository. 
   * **Windows:** Use `C:\Users\[YourName]\github\company_name\project-name\`
   * **Mac:** Use `/Users/[YourName]/github/company_name/project-name/`
4. Click **Clone**.

**Step 3: Fill the Box & Initialize Templates**
1. **Preferred:** skip Steps 1–2 and create the repository directly from the template on GitHub ("Use this template" → "Create a new repository"; see the template's own README, §1). This copies everything — folders 01–09, `.claude/`, `.githooks/`, `CLAUDE.md`, `.gitignore` — with a clean history.
2. **Manual alternative:** copy the *entire* contents of the template (including the hidden `.claude/`, `.githooks/` and `.gitignore`) into your newly cloned, empty project folder.
3. **Turn on the commit safety check:** in a terminal at the project folder, run `git config core.hooksPath .githooks` once. This activates the pre-commit hook that asks before large data files are committed (see Section 5).
4. **Activate the Project README:** * Copy `README_template.md` from `08_ai_management/03_system_templates/` into the root directory as `README.md` (replacing the scaffold's own README).
   * Open it and fill in the project-specific details (Project Name, PI, methodology, etc.).
   * `CLAUDE.md` is already in the root and ready to use — just delete the "Template note" at the top once you've read it. (There is no separate CLAUDE template to copy.)
5. **Create the Setup File:**
   * Open `01_references/00_guidelines/setup_paths_template.md`.
   * Copy the code for your primary language (R, Stata, or Python) and save it as a new file in `04_scripts/` named `00_setup_paths.[R/do/py]`. Configure your local paths inside it.

**Step 4: Migrating Legacy Projects (If Applicable)**
*If you are transitioning an existing project into this new Git framework:*
1. Locate your old `.do`, `.R`, or `.py` scripts and any relevant methodology notes, deliverables, reports, etc.
2. Copy and paste them strictly into the `09_legacy_vault/` folder.
3. **Why do we do this?** This folder is strictly read-only. It acts as a quarantined "ground truth" for the AI (Claude Code CLI). Once the files are in the vault, we can instruct the AI to read the messy legacy code and rewrite it cleanly into our new `04_scripts/` structure without ever risking the original files.

**Step 5: The Genesis Commit & Push**
1. Open GitHub Desktop. You will see all the new, customized files in green. 
2. In the Summary box (bottom left), type: `chore: initial project setup and template initialization`.
3. Click **Commit to main**, then click **Push origin** at the top of the screen to back it up to the cloud.
4. Go to GitHub.com -> **Settings** -> **Collaborators** -> Add your team members.
---

## 4. Phase 1: Regular routine
*This section describes the daily routine followed by anyone writing new code, as well as the activities of the data manager to update the code folder in the Shared folder. The goal is to keep everyone in sync and prevent conflicts.*

### Setting Up a New User (First-Time Setup)
Because Code and Data live in different places, we use a central configuration file so scripts work seamlessly across operating systems.
1. Ensure Git and GitHub Desktop are installed on your computer.
2. Open GitHub Desktop -> **File** -> **Clone Repository**. Clone the project to your **Safe Local Folder** (e.g., `~/github/company_name/project-name/`). *Never clone into Google Drive!*
3. **Turn on the commit safety check** (once per clone): open a terminal in the project folder and run `git config core.hooksPath .githooks`. Git never activates hooks automatically on a fresh clone, so each person does this once. If you skip it nothing breaks — you simply don't get the large-file check.
4. Open the central config file located at `04_scripts/00_setup_paths.[R/do/py]`.
5. Add your OS username and the absolute path to the project's Google Drive `03_data` folder to the `if/else` block (check where raw/temp/clean data live and make sure you add the specific subflder). 
6. **In your actual analysis scripts:** Do not copy-paste a massive path header. Simply add one line at the top to call the config file:
   * **R:** `source(here::here("04_scripts", "00_setup_paths.R"))`
   * **Stata:** `do "04_scripts/00_setup_paths.do"` (with Stata's working directory at the repo root; `$GITHUB_PATH` only exists after this runs)

### Phase A: Start of Day (The Pull)
Always do this before you type a single line of code so you don't overwrite your team's work.
1. Open GitHub Desktop.
2. Click **Fetch origin** (this checks the cloud for updates).
3. If new changes appear, click **Pull origin** (this downloads them to your computer).

### Phase B: The End of Day (The Push)
Choose the correct protocol based on the complexity of your work.
* **Sanity Check:** Look at the list of files you are about to commit (`git status`, or the Changes tab in GitHub Desktop). Nothing from the Google Drive data folders should be there. The pre-commit hook will also stop and list any data file over 5 MB (or any file over 25 MB):
    * *In a terminal*, it asks `Commit anyway? [y/N]` — answer `y` if the file genuinely belongs in the repository.
    * *In GitHub Desktop* (or RStudio's Git pane), it cannot ask, so it stops the commit and shows the list. Untick the file, or — if it should be committed — run `git commit` from a terminal and answer `y` there.

**Scenario 1: Routine Work (Direct to Main)**
* **Definition:** Minor fixes, data cleaning, or working on independent scripts that do not affect others.
* **Commit:** Write a summary (e.g., `feat: Cleaned Section 5 of survey`) and click Commit to main (saves locally).
* **Push:** Click Push origin (uploads to the cloud).

**Scenario 2: Major Work (Branching)**
* **Definition:** Creating a new index, changing the master analysis file, or testing a new model.
* **STOP & CONSULT:** Message the team: "I am about to rewrite the Poverty Index on a new branch."
* **Create Branch:** In GitHub Desktop -> Current Branch -> New Branch. Name it: e.g., `feature-poverty-index`.
* **Work & Commit:** Work and commit normally. Your changes are safely isolated from the `main` project.
* **Pull Request (The Handoff):** Click **Publish branch**. Go to GitHub.com -> **Compare & pull request**. Assign the PI or DM to review it.
    * **Status:** Your work is now "Pending Review." It is safe on GitHub, but not yet in the Main code.
    * **The Review Process:** If the PI approves: They merge it. If the PI is delayed: Do not panic. Your branch is safe. You can switch back to main to do other work, or continue working on your branch.

---

## 5. Working with Claude Code
When using the Claude Code CLI, Claude will write code and propose saving it to GitHub. 
* **No Auto-Commits:** Claude is strictly instructed to *propose* a commit message and wait for human approval. 
* **Human Verification:** When Claude asks, *"Would you like me to run `git commit`?"*, you must read the terminal output to verify what files are being staged. If Claude accidentally staged a data file, answer `No` and ask it to unstage the file.
* **Built-in safety net:** the project's `.claude/settings.json` makes Claude Code ask you before *every* `git commit` / `git push` Claude runs, and — through the hook in `.claude/hooks/check_large_files.sh` — lists any large data file in that commit in the same prompt. It also stops Claude from editing `04_scripts/00_setup_paths.*`, anything in `09_legacy_vault/`, or Google Drive `01_raw_data/` folders.

---

## 6. The Admin Protocol
Because Data lives in Shared Drive and Code lives in Personal/Local Drive, we need a manual "bridge" so non-coders can see the latest scripts in the Shared folder.

**Option A: The Manual Method**
1. Open your local GitHub repository folder.
2. Copy the entire repository (excluding the hidden `.git` folder).
3. Open the Shared Drive project directory.
4. Delete the old `04_code_SNAPSHOT` (if it exists).
5. Paste the new folder and rename it `04_code_SNAPSHOT`.

**Option B: The "1-Click" Automated Method**
Setup this script once, then just double-click it every Friday. (Note: `SOURCE` is your local repository folder — never a Google Drive path — and `DEST` is the Shared Drive snapshot folder. Both scripts skip the hidden `.git` folder.)

For Windows Users (backup.bat)
    1. Open Notepad.
    2. Paste the code below (edit the YourName and Project_X parts).
    3. Save as backup_project.bat (Make sure to select "All Files" type).

```
@echo off
:: CONFIGURATION
set SOURCE="C:\Users\YourName\github\company_name\project_example"
set DEST="G:\Shared Drives\CD_3_Projects\Active Projects\project_example\03_data\04_code_SNAPSHOT"

:: EXECUTION
echo ---------------------------------------------------
echo Backing up Code from Personal Drive to Shared Drive
echo ---------------------------------------------------
echo Source: %SOURCE%
echo Dest:   %DEST%

:: robocopy /MIR = mirror the folder (copies subfolders, removes files deleted from the source)
:: /XD .git      = exclude the hidden .git folder (the git history does not belong on the Shared Drive)
robocopy %SOURCE% %DEST% /MIR /XD .git

echo.
echo ✅ Backup Complete!
pause
```

For Mac Users (backup.command)
1. Open TextEdit.
2. Paste the code below.
3. Format -> Make Plain Text (Shift+Cmd+T).
4. Save as backup_project.command.
5. *One-time Setup: Open Terminal, type chmod +x (with a space), drag the file into the window, and hit Enter. This makes it clickable.*

```
#!/bin/bash
# CONFIGURATION
# Note: Google Drive path on Mac is usually under /Volumes or ~/Library/CloudStorage
SOURCE="/Users/yourname/github/company_name/project_example/"
DEST="/Volumes/GoogleDrive/Shared Drives/CD_3_Projects/Active Projects/project_example/03_data/04_code_SNAPSHOT/"

echo "---------------------------------------------------"
echo "Backing up Code from Personal Drive to Shared Drive"
echo "---------------------------------------------------"

# rsync is the standard Mac copy tool. -a = archive mode, -v = verbose, --delete = remove files in dest that are gone in source,
# --exclude .git/ = do not copy the git history into the Shared Drive
rsync -av --delete --exclude '.git/' "$SOURCE" "$DEST"

echo "✅ Backup Complete!"
```

---

## 7. Phase 2: Project closure
What happens when the project is finished? We must ensure the work is preserved and documented.
* **Final Snapshot:** Run the Snapshot script one last time to ensure the Shared Drive has the final code.
* **Clean the Data:** Ensure the Google Drive `03_data\03_clean_data` folder contains the final analysis dataset and variable labels are correct.
* **Update README:** Open `README.md` in the code folder. Update the Title, Abstract, and Citation. List the final output files.
* **Archive Repository:** Go to GitHub.com -> Settings -> General. Select Archive this repository. Result: The code becomes "Read-Only." No one can change it, but anyone in the company can still download it for future reference.

---

## Appendix A: The Central Configuration File

The canonical guide lives at `01_references/00_guidelines/setup_paths_template.md`. It contains the up-to-date R, Python, and Stata code blocks for `00_setup_paths.[R/py/do]`, plus guidance on how to source the file at the top of every analysis script and how to orchestrate sequential master scripts. **Use that document as the single source of truth** to avoid drift between two copies of the same code.

Variables defined by the setup file:
* `GITHUB_PATH` — root of the local code repository (e.g., `/Users/yourname/github/company_name/project_example`).
* `GDRIVE_PATH` — root of the Google Drive `…/03_data/` folder for the project (e.g., `/Volumes/GoogleDrive/Shared Drives/CD_3_Projects/Active Projects/project_example/03_data`).
* `DATA_RAW`, `DATA_TEMP`, `DATA_CLEAN` — standardised sub-paths built from `GDRIVE_PATH` so that all scripts point to the same folders regardless of who is running them.

## Appendix B: A Beginner's Guide to Git, GitHub, and AI-Assisted Coding

If you are new to version control, do not panic. Moving from Google Drive to GitHub might feel like learning a new language, but it is the single most important technical skill you will learn for modern data analysis.

### 1. Why GitHub? (The Industry Standard)
In the international development and applied economics space, "reproducibility" is the gold standard. A shared Google Drive folder full of scripts named `analysis_v1.do`, `analysis_v2_RA.do`, and `analysis_FINAL_really.do` is chaotic, error-prone, and no longer acceptable for high-level research.

By using Git and GitHub, we are aligning ourselves with the exact code-management protocols required by the American Economic Association (AEA) and used by top-tier organizations like:
* **J-PAL (Abdul Latif Jameel Poverty Action Lab)**
* **IPA (Innovations for Poverty Action)**
* **World Bank DIME (Development Impact Evaluation)**
* **IDinsight & CEGA**

### 2. Why GitHub is Mandatory for AI Agents (Claude Code CLI)
We may utilize advanced AI agents to assist with coding and data cleaning. Giving an AI access to a standard Google Drive folder is highly dangerous. If an AI hallucinates or makes a bad decision, it could instantly overwrite and destroy your `analysis.do` file forever. 

**Git acts as our safety net.** Because Git tracks every single keystroke, if Claude Code writes 500 lines of terrible code, we can simply look at the "Git History" and instantly revert the file back to the way it was 5 minutes ago. Git allows us to safely unleash the power of AI without ever risking our core codebase.

### 3. The Core Concepts (The Vocabulary)

**The Repository (The "Repo")**
A repository is just a folder on your computer that Git is watching. It tracks every file inside it (except the datasets, which we tell it to ignore via the `.gitignore` file).

**Commit (Taking a Snapshot)**
When you "Commit," you are telling Git: *"Take a photograph of my files exactly as they look right now."* 
* *Analogy:* Saving your game at a checkpoint. If you mess up your code tomorrow, you can instantly time-travel back to today's commit.
* *Note:* Commits only save to your *local computer*.

**Push (Uploading to the Cloud)**
When you "Push," you are uploading all your local commits (photographs) up to GitHub.com.
* *Analogy:* Uploading your photos to a secure online album so the rest of the team can see them and back them up.

**Fetch (Checking for Updates)**
When you "Fetch," you are asking GitHub: *"Has anyone else on the team pushed new code since I last checked?"* It does **not** download or change your files; it just safely updates your dashboard to show you what your teammates have done.
* *Analogy:* Checking your inbox to see if you have unread emails, without actually opening them yet.

**Pull (Downloading from the Cloud)**
When you "Pull," you are downloading the latest commits that your teammates have pushed to GitHub.com.
* *Analogy:* Refreshing a Google Doc to see the paragraphs your coworker just wrote. 

**Branches (Safe Parallel Universes)**
The default, master version of your project is called the **`main`** branch. But what if you want to test a complex new econometric model without breaking the code for everyone else? You create a **Branch**.
* *Analogy:* Making a parallel universe. You can change anything you want in your branch. If the model works, we "Merge" it back into `main`. If the model fails, we delete the branch, and the `main` code was never touched.

### 4. Further Reading & Resources
If you want to deepen your understanding of Git and reproducible research, check out these highly recommended resources:

1. **GitHub's "Hello World" Tutorial:** A 10-minute interactive guide to understanding branches, commits, and pull requests.
   * [https://docs.github.com/en/get-started/quickstart/hello-world](https://docs.github.com/en/get-started/quickstart/hello-world)
2. **World Bank DIME Wiki - Getting Started with GitHub:** The World Bank's internal guide for development economists learning Git.
   * [https://dimewiki.worldbank.org/Getting_started_with_GitHub](https://dimewiki.worldbank.org/Getting_started_with_GitHub)
3. **J-PAL Coding Resources for Randomized Evaluations:** Read why J-PAL explicitly recommends version control for team-based social science coding.
   * [https://www.povertyactionlab.org/resource/coding-resources-randomized-evaluations](https://www.povertyactionlab.org/resource/coding-resources-randomized-evaluations)
4. **Atlassian Git Tutorials:** Excellent, visual explanations of how Git works under the hood.
   * [https://www.atlassian.com/git/tutorials](https://www.atlassian.com/git/tutorials)