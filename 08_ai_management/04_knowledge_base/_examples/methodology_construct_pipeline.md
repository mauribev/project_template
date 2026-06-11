---
title: "Methodology — Construct Pipeline (Phase G)"
author: "BRCiS III Evaluation Team"
date: "2026-05-27"
type: methodology
status: v1
applies_to:
  - 04_scripts/07_construct/01_indicators_bl.R
  - 04_scripts/07_construct/02_indicators_ml.R
  - 04_scripts/07_construct/05_rsi_index_bl.R
  - 04_scripts/07_construct/06_rsi_index_ml.R
  - 04_scripts/07_construct/08_tango_bl.R
  - 04_scripts/07_construct/09_tango_ml.R
  - 04_scripts/00_setup/01_functions/indicator_constructors.R
---

# Methodology — Construct Pipeline (Phase G)

**BRCiS III Midline Evaluation — indicator construction, Resilience Spectrum Index (RSI), TANGO Resilience Capacity Index, and last-observation-carried-forward (LOCF) policy.**

---

## 0. Preface

### 0.1 What this document is

This is the methodological reference for **Phase G — Construct** of the BRCiS III evaluation pipeline. Phase G takes cleaned household-level data (from `05_clean/`) plus survey weights (from `06_weights/`) and produces three analytical layers that every downstream report depends on:

1. **Logframe / KPI 4 indicators** — household-level outcome indicators implementing standard food-security, livelihood, and welfare scales (FCS, HDDS, FIES, rCSI, LCS, social capital, SRI, and many more).
2. **Resilience Spectrum Index (RSI)** — Anderson's (2008) inverse-covariance-weighted composite over three sub-indices (Leadership, Ecosystem, Market).
3. **TANGO Resilience Capacity Index** — Frankenberger et al. (2012) three-capacity (Absorptive / Adaptive / Transformative) factor-analytic composite.

The goal of this document is the same as its companion `methodology_prepost_weights.md`: make every analytical choice in Phase G **legible, defensible, and reproducible by a colleague who does not have AI tooling**. Each section answers: (a) what does the code compute, (b) why is that the right quantity to compute, (c) what would the alternatives have been, (d) what is the explicit literature reference for the choice.

### 0.2 What this document is not

It is **not** a re-derivation of the existing methodology QMDs. The RSI and TANGO methodologies are documented in deep technical detail at:

- `04_scripts/07_construct/07_rsi_methodology.qmd` — RSI variable lists, ICW weights per sub-index, sub-index histograms, BL→ML driver decomposition, coverage diagnostics.
- `04_scripts/07_construct/10_tango_methodology.qmd` — TANGO BL factor loadings, polychoric correlation structure, kNN missingness handling, the access-insurance LOCF deep-dive, BL→ML driver decomposition.

This document **integrates** those references into a single end-to-end view of Phase G and adds the indicator-construction layer (which the QMDs do not cover). Where a topic is documented in depth in one of the QMDs, this document gives the essential math + decisions and points to the QMD for the deep dive.

It is **not** a sampling-theory or factor-analysis textbook. Where derivations are non-trivial, we point to the source publications (Anderson 2008 for ICW; standard factor-analysis texts for the polychoric-correlation factor model).

### 0.3 How this document pairs with `methodology_prepost_weights.md`

The two methodology docs form a complementary pair:

| Doc | Phase | Question answered |
|---|---|---|
| `methodology_construct_pipeline.md` (this doc) | G — Construct | *How are the indicators, RSI, and TANGO produced from cleaned data?* |
| `methodology_prepost_weights.md` | downstream (panel + report) | *How are paired BL→ML changes in those indicators estimated with correct survey-weighted standard errors?* |

A new analyst onboarding to BRCiS should read this doc first (to understand what the indicators *are*) and then the prepost doc (to understand how to *report on them*).

### 0.4 Notation

| Symbol | Meaning |
|---|---|
| $i$ | Household index. |
| $j$ | Indicator / variable index. |
| $c(i)$ | Community of household $i$. |
| $N_{\text{panel}}$ | Panel sample size = 3,889 households. |
| $x_{ij}$ | Raw value of indicator $j$ for household $i$. |
| $z_{ij}$ | Z-scored value of indicator $j$ for household $i$, computed using BL mean $\mu_{BL,j}$ and BL standard deviation $\sigma_{BL,j}$. |
| $\Sigma$, $R$ | Variance-covariance matrix (Pearson) and polychoric correlation matrix of indicators, respectively, both computed on BL data. |
| $L$ | Vector of factor loadings (1-factor solution). |
| $w$ | Vector of weights: $w_{\text{ICW}} = (\mathbf{1}^\top \Sigma^{-1} \mathbf{1})^{-1} \mathbf{1}^\top \Sigma^{-1}$ for RSI; $w_{\text{TANGO}} = R^{-1} L$ for TANGO. |
| $s_{i,k}$ | Sub-index / capacity $k$ score for household $i$. |
| LOCF | Last Observation Carried Forward — use a household's BL value as a stand-in for an unobserved ML value. |

---

## 1. The construct phase in the pipeline (Phase G)

### 1.1 Position in the pipeline

The full BRCiS III pipeline is documented in `04_scripts/README.md`. Phase G is the **last analytical phase before the panel build**:

```
Phases A-F (cleaning + outliers) → Phase G (this doc) → Harmonize → Reports
                                        │
                                        ├── Logframe / KPI 4 indicators
                                        ├── Resilience Spectrum Index (RSI)
                                        └── TANGO Resilience Capacity Index
```

Phase G's outputs feed both `08_harmonize/01_build_panel_dataset.R` (which produces the canonical `panel_long.rds` / `panel_wide.rds` for every downstream report) and the diagnostic QMDs.

### 1.2 Inputs

Phase G reads from `DATA_CLEAN/`:

- `hh/brcisIII_{baseline,midline}_hh_final.{rds,dta}` — cleaned household-level data (Phases A–F outputs).
- `hh/weights/brcisIII_{baseline,midline}_panel_weights.rds` — panel-sample weights (`06_weights/02_panel_weights.R`). The inner-join with this file is what **defines** the analytical sample (§2 below).
- `household_surveys/{baseline,midline}/brcisIII_{baseline,midline}_shocks_long_labelled.dta` — repeat-group shock data (long format).
- `household_surveys/{baseline,midline}/brcisIII_{baseline,midline}_agr-crop_long_labelled.dta` — repeat-group crop data.
- `arcd/brcisIII_{baseline,midline}_arcd_wide.rds` — community-level Adapted Resilience for Community Development (ARC-D) data.
- `household_surveys/midline/brcisIII_bl_ml_household_survey_merge_key.dta` — BL ↔ ML UUID mapping (only needed by ML scripts).

### 1.3 Outputs

Phase G writes to `DATA_CLEAN/`:

```
DATA_CLEAN/indicators/   brcisIII_baseline_hh_indicators.{rds,dta}   3,889 × ~1,180 cols
                         brcisIII_midline_hh_indicators.{rds,dta}    3,889 × ~1,390 cols
DATA_CLEAN/rsi/          brcisIII_baseline_hh_rsi.{rds,dta}          3,889 × ~13 RSI cols
                         brcisIII_midline_hh_rsi.{rds,dta}
                         bl_artifacts.rds                            BL params for ML projection
DATA_CLEAN/tango/        brcisIII_baseline_hh_tango.{rds,dta}        3,889 × ~10 TANGO cols
                         brcisIII_midline_hh_tango.{rds,dta}
                         bl_artifacts.rds                            BL params for ML projection
```

These were previously in `DATA_TEMP/` but were migrated to `DATA_CLEAN/` on 2026-05-27 because they are canonical analysis-ready outputs that downstream scripts depend on (see `08_ai_management/01_progress_logs/2026-05-27_session.md` for the migration trace, and `methodology_prepost_weights.md` §1.3 for the descriptive-vs-analytic distinction that motivates the "clean, not temp" placement).

### 1.4 Run order

```bash
# Logframe / KPI 4 indicators (BL first, ML reads BL for cross-round ops):
Rscript 04_scripts/07_construct/01_indicators_bl.R          # ~4 s
Rscript 04_scripts/07_construct/02_indicators_ml.R          # ~4 s

# RSI (BL fit must precede ML projection — ML reuses BL anchors):
Rscript 04_scripts/07_construct/05_rsi_index_bl.R           # ~5 s
Rscript 04_scripts/07_construct/06_rsi_index_ml.R           # ~7 s

# TANGO (BL first; ML projects through BL loadings):
Rscript 04_scripts/07_construct/08_tango_bl.R               # ~2 s
Rscript 04_scripts/07_construct/09_tango_ml.R               # ~2 s
```

Total runtime ≈ 25 s. There is no sub-master (`00_master_construct.R`) yet — scripts are run individually. Each script writes to `DATA_CLEAN/` and prints a timing report.

### 1.5 The 3-source variable-lookup convention

Downstream code (`08_harmonize/01_build_panel_dataset.R`, the preliminary report, future reports) resolves harmonization-map variable references using a **3-source priority chain**: indicators → RSI → TANGO, first hit wins. This lets the harmonization map at `02_survey_tools/01_quant_tools/prepost_harmonization_map.xlsx` reference any constructed variable without the analyst needing to remember which sub-script produced it. The convention is documented in `04_scripts/08_harmonize/README.md`; we mention it here so readers understand why some variables that "feel like indicators" actually live in `hh_rsi_*.rds` or `hh_tango_*.rds` rather than `hh_indicators_*.rds` — see §4 / §5 below.

---

## 2. The analytical-sample contract

### 2.1 The panel sample

Every script in `07_construct/` operates on the **same analytical sample**: the 3,889 households that are in BL ∩ ML × Random Walk. This sample is defined upstream in `04_scripts/06_weights/02_panel_weights.R`; the construct scripts simply enforce it via an inner-join with the weights file at the top of each script.

The full derivation of the sample is in `methodology_prepost_weights.md` §2.2; the funnel is:

```
Full BL household survey                 : 5,162
BL Random-Walk subsample                 : 4,309   (-853 minority oversample)
ML revisits (consenting HHs)             : 3,892
Panel (BL ∩ ML ∩ Random Walk)            : 3,889   (-3 leaked minority HHs)
```

Every indicator value in `hh_indicators_*.rds`, every RSI score in `hh_rsi_*.rds`, every TANGO score in `hh_tango_*.rds` is computed on these 3,889 households. There is no other sample.

The panel is distributed across **171 communities**, one fewer than the 172 visited at BL: **Afweyne Banan** (Dhuusamareeb district, Galgaduud region, NRC member) had 27 BL households but **zero** ML revisits and is therefore absent from the panel entirely. The community is a "complete attriter" — relevant to the attrition-bias caveat (`methodology_prepost_weights.md` §11.2 caveat #1).

This invariant is enforced by a **fail-fast assertion** at the top of every Phase G script: after the inner-join with the weights file, the script verifies that `nrow(data)` equals the expected panel size and aborts if not.

### 2.2 ARC-D availability differs across rounds

A subtlety inherited from the field: the **Adapted Resilience for Community Development (ARC-D)** community-level survey has full coverage at BL (172 of 172 communities) but is missing at ML for **three communities**: DegAdey, Ceeldhiinle, and Dhugile (73 panel households, ≈ 1.9 % of the panel). Several variables in the indicators, RSI, and TANGO layers depend on ARC-D constructs — these inherit the NA propagation:

- **Indicators** with ARC-D dependence: `avail_inf_safety`, `avail_financial`, `avail_communal`, `avail_basic_services`, and all `asset_ownership` composites that include ARC-D-derived groups. At ML, these are NA for the 73 HHs in ARC-D-missing communities.
- **RSI**: 97 ML HHs end up without a final RSI score — the 73 ARC-D-missing plus 24 in covered communities with sporadic ARC-D NA on `arcd24/25/26` (the inputs to `arcd24_26`).
- **TANGO**: 73 ML HHs without a TANGO score (the 3 ARC-D-missing communities only — TANGO inputs are mostly community-level constructed indicators, not raw `arcd*` items).

This is a feature, not a bug: we propagate the genuine missingness rather than imputing the community-level values we don't have. The full impacted-variable table is in `04_scripts/07_construct/03_indicators_diagnostics.qmd`.

---

## 3. The indicator-construction layer

### 3.1 The `construct_*()` function library

Indicator construction is implemented in `04_scripts/00_setup/01_functions/indicator_constructors.R` — a library of **14 `construct_*()` functions** plus two utility helpers and a `CONSTRUCTION_LOG`. Each function takes a household data.frame and returns the data.frame augmented with constructed indicator columns. The library structure is summarized in Appendix B.

The library-level conventions:

- **Input contract.** Each function expects specific raw variables to exist in `data`. The `check_required(data, required_vars, indicator_name)` helper guards each function — if any required variable is missing, it logs the failure to `CONSTRUCTION_LOG` and returns `data` unchanged. This lets the BL and ML scripts share the same constructor library even when the two rounds have different raw variable inventories.
- **Output contract.** Each function adds named columns to `data` and returns the augmented frame. Original columns are never dropped — downstream code that needs to inspect the raw inputs always can.
- **Side-effect logging.** `log_construction(indicator, status, details)` records every constructor call (`OK` / `MISSING_VARS` / `ERROR`) for the post-run audit. The accumulated log is printed by the calling script (`01_indicators_bl.R` or `02_indicators_ml.R`).

The two driver scripts (`01_indicators_bl.R`, `02_indicators_ml.R`) call the constructors in a deterministic order, occasionally interleaved with project-specific custom code for indicators that don't generalise enough to live in the library (e.g., the per-section indicators built inline in §15 — TANGO sub-component variables — of `01_indicators_bl.R`).

### 3.2 Food security indicators

These are the most heavily standardised; we follow international convention for each.

#### Food Consumption Score (FCS)

**Methodology.** WFP (2008) Food Consumption Analysis. Weighted frequency over the past 7 days across 8 food groups; food groups have severity weights (e.g., main staples = 2, pulses = 3, meat/fish = 4, oils = 0.5). FCS = $\sum_g w_g \cdot \text{days}_g$, with $\text{days}_g$ capped at 7. Standard thresholds:

| FCS | Category |
|---|---|
| 0 – 21 | Poor |
| 21.5 – 35 | Borderline |
| > 35 | Acceptable |

The thresholds are adjusted upward (0–28 / 28.5–42 / > 42) in contexts where oil and sugar consumption is high. BRCiS uses the standard thresholds.

**Reference.** WFP (2008). *Food Consumption Analysis: Calculation and Use of the Food Consumption Score in Food Security Analysis.* Technical Guidance Sheet. Rome: World Food Programme, Vulnerability Analysis and Mapping Branch (VAM). [WFP VAM Resource Centre — FCS](https://resources.vam.wfp.org/data-analysis/quantitative/food-security/food-consumption-score).

**Implementation.** `construct_fcs_logframe()` in `indicator_constructors.R`; outputs `fcs` (continuous), `fcs_poor` / `fcs_borderline` / `fcs_acceptable` (binaries), and `fcs_poor_border = fcs_poor + fcs_borderline` for the LogFrame "% food insecure" indicator.

#### Food Insecurity Experience Scale (FIES)

**Methodology.** Cafiero, Viviani & Nord (2018). Eight binary items asking the respondent about household-level food-insecurity experiences over the past 12 months (worried about food, ate less than thought should, ran out of food, hungry but didn't eat, lost weight, didn't eat for a whole day, skipped meal, ate less variety). The raw score is the count of "yes" responses (0–8).

**Reference.** Cafiero, C., Viviani, S., & Nord, M. (2018). "Food security measurement in a global context: The Food Insecurity Experience Scale." *Measurement*, 116, 146–152. DOI [10.1016/j.measurement.2017.10.065](https://doi.org/10.1016/j.measurement.2017.10.065). [FAO FIES Technical Paper (open access)](https://www.fao.org/fileadmin/templates/ess/voh/FIES_Technical_Paper_v1.1.pdf).

**⚠️ Important caveat — the BRCiS 4-category classification is NOT the FAO standard.**

| | 0 | 1–3 | 4–6 | 7–8 |
|---|---|---|---|---|
| **FAO SDG 2.1.2 standard** (3 categories) | food secure | food secure | moderately food insecure | severely food insecure |
| **BRCiS LogFrame reporting** (4 categories) | food secure | mildly food insecure | moderately food insecure | severely food insecure |

The official SDG 2.1.2 standard published by FAO and used by UN Stats is a **3-category** classification (0–3 = food secure; 4–6 = moderate; 7–8 = severe). The BRCiS pipeline reports a **4-category** disaggregation that splits the "food secure" bucket into "0 yes responses" and "1–3 yes responses." This is a defensible descriptive disaggregation but is **not** the FAO standard for SDG 2.1.2 reporting. Any external publication that reports the BRCiS FIES distribution at the 4-category level should explicitly flag this as a project-level disaggregation. Cross-references: SDG 2.1.2 metadata at the [UN Stats SDG Indicators portal](https://unstats.un.org/sdgs/metadata/files/Metadata-02-01-02.pdf).

The LogFrame's "moderate or severe food insecurity" headline indicator is built as a binary: `fies_mod_sev = as.integer(fies >= 4)`, which matches the FAO standard's "moderate or severe" union.

**Implementation.** `construct_fies()` in `indicator_constructors.R`; outputs `fies` (0–8), `fies_cat` (4-category factor), and `fies_mod_sev` (binary).

#### Reduced Coping Strategies Index (rCSI)

**Methodology.** Maxwell & Caldwell (2008). Five standardised behavioural items asked over the past 7 days, each weighted by severity:

| Behaviour | Severity weight |
|---|---|
| Rely on less preferred / less expensive foods | 1 |
| Borrow food, or rely on help from friend / relative | 2 |
| Limit portion size at mealtime | 1 |
| Restrict adult consumption so that small children can eat | 3 |
| Reduce number of meals eaten in a day | 1 |

rCSI = $\sum_q w_q \cdot \text{days}_q$, with $\text{days}_q$ capped at 7. Range: 0–56.

**Reference.** Maxwell, D., & Caldwell, R. (2008). *The Coping Strategies Index: A Tool for Rapid Measurement of Household Food Security and the Impact of Food Aid Programs in Humanitarian Emergencies — Field Methods Manual* (2nd ed.). Feinstein International Center / TANGO International / CARE / WFP. [PDF at WFP](https://docs.wfp.org/stellent/groups/public/documents/manual_guide_proced/wfp211058.pdf).

**Important note on BRCiS availability.** `csi1`-`csi5` (the raw rCSI behavioural items) were collected at BL but **not** at ML. The LogFrame `rcsi` row is therefore `bl_only` in the harmonization map. This is documented in `08_ai_management/01_progress_logs/PENDING.md` (resolved 2026-05-27).

**Implementation.** `construct_lcs()` in `indicator_constructors.R`; the rCSI is computed alongside the broader LCS module (next).

#### Livelihood Coping Strategies (LCS)

**Methodology.** WFP / FEWS NET guidance. Behaviours over the past 30 days (or "exhausted within the past 12 months") classified into three severity tiers:

- **Stress strategies** — minor adjustments (e.g., borrowing money, spending savings, selling non-productive assets).
- **Crisis strategies** — moderate adjustments that compromise future productive capacity (e.g., selling productive assets, withdrawing children from school).
- **Emergency strategies** — severe and often irreversible (e.g., begging, selling the last female breeding animals, illegal income activities).

A household is classified at its **maximum severity tier observed** — if it has used any emergency strategy in the period, it is "emergency-coping," regardless of whether it also uses stress or crisis strategies.

**Reference.** WFP (2024). *Livelihood Coping Strategies Indicator for Food Security — Guidance Note*. Rome: WFP. [PDF](https://docs.wfp.org/api/documents/WFP-0000147801/download/). [WFP VAM landing page](https://vamresources.manuals.wfp.org/docs/livelihood-coping-strategies-food-security). Supplementary FEWS NET guidance: [Contextualizing the LCS Module (Nov 2024)](https://fews.net/sites/default/files/2024-11/Guidance-Contextualizing-LCS-Module-202411.pdf).

**Caveat.** LCS has no peer-reviewed primary source — only WFP/FEWS NET institutional guidance. We cite the WFP Guidance Note as the authoritative reference.

**Implementation.** `construct_lcs()` in `indicator_constructors.R`; outputs `lcs_stress`, `lcs_crisis`, `lcs_emergency` (binaries for "any strategy in this tier used") plus `lcs_max` (the max severity tier as a factor).

#### Household Dietary Diversity Score (HDDS)

**Methodology.** Swindale & Bilinsky (2006). Count of how many of 12 food groups any household member consumed in the **previous 24 hours**. Range: 0–12.

| HDDS food group |
|---|
| Cereals; white roots and tubers; vegetables; fruits; meat; eggs; fish and seafood; pulses, legumes and nuts; milk and milk products; oils and fats; sweets; spices, condiments and beverages |

**Reference.** Swindale, A., & Bilinsky, P. (2006). *Household Dietary Diversity Score (HDDS) for Measurement of Household Food Access: Indicator Guide* (Version 2). Washington, DC: Food and Nutrition Technical Assistance Project (FANTA), Academy for Educational Development. [PDF at FANTA](https://www.fantaproject.org/sites/default/files/resources/HDDS_v2_Sep06_0.pdf).

**Important note on BRCiS availability.** Per the indicator-comparability verification documented in `learnings.md` (2026-04-14), the 16 raw food items required for HDDS reconstruction were **BL-only**. The HDDS LogFrame indicator is therefore `bl_only`; we do not report HDDS at ML.

#### Consolidated Approach for Reporting Indicators of Food Security (CARI)

**Methodology.** WFP (2021, 3rd ed.). A consolidated 4-class Food Security Index combining a **current-status domain** (FCS + rCSI or Household Hunger Scale) with a **coping-capacity domain** (LCS + food-expenditure share). The output is one of: food secure, marginally food secure, moderately food insecure, severely food insecure.

**Reference.** World Food Programme (2021, 3rd ed.). *Consolidated Approach for Reporting Indicators of Food Security (CARI) — Technical Guidance Note.* Rome: WFP. [PDF](https://docs.wfp.org/api/documents/WFP-0000107743/download/). [WFP landing page](https://resources.vam.wfp.org/data-analysis/quantitative/food-security/the-consolidated-approach-for-reporting-indicators-of-food-security-cari).

BRCiS reports the individual CARI components (FCS, rCSI, LCS) rather than the combined CARI classification. CARI is mentioned here for context — it is the standard framework that ties FCS / rCSI / LCS together at the policy level.

### 3.3 Resilience-component indicators

These are intermediate indicators that serve as inputs to RSI (§4) and TANGO (§5). They are also reported individually in the LogFrame / KPI 4 tables.

#### Social capital — bonding / bridging / linking

**Methodology.** Following Szreter & Woolcock (2004), three distinct dimensions of social capital are captured:

- **Bonding** — within-group ties (e.g., trust and reciprocity among family / clan / close friends).
- **Bridging** — across-group ties of approximately equal social standing (e.g., trust across ethnic / religious lines or across livelihoods).
- **Linking** — vertical ties across formal power gradients (e.g., trust between citizens and public officials, NGOs, or other institutions).

Each is constructed from a battery of survey items measuring perceived trust, willingness to lend / borrow, and frequency of interaction in the relevant domain. The three dimensions are typed and constructed separately so that policy interventions targeting one can be evaluated without conflating effects.

**Gender disaggregation.** As of 2026-05-25, the BRCiS LogFrame requires **gender-disaggregated** social capital indicators. The construct library produces six variants — `{bonding, bridging, linking}_social_capital_{fhh, mhh}` — gated by household sex (`hh_sex`); non-matching households receive `NA`. The `_fhh` / `_mhh` suffixes were chosen to stay under Stata's 32-character variable-name limit (the more descriptive `_female_headed` / `_male_headed` would have produced names like `bonding_social_capital_female_headed` at 35 chars, breaking `haven::write_dta`).

**References.**

- Szreter, S., & Woolcock, M. (2004). "Health by association? Social capital, social theory, and the political economy of public health." *International Journal of Epidemiology*, 33(4), 650–667. DOI [10.1093/ije/dyh013](https://doi.org/10.1093/ije/dyh013). [Oxford Academic](https://academic.oup.com/ije/article-abstract/33/4/650/665431). — *The canonical academic citation for the three-way bonding / bridging / linking typology.*
- Woolcock, M., & Narayan, D. (2000). "Social capital: Implications for development theory, research, and policy." *World Bank Research Observer*, 15(2), 225–249. DOI [10.1093/wbro/15.2.225](https://doi.org/10.1093/wbro/15.2.225). — *Earlier antecedent that foreshadows linking.*
- Putnam, R. D. (2000). *Bowling Alone: The Collapse and Revival of American Community.* New York: Simon & Schuster. ISBN 978-0-684-83283-8. — *Popular reference for the bonding / bridging distinction; does not originate the three-way framework.*

**Implementation.** `construct_social_capital()` in `indicator_constructors.R`; called from `01_indicators_bl.R` §14 and `02_indicators_ml.R` §14.

#### Self-Reliance Index (SRI)

**Methodology.** Refugee Self-Reliance Initiative (RSRI). A multi-domain index covering housing, food, education, healthcare, health status, safety, employment, financial resources, assistance, debt and savings, and social capital. Each domain is scored on a fixed scale and the household-level index aggregates across domains.

**References.**

- Refugee Self-Reliance Initiative. [https://www.refugeeselfreliance.org/sri](https://www.refugeeselfreliance.org/sri) — methodology landing page; current methodology is SRI 3.0 (2024 release).
- Easton-Calabria, E., Krause, U., et al. (2021). "Measuring self-reliance among refugee and internally displaced households: the development of an index in humanitarian settings." *Conflict and Health*, 15, 51. DOI [10.1186/s13031-021-00389-y](https://doi.org/10.1186/s13031-021-00389-y). — *Peer-reviewed validation paper.*

**Implementation.** `construct_sri()` in `indicator_constructors.R`. SRI in BRCiS uses a project-specific subset of domains adapted to the Somalia context.

#### Other resilience-component indicators

The remaining `construct_*()` functions (`construct_water_access`, `construct_wash`, `construct_financial_access`, `construct_group_participation`, `construct_aspirations`, `construct_income`, `construct_household_composition`) implement BRCiS-specific composites — typically a count or proportion across a small number of survey items measuring access, participation, or psychosocial state. They follow the same library conventions and are documented in their own headers and in Appendix B.

### 3.4 Special construction patterns

Three patterns recur across the indicator library and deserve explicit mention because they affect downstream reporting:

#### Subgroup conditioning via NA propagation

Some indicators are defined only for a subset of households. For example:

- `water_productive_use_normal_year` — only households with `farmer == 1` are asked the question, so non-farmer households are set to `NA` at construction time.
- `{bonding, bridging, linking}_social_capital_{fhh, mhh}` — gender-disaggregated; the `_fhh` variants are NA for male-headed HHs and vice versa.

The pattern is: **set non-subgroup households' values to NA in `hh_indicators_*.rds`**, then let the downstream report's survey-weighted estimator handle the subgroup automatically via `na.rm = TRUE`. The math behind why this gives the correct subpopulation estimator (and correct standard errors) is in `methodology_prepost_weights.md` §7.

#### Same-name same-question, different machinery

Two patterns within this case:

- **Same conceptual construct, different question-type machinery.** E.g., `cope_save` (a binary indicating that the household saves money to cope with shocks) was a single-choice question at BL and became a multi-choice question at ML. The construct is conceptually the same, but the denominators differ. Resolution: keep the same harmonized name `cope_save`, flag `comparable = no` in the harmonization map, report both round means but no Δ.

- **Different parent question entirely.** E.g., `total_inc_increased` / `total_inc_decreased` had the same variable name at both rounds but referred to **different parent questions**: at BL, "income change over the past 12 months"; at ML, "income change vs. ~2 years pre-project" (i.e., a much longer reference period). Resolution: rename to make the divergence visible at the variable-name level — `inc_increased_12mo_perception` / `inc_decreased_12mo_perception` at BL; `inc_increased_vs_prebrcis` / `inc_decreased_vs_prebrcis` at ML. The harmonization map treats them as `bl_only` + `ml_only`, with no Δ.

Both patterns are codified into the constructor library and into the harmonization map; the design decision sits in `decision_log.md` (2026-05-25 entries).

#### Structural absence at one round

Some variables are structurally absent at one of the two rounds:

- `save_formal` — asked at BL only; was inadvertently being created as an all-NA column at ML in early versions of `02_indicators_ml.R`. As of 2026-05-25 the column is **not created at all** at ML; the harmonization map treats it as `bl_only`. Better than carrying an all-NA column.
- `csi1`-`csi5` (rCSI inputs) — BL only; rCSI itself is therefore `bl_only`. Confirmed 2026-05-27 per PENDING.md.
- `access_insurance` — BL only; handled specially via LOCF in TANGO ML projection (§6 below).
- HDDS food items — BL only; HDDS is therefore `bl_only`.

The general rule: if a variable is genuinely not collected at a round, **do not create the column at that round** (avoid all-NA columns). Document the bl_only / ml_only status in the harmonization map. Make any LOCF or other cross-round imputation explicit in code (not implicit in the data).

---

## 4. The Resilience Spectrum Index (RSI)

This section gives the essential methodology and decisions. The deep-dive — sub-index variable lists, the per-sub-index ICW weights, BL→ML distribution shifts, top driver decomposition, coverage diagnostics — lives in `04_scripts/07_construct/07_rsi_methodology.qmd`. Refer there for any quantitative spot check.

### 4.1 The Anderson (2008) ICW estimator

**Reference.** Anderson, M. L. (2008). "Multiple Inference and Gender Differences in the Effects of Early Intervention: A Reevaluation of the Abecedarian, Perry Preschool, and Early Training Projects." *Journal of the American Statistical Association*, 103(484), 1481–1495. DOI [10.1198/016214508000000841](https://doi.org/10.1198/016214508000000841). [UC eScholarship open-access preprint](https://escholarship.org/uc/item/15n8j26f).

Anderson's Inverse Covariance Weighted (ICW) summary-index estimator combines $J$ standardised outcomes into a single summary index using a GLS-style weighted average. The estimator is:

$$
s_i \;=\; \big(\mathbf{1}^\top \Sigma^{-1} \mathbf{1}\big)^{-1} \, \mathbf{1}^\top \Sigma^{-1} \, \tilde{y}_i,
$$

where $\tilde{y}_i$ is the column vector of $J$ standardised outcomes for household $i$ and $\Sigma$ is the variance-covariance matrix of those outcomes (computed on the BL data — see §4.4). The implied **weight vector** is:

$$
w_{\text{ICW}} \;=\; \big(\mathbf{1}^\top \Sigma^{-1} \mathbf{1}\big)^{-1} \, \mathbf{1}^\top \Sigma^{-1}.
$$

The weights sum to 1 by construction. The intuition: components that carry **independent** information (low correlation with the others) get **higher** weights, because they convey more "new" content; components that overlap heavily with others (high correlation) get **lower** weights, because their information is already captured by other components.

Negative weights can arise. They do not indicate a bug — ICW penalises positively-correlated indicators to net out shared variance, and the resulting weights can be negative. We retain negative weights as Anderson's formula produces; the per-sub-index weight tables in `07_rsi_methodology.qmd` §2.1–2.3 surface them explicitly so the reader can inspect them.

### 4.2 The three sub-indices

RSI is composed of three sub-indices, each computed via ICW on its own indicator set:

| Sub-index | Theme | # variables | BAE weight |
|---|---|---|---|
| **S1 — Leadership** | Community leadership, governance, conflict resolution | 26 | 0.32 |
| **S2 — Ecosystem** | Natural resource access, ecosystem services | 18 | 0.38 |
| **S3 — Market** | Market access, financial inclusion, livelihoods | 15 | 0.30 |

The composite RSI is the BAE-weighted (Budget Allocation Exercise — a participatory weighting performed during BRCiS programme design) sum of the three rescaled sub-indices:

$$
\text{RSI} \;=\; 0.32 \cdot s_1^* \;+\; 0.38 \cdot s_2^* \;+\; 0.30 \cdot s_3^*,
$$

where $s_k^*$ is the rescaled sub-index (§4.3). The full variable lists per sub-index are in `07_rsi_methodology.qmd` §1.1 and `05_rsi_index_bl.R` (search for `columns_s1`, `columns_s2`, `columns_s3`).

### 4.3 Two rescaling families — Min-Max and pnorm

Each raw sub-index $s_k$ is computed in z-score space (mean 0, varying scale). For interpretability, both ICW sub-index scores and the composite are rescaled to a **1–5 ruler**. The pipeline computes **two parallel rescalings**:

- **Min-Max (linear):**

$$
s^* \;=\; 1 \;+\; 4 \cdot \frac{s - s_{\min}^{BL}}{s_{\max}^{BL} - s_{\min}^{BL}}.
$$

Linear; preserves linear differences uniformly across the range; ML scores can fall outside $[1, 5]$ if the construct shifts beyond the BL range.

- **pnorm (nonlinear):**

$$
s^* \;=\; 1 \;+\; 4 \cdot \Phi\big(s \cdot \sqrt{k_{BL}}\big),
$$

where $\Phi$ is the standard normal CDF and $k_{BL}$ is a per-sub-index visual-uniformity parameter set at BL (legacy values: $k_{BL} = 20$ for S1, $k_{BL} = 10$ for S2 and S3). Bounded in $[1, 5]$ by $\Phi$; tail shifts get compressed, mid-range shifts amplified.

Both rescalings use **only BL parameters** ($s_{\min}^{BL}$, $s_{\max}^{BL}$, $k_{BL}$) and are fixed-function ("Type B") rescalings, so BL→ML comparability is preserved by construction. Refitting per round (e.g., recomputing min/max at ML) would erase any level shift in the construct — useless for tracking change.

**For external reporting**, the preliminary report uses **pnorm** as the headline rescaling — the BL distribution is right-skewed and pnorm's nonlinear stretch makes the 1–5 range actually used. The Min-Max rescaling is retained as a robustness column in the data files (columns `s1_minmax`, `s2_minmax`, `s3_minmax`, `rsi_minmax`).

### 4.4 BL anchoring protocol

Four BL artifacts are saved to `DATA_CLEAN/rsi/bl_artifacts.rds` at the end of `05_rsi_index_bl.R` and re-used unchanged by `06_rsi_index_ml.R`:

| BL artifact | ML use | Why it must come from BL |
|---|---|---|
| Column means $\mu_{BL,j}$ and SDs $\sigma_{BL,j}$ | Standardise ML data: $z_{ML} = (x_{ML} - \mu_{BL}) / \sigma_{BL}$ | Same physical HH at BL and ML should get the same z-score — locking the reference at BL preserves meaning. |
| ICW weights $w_{BL}$ per sub-index | Linear combination: $s_{ML} = z_{ML} \cdot w_{BL}$ | Locking weights means index movement comes from indicator changes, not from a shifting weighting scheme. |
| BL min/max per sub-index and BL $k$ | Rescale $s_{ML}$ to 1–5 | A score of 3.5 means the same thing at both rounds; ML may fall outside $[1, 5]$ under Min-Max if the construct shifted. |
| BL terciles of the composite RSI | Classify ML into Low / Medium / High | Recomputing terciles at ML would force ML into balanced thirds by construction, erasing compositional shift. |

The `bl_artifacts.rds` schema is documented in `07_rsi_methodology.qmd` and in the header comments of `05_rsi_index_bl.R`.

### 4.5 Imputation policy

**Missing data** in the sub-index variables (mostly at BL where some variables have moderate NA rates) is handled by kNN imputation:

- $k = 5$.
- Weighted by inverse Euclidean distance in z-score space.
- Weighted mean for numeric variables (via `VIM::kNN` with `laeken::weightedMean`).

Two carve-outs:

1. **At BL, kNN is applied to all sub-index variables.**
2. **At ML, kNN is applied only to non-ARC-D variables.** ARC-D-sourced variables are intentionally **not imputed** — the three ML communities lacking ARC-D (DegAdey, Ceeldhiinle, Dhugile) keep their NAs, so when the ICW linear combination is computed, those HHs land at NA on the sub-index and consequently on RSI. They get **no ML RSI score** rather than have ARC-D values manufactured for them.

The total ML RSI coverage: 3,792 / 3,889 (97 HHs without ML RSI: the 73 ARC-D-missing plus 24 with sporadic `arcd24/25/26` NA in covered communities). This is documented in `07_rsi_methodology.qmd` §5.

### 4.6 PI-agreed deviations from legacy

The midline RSI follows the legacy BL construction (ported from `09_legacy_vault/codes/baseline/03_clean_data/04_03_Resilience Spectrum Index.R`) with three small adjustments agreed with the PI on 2026-05-23:

1. **S3 variable trim** — `access_insurance` removed (not asked at ML); `female_eco_decision` removed (high BL NA rate, kNN imputation share too large to be reliable).
2. **Min-Max rescaling computed alongside pnorm** — pnorm is the headline rescaling, but Min-Max is retained for robustness (linear interpretation easier to communicate to stakeholders).
3. **Per-sub-index 5-category breakdown dropped** — the legacy script produced `s1_cat`, `s2_cat`, `s3_cat` with hardcoded breakpoints `c(-Inf, -0.2, -0.05, 0.05, 0.2, Inf)` that we judged arbitrary and unhelpful for tracking change. The 3-category RSI (Low / Medium / High via BL terciles) is retained.

These decisions are formalised in `08_ai_management/02_quality_reports/decision_log.md` (entries dated 2026-05-23 and 2026-05-24).

---

## 5. The TANGO Resilience Capacity Index

This section gives the essential methodology and decisions. The deep-dive — per-capacity factor loadings, polychoric correlation heatmaps, the kNN missingness handling, BL→ML driver decomposition, the full "access_insurance problem" treatment — lives in `04_scripts/07_construct/10_tango_methodology.qmd`. Refer there for any quantitative spot check.

### 5.1 The Frankenberger / TANGO three-capacity framework

**Reference.** Frankenberger, T., Langworthy, M., Spangler, T., Nelson, S., Campbell, J., & Njoka, J. (2012). *Enhancing Resilience to Food Security Shocks in Africa.* Discussion Paper. Tucson, AZ: TANGO International (prepared for USAID / DFID / World Bank). [PDF at FSN Network](https://www.fsnnetwork.org/sites/default/files/discussion_paper_usaid_dfid_wb_nov._8_2012.pdf). Foundational reference for USAID Feed-the-Future resilience analysis.

**Secondary reference (resilience measurement principles).** Constas, M., Frankenberger, T., & Hoddinott, J. (2014). *Resilience Measurement Principles: Toward an Agenda for Measurement Design.* FSIN Technical Series No. 1. Rome: FSIN / World Food Programme. [PDF at FSIN](https://www.fsinplatform.org/sites/default/files/paragraphs/documents/FSIN_TechnicalSeries_1.pdf).

The Frankenberger et al. (2012) framework distinguishes three latent **resilience capacities** that households draw on when shocks materialise:

- **Absorptive capacity** — the ability to cope with shocks without major adjustments to existing livelihoods (savings, insurance, social capital, mitigation).
- **Adaptive capacity** — the ability to make incremental adjustments to livelihoods in response to shocks (diversification, education, information).
- **Transformative capacity** — the ability to effect structural / institutional change (community institutions, basic services, participation in decision-making).

The three capacities are not mutually exclusive — some indicators (e.g., `asset_ownership`, `bridging_social_capital`, `linking_social_capital`) sit in two or more capacity variable lists, and each capacity is fit independently so a shared variable can receive slightly different imputed values across capacities (different kNN neighbours).

TANGO International (the organisation) is a Tucson-based research and evaluation firm specialising in resilience measurement; the methodology and the organisation share a name, which can be confusing. The framework is a USAID-funded methodology authored by TANGO; "the TANGO Index" refers to the operationalisation of the three-capacity framework as a factor-analytic composite.

### 5.2 Variable lists

The legacy active variable lists from `09_legacy_vault/.../04_02_Construct TANGO indicators.R` are kept verbatim at BL:

| Capacity | Variables (count) |
|---|---|
| **Absorptive** (8) | `avail_inf_safety`, `bonding_social_capital`, `access_savings`, `access_remittances`, `asset_ownership`, `shock_prep_mitig`, `access_insurance`, `access_hum_assist` |
| **Adaptive** (9) | `bridging_social_capital`, `linking_social_capital`, `education_training`, `livelihood_diversification`, `exposure_information`, `asset_ownership`, `avail_financial`, `asp_conf_adapt_index`, `support_network` |
| **Transformative** (6) | `avail_communal`, `avail_basic_services`, `bridging_social_capital`, `linking_social_capital`, `coll_action_num`, `part_decision_making` |

`asset_ownership` appears in both Absorptive and Adaptive; `bridging_social_capital` and `linking_social_capital` appear in both Adaptive and Transformative — see the §6 deep-dive on this.

`access_insurance` is a notable case. At BL it is observed; at ML the question is **not asked** by the survey instrument. The naive fix would be to drop it from the Absorptive list and run a 7-variable factor analysis at both rounds. We attempted that and the result was a **degenerate factor**: the absorptive score collapsed onto `shock_prep_mitig` alone (loading 0.998 with very little signal from the other indicators), because `access_insurance` was the "hub" variable linking `access_savings` and `shock_prep_mitig` in the BL factor structure. We instead **keep `access_insurance` in the 8-variable list at BL** and **inject each ML HH's BL value via LOCF** at ML; §6 below documents the LOCF policy in full.

### 5.3 Two-stage factor analysis

The TANGO methodology applies factor analysis in **two stages**.

**Stage 1 — Per-capacity 1-factor solution.** For each capacity $k \in \{\text{abs}, \text{adp}, \text{trf}\}$:

1. Subset the BL data to the capacity's indicator variables (8, 9, or 6 columns).
2. Z-score each variable using its own BL mean and SD (NAs removed): $z_{ij} = (x_{ij} - \mu_{BL,j}) / \sigma_{BL,j}$.
3. kNN-impute the z-scored data ($k = 5$, weighted by inverse distance — see §5.5 for the imputation policy).
4. Compute the **polychoric / polyserial correlation matrix** $R_k$ of the (z-scored, imputed) indicators via `polycor::hetcor(ML = TRUE)`. Polychoric correlations are the right tool for mixed binary / ordinal / continuous indicators; `hetcor` detects the type of each variable automatically.
5. Fit a **1-factor maximum-likelihood factor analysis** on $R_k$ via `psych::fa(nfactors = 1, fm = "ml", rotate = "none")`. The output is a vector of factor loadings $L_k$.
6. Compute **regression-based factor-score weights**: $w_k = R_k^{-1} L_k$. The per-HH capacity score is $s_{i,k} = z_{i, \cdot}^{(k)} \cdot w_k$.

**Stage 2 — Meta factor analysis on capacity scores.** Repeat steps 2–6 with the three raw (unrescaled) capacity scores $(s_{i, \text{abs}}, s_{i, \text{adp}}, s_{i, \text{trf}})$ as the input matrix. Since these inputs are continuous, `hetcor` falls back to Pearson correlations. The output is a meta-loading vector and meta-weight vector that combine the three capacities into an overall TANGO score.

Both stages use the **regression-based factor-score** formula $w = R^{-1} L$ rather than Bartlett-style or Thurstone scores. The choice is documented in `10_tango_methodology.qmd` §1.2.

### 5.4 BL anchoring protocol

The same logic as RSI applies (§4.4): all BL parameters are persisted in `DATA_CLEAN/tango/bl_artifacts.rds` and re-used unchanged at ML. The artifacts include:

- Per-capacity column means $\mu_{BL,j}$ and SDs $\sigma_{BL,j}$.
- Per-capacity polychoric correlation matrices $R_k$ and loadings $L_k$.
- Per-capacity raw min/max for the 0–100 rescaling.
- Meta-stage correlation matrix and loadings for the overall TANGO.
- Overall TANGO BL terciles for Low / Medium / High classification.

### 5.5 Imputation policy

kNN imputation ($k = 5$, weighted by inverse distance) with two hold-outs at ML:

1. **ARC-D-sourced variables** (4 indicators: `avail_inf_safety`, `avail_financial`, `avail_communal`, `avail_basic_services`) are **not imputed at ML**. The three ARC-D-missing communities (73 panel HHs) keep NAs, which propagate to NA on the relevant capacity and on overall TANGO.
2. **`access_insurance`** is **not imputed**. Each ML panel HH's BL value is injected via LOCF (next section); the variable is then treated as observed for the projection.

Total ML TANGO coverage: 3,816 / 3,889 (73 HHs without ML TANGO — exactly the three ARC-D-missing communities). TANGO has fewer NAs than RSI's 97 because TANGO inputs are mostly community-level constructed indicators, not raw `arcd24/25/26` items that can be sporadically missing within otherwise-covered communities.

### 5.6 Rescaling — 0 to 100

The overall TANGO score and the three capacity scores are linearly rescaled to a 0–100 range using BL anchors:

$$
s^* \;=\; 100 \cdot \frac{s - s_{\min}^{BL}}{s_{\max}^{BL} - s_{\min}^{BL}}.
$$

A TANGO score of 50 means the same thing at BL and ML. ML scores may fall outside $[0, 100]$ if the construct shifted beyond BL extremes; this is the desired behaviour for tracking change.

### 5.7 PI-agreed deviations from legacy

The midline TANGO follows the legacy approach with two notable PI-agreed adjustments:

1. **`access_insurance` kept at BL, LOCF-injected at ML** — the alternative (dropping it from the 8-var list) produced a degenerate absorptive factor. Full rationale in §6 below and in `10_tango_methodology.qmd` §7.
2. **Per-capacity 5-category breakdown not built** — the legacy code did not produce 5-bin cuts per capacity, and we follow that. Only the overall TANGO index gets a 3-category Low / Medium / High via BL terciles.

---

## 6. The LOCF policy

### 6.1 What LOCF is

**Last Observation Carried Forward (LOCF)** is a standard imputation technique for longitudinal data: when a variable is observed at an earlier time point ($t = 0$) but not at a later time point ($t = 1$), the earlier observation is used as a stand-in for the unobserved later value. It is an explicit assumption that the variable has not changed in the interim — an assumption that may or may not be defensible depending on the variable.

LOCF in BRCiS is applied to **exactly one variable** — `access_insurance` — and **only inside the TANGO ML projection**. The policy is intentionally narrow:

- **NOT** applied to `hh_indicators_ml.rds` — the indicators file preserves the genuine NA semantics; `access_insurance` is `NA` at ML in `hh_indicators_ml.rds`, period.
- **NOT** applied to RSI — the RSI script drops `access_insurance` from the S3 variable list entirely (the simpler fix in that context).
- **APPLIED** to TANGO ML only, inside `09_tango_ml.R` §1a, where it is necessary to preserve the BL absorptive factor structure.

### 6.2 Where it is applied — `09_tango_ml.R` §1a

The mechanism in `09_tango_ml.R` (lines 105–139):

1. Load `DATA_CLEAN/indicators/brcisIII_baseline_hh_indicators.rds`.
2. Load the BL↔ML merge key (`brcisIII_bl_ml_household_survey_merge_key.dta`).
3. For each ML panel HH, look up the matching BL `_uuid` via the merge key, then look up `access_insurance` from BL indicators at that BL `_uuid`.
4. Inject the looked-up value as a new column `access_insurance` in the ML data **before the projection** (i.e., before the standardisation in step 3 of the per-capacity stage-1 flow described in §5.3).
5. The variable is then treated as observed for the absorptive-capacity factor projection. kNN imputation is **not** applied to this column at ML.

The key fact: the LOCF-injected `access_insurance` lives **only in memory** inside `09_tango_ml.R`. It is **not persisted** to `hh_indicators_ml.rds` or any other downstream file. The harmonization map and the preliminary report continue to see `hh_indicators_ml.access_insurance` as `NA`.

### 6.3 Why LOCF is necessary (and why not just drop the variable)

We attempted the simpler fix — drop `access_insurance` from the Absorptive list and run a 7-variable factor analysis at both rounds. The result was a **degenerate factor** at both rounds:

- The absorptive factor score collapsed onto `shock_prep_mitig` alone.
- Factor loading for `shock_prep_mitig` rose from ~0.51 (in the 8-var BL fit) to ~0.998.
- Loadings for the other six absorptive variables (savings, remittances, asset ownership, etc.) all dropped close to zero.

The interpretation: in the BL factor structure, `access_insurance` was a **hub variable** — it had moderate, balanced correlations with most other absorptive indicators (in particular with `access_savings` and `shock_prep_mitig`), and removing it collapsed the latent factor onto whichever indicator was most strongly correlated with all the others (`shock_prep_mitig`). The 7-variable absorptive score was no longer a meaningful "absorptive capacity" composite — it was effectively just a measure of shock preparation and mitigation.

LOCF resolves this by **keeping the BL factor structure intact** at both rounds. The implicit assumption is that household-level access to insurance has not changed materially between BL and ML — which is plausible for the BRCiS population given that formal insurance markets in rural Somalia evolve slowly, but is not directly testable without ML data on the variable.

### 6.4 The implicit assumption and its plausibility

The LOCF assumption is: **for each panel household, access_insurance at ML equals access_insurance at BL**.

Plausibility for the BRCiS population:

- Formal insurance products targeting rural Somali households are rare and evolve slowly. Programme-induced changes (e.g., a community insurance scheme launched between BL and ML) are localised and would be observable through other indicators (membership in cooperative groups, group savings).
- Informal insurance (relationships with relatives, community pooling) varies more, but is captured by other indicators (`access_remittances`, `bonding_social_capital`).
- The variable is binary (0/1) at BL — coarse enough that small changes in access don't flip the value.

Sensitivity analysis: the deep-dive in `10_tango_methodology.qmd` §7 walks through alternative treatments — dropping `access_insurance` entirely, imputing it via the meta-survey median, etc. — and shows that the absorptive capacity score is sensitive to the variable's treatment but the **overall TANGO score** (after the second-stage factor aggregation) is much less sensitive. The TANGO 0–100 rescaling further dampens the sensitivity. Net: LOCF is the cleanest defensible treatment given the constraints.

### 6.5 What we would do differently

If `access_insurance` were a critical headline indicator (it is not — it is one of 8 absorptive sub-components), we would have asked the survey team to include the question at ML. The lesson for future evaluations: identify "hub" indicators in the BL factor structure early, and ensure they are re-asked at ML to avoid this kind of structural imputation. The Constas-Frankenberger-Hoddinott (2014) FSIN principles paper recommends exactly this — preserve the indicator scaffolding across rounds even when the substantive questionnaire evolves.

---

## 7. BL→ML projection conventions

The construct phase splits cleanly into a **BL fit** and an **ML projection**. The BL scripts (`01_indicators_bl.R`, `05_rsi_index_bl.R`, `08_tango_bl.R`) produce both the per-HH outputs and a `bl_artifacts.rds` bundle containing every parameter the ML scripts need. The ML scripts (`02_indicators_ml.R`, `06_rsi_index_ml.R`, `09_tango_ml.R`) read those artifacts and project through them without any re-fitting.

### 7.1 Why BL parameters anchor ML

The principle is simple: **anything that can shift between rounds must be locked at BL** for BL→ML comparability. Specifically:

| Parameter | Why locked at BL |
|---|---|
| Variable means $\mu_j$ and SDs $\sigma_j$ for z-scoring | A household with identical values at BL and ML must produce identical z-scores. Refitting at ML would erase any level shift. |
| ICW weights (RSI) and factor loadings (TANGO) | Locking weights means the index movement is driven by indicator changes, not by a shifting weighting scheme. |
| Rescaling anchors (min/max for Min-Max, $k$ for pnorm, raw min/max for TANGO 0–100) | A score of 3.5 or 50 means the same thing at both rounds. ML scores can exceed the BL range — that is exactly the kind of compositional shift we want to detect. |
| Terciles for Low / Medium / High classification | Recomputing terciles at ML would force ML into balanced thirds by construction. The whole point of round-comparable categorisation is to show compositional shift, not erase it. |

### 7.2 `bl_artifacts.rds`

Both `05_rsi_index_bl.R` and `08_tango_bl.R` write a `bl_artifacts.rds` bundle to `DATA_CLEAN/{rsi,tango}/bl_artifacts.rds`. The bundle is a named list whose exact schema is documented in the script headers and methodology QMDs. Critical fields:

- **RSI** — per sub-index: `variables` (the active variable list), `mu`, `sigma`, `R` (correlation matrix), `weights` (ICW weights), `s_min`, `s_max` (Min-Max anchors), `k` (pnorm anchor). Plus `terciles_RSI` for the composite.
- **TANGO** — per capacity: `vars`, `mu`, `sigma`, `R` (polychoric), `loadings`, `weights` ($= R^{-1} L$), `min`, `max`. Plus the meta-stage `R_meta`, `loadings_meta`, `weights_meta`, `min_meta`, `max_meta`, and overall terciles.

### 7.3 Fail-fast assertions in ML scripts

The ML scripts include explicit assertions at the top to catch BL-artifact mismatches:

- Panel-size assertion: after the weights inner-join, `nrow(data)` must equal `bl_artifacts$metadata$n_panel`. Aborts if not.
- Variable-list assertion: the columns required by `bl_artifacts$s1$variables` (etc.) must all exist in the ML data. Aborts if not.
- Loadings-dimension assertion: the loadings vector and the data subset must have matching dimensions.

These assertions are intentional — they catch the class of bug where a future change to `01_indicators_bl.R` produces a variable list inconsistent with the ML scripts, and fail loudly rather than silently producing nonsense ML scores.

---

## 8. Verification and diagnostics

### 8.1 The three diagnostic QMDs

| QMD | Renders to | Purpose |
|---|---|---|
| `04_scripts/07_construct/03_indicators_diagnostics.qmd` | `05_outputs/04_reports/07_construct/03_indicators_diagnostics.html` | Indicator-level inventory + headline statistics. One row per constructed indicator, columns for BL/ML presence, BL/ML mean, BL/ML missing %. Includes the impacted-variables table for ARC-D NA propagation. |
| `04_scripts/07_construct/07_rsi_methodology.qmd` | `05_outputs/04_reports/07_construct/07_rsi_methodology.html` | RSI deep-dive: per-sub-index ICW weights, BL/ML histograms, top-driver decomposition, coverage diagnostics. |
| `04_scripts/07_construct/10_tango_methodology.qmd` | `05_outputs/04_reports/07_construct/10_tango_methodology.html` | TANGO deep-dive: per-capacity factor loadings, polychoric correlation heatmaps, kNN imputation summary, the access_insurance LOCF treatment in §7, BL→ML driver decomposition. |

The QMDs are rendered manually (not part of a master script — there is no `00_master_construct.R` yet) and the resulting HTMLs are moved to `05_outputs/04_reports/07_construct/` per the no-`_quarto.yml` convention.

### 8.2 What to check before trusting a construct change

If you modify any indicator constructor, RSI, or TANGO script, re-run the affected scripts and inspect:

1. **Row count** — `nrow(data)` must remain 3,889 after the inner-join with weights (the assertion will catch this, but verify the assertion fires).
2. **Headline statistics in the diagnostic QMD** — re-render `03_indicators_diagnostics.qmd` and spot-check the indicator means / proportions for the variable you touched. A BL mean shift of more than ~0.01 in a stable indicator is suspicious.
3. **ARC-D NA propagation** — the impacted-variables table at the bottom of `03_indicators_diagnostics.qmd` should still show the same 4 ARC-D-derived variables (`avail_inf_safety`, `avail_financial`, `avail_communal`, `avail_basic_services`) and the same 73-HH NA count at ML.
4. **RSI / TANGO coverage** — 3,792 ML HHs with RSI, 3,816 with TANGO. Deviations indicate either an ARC-D handling regression or a new NA source.
5. **bl_artifacts consistency** — if you change a variable list, re-run the BL script to refresh `bl_artifacts.rds` BEFORE running the ML script. Otherwise the ML script will fail the variable-list assertion.

### 8.3 The verification script for downstream consumers

`04_scripts/09_preliminary_report/_scratch/verify_prepost_math.R` provides mechanical verification that the construct outputs are correctly consumed by the report layer (Horvitz-Thompson means agree with manual calculations; NA propagation ≡ subset; etc.). If a construct change is suspected of breaking something downstream, run that script — it exits 0 on agreement.

---

## 9. Decisions departed from legacy

This is a single-source roll-up of the PI-agreed deviations from the legacy BL construction in `09_legacy_vault/`. Each is documented in `08_ai_management/02_quality_reports/decision_log.md` with the rationale and the date.

### Indicators

| Change | What changed | Why | Decision-log entry |
|---|---|---|---|
| FIES categorisation | 4-category (0 / 1–3 / 4–6 / 7–8) for descriptive reporting; 3-category (0–3 / 4–6 / 7–8) for FAO SDG 2.1.2 conformance. Binary `fies_mod_sev = (fies >= 4)` for LogFrame. | Disaggregated reporting requested by the BRCiS consortium; SDG-conformant 3-cat available for any external publication. | 2026-05-25 |
| `save_formal` at ML | Column not created at ML (was previously all-NA). | All-NA columns are noise. The harmonization map captures the `bl_only` presence explicitly. | 2026-05-25 |
| `cope_save_grains` at ML | Construction uses `cope_past1 == 1 OR cope_past2 == 1` (ML's multi-choice form), not the BL `cope_past %in% c(1, 2)`. | At ML, `cope_past` is a `select_multiple`, not a `select_one`. | 2026-05-25 |
| `cope_save` (new variable) | Built at both rounds; `comparable = no` in the map. | BL forces single-choice and ML allows multi-choice — the rates capture different denominators. Keeping both means visible but no Δ. | 2026-05-25 |
| `total_inc_increased` / `total_inc_decreased` rename | BL → `inc_increased_12mo_perception`, `inc_decreased_12mo_perception`. ML → `inc_increased_vs_prebrcis`, `inc_decreased_vs_prebrcis`. | Different parent questions at BL vs ML (12-month vs ~2-year reference); rename makes the divergence visible at the variable-name level. | 2026-05-25 |
| Gender-disaggregated social capital | Six new variables `{bonding, bridging, linking}_social_capital_{fhh, mhh}`. | LogFrame requires gender breakdown. Suffix kept short for Stata 32-char limit. | 2026-05-25 |
| `water_productive_use_normal_year` | New farmer-gated indicator (`water10 == 1` conditional on `farmer == 1`); non-farmers → NA. | LogFrame's "productive water use among farmers" headline. Subgroup conditioning via NA propagation. | 2026-05-25 |

### RSI

| Change | Why | Decision-log entry |
|---|---|---|
| S3 trim — `access_insurance` removed | Variable not asked at ML. | 2026-05-23 |
| S3 trim — `female_eco_decision` removed | High BL NA rate; kNN would impute a large share. | 2026-05-23 |
| Min-Max rescaling computed alongside pnorm | pnorm headline; Min-Max retained for robustness. | 2026-05-23 |
| Per-sub-index 5-category breakdown (`s*_cat`) dropped | Hardcoded breakpoints, arbitrary, not used downstream. | 2026-05-23 |

### TANGO

| Change | Why | Decision-log entry |
|---|---|---|
| `access_insurance` kept in 8-var absorptive list at BL | Dropping it produces a degenerate factor (collapses onto `shock_prep_mitig`). | 2026-05-24 |
| `access_insurance` LOCF-injected at ML | Preserves BL factor structure; assumption is plausible for binary insurance access in rural Somalia. | 2026-05-24 |
| ARC-D variables held out from kNN at ML | The 3 ARC-D-missing communities propagate genuine NAs rather than have community-level values manufactured. | 2026-05-24 |

---

## 10. References

All citations have been verified against publisher or DOI-resolver pages.

**Books**

1. Putnam, R. D. (2000). *Bowling Alone: The Collapse and Revival of American Community.* New York: Simon & Schuster. ISBN 978-0-684-83283-8.

**Foundational papers — resilience / index aggregation**

2. Anderson, M. L. (2008). Multiple Inference and Gender Differences in the Effects of Early Intervention: A Reevaluation of the Abecedarian, Perry Preschool, and Early Training Projects. *Journal of the American Statistical Association*, 103(484), 1481–1495. DOI [10.1198/016214508000000841](https://doi.org/10.1198/016214508000000841). [UC eScholarship open-access preprint](https://escholarship.org/uc/item/15n8j26f). — *Canonical reference for the ICW summary-index estimator.*
3. Constas, M., Frankenberger, T., & Hoddinott, J. (2014). *Resilience Measurement Principles: Toward an Agenda for Measurement Design.* FSIN Technical Series No. 1. Rome: FSIN / WFP. [PDF](https://www.fsinplatform.org/sites/default/files/paragraphs/documents/FSIN_TechnicalSeries_1.pdf).
4. Frankenberger, T., Langworthy, M., Spangler, T., Nelson, S., Campbell, J., & Njoka, J. (2012). *Enhancing Resilience to Food Security Shocks in Africa.* Discussion Paper. Tucson, AZ: TANGO International (USAID / DFID / World Bank). [PDF at FSN Network](https://www.fsnnetwork.org/sites/default/files/discussion_paper_usaid_dfid_wb_nov._8_2012.pdf). — *Three-capacity resilience framework.*

**Food security indicators**

5. Cafiero, C., Viviani, S., & Nord, M. (2018). Food security measurement in a global context: The Food Insecurity Experience Scale. *Measurement*, 116, 146–152. DOI [10.1016/j.measurement.2017.10.065](https://doi.org/10.1016/j.measurement.2017.10.065). [FAO FIES Technical Paper (open access)](https://www.fao.org/fileadmin/templates/ess/voh/FIES_Technical_Paper_v1.1.pdf). — *Canonical reference for FIES.*
6. Maxwell, D., & Caldwell, R. (2008). *The Coping Strategies Index: A Tool for Rapid Measurement of Household Food Security and the Impact of Food Aid Programs in Humanitarian Emergencies — Field Methods Manual* (2nd ed.). Boston / Tucson / Atlanta / Rome: Feinstein International Center, TANGO International, CARE, WFP. [PDF](https://docs.wfp.org/stellent/groups/public/documents/manual_guide_proced/wfp211058.pdf). — *Canonical reference for rCSI.*
7. Swindale, A., & Bilinsky, P. (2006). *Household Dietary Diversity Score (HDDS) for Measurement of Household Food Access: Indicator Guide* (Version 2). Washington, DC: FANTA / AED. [PDF](https://www.fantaproject.org/sites/default/files/resources/HDDS_v2_Sep06_0.pdf).
8. World Food Programme (2008). *Food Consumption Analysis: Calculation and Use of the Food Consumption Score in Food Security Analysis.* Technical Guidance Sheet. Rome: WFP VAM. [WFP VAM Resource Centre — FCS](https://resources.vam.wfp.org/data-analysis/quantitative/food-security/food-consumption-score).
9. World Food Programme (2021). *Consolidated Approach for Reporting Indicators of Food Security (CARI) — Technical Guidance Note* (3rd ed.). Rome: WFP. [PDF](https://docs.wfp.org/api/documents/WFP-0000107743/download/). [WFP landing page](https://resources.vam.wfp.org/data-analysis/quantitative/food-security/the-consolidated-approach-for-reporting-indicators-of-food-security-cari).
10. World Food Programme (2024). *Livelihood Coping Strategies Indicator for Food Security — Guidance Note.* Rome: WFP. [PDF](https://docs.wfp.org/api/documents/WFP-0000147801/download/). FEWS NET supplementary guidance: [Contextualizing LCS Module (Nov 2024)](https://fews.net/sites/default/files/2024-11/Guidance-Contextualizing-LCS-Module-202411.pdf).

**Social capital**

11. Szreter, S., & Woolcock, M. (2004). Health by association? Social capital, social theory, and the political economy of public health. *International Journal of Epidemiology*, 33(4), 650–667. DOI [10.1093/ije/dyh013](https://doi.org/10.1093/ije/dyh013). — *Canonical academic citation for the three-way bonding / bridging / linking typology.*
12. Woolcock, M., & Narayan, D. (2000). Social capital: Implications for development theory, research, and policy. *World Bank Research Observer*, 15(2), 225–249. DOI [10.1093/wbro/15.2.225](https://doi.org/10.1093/wbro/15.2.225).

**Self-reliance**

13. Easton-Calabria, E., Krause, U., et al. (2021). Measuring self-reliance among refugee and internally displaced households: the development of an index in humanitarian settings. *Conflict and Health*, 15, 51. DOI [10.1186/s13031-021-00389-y](https://doi.org/10.1186/s13031-021-00389-y).
14. Refugee Self-Reliance Initiative. SRI methodology. [https://www.refugeeselfreliance.org/sri](https://www.refugeeselfreliance.org/sri).

**Project-internal references**

15. `04_scripts/00_setup/01_functions/indicator_constructors.R` — the construct_*() library.
16. `04_scripts/07_construct/01_indicators_bl.R`, `02_indicators_ml.R` — driver scripts for the indicator layer.
17. `04_scripts/07_construct/05_rsi_index_bl.R`, `06_rsi_index_ml.R`, `07_rsi_methodology.qmd` — RSI implementation + deep-dive.
18. `04_scripts/07_construct/08_tango_bl.R`, `09_tango_ml.R`, `10_tango_methodology.qmd` — TANGO implementation + deep-dive.
19. `04_scripts/07_construct/03_indicators_diagnostics.qmd` — indicator inventory diagnostic.
20. `08_ai_management/02_quality_reports/decision_log.md` — methodology decisions.
21. `08_ai_management/04_knowledge_base/methodology_prepost_weights.md` — downstream pre/post analysis on the panel.

---

## Appendix A. Glossary

| Term | Definition |
|---|---|
| **ARC-D** | Adapted Resilience for Community Development — community-level resilience survey instrument complementing the household survey. |
| **BAE** | Budget Allocation Exercise — a participatory weighting performed during BRCiS programme design to derive the RSI sub-index weights (0.32 S1, 0.38 S2, 0.30 S3). |
| **CARI** | Consolidated Approach for Reporting Indicators of Food Security (WFP). |
| **CSI / rCSI** | (reduced) Coping Strategies Index. |
| **FA** | Factor Analysis. The TANGO methodology uses 1-factor maximum-likelihood factor analysis on polychoric correlation matrices. |
| **FCS** | Food Consumption Score (WFP). |
| **FIES** | Food Insecurity Experience Scale (FAO). |
| **FSIN** | Food Security Information Network — collaborative platform housed at WFP. |
| **HDDS** | Household Dietary Diversity Score (FANTA / FAO). |
| **ICW** | Inverse Covariance Weighted (Anderson 2008) — the summary-index estimator used for RSI. |
| **kNN** | k-Nearest Neighbours — imputation technique used for missing data in RSI and TANGO. |
| **LCS** | Livelihood Coping Strategies (WFP / FEWS NET). |
| **LOCF** | Last Observation Carried Forward — imputation technique used for `access_insurance` in TANGO ML projection. |
| **Polychoric correlation** | Correlation between two ordinal variables under the assumption that each is a discretisation of an underlying continuous normal variable. Computed via `polycor::hetcor()`. |
| **RSI** | Resilience Spectrum Index — BRCiS-specific ICW-weighted composite over three sub-indices (Leadership, Ecosystem, Market). |
| **SRI** | Self-Reliance Index (Refugee Self-Reliance Initiative). |
| **TANGO** | (1) Resilience Capacity Index — three-capacity (Absorptive / Adaptive / Transformative) factor-analytic composite. (2) TANGO International — the Tucson-based research and evaluation firm that authored the methodology. |
| **VAM** | Vulnerability Analysis and Mapping — WFP branch responsible for food security analytics; publishes the FCS and related guidance. |

---

## Appendix B. The `construct_*()` function library

Brief catalogue of the 14 functions in `04_scripts/00_setup/01_functions/indicator_constructors.R`. Full headers + parameter descriptions in the source file.

| Function | Builds | Key inputs | BL/ML availability |
|---|---|---|---|
| `construct_household_composition()` | Sex ratios, dependency ratios, head-of-HH characteristics | `member_*`, `hh_sex`, `age` | Both |
| `construct_fies()` | FIES (0–8), 4-cat factor, `fies_mod_sev` binary | `fies1`–`fies8` | Both |
| `construct_fcs_logframe()` | FCS, FCS thresholds, LogFrame food-security indicators | `food1`–`food8` (frequency); food-group weights | Both |
| `construct_lcs()` | rCSI, LCS stress/crisis/emergency, LCS max severity | `csi1`–`csi5`, `lcs*` | rCSI BL only; LCS both |
| `construct_water_access()` | Water access (improved/safe), `water_productive_use_normal_year` (farmer-gated) | `water1`–`water10`, `farmer` | Both |
| `construct_wash()` | WASH composite (water + sanitation + hygiene) | `water_*`, `sanitation_*`, `hygiene_*` | Both |
| `construct_financial_access()` | `access_savings`, `access_remittances`, `access_insurance` (BL only), `access_hum_assist` | `fin_*` | `access_insurance` BL only |
| `construct_group_participation()` | `group_*` participation indicators, `coll_action_num` | `gp_*`, `group_*` | Both |
| `construct_aspirations()` | `asp_*` and `asp_conf_adapt_index` | `asp1`–`asp_k` | Both |
| `construct_sri()` | Self-Reliance Index composite (12-domain adapted to Somalia) | `sri_*` domain items | Both |
| `construct_income()` | Income composites, `total_inc_increased/decreased` (renamed per round) | `inc_*`, `income_change` | Both (with renaming) |
| `construct_social_capital()` | `{bonding, bridging, linking}_social_capital`, plus 6 gender-disaggregated variants | `sc_*`, `hh_sex` | Both |
| `construct_tango_components()` | TANGO sub-component variables (avail_inf_safety, exposure_information, etc.) | Various raw + ARC-D | Both |
| `construct_logframe_kpis()` | KPI 4 + LogFrame composite indicators | All of the above | Both |

Two utility helpers also live in the library:

- `check_required(data, required_vars, indicator_name)` — guard that returns silently if required vars exist, logs and returns `FALSE` otherwise.
- `log_construction(indicator, status, details)` — append a row to the shared `CONSTRUCTION_LOG` list for the post-run audit.

---

## Appendix C. Quick decision tree

```
Q: I need to add a new indicator. Where does it go?
   - If it's a generic composite (used across projects) → add to indicator_constructors.R as construct_*()
   - If it's BRCiS-specific (one-shot) → add inline to 01_indicators_bl.R / 02_indicators_ml.R section that matches the topic
   - If it's a RSI / TANGO component → add to the variable list in 05_rsi_index_bl.R / 08_tango_bl.R AND make sure it's
     constructed upstream in 01/02_indicators_*.R

Q: A variable is structurally NA at one round. What do I do?
   - If it's a generic indicator → mark presence = bl_only or ml_only in the harmonization map; do NOT create an all-NA column.
   - If it's a TANGO / RSI input → either drop it from the variable list (RSI does this for access_insurance, female_eco_decision)
     OR inject LOCF if dropping would break the factor structure (TANGO does this for access_insurance).

Q: A variable has the same name at BL and ML but means something different. What do I do?
   - Different parent question → rename so the divergence is visible (e.g., total_inc_* → inc_*_12mo / inc_*_vs_prebrcis).
   - Same conceptual construct but different machinery → keep the name, flag comparable = no in the map.

Q: A variable is only meaningful for a subgroup. How do I report it?
   - Set non-subgroup HHs to NA in the constructor.
   - Downstream report uses svymean(..., na.rm = TRUE) — gives correct subpopulation mean + SE automatically.
   - The n_bl / n_ml / n_paired columns in the report surface the subgroup conditioning explicitly.

Q: I want to change a RSI / TANGO variable list. What is the impact?
   - You break BL→ML comparability for that index until BOTH the BL and ML scripts are re-run.
   - Order: re-run 05_rsi_index_bl.R (or 08_tango_bl.R) first to refresh bl_artifacts.rds.
   - Then re-run 06_rsi_index_ml.R (or 09_tango_ml.R) — its variable-list assertion will catch a mismatch.
   - Then re-run 01_build_panel_dataset.R to refresh the panel.
   - Then re-render any report that has been rendered against the old data.
```
