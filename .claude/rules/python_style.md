---
paths:
  - "**/*.py"
  - "**/*.ipynb"
---

# Python conventions

- **Top of every script:** `from pyprojroot import here; exec(open(here("04_scripts/00_setup_paths.py")).read())`, then the imports. Set the README's random seed if the script uses randomness.
- **Dependencies:** work inside the project virtual environment (`venv/`). When you add a package, run `pip freeze > requirements.txt` and note the package in the README.
- **Running other steps:** master scripts call sub-scripts with `subprocess.run([...], check=True)` (numbered file names can't be imported), and notebooks with `papermill`. See `01_references/00_guidelines/setup_paths_template.md`.
