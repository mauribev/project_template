# Survey Tool Learnings

This file captures learnings and methods for working with quantitative survey instruments (XLSForms, SurveyCTO, ODK). The goal is to build a knowledge base that accelerates the design-test-deploy cycle for household surveys.

---

## [2026-04-14] - Programmatic XLSForm Parsing and Cross-Round Comparison

**Summary::** We built a Python script (`04_scripts/00_exploration/01_parse_xlsforms.py`) that reads BRCiS III Baseline and Midline household survey XLSForms (`.xlsx`) using `openpyxl`, extracts the full questionnaire architecture, and generates three standalone HTML documents: one for BL, one for ML, and one BL-ML comparison. The script handles SurveyCTO's XLSForm dialect (space-separated types like `begin group` vs. underscore `begin_group`, extra annotation columns like `Comments CMU`, `Contribution analysis relevant`), and produces module trees, question inventories, choice list catalogues, skip logic maps, and calculated field registries.

**Tags:** #survey_design, #data_engineering, #coding_architecture

### The Core Insight

XLSForm `.xlsx` files are structured data — they follow a standard schema (`survey`, `choices`, `settings` sheets) that can be parsed programmatically. This means survey instrument review, documentation, and cross-round comparison can be automated instead of done manually in Excel.

The key technical details for parsing XLSForms:

1. **Sheet structure:** Standard XLSForm has 3 sheets: `survey` (questions), `choices` (option lists), `settings` (form metadata). Real-world instruments often have additional sheets — the ML form had `survey_w_additions`, `backup_survey`, `survey_with_notes`, indicating design iterations. Always check `wb.sheetnames` first.

2. **Column headers vary between instruments.** BL and ML had different column orders and the ML had extra columns (`Comments CMU`, `Comments CD`, `Contribution analysis relevant`). Build a column-finder function rather than hardcoding indices:
   ```python
   def _find_col(headers, candidates):
       for i, h in enumerate(headers):
           if h and str(h).strip().lower() in [c.lower() for c in candidates]:
               return i
       return None
   ```

3. **Type field format matters.** SurveyCTO uses space-separated types (`begin group`, `end group`, `select_one listname`) while ODK uses underscores (`begin_group`). The parser must handle both. Critical bug we caught: the `end` type for `end_time` (metadata) was matching our `startswith("end")` check and popping the group stack prematurely. Fix: match explicit strings `"end group"`, `"end_group"`, `"end repeat"`, `"end_repeat"` — never just `startswith("end")`.

4. **Group/repeat hierarchy** is reconstructed by maintaining a stack: push on `begin group`/`begin repeat`, pop on `end group`/`end repeat`. Everything between is a child of the current group. This produces the module tree that shows how the survey is organized (e.g., `mod_hh` → `hhs_counts` → individual questions).

5. **Choice lists** are keyed by `list_name` (first column in `choices` sheet). BL used a space `" "` as the header for this column instead of `list_name` — another reason to use flexible column matching.

6. **Cross-round comparison** is done by building a `{question_name: row_dict}` index for each form, then computing set differences (added/removed) and field-by-field diffs (modified label, skip logic, constraint, type, etc.). Choice list comparison checks for added/removed/relabeled options.

### Application to This Project

- **BL form:** 1,008 rows, 571 data questions, 72 groups, 158 choice lists
- **ML form:** 1,126 rows, 664 data questions, 75 groups, 217 choice lists
- The comparison revealed ML has ~93 more data questions and 59 more choice lists, plus structural additions (3 new groups) and the contribution analysis annotation columns
- The ML form's extra `Comments CMU` and `Contribution analysis relevant` columns contain design-stage metadata that documents *why* questions were included — this is valuable context for analysis

### Key Takeaways & Nuances

- **`openpyxl` in read-only mode** returns `None` for `max_row`/`max_column` — you must iterate to count. Use `data_only=True` to get computed cell values.
- **The `choices` sheet** often contains operational data (enumerator names, location hierarchies with region/district/cluster filters) mixed with actual survey response options. Filter by `list_name` to separate them.
- **Relevance (skip logic) expressions** use XPath-like syntax referencing `${variable_name}`. These can be parsed to build a dependency graph showing which questions gate which others — a future enhancement.
- **Calculated fields** contain the survey's internal logic (auto-computed values, repeat counts, conditional assignments). These are the "hidden brain" of the survey and critical for understanding derived variables in the data.
- **Repeat groups** produce separate datasets in the exported data. Understanding the repeat structure from the XLSForm directly maps to the data architecture (e.g., household-level vs. member-level vs. crop-level datasets).
- **Version tracking:** The `settings` sheet contains `form_id` and `version` (timestamp format in SurveyCTO, e.g., `2512300905`). This is essential for knowing which form version produced which data.

### What We Could Build Next

1. **Skip logic dependency graph** — parse `relevance` expressions to show which questions depend on which, enabling rapid diagnosis of "why is this variable missing for these households?"
2. **Data dictionary generator** — combine XLSForm parsing with actual data to produce a complete data dictionary with variable name, survey label, type, response options, skip logic, and observed distribution
3. **Form diff tool** — a CLI skill that takes two XLSForm files and produces a structured change log (useful for version control of survey instruments)
4. **Automated test case generator** — from the skip logic and constraints, generate test scenarios that should be verified on a test device before deployment
5. **Translation QA** — compare `label:English` and `label:Somali` columns to flag missing translations or significant length differences

### References & Further Reading

- XLSForm specification: https://xlsform.org/en/
- SurveyCTO documentation (XLSForm extensions): https://docs.surveycto.com/02-designing-forms/01-core-concepts/
- ODK XLSForm reference: https://docs.getodk.org/xlsform/
- `openpyxl` documentation: https://openpyxl.readthedocs.io/
