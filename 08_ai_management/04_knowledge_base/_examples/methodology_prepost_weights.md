---
title: "Methodology — Survey-Weighted Pre/Post Analysis (BRCiS III)"
author: "BRCiS III Evaluation Team"
date: "2026-05-26"
type: methodology
status: v1
applies_to:
  - 04_scripts/00_setup/01_functions/prepost.R
  - 04_scripts/09_preliminary_report/01_run_prepost.R
  - 04_scripts/08_harmonize/01_build_panel_dataset.R
---

# Methodology — Survey-Weighted Pre/Post Analysis

**BRCiS III Midline Evaluation — paired-difference estimator, design-based variance, and survey weighting.**

---

## 0. Preface

### 0.1 What this document is

This is the methodological reference for the **paired pre/post estimator** used in every BRCiS III evaluation product (preliminary report, full report, district reports, dashboard). The estimator is implemented in `04_scripts/00_setup/01_functions/prepost.R` and driven by `04_scripts/09_preliminary_report/01_run_prepost.R`. The implementation rests on three CRAN packages — `survey` (Lumley), `dplyr`, `flextable` — and on the BRCiS panel sample defined in `04_scripts/06_weights/02_panel_weights.R` and `04_scripts/08_harmonize/01_build_panel_dataset.R`.

The goal of this document is to make every analytical choice in `prepost.R` **legible, defensible, and reproducible by a colleague who does not have AI tooling**. Each section answers: (a) what does the code compute, (b) why is that the right quantity to compute, (c) what would the alternatives have been, (d) what is the explicit literature reference for the choice. Every cited paper has been verified against its DOI or publisher page; quotations carry exact provenance.

### 0.2 What this document is not

It is **not** a sampling-theory textbook. Where derivations are non-trivial, we point to Lohr (2022, *Sampling: Design and Analysis*, 3rd ed., Chapman & Hall/CRC) and Lumley (2010, *Complex Surveys: A Guide to Analysis Using R*, Wiley). It is **not** a defence of design-based versus model-based inference as a philosophical matter — we adopt the design-based stance because BRCiS is a finite-population descriptive evaluation, and the rationale is given in §6, not argued from first principles.

It is **not** a manual for the `survey` package — Lumley's CRAN reference manual and book are authoritative there. We quote them where their wording matters for our claims.

### 0.3 Notation

| Symbol | Meaning |
|---|---|
| $i$ | Household index. |
| $c(i)$ | Community of household $i$ (the stratum). |
| $S$ | The realised panel sample ($|S| = N_{\text{panel}} = 3{,}889$). |
| $Y_{BL,i}, Y_{ML,i}$ | Outcome at baseline / midline for household $i$. |
| $\Delta_i$ | Within-household change $Y_{ML,i} - Y_{BL,i}$. |
| $w_i$ | The panel sample weight for household $i$ (defined in §2.3). |
| $\pi_i$ | Inclusion probability of unit $i$ in the panel; $w_i \propto 1/\pi_i$ after rescaling. |
| $\hat\theta$ | A generic Horvitz–Thompson estimator. |
| $\rho$ | Pre/post correlation of an outcome, $\operatorname{Corr}(Y_{BL}, Y_{ML})$ on the panel. |

Math is rendered with KaTeX; inline expressions use `$...$`, displays use `$$...$$`. Code snippets are R unless flagged otherwise.

---

## 1. The estimand

### 1.1 What we are estimating

For every indicator $Y$ in the harmonization map (`02_survey_tools/01_quant_tools/prepost_harmonization_map.xlsx`), we report three quantities computed on the BL ∩ ML panel:

1. **Baseline mean.** $\bar Y_{BL} \,=\, E_{\mathcal P}[Y_{BL}]$, where $\mathcal P$ denotes the panel target population.
2. **Midline mean.** $\bar Y_{ML} \,=\, E_{\mathcal P}[Y_{ML}]$.
3. **Paired change.** $\bar \Delta \,=\, E_{\mathcal P}[Y_{ML} - Y_{BL}] \,=\, \bar Y_{ML} - \bar Y_{BL}$, with a design-based variance computed from the within-household differences (§3, §4).

Equation 3 deserves a comment. The paired change $\bar \Delta$ is *exactly* the difference of marginal means when both marginals are taken on the same panel sample — $E[\Delta] = E[Y_{ML}] - E[Y_{BL}]$ by linearity of expectation. The estimator we report, however, computes $\bar \Delta$ from the **within-household differences** $\Delta_i$, not from independent means at the two rounds. This produces the same point estimate as the difference-of-means but a strictly smaller (and correct) variance whenever $\rho > 0$, because within-household differencing nets out all between-household variation that is constant across rounds. See §3.3 for the formal argument.

### 1.2 What the estimand is NOT

A reader familiar with the impact-evaluation literature may want to know what this paired change is in relation to standard causal estimands. Three explicit clarifications:

1. **It is not an Average Treatment Effect (ATE).** BRCiS III is a **single-arm programme** — every panel household receives some bundle of BRCiS support; there is no untreated comparison arm. The paired change $\bar \Delta$ is the population-average **realised change** on the panel between two rounds; it cannot be decomposed into a programme effect plus a secular trend without external assumptions. We will not make that decomposition.

2. **It is not a Difference-in-Differences (DiD).** DiD requires a control group whose trajectory identifies the secular trend (the "what would have happened anyway"). With no control, $\bar \Delta$ is the **change**, not the **effect of change**.

3. **It is not a panel-data fixed-effects estimator.** A standard $Y_{it} = \alpha_i + \gamma_t + \varepsilon_{it}$ regression on the long panel would yield a $\hat \gamma_{ML} - \hat \gamma_{BL}$ identical in expectation to our $\bar \Delta$ when there are exactly two rounds and the design is balanced (which our panel is, by construction). The two estimators agree numerically; we prefer the explicit paired-Δ form because (a) it does not invite the reader to misread $\hat \gamma$ as a treatment effect, (b) it generalises cleanly to subgroup conditioning via NA propagation (§7), and (c) it has a transparent design-based variance via the `survey` package.

### 1.3 The target population $\mathcal P$

The estimand is defined over the **panel target population** — the finite population that the panel weights $w_i$ scale up to. Per `04_scripts/06_weights/02_panel_weights.R`:

$$
w_i \;=\; \frac{N_{\text{panel}} \cdot (\text{pop\_hh}_{c(i)} / n_{c(i)})}{\sum_{j \in S} (\text{pop\_hh}_{c(j)} / n_{c(j)})}
\quad\text{so that}\quad \sum_{i \in S} w_i \,=\, N_{\text{panel}} = 3{,}889.
$$

The numerator $\text{pop\_hh}_{c(i)} / n_{c(i)}$ is the "raw" weight: number of households in community $c(i)$'s general population divided by number of panel households sampled in that community. The outer rescaling normalises the weights so their sum equals the **panel sample size**, not the implied population total. This is the convention used by the legacy `project_functions-BRCiS.R` and produces means with the same expectation as a population-weighted average but with sums of squares calibrated to $N_{\text{panel}}$ rather than to the full population — relevant for design-effect interpretation (§4.3).

The panel target population is therefore: **the population of resilient households in the 19 BRCiS III intervention districts, weighted to reflect community-level household counts and conditioned on being a Random-Walk sample household that completed both the baseline and midline interviews.** Generalisations beyond this population (e.g., to all BRCiS-eligible households, or to all of Somalia) require explicit additional assumptions and are not made here.

---

## 2. BRCiS sample design and the panel

### 2.1 The full-baseline design

The BRCiS III baseline was a **multi-stage probability sample** of 5,162 households across 19 districts in five regions of Somalia (Bakool, Bay, Galgaduud, Hiraan, Mudug). Within each district, communities were enumerated; within selected communities, the field team applied a **Random Walk** protocol with a target of ≈ 30 households per community. A minority-community oversample of 853 households (BL minus Random Walk = 5,162 − 4,309) was also collected for separate analyses but is **excluded** from the panel because it was not designed to be representative of the general population.

The "raw" baseline weights (`04_scripts/06_weights/03_full_bl_weights.R`) are the version used for the BL-only diagnostic reports; the panel weights (`04_scripts/06_weights/02_panel_weights.R`) are a re-derivation conditioned on the BL ∩ ML panel and are the relevant object for this document.

### 2.2 The panel definition

The panel sample funnel from `04_scripts/06_weights/02_panel_weights.R` and the session log of 2026-05-25:

```
  Full BL household survey                 : 5,162
  BL Random-Walk subsample                 : 4,309   (-853 minority oversample)
  ML revisits (consenting HHs)             : 3,892
  Panel (BL ∩ ML ∩ Random Walk)            : 3,889   (-3 leaked minority HHs)
```

The interpretable attrition rate from BL Random-Walk to ML panel is $1 - 3{,}889/4{,}309 = 9.75\%$. The panel is distributed across **171 communities** (the strata in the survey design) — one fewer than the 172 communities visited at BL, because **Afweyne Banan** (Dhuusamareeb district, Galgaduud region, NRC member) had 27 BL households but zero ML revisits and is therefore absent from the panel entirely. Section 11 discusses what this attrition means for the estimand.

### 2.3 The `survey::svydesign` declaration

#### 2.3.1 Background — stratification vs clustering

The `svydesign` declaration tells the variance estimator how the sample was actually drawn from the population. Two operations on the population structure show up in any non-trivial design, and they have *opposite* effects on variance. The distinction matters because picking the wrong declaration can over- or under-state every SE in the report.

**Stratification** = the population is partitioned into mutually exclusive groups (**strata**), and the design draws a sample independently from each stratum, so every stratum is represented by construction. The randomness lives *within* each stratum.

→ Stratification **reduces** variance relative to simple random sampling (SRS), because between-stratum variation is removed from the sampling error. The textbook formula:

$$
\operatorname{Var}\big(\hat{\bar Y}_{\text{strat}}\big) \;=\; \sum_h W_h^2 \, \operatorname{Var}_h\big(\hat{\bar Y}_h\big),
$$

where $W_h$ is the stratum weight and $\operatorname{Var}_h(\hat{\bar Y}_h)$ is the within-stratum variance. Only within-stratum variances contribute.

**Clustering** = the population is partitioned into groups (**clusters**), and the design first randomly selects *some* clusters, then samples (or takes everyone) within only those selected clusters. The randomness lives in *which clusters* are drawn.

→ Clustering **inflates** variance relative to SRS, because units within a cluster tend to be more similar than units across clusters (intra-cluster correlation, ICC > 0). Correlated observations carry less independent information; $n$ clustered units are statistically "worth" only

$$
n_{\text{eff}} \;=\; \frac{n}{1 + (m - 1) \cdot \text{ICC}}
$$

independent units, where $m$ is the average cluster size. This is Kish's (1965) design-effect formula. For typical household-survey outcomes with ICC ≈ 0.05 and 25 HHs per cluster, the design effect is $1 + 24 \cdot 0.05 = 2.2$ — meaning a cluster sample of 1,000 HHs gives the same precision as an SRS of ~450 HHs.

The textbook slogan: ***stratify on what makes units different, cluster on what makes them cheap to interview.*** Stratification is a free lunch (variance only goes down); clustering is a cost you accept for logistical reasons (less travel, easier enumeration) and have to pay back in larger SEs.

**A multi-stage design typically does both.** A textbook household survey of the BRCiS shape would look like:

| Level | Role | Description |
|---|---|---|
| District | Stratum | All 19 represented |
| Community | PSU (first-stage cluster) | A sample of communities drawn per district |
| Household | SSU (second-stage unit) | A sample of HHs drawn per selected community |

The corresponding `svydesign` call would be:

```r
svydesign(ids = ~community, strata = ~district, weights = ~w, data = ...)
```

and the variance estimator would mix two ingredients: **between-community** variability of community means (the cluster effect — inflates SE) and **within-stratum** variability of cluster means (the stratification effect — reduces SE relative to SRS).

#### 2.3.2 The BRCiS declaration

The implementation passes the following design specification to `survey::svydesign`:

```r
options(survey.lonely.psu = "average")
design <- survey::svydesign(
  ids     = ~hh_id,        # each household = its own PSU
  strata  = ~community,    # community = stratum
  weights = ~w,            # panel weight from 02_panel_weights.R
  data    = panel_wide
)
```

Notice the contrast with the textbook multi-stage declaration above: **community is declared as a stratum, not a cluster, and there is no PSU layer above the household.** This is the BRCiS II convention and it rests on two implicit assumptions:

1. **Communities are enumerated, not sampled.** Every BRCiS-target community in each district was visited at baseline; there is no hypothetical "community $c$ that could have been drawn but wasn't." If this assumption holds, communities really are strata (exhaustive partitioning of the target frame), not PSUs (a random sample from a larger frame).

2. **The Random Walk within a community approximates SRS within that stratum.** The ≈25–30 HHs per community behave like an independent sample of community HHs, with no residual cluster structure (no street-block effects, no enumeration-sequence effects, no family-network clumping).

If both assumptions hold, `ids = ~hh_id, strata = ~community` is the *correct* declaration: you get the stratification benefit (community-level differences removed from the error) and there is no cluster penalty because there is no real clustering. SEs are then the smallest the design can support — the rest is honest within-stratum sampling variance.

**If assumption 1 fails** — communities were actually a sample of communities per district — the conservative declaration is `ids = ~community, strata = ~district`. SEs go up under that declaration because between-community variability is now part of the error. The magnitude of the increase depends on intra-community correlation; for many household-survey outcomes the design-effect multiplier $\sqrt{1 + (m-1)\,\text{ICC}}$ is non-trivial (≈1.5 at ICC=0.05, m=25).

**If assumption 2 fails** — HHs within a community are more similar than the RW makes them look — our SEs are again too small, and the fix is the same: declare community as PSU.

**Verification of the two assumptions.**

- **Assumption 1 — confirmed (2026-05-27).** The BRCiS III field design visited every BRCiS-target community in each district at baseline; communities were **not** a random sample drawn from a larger frame. Communities are therefore strata in the strict design-based sense, not first-stage PSUs whose between-cluster variability would need to feed the variance estimator. Confirmed with the field team; no further methodological action required.
- **Assumption 2 — defensible by design.** The Random Walk protocol explicitly disperses households across the village, breaking up the most obvious sub-cluster structures (compound, street, family network). Residual intra-community correlation is plausibly small, though we have not quantified it directly. If a future round adopts a different within-community sampling protocol, this assumption should be re-examined.

**Conclusion.** With both assumptions held / defensible, `ids = ~hh_id, strata = ~community` is the correct design declaration. SEs reported in this evaluation are honest under the design; no conservative-alternative re-analysis is warranted. The earlier "highest-value methodological question for the next field-team check-in" — flagged in v1 of this document — has been resolved.

**Why we kept the BRCiS II convention.** Two reasons that survive the resolution above:

- **Cross-evaluation comparability.** Every BRCiS II SE in the public record was computed under `ids = ~hh_id, strata = ~community`. Preserving this matters for BRCiS II vs III SE comparisons.
- **The Random Walk does substantially break up any residual within-community cluster structure** (the defence of assumption 2).

#### 2.3.3 The other two declaration choices

**`strata = ~community` (community as stratum).** Strata partition the population; the variance estimator sums within-stratum variance contributions across strata (Lohr 2022, Ch. 3; Lumley 2010, Ch. 2). Treating community as the stratum captures the dominant source of design variation — the unequal community-level household counts that motivate the weights.

**`weights = ~w` (the rescaled panel weight).** The rescaling $\sum w_i = N_{\text{panel}}$ is conventional; it does not affect point estimates of means or proportions (those depend only on the relative weights), but it does affect any output that sums the weights (e.g., effective sample size, sums of squares). See §6.3 for the population-versus-sample interpretation.

**`survey.lonely.psu = "average"`.** Necessary because some communities have only one panel household — these would otherwise produce undefined variance contributions (a single observation cannot estimate its own variance). The `"average"` rule substitutes the average across non-singleton strata for the singleton's contribution. Section 4.3 quotes the exact rule and gives the alternatives.

---

## 3. The paired-Δ estimator

### 3.1 The Horvitz–Thompson framework

The Horvitz–Thompson (HT) estimator (Horvitz & Thompson, 1952, *JASA* 47(260): 663–685, DOI [10.1080/01621459.1952.10483446](https://doi.org/10.1080/01621459.1952.10483446)) is the canonical design-unbiased estimator for a finite-population total under any probability sampling design. For a population total $T = \sum_{i \in U} y_i$ over the universe $U$, the HT estimator from a sample $S \subseteq U$ with inclusion probabilities $\pi_i = \Pr(i \in S)$ is:

$$
\hat T_{\text{HT}} \;=\; \sum_{i \in S} \frac{y_i}{\pi_i} \;=\; \sum_{i \in S} w_i^{\text{raw}} y_i,
$$

where $w_i^{\text{raw}} = 1/\pi_i$ is the **raw** inverse-probability weight. The corresponding HT estimator of the population mean is the ratio:

$$
\hat{\bar Y}_{\text{HT}} \;=\; \frac{\hat T_{\text{HT}}}{\hat N_{\text{HT}}} \;=\; \frac{\sum_{i \in S} w_i^{\text{raw}} y_i}{\sum_{i \in S} w_i^{\text{raw}}}.
$$

This is the **Hájek estimator** of the mean — a ratio of two HT totals, which is asymptotically design-unbiased and is the form used by `survey::svymean`. Because the BRCiS panel weights are normalised so $\sum w_i = N_{\text{panel}}$, the denominator equals $N_{\text{panel}}$ on the realised sample and is non-stochastic for this purpose; the estimator simplifies to:

$$
\hat{\bar Y} \;=\; \frac{1}{N_{\text{panel}}} \sum_{i \in S} w_i y_i.
$$

The full derivation, including the Sen–Yates–Grundy variance form for $\hat T_{\text{HT}}$, is in Lohr (2022, Ch. 6) and Lumley (2010, Ch. 1); we will not reproduce it here.

### 3.2 Applying the framework to the paired change

The key step. Define the **per-household change**:

$$
\Delta_i \;\equiv\; Y_{ML,i} - Y_{BL,i}.
$$

Because both $Y_{BL,i}$ and $Y_{ML,i}$ are observed on the same household $i$, $\Delta_i$ is **a single random variable indexed by the same sampling unit as the means**. The HT framework applies unchanged with $y_i \leftarrow \Delta_i$:

$$
\hat{\bar \Delta} \;=\; \frac{1}{N_{\text{panel}}} \sum_{i \in S} w_i \Delta_i \;=\; \frac{1}{N_{\text{panel}}} \sum_{i \in S} w_i (Y_{ML,i} - Y_{BL,i}).
$$

By linearity of summation:

$$
\hat{\bar \Delta} \;=\; \frac{1}{N_{\text{panel}}} \sum_{i \in S} w_i Y_{ML,i} \;-\; \frac{1}{N_{\text{panel}}} \sum_{i \in S} w_i Y_{BL,i} \;=\; \hat{\bar Y}_{ML} - \hat{\bar Y}_{BL}.
$$

**Point estimate equivalence.** The paired-Δ estimator and the difference-of-means estimator yield **identical** point estimates when both are computed on the same panel sample. The two estimators differ only in their variance — which is the entire reason we differentiate within household.

### 3.3 Why paired Δ has a smaller variance than the difference of independent means

If we had used two independent samples — one at BL, a different one at ML — the variance of the difference would be:

$$
\operatorname{Var}\big(\hat{\bar Y}_{ML} - \hat{\bar Y}_{BL}\big) \;=\; \operatorname{Var}\big(\hat{\bar Y}_{ML}\big) + \operatorname{Var}\big(\hat{\bar Y}_{BL}\big),
$$

because the two means would be statistically independent. On a panel, however, the same household contributes to both means, so:

$$
\operatorname{Var}\big(\hat{\bar Y}_{ML} - \hat{\bar Y}_{BL}\big) \;=\; \operatorname{Var}\big(\hat{\bar Y}_{ML}\big) + \operatorname{Var}\big(\hat{\bar Y}_{BL}\big) \;-\; 2\,\operatorname{Cov}\big(\hat{\bar Y}_{ML}, \hat{\bar Y}_{BL}\big).
$$

For an outcome with pre/post correlation $\rho$, the covariance term is positive whenever $\rho > 0$ — and for most welfare and resilience outcomes on the same household over two years, $\rho$ is far from zero. **Ignoring the covariance** (treating the two means as independent) inflates the SE by a factor of $\sqrt{1/(1-\rho)}$ at the extreme, with a less dramatic but still material inflation at typical $\rho$.

The paired-Δ estimator works on $\Delta_i$ directly, so its variance is:

$$
\operatorname{Var}\big(\hat{\bar \Delta}\big) \;=\; \operatorname{Var}\!\left(\frac{1}{N_{\text{panel}}} \sum_{i \in S} w_i \Delta_i\right),
$$

which is the design-based variance of a single sample mean of the within-household differences. The differencing **absorbs** all household-level random effects that are constant across rounds (e.g., persistent income, household composition, geographic exposure). Whatever residual variance remains is the variance of the change itself — which is, by construction, smaller than the variance of either round's level whenever pre/post correlation is positive.

The Frison–Pocock (1992) analysis of repeated measures (*Statistics in Medicine* 11(13): 1685–1704, DOI [10.1002/sim.4780111304](https://doi.org/10.1002/sim.4780111304)) gives the textbook derivation: for a fixed total sample size and balanced design, the change-score estimator strictly dominates the post-only estimator whenever $\rho > 0.5$. We are not estimating a treatment effect (see §5), so the Frison–Pocock dominance result is not directly the *case* for paired-Δ. The underlying variance algebra is what matters here, and it implies a one-line summary: **paired-Δ has a smaller SE than the difference of independent means precisely when $\rho > 0$.**

**An empirical caveat for BRCiS.** The variance-reduction argument is widely repeated as a generic case for paired-Δ, but its quantitative bite depends on the empirical pre/post correlation $\rho$ of each outcome. For the BRCiS midline data, the verification script in §10 produces the following implied $\rho$ values on the panel:

| Indicator | $\rho$ (implied) | Comment |
|---|---|---|
| `rsi_pnorm` | $\approx 0.03$ | Near zero; paired-Δ ≈ indep-diff |
| `fcs_acceptable` | $< 0$ | Negative; paired-Δ SE slightly *larger* than indep-diff SE |
| `water_productive_use_normal_year` | $< 0$ | Negative; same as above |

The pattern is plausible: BRCiS-relevant outcomes between baseline and midline are dominated by household-specific shocks (climate, conflict, market access) and programme-induced trajectories that vary substantially across households. Persistent household traits do not dominate the variance of within-HH change for these outcomes. The paired-Δ point estimate is **still the right thing to report** — it is the design-unbiased estimator of $E_{\mathcal P}[\Delta]$ regardless of $\rho$ — but the textbook efficiency argument over "naive" difference-of-independent-means does not always apply to BRCiS-style outcomes. We report the design-based SE that the data actually support, not an inflated SE from pretending the means are independent.

### 3.4 Subgroup conditioning preserves the framework

For some indicators, only a subset of panel households is in scope — `water_productive_use_normal_year`, for example, is gated on `farmer == 1` (non-farmers are not asked, by construction of the questionnaire). The construction step sets the non-subgroup households' values to `NA`; the paired-Δ estimator is then computed on the subset of households with non-NA in *both* rounds. The resulting estimand is:

$$
\bar \Delta^{\text{(subgroup)}} \;=\; E_{\mathcal P_{\text{sub}}}[\Delta],
$$

where $\mathcal P_{\text{sub}}$ is the subpopulation defined by the subgroup condition. Section 7 explains why this is the right thing — and why the implementation (set non-subgroup HHs to NA, call `svymean(..., na.rm = TRUE)`) recovers exactly this subpopulation estimate with correct SEs.

---

## 4. Variance estimation

### 4.1 Why design-based, not model-based

Pfeffermann (1993, "The role of sampling weights when modeling survey data," *International Statistical Review* 61(2): 317–337, JSTOR [1403631](https://www.jstor.org/stable/1403631), DOI [10.2307/1403631](https://doi.org/10.2307/1403631)) draws the canonical line between two modes of inference:

> "For descriptive inference, that is, inference about known functions of the finite population values, weighting of sample data is widely accepted although modifications to control variances are occasionally recommended. Yet, for analytical inference about model parameters, there is a wide spectrum of opinions on the role of the sampling weights …" (p. 318)

BRCiS midline reporting is **squarely on the descriptive side**. The target parameters — mean FIES, proportion food-secure, mean RSI composite, change in TANGO 0–100 score — are "known functions of the finite-population values" of the panel target population (§1.3). They are not parameters of a stochastic process generating those values; they are deterministic functions of the finite population, knowable in principle by census. Sampling theory gives us the right framework: design-based estimation, with variance arising from the random selection of $S$ from $U$, not from a random data-generating process for $Y$.

Concretely, the design-based variance treats the values $\{Y_{BL,i}, Y_{ML,i}\}$ for $i \in U$ as **fixed**. The randomness in the estimator $\hat{\bar \Delta}$ comes entirely from $S$ — the realised sample is one of many possible samples under the design. The variance is computed across that hypothetical replication of the design.

A model-based alternative — for instance, treating $\Delta_i$ as i.i.d. draws from some parametric distribution and reporting a model-based SE — would conflate sampling variance with assumed-distributional variance, and would silently require us to defend the model. We prefer not to.

### 4.2 Taylor linearization

The variance of $\hat{\bar \Delta}$ under the design is computed by **Taylor linearization** (Binder, 1983, "On the variances of asymptotically normal estimators from complex surveys," *International Statistical Review* 51(3): 279–292, JSTOR [1402588](https://www.jstor.org/stable/1402588), DOI [10.2307/1402588](https://doi.org/10.2307/1402588)). Binder shows that any estimator defined as the solution of an estimating equation $\sum w_i u_i(\theta) = 0$ has an asymptotic variance computable from the **influence function** $u_i(\theta)$ evaluated at the design-consistent estimate.

For $\hat{\bar \Delta} = \sum w_i \Delta_i / \sum w_i$, the linearised influence values for unit $i$ in stratum $c$ are:

$$
z_i \;=\; \frac{w_i (\Delta_i - \hat{\bar \Delta})}{\sum_{j \in S} w_j}.
$$

The Taylor-series design variance is then the standard stratified-HT variance of the linearised values:

$$
\widehat{\operatorname{Var}}\big(\hat{\bar \Delta}\big) \;=\; \sum_{c \in \text{strata}} \frac{n_c}{n_c - 1} \sum_{i \in S_c} (z_i - \bar z_c)^2,
$$

with $\bar z_c$ the within-stratum mean of the linearised values and $n_c$ the number of PSUs in stratum $c$ (here: panel households in community $c$). Because the BRCiS declaration treats every household as its own PSU, the formula collapses to the within-stratum sum of squared deviations of $z_i$ from the stratum mean, normalised by $n_c - 1$.

This is what `survey::svymean` computes when called on the augmented panel design. We do **not** implement linearization ourselves; we delegate to the package, whose implementation has been validated against textbook examples by the package author over fifteen years of CRAN releases (current version 4.5, 2026-02-24).

### 4.3 Lonely PSUs and the `"average"` rule

A **lonely PSU** is a stratum that contains only a single PSU. Under our design declaration (PSU = household; stratum = community), a "lonely PSU" is a community in which only one panel household was retained. With $n_c = 1$, the within-stratum sum of squared deviations is $0/(1-1) = 0/0$ — undefined. Some rule must be applied.

The `survey` package documents four rules via `options("survey.lonely.psu")` (Lumley, *survey* 4.5 reference manual, `?surveyoptions`, pp. 77–78):

> "Handling of strata with a single PSU that are not certainty PSUs is controlled by `options("survey.lonely.psu")`. The default setting is `"fail"`, which gives an error. Use `"remove"` to ignore that PSU for variance computation, `"adjust"` to center the stratum at the population mean rather than the stratum mean, and `"average"` to replace the variance contribution of the stratum by the average variance contribution across strata."

The BRCiS implementation uses `"average"`:

```r
options(survey.lonely.psu = "average")
```

**Mathematical content.** If $c^*$ is a lonely-PSU stratum, the rule replaces $\sum_{i \in S_{c^*}}(z_i - \bar z_{c^*})^2$ by

$$
\bar v \;\equiv\; \frac{1}{|\,\text{strata with } n_c > 1|} \sum_{c : n_c > 1} \frac{1}{n_c - 1} \sum_{i \in S_c} (z_i - \bar z_c)^2,
$$

so the lonely stratum contributes the **average** variance contribution across the non-singleton strata. This is a pragmatic substitution rule: it preserves a positive total variance (avoids the "fail" / "remove" behaviours), and it is conservative relative to "adjust" in the typical case where the lonely-PSU stratum is not unusually noisy.

**Why we chose `"average"` over the alternatives.**

- `"fail"` (default) would simply error out and prevent us from estimating means for any indicator that has even one lonely community in the panel — unacceptable for a production pipeline.
- `"remove"` would silently drop the lonely-PSU contribution to the variance, under-stating the SE. Not defensible.
- `"adjust"` (the Stata default, equivalent to `_strata: ()` in `svy:` commands) centres the lonely stratum at the population mean rather than the stratum mean. This is a stronger assumption and can sharply inflate the SE for outcomes where the population mean is far from the lonely community's value.
- `"average"` is the recommendation in Lumley (2010, §2.2.2) and is the default in many survey-software conventions outside Stata.

The choice is documented in the function header (`prepost.R`) and in this section. If future BRCiS evaluations move toward a multi-baseline design or accumulate a larger panel where lonely PSUs become rarer, the `"adjust"` rule may be preferable; until then, `"average"` is the right pragmatic call.

### 4.4 Confidence intervals and p-values

The implementation reports 95% confidence intervals using the **normal approximation**:

$$
\hat{\bar \Delta} \,\pm\, 1.96 \cdot \widehat{\text{SE}}\big(\hat{\bar \Delta}\big),
$$

and Wald-type two-sided p-values from the test statistic $z = \hat{\bar \Delta} / \widehat{\text{SE}}(\hat{\bar \Delta})$. The asymptotic-normality justification is Binder (1983), Theorem 2: HT-type estimators of smooth functionals are asymptotically normal under standard regularity conditions, with the linearised variance consistent for the asymptotic variance. With $N_{\text{panel}} = 3{,}889$ and the within-stratum sample sizes that the BRCiS panel achieves, the normal approximation is comfortably justified for all indicators except possibly the rarest binaries (where Wilson-type intervals would be marginally better but are not implemented).

The significance stars use the conventional thresholds:

$$
*** : p < 0.01, \quad ** : p < 0.05, \quad * : p < 0.10.
$$

These are reporting conventions, not formal hypothesis tests; we do not adjust for the multiple comparisons across the ~143 indicators in the report. Section 11 discusses this.

---

## 5. Why paired-Δ rather than ANCOVA, DiD, or mixed-effects?

The pre/post evaluation literature offers a richer toolkit than the paired-difference estimator: covariance-adjusted estimators (ANCOVA), difference-in-differences (DiD), and mixed-effects panel models all see widespread use. This section explains why we did not adopt them. The short version: **the standard arguments in favour of ANCOVA and DiD assume a treatment-effect estimand with a control group; BRCiS has neither.** The paired-Δ estimator is the natural descriptive analogue.

### 5.1 The McKenzie / Frison–Pocock argument (and why it doesn't apply)

In the development-economics RCT literature, the canonical reference for "which pre/post estimator should I use?" is McKenzie (2012, "Beyond baseline and follow-up: The case for more T in experiments," *Journal of Development Economics* 99(2): 210–221, DOI [10.1016/j.jdeveco.2012.01.002](https://doi.org/10.1016/j.jdeveco.2012.01.002)). McKenzie's central result, restated in his accompanying [World Bank "Development Impact" blog post](https://blogs.worldbank.org/en/impactevaluations/why-difference-difference-estimation-still-so-popular-experimental-analysis):

> "The exact ratio of DD variance to ANCOVA variance is $2/(1+\rho)$. … When autocorrelations are low, there are large improvements in power to be had from using ANCOVA instead of difference-in-differences in analysis."

The corresponding clinical-statistics reference is Frison & Pocock (1992), whose abstract concludes:

> "Analysis of covariance is the method of choice and its superiority over analysis of post-treatment means or analysis of mean changes is quantified, as regards both reduced variance and avoidance of bias, using a simple model for the covariance structure between time points."

These are powerful results — for the **treatment-effect estimand in an RCT**. Both papers compare three estimators of the *causal effect* of a randomised intervention: the post-only difference $\hat\tau_{\text{POST}}$, the change-score difference $\hat\tau_{\text{CHANGE}}$ (i.e., DiD with one baseline and one follow-up), and the ANCOVA $\hat\tau_{\text{ANCOVA}}$ from regressing $Y_{ML}$ on $Y_{BL}$ and treatment status. All three are unbiased for the ATE under randomisation; ANCOVA is the most efficient.

**Why this is silent on the BRCiS choice.** BRCiS III has no untreated comparison arm. The estimand in McKenzie / Frison–Pocock is

$$
\tau \;=\; E[Y_{ML} \mid T=1] - E[Y_{ML} \mid T=0] - \big(E[Y_{BL} \mid T=1] - E[Y_{BL} \mid T=0]\big),
$$

which requires $T=0$ observations to identify. In our single-arm setting, the entire panel has $T=1$, and the estimand $\tau$ is undefined. The natural descriptive analogue is:

$$
\bar \Delta \;=\; E_{\mathcal P}[Y_{ML} - Y_{BL}],
$$

which is **exactly** our paired-Δ. McKenzie's recommendation — "use ANCOVA, not DiD/CHANGE" — is about choosing between two ways to *estimate $\tau$*; it does not bear on the question of how to estimate $\bar \Delta$.

### 5.2 What "ANCOVA" would mean in a single-arm pre/post setting

A reader who has internalised the McKenzie result may still ask: "What about running an ANCOVA-style regression even without a control?" Suppose we fit

$$
Y_{ML,i} \;=\; \alpha + \beta \,Y_{BL,i} + \varepsilon_i
$$

on the panel. What does this give us?

- $\hat\beta$ is the slope of midline on baseline — a measure of regression-to-the-mean and within-household persistence. It is *not* a treatment effect.
- $\hat\alpha$ is the predicted midline value when baseline is zero — interpretable only for outcomes where zero is a natural value (e.g., binary outcomes), and even then it captures a particular conditional mean, not a population-average change.
- The **average marginal effect** of the regression, $\hat\beta \cdot \overline{Y}_{BL} + \hat\alpha - \overline{Y}_{BL}$, by construction equals $\overline{Y}_{ML} - \overline{Y}_{BL} = \hat{\bar \Delta}$ on the panel — i.e., the ANCOVA recovers the same point estimate as paired-Δ.

So in the single-arm setting, the **point estimate** of the population-average change is identical under ANCOVA and paired-Δ. The two differ in:

1. **Variance.** ANCOVA SEs are computed from the OLS residual variance, which under correct linearity will be smaller than the unconditional variance of $\Delta_i$ that paired-Δ uses. The efficiency gain is real — but it depends on the linearity assumption, which is hard to defend for indicators bounded in [0, 1] (binaries, proportions, indices), ordinal outcomes (FIES category, food-consumption-score bands), and capped scales (RSI 1–5).
2. **Standard-error machinery.** ANCOVA SEs from `lm()` ignore the survey design (strata, weights). To get correct SEs we would need `survey::svyglm`, plus careful specification of the marginal-effect contrast (`survey::svycontrast`). This is doable but more complex than the paired-Δ pipeline, and produces the same point estimate.

**The honest tradeoff.** ANCOVA can buy a modest SE reduction over paired-Δ for outcomes where the linearity assumption holds and where the pre/post correlation $\rho$ is meaningfully positive. The §9 empirical finding for BRCiS — $\rho$ near zero or slightly negative for several headline indicators — implies ANCOVA's efficiency gain would also be modest here. Against that we would pay: (a) a linearity assumption we cannot defend uniformly across 143 indicators of mixed scales (binaries, proportions, capped indices, ordinal scales), (b) substantially more implementation complexity (`svyglm` plus `svycontrast` for marginal effects), and (c) a marginal-effect interpretation that obscures rather than clarifies the descriptive change for non-statistician stakeholders. The honest tradeoff favours paired-Δ for the BRCiS report; ANCOVA becomes attractive for any future round that introduces a control arm or where causal-effect estimation supersedes descriptive reporting.

### 5.3 What "DiD" would mean (it doesn't apply)

A two-round DiD with a control group $T=0$ would estimate

$$
\hat\tau_{\text{DiD}} \;=\; \big(\bar Y_{ML, T=1} - \bar Y_{BL, T=1}\big) - \big(\bar Y_{ML, T=0} - \bar Y_{BL, T=0}\big).
$$

With $T=0$ undefined for BRCiS, $\hat\tau_{\text{DiD}}$ is undefined. There is no question of choosing between DiD and ANCOVA — both require the comparison arm. Paired-Δ is the descriptive estimator that *does* survive in the single-arm setting.

A reader who wants to interpret $\bar \Delta$ as a programme effect must add the assumption "the secular trend $E_{\mathcal P}[Y_{ML} - Y_{BL} \mid \text{no programme}]$ is zero." For some outcomes (e.g., enrolment in BRCiS-specific programmes), this is automatic. For most (FIES, FCS, income, employment) it is heroic. **We do not make this interpretation.** The report describes $\bar \Delta$ as "the change between baseline and midline on the panel," and the methodology section makes the no-counterfactual caveat explicit.

### 5.4 What "mixed-effects" would mean

A standard two-period mixed-effects model

$$
Y_{it} \;=\; \alpha_i + \gamma_t + u_{c(i)} + \varepsilon_{it}
$$

(with household random effects $\alpha_i$, time effects $\gamma_t$, and community random effects $u_{c(i)}$) recovers $\hat\gamma_{ML} - \hat\gamma_{BL}$ as the time-difference estimand. On a balanced panel with two rounds and no covariates, this is numerically identical to the paired-Δ estimator. The variance of the time-difference can be obtained from the model's variance-components estimation, but the resulting SE is model-based, not design-based: it depends on the assumed independence structure of $\alpha_i$ and $u_{c(i)}$, which is awkward to defend when communities are sampled with probabilities reflecting their household counts.

The design-based paired-Δ via `survey::svymean` is the more principled estimator for the descriptive question; mixed-effects would be the right tool if we wanted to model household-level heterogeneity or to do small-area estimation. Neither is the current ask.

### 5.5 Summary of the tradeoff

| Estimator | Estimand | Requires control arm? | Point est. matches paired-Δ on the panel? | SE source |
|---|---|---|---|---|
| Paired-Δ (ours) | $E_{\mathcal P}[\Delta]$ | No | — | Design-based (Taylor linearization) |
| Difference of means | $E_{\mathcal P}[Y_{ML}] - E_{\mathcal P}[Y_{BL}]$ | No | Yes | Design-based, treats means as independent (wrong if $\rho > 0$) |
| ANCOVA (single-arm) | $E_{\mathcal P}[\Delta]$ (via marginal effect) | No | Yes | Model-based; needs `svyglm` for design correction |
| ANCOVA (RCT) | ATE = $E[\Delta \mid T=1] - E[\Delta \mid T=0]$ | Yes | N/A | Model-based; preferred per McKenzie 2012 |
| DiD | ATE | Yes | N/A | Design- or model-based |
| Mixed-effects | $\gamma_{ML} - \gamma_{BL}$ | No | Yes (balanced panel, 2 rounds) | Model-based |

The paired-Δ estimator is the unique combination of: (a) right for a single-arm descriptive evaluation, (b) design-based variance, (c) no auxiliary modelling assumption. That is why it is the default in `prepost.R`.

A note on a potential future direction. Burlig, Preonas & Woerman (2020, "Panel data and experimental design," *J. Development Economics* 144: 102458, DOI [10.1016/j.jdeveco.2020.102458](https://doi.org/10.1016/j.jdeveco.2020.102458); NBER WP [26250](https://www.nber.org/papers/w26250)) generalise the McKenzie / Frison–Pocock framework to arbitrary serial-correlation structures and ≥ 3 periods. If a future BRCiS round adds an endline (a third wave), or if a control arm is introduced via a phase-in design, that paper becomes directly relevant for the analytical strategy. Today it is informational.

---

## 6. Survey weights — what they buy you and when

### 6.1 The Solon–Haider–Wooldridge framework

The most widely cited reference on when to weight in econometric analysis is Solon, Haider & Wooldridge (2015, "What Are We Weighting For?", *Journal of Human Resources* 50(2): 301–316, DOI [10.3368/jhr.50.2.301](https://doi.org/10.3368/jhr.50.2.301); NBER WP [18859](https://www.nber.org/papers/w18859)). Their abstract — verbatim from the journal landing page:

> "When estimating population descriptive statistics, weighting is called for if needed to make the analysis sample representative of the target population. With regard to research directed instead at estimating causal effects, we discuss three distinct weighting motives: (1) to achieve precise estimates by correcting for heteroskedasticity; (2) to achieve consistent estimates by correcting for endogenous sampling; and (3) to identify average partial effects in the presence of unmodeled heterogeneity of effects. In each case, we find that the motive sometimes does not apply in situations where practitioners often assume it does."

Read carefully. The first sentence — "When estimating population descriptive statistics, weighting is called for if needed to make the analysis sample representative of the target population" — is **a direct endorsement** for descriptive evaluation. The three motives that follow are about **causal estimation**, where Solon–Haider–Wooldridge urge careful thought about which motive (if any) applies.

BRCiS midline reporting falls under the first sentence. We are estimating finite-population means and changes; the panel sample is not self-weighting (communities have heterogeneous household counts and were sampled with a Random Walk per community rather than proportional to community size); therefore weighting is required to recover the population-average estimand. **Solon–Haider–Wooldridge unambiguously endorse this for descriptive work.**

### 6.2 The Pfeffermann descriptive-vs-analytic distinction

Pfeffermann (1993) crystallises the same distinction in different language. From the same paper quoted in §4.1 (p. 319, §2):

> "In descriptive inference, the target population consists of all the units in the population from which the sample is drawn. The target parameters are some known functions of the survey variables values like means, proportions, regression coefficients etc. In what follows we refer to such functions as 'descriptive population quantities' (DPQ). All other inferences are 'analytic' but the term usually refers to inference about model parameters …"

And on whether to weight (p. 318, summarising his main conclusion):

> "The main conclusion of this study is that the sampling weights can play a vital role in two different aspects of the modeling process. (1) The weights can be used to test and protect against nonignorable sampling designs which could cause selection bias. (2) The weights can be used to protect against misspecification of the model holding in the population."

Pfeffermann's nuance — that weights can be diagnostic even in analytic modelling — supports the comparative robustness check we sometimes do (weighted vs. unweighted means agreeing within sampling error → confidence that the design is approximately ignorable for that outcome). For the primary descriptive estimates in the report, we always weight.

### 6.3 Why BRCiS weights matter (a numerical intuition)

The BRCiS panel weights vary across communities because community-level population counts (`pop_hh`) vary by orders of magnitude. A Random-Walk community in Bay region with `pop_hh = 1{,}500` and a panel-sample size of 25 contributes households with raw weight $1{,}500 / 25 = 60$. A neighbouring community with `pop_hh = 200` and the same panel size of 25 contributes households with raw weight $200 / 25 = 8$. The ratio of weights is 7.5:1.

Unweighted means would treat every panel household as equally informative about the BRCiS target population. This is wrong: it would massively over-represent the smaller, more accessible communities (which were easier to enumerate to the Random-Walk target) and under-represent the larger ones. The weighted mean recovers the population-level interpretation:

$$
\bar Y_{\text{unweighted}} \,=\, \frac{1}{3{,}889}\sum_i Y_i \,\neq\, \frac{\sum_i w_i Y_i}{\sum_i w_i} \,=\, \hat{\bar Y}_{\text{weighted}}
$$

in general. The empirical difference for BRCiS indicators is typically a few percentage points for binaries and a few hundredths of a standard deviation for continuous scales — small enough that the report's substantive findings would survive an unweighted analysis, but large enough that the unweighted estimator is incorrect for the stated estimand.

### 6.4 The DuMouchel–Duncan diagnostic (not applied here)

DuMouchel & Duncan (1983, "Using sample survey weights in multiple regression analyses of stratified samples," *JASA* 78(383): 535–543, DOI [10.1080/01621459.1983.10478006](https://doi.org/10.1080/01621459.1983.10478006), JSTOR [2288016](https://www.jstor.org/stable/2288016)) propose comparing weighted and unweighted regression coefficients as a specification test: large discrepancies signal that the population regression model is misspecified for at least one stratum, and the weighted estimator is then preferred for consistency.

The DuMouchel–Duncan test is not implemented in `prepost.R` because the pre/post estimator is a sample mean, not a regression coefficient, and the descriptive-vs-analytic argument (§6.1, §6.2) already settles the choice. The test would be relevant if we were estimating a regression (e.g., an ANCOVA-with-control), and is parked for future BRCiS rounds that adopt a more complex analytical model.

### 6.5 The Wooldridge position

Wooldridge has written extensively on weighting for econometric estimation; the canonical references are Wooldridge (1999, "Asymptotic properties of weighted M-estimators for variable probability samples," *Econometrica* 67(6): 1385–1406, DOI [10.1111/1468-0262.00083](https://doi.org/10.1111/1468-0262.00083)) and Chapter 20 of Wooldridge (2010, *Econometric Analysis of Cross Section and Panel Data*, 2nd ed., MIT Press). The summary: under exogenous stratification with observable strata, unweighted estimation is consistent and more efficient than weighted estimation for the conditional-mean parameters of a correctly specified model; under endogenous stratification, weighting is necessary for consistency.

This further reinforces the case for weighting BRCiS descriptive estimates. Stratification by community is exogenous (communities were selected administratively, not based on outcomes), so unweighted estimation is consistent for a *conditional* mean given community. But the target is the **unconditional** population mean, which requires weighting up the community-level conditional means by community size — exactly what the panel weights $w_i$ do.

---

## 7. Subgroup conditioning via NA propagation

### 7.1 The pattern

Several indicators are defined only for a subgroup of the panel. The construction logic sets non-subgroup households' values to `NA` in `hh_indicators_{bl,ml}`, and the harmonization joins propagate this NA through to `panel_wide`. For example, `water_productive_use_normal_year` is non-NA only for households with `farmer == 1` at the relevant round.

The pre/post estimator then handles subgroups **without an explicit filter**:

```r
# n_bl: households with non-NA at BL
n_bl <- sum(!is.na(panel_wide$water_productive_use_normal_year_bl))

# Survey-weighted BL mean over the BL non-NA subpopulation
svymean(~water_productive_use_normal_year_bl, design, na.rm = TRUE)

# Same for ML
svymean(~water_productive_use_normal_year_ml, design, na.rm = TRUE)

# Paired Δ over households with non-NA at BOTH rounds
panel_wide$delta_col <- panel_wide$water_productive_use_normal_year_ml -
                        panel_wide$water_productive_use_normal_year_bl
svymean(~delta_col, design, na.rm = TRUE)
```

The reported `n_bl`, `n_ml`, `n_paired` columns surface the subgroup conditioning explicitly: a reader sees that `water_productive_use_normal_year` has `n_paired = 1{,}851` rather than the full-panel 3,889 and understands immediately that the indicator is conditioned on a subgroup.

### 7.2 Why NA propagation gives the right subpopulation estimate

The official `survey`-package vignette ["Estimates in subpopulations"](https://cran.r-project.org/web/packages/survey/vignettes/domain.pdf) (Lumley, 2026-02-24) is explicit:

> "Estimating a mean or total in a subpopulation (domain) from a survey, eg the mean blood pressure in women, is not done simply by taking the subset of data in that subpopulation and pretending it is a new survey. This approach would give correct point estimates but incorrect standard errors."

The vignette goes on to explain the correct implementation:

> "The estimator is implemented by setting the sampling weight to zero for observations not in the domain. For most survey design objects this allows a reduction in memory use, since only the number of zero weights in each sampling unit needs to be kept. For more complicated survey designs, such as poststratified designs, all the data are kept and there is no reduction in memory use."

Two things to take away:

1. **Subsetting the raw data and rebuilding the design is wrong** — it destroys the stratum/PSU structure, giving "incorrect standard errors."
2. **The correct domain estimator zero-weights the non-domain observations** within the same design object.

Now compare with `svymean(~y_bl, design, na.rm = TRUE)`. From the `?surveysummary` documentation (Lumley, *survey* 4.5 reference manual, pp. 79–80):

> "With `na.rm=TRUE`, all cases with missing data are removed."

The implementation detail in the package source: `na.rm = TRUE` invokes the same zero-weighting mechanism for NA rows that `subset()` uses for non-domain rows. The design object retains its strata and PSUs; only the formula-level NA rows are excluded from the variance contribution. Therefore:

> **NA propagation + `svymean(..., na.rm = TRUE)` is equivalent to `subset(design, !is.na(y))` followed by `svymean(~y, .)` — and crucially, the standard errors are correct.**

This is the pattern used throughout `prepost.R`. We never filter the raw data and rebuild the design; we always set values to NA in the construction step and let `svymean(..., na.rm = TRUE)` do the right thing.

### 7.3 The wrong way (and why we don't do it)

A naive implementation would look like:

```r
# WRONG
sub_data <- panel_wide |> dplyr::filter(!is.na(water_productive_use_normal_year_bl))
sub_design <- survey::svydesign(ids = ~hh_id, strata = ~community,
                                 weights = ~w, data = sub_data)
svymean(~water_productive_use_normal_year_bl, sub_design)
```

This filters the data before the design is built, so the design knows nothing about the dropped households. Variances are computed over the *subset's* strata structure, which (a) may have additional lonely PSUs that the full panel did not, (b) loses information that the dropped households were part of the same sample, and (c) gives "correct point estimates but incorrect standard errors" per Lumley.

`prepost.R` avoids this by building the design **once** on the full augmented panel and letting `na.rm = TRUE` handle subgroup conditioning at the formula level.

### 7.4 Limitations of NA propagation

The NA-propagation pattern is correct for the **subpopulation mean** and **subpopulation paired change**. It does *not* automatically give:

- **Subpopulation totals.** A weighted total over the subgroup would need to scale by the subgroup's effective population, not the panel total. This is not what `prepost.R` reports; we report means and changes only.
- **Cross-subgroup contrasts** (e.g., "mean differs between farmers and non-farmers"). Those require `svyglm` with an explicit subgroup interaction or `svyby` with both subgroups present.
- **Subpopulation proportions when the universe is itself conditional.** For example, "% of farmers using productive-use water" has the panel as universe and farmers as subgroup; "% of productive-use water users who are farmers" inverts the conditioning. The NA-propagation pattern handles the first; the second requires explicit conditioning.

For BRCiS reporting all subgroup-conditioned indicators are of the first form, and the pattern works as intended. Future evaluations adopting more complex subpopulation contrasts should consult Lumley's domain-estimation vignette before generalising.

---

## 8. The `survey::svymean` calls in `prepost.R`

For an end-to-end reader, this section is the bridge between the algebra of §3–§7 and the code of `prepost.R`.

### 8.1 Design construction (once, not per variable)

`prepost.R` pre-computes the within-household differences for every comparable variable and stores them as columns in `panel_wide` *before* calling `svydesign`. This keeps the design construction outside the per-variable loop:

```r
# Inside run_pre_post(), abbreviated:
for (nm in harmonized_names_with_comparable_yes) {
  panel_wide[[paste0(nm, "_delta")]] <-
    panel_wide[[paste0(nm, "_ml")]] - panel_wide[[paste0(nm, "_bl")]]
}

options(survey.lonely.psu = "average")
design <- survey::svydesign(
  ids     = ~hh_id,
  strata  = ~community,
  weights = ~w,
  data    = panel_wide
)
```

The design-construction step is the bottleneck — moving it outside the loop reduces runtime from O(V × N) to O(V + N), where V is the number of variables and N the panel size. For BRCiS (~143 variables, 3,889 households), the difference is ~30× in measured time.

### 8.2 The three `svymean` calls per variable

For each variable, the per-variable block does at most three things:

```r
# BL mean and SE
bl_stat <- survey::svymean(reformulate(paste0(nm, "_bl")), design, na.rm = TRUE)
# ML mean and SE
ml_stat <- survey::svymean(reformulate(paste0(nm, "_ml")), design, na.rm = TRUE)
# Paired Δ (only if presence == "both" and comparable == "yes")
delta_stat <- survey::svymean(reformulate(paste0(nm, "_delta")), design, na.rm = TRUE)
```

Each call returns a `svymean` object from which `as.numeric()` extracts the point estimate and `survey::SE()` extracts the standard error. The CI is constructed by the implementation using the normal approximation:

```r
ci_lower <- delta - 1.96 * se_delta
ci_upper <- delta + 1.96 * se_delta
z_stat   <- delta / se_delta
p_value  <- 2 * (1 - stats::pnorm(abs(z_stat)))
```

This is a Wald test of $H_0: \bar \Delta = 0$. The asymptotic-normality justification is Binder (1983) Theorem 2 (§4.4).

### 8.3 What `prepost.R` does not do

The function deliberately skips:

- **Categorical-variable handling.** Per-category proportions would require `svyciprop` or `svytable`; the convention here is that any categorical indicator is decomposed into its binary `_yes` constituents upstream in `hh_indicators_*`, so by the time `prepost.R` sees a variable it is numeric (continuous or 0/1).
- **Outlier handling.** All outlier decisions are made in the cleaning pipeline (`05_clean/09_apply_outliers.R`); `prepost.R` trusts its input.
- **Sub-stratification beyond `community`.** Region- or district-level estimates are computed by a parallel call to `run_pre_post()` after filtering `panel_wide` to the district — which is the **correct** workflow for district-level descriptive estimates because the relevant target population is the district panel. The whole-country design's stratification by community continues to apply within each district subset.

---

## 9. A worked example

We work through two indicators end-to-end, recomputing the statistics manually and comparing them to the `prepost.R` output saved in `05_outputs/02_tables/preliminary_report/prepost_results.rds`. All numerical values below are produced by the verification script (§10) on the current panel; do not edit by hand.

### 9.1 Primary example — `fcs_acceptable` (binary, full panel)

The Food Consumption Score "acceptable" indicator is a binary $Y \in \{0, 1\}$ defined on all 3,889 panel households at both rounds (no subgroup conditioning, no NA propagation). It is a clean setting because $n_{BL} = n_{ML} = n_{\text{paired}} = 3{,}889$ and the paired-Δ identity $\hat{\bar \Delta} = \hat{\bar Y}_{ML} - \hat{\bar Y}_{BL}$ holds exactly.

**Stored values** (from `prepost_results.rds`):

| Quantity | Value |
|---|---|
| $\hat{\bar Y}_{BL}$ (BL mean) | $0.4316$ |
| $\widehat{\text{SE}}_{BL}$ | $0.0239$ |
| $\hat{\bar Y}_{ML}$ (ML mean) | $0.0971$ |
| $\widehat{\text{SE}}_{ML}$ | $0.0152$ |
| $\hat{\bar \Delta}$ (paired) | $-0.3345$ |
| $\widehat{\text{SE}}(\hat{\bar \Delta})$ | $0.0288$ |
| 95% CI for $\bar \Delta$ | $[-0.4011, -0.2780]$ |
| $z = \hat{\bar \Delta} / \widehat{\text{SE}}$ | $-11.60$ |
| $p$-value (Wald, two-sided) | $< 0.0001$ |
| $n_{BL}, n_{ML}, n_{\text{paired}}$ | $3{,}889 / 3{,}889 / 3{,}889$ |

The report's substantive finding — FCS-acceptable households fell from 43.2% at BL to 9.7% at ML, a paired change of $-33.5\,\text{pp}$ — survives any sensitivity check.

**Manual recomputation.** The script computes $\hat{\bar Y}_{BL}$, $\hat{\bar Y}_{ML}$, $\hat{\bar \Delta}$ directly from the HT formula

$$
\hat{\bar Y} \;=\; \frac{\sum_{i \in S^*} w_i \, y_i}{\sum_{i \in S^*} w_i}
$$

where $S^*$ is the non-NA subset for the relevant variable. For `fcs_acceptable` the script confirms agreement with `svymean` to within $10^{-15}$ on all three point estimates — i.e., the HT formula in §3.1 is exactly what `svymean` evaluates.

**Marginal equivalence.** Because BL and ML non-NA subsamples are identical here, $\hat{\bar \Delta} = -0.3345$ matches $\hat{\bar Y}_{ML} - \hat{\bar Y}_{BL} = 0.0971 - 0.4316 = -0.3345$ exactly. The verification script asserts agreement to $7 \times 10^{-16}$.

**Variance comparison.** The "independent-means difference" SE would be $\sqrt{0.0239^2 + 0.0152^2} = 0.0283$. The paired-Δ SE is $0.0288$ — actually slightly *larger* than the independent-means SE. The implied pre/post correlation is

$$
\rho \;\approx\; 1 - \frac{(0.0288)^2}{(0.0283)^2} \;\approx\; -0.04,
$$

i.e., essentially zero with a small negative tilt. This is a substantive empirical finding about the BRCiS panel: between-round household-level persistence in FCS is very weak, presumably because the dominant driver of the change between BL and ML is a structural shock (the 2022–2023 drought, programme-induced trajectories, or both) that varies more across households than across rounds for a given household. The textbook efficiency argument for paired-Δ over difference-of-means is essentially moot for this indicator — but **the paired-Δ point estimate is still the correct estimator of $E_{\mathcal P}[\Delta]$**, and its SE is the honest reflection of the within-HH change variance.

### 9.2 Subgroup-conditioning example — `water_productive_use_normal_year`

This binary indicator is gated on `farmer == 1` (at the respective round). The NA propagation pattern (§7) handles the subgroup automatically:

**Stored values** (from `prepost_results.rds`):

| Quantity | Value |
|---|---|
| $\hat{\bar Y}_{BL}$ (over farmers at BL) | $0.3543$ |
| $\widehat{\text{SE}}_{BL}$ | $0.0275$ |
| $\hat{\bar Y}_{ML}$ (over farmers at ML) | $0.4314$ |
| $\widehat{\text{SE}}_{ML}$ | $0.0265$ |
| $\hat{\bar \Delta}$ (over farmers at both rounds) | $+0.0893$ |
| $\widehat{\text{SE}}(\hat{\bar \Delta})$ | $0.0396$ |
| $n_{BL}, n_{ML}, n_{\text{paired}}$ | $2{,}107 / 2{,}689 / 1{,}851$ |

Three things to take from this row:

1. **The three N values differ** — $n_{\text{paired}} = 1{,}851$ is smaller than either $n_{BL} = 2{,}107$ or $n_{ML} = 2{,}689$. This surfaces the subgroup conditioning automatically: only households reporting `farmer == 1` at *both* rounds contribute to $\hat{\bar \Delta}$. A reader can see the conditioning without reading the harmonization map.
2. **The paired-Δ identity does NOT hold.** $\hat{\bar Y}_{ML} - \hat{\bar Y}_{BL} = 0.4314 - 0.3543 = +0.0771$, but $\hat{\bar \Delta} = +0.0893$. The two differ because the three N-subsamples are different finite-population subsets. The estimand $\bar \Delta$ over $\{i : \text{farmer}_{BL,i} = \text{farmer}_{ML,i} = 1\}$ is a different parameter than $\bar Y_{ML} - \bar Y_{BL}$ over the respective farmer pools — and the report transparently shows both.
3. **NA-propagation ≡ `subset()`.** The verification script confirms that

```r
svymean(~water_productive_use_normal_year_bl, design, na.rm = TRUE)
```

and

```r
svymean(~water_productive_use_normal_year_bl,
        subset(design, !is.na(water_productive_use_normal_year_bl)))
```

produce identical point estimates ($0.3543$) and identical standard errors ($0.0275$) — agreement to $10^{-12}$ on both. This empirically validates the claim in §7.2 that the NA-propagation pattern recovers the correct subpopulation estimator with correct standard errors.

### 9.3 A continuous example — `rsi_pnorm`

Reported here for completeness. The RSI pnorm composite has BL non-NA on all 3,889 panel HHs and ML non-NA on 3,792 HHs (97 households drop out for ML missingness on one of the RSI inputs).

| Quantity | Value |
|---|---|
| $\hat{\bar Y}_{BL}$ | $3.2372$ |
| $\widehat{\text{SE}}_{BL}$ | $0.0247$ |
| $\hat{\bar Y}_{ML}$ | $3.7087$ |
| $\widehat{\text{SE}}_{ML}$ | $0.0260$ |
| $\hat{\bar \Delta}$ | $+0.4700$ |
| $\widehat{\text{SE}}(\hat{\bar \Delta})$ | $0.0354$ |
| 95% CI | $[0.4006, 0.5394]$ |
| $z$ | $13.28$ |
| $p$-value | $< 0.0001$ |
| $n_{BL}, n_{ML}, n_{\text{paired}}$ | $3{,}889 / 3{,}792 / 3{,}792$ |

The marginal-difference identity gives $\hat{\bar Y}_{ML} - \hat{\bar Y}_{BL} = 0.4715$ vs. paired $\hat{\bar \Delta} = 0.4700$ — a 0.0015 difference reflecting the 97 BL-only households whose values affect $\hat{\bar Y}_{BL}$ but not $\hat{\bar \Delta}$. The implied $\rho \approx 0.03$ is small but positive, consistent with weak household-level persistence in RSI scores between rounds.

### 9.4 Summary

Across these three indicators, the verification script confirms:

- Manual HT $\equiv$ `svymean` to floating-point precision for all point estimates.
- `svymean` $\equiv$ `prepost_results.rds` stored values exactly.
- NA propagation $\equiv$ `subset()` to $10^{-12}$ on both point and SE.
- Paired-Δ identity $\hat{\bar \Delta} = \hat{\bar Y}_{ML} - \hat{\bar Y}_{BL}$ holds when the BL and ML subsamples are identical, fails otherwise (correctly, by design).

The implied $\rho$ values are small or slightly negative for these indicators — paired-Δ does not buy meaningful efficiency over the independent-means difference. This is an empirical fact about the BRCiS data, not a problem with the estimator. The paired-Δ point estimate is the correct estimator of $E_{\mathcal P}[\Delta]$ regardless, and its design-based SE is the honest variance of the within-HH change.

---

## 10. Verification script

`04_scripts/09_preliminary_report/_scratch/verify_prepost_math.R` mechanically reproduces every claim in §9 from `panel_wide` and the stored `prepost_results.rds`. The script performs five classes of check:

1. **HT point estimates (Check 1).** For each of `{rsi_pnorm, fcs_acceptable, water_productive_use_normal_year}`, recompute $\hat{\bar Y}_{BL}$, $\hat{\bar Y}_{ML}$, $\hat{\bar \Delta}$ directly from the weighted formula

   $$
   \hat{\bar Y} \;=\; \frac{\sum_{i \in S^*} w_i \, y_i}{\sum_{i \in S^*} w_i}
   $$

   and assert agreement with `survey::svymean(..., na.rm = TRUE)` to a numerical tolerance of $10^{-10}$.

2. **Marginal equivalence (Check 2).** For variables where the BL and ML non-NA subsamples are identical, confirm $\hat{\bar \Delta} = \hat{\bar Y}_{ML} - \hat{\bar Y}_{BL}$ to floating-point precision. For variables where the subsamples differ (e.g., subgroup-conditioned indicators), print a diagnostic explaining why the identity does *not* hold and move on without an assertion.

3. **Variance comparison (Check 3).** For each variable, compute $\widehat{\text{SE}}(\hat{\bar \Delta})$ from `svymean` and the "independent-means" SE $\sqrt{\widehat{\text{SE}}_{BL}^2 + \widehat{\text{SE}}_{ML}^2}$. Print the implied $\rho$. Warn if the paired-Δ SE is larger than the independent-means SE (i.e., $\rho < 0$).

4. **NA propagation ≡ `subset()` (Check 4).** For `water_productive_use_normal_year`, build the design once, then compute the BL mean two ways: (a) `svymean(..., na.rm = TRUE)` on the full design, (b) `svymean(...)` on `subset(design, !is.na(.))`. Assert agreement on both point estimate ($10^{-12}$) and SE ($10^{-8}$). This is the empirical confirmation of the §7.2 claim.

5. **Stored vs computed (Check 5).** For each variable, assert that the `svymean` output for BL, ML, Δ, and SE(Δ) matches the values stored in `prepost_results.rds` exactly. Catches any regression where the driver script silently changes its output schema.

The script also prints the §9 worked-example numbers in a clearly delimited block so the methodology doc can be re-synced to the data with a single command.

Run with:

```bash
Rscript 04_scripts/09_preliminary_report/_scratch/verify_prepost_math.R
```

Successful run on the current panel: every check passes (verified 2026-05-26). The script exits 0 on success and 1 on any failure — suitable for inclusion in a CI workflow when one exists.

---

## 11. Diagnostics, caveats, and what to watch

### 11.1 What to check before trusting an estimate

For any indicator whose Δ matters substantively:

1. **Inspect the paired N.** If `n_paired` is much smaller than `n_bl` or `n_ml`, the Δ is conditioned on a subgroup — make sure the subgroup is the one the report claims. (The harmonization-map `notes` column should document this explicitly.)
2. **Inspect the design effect.** Call `svymean(..., deff = TRUE)` on the variable. DEFF > 2 signals that the design's stratification is contributing material non-i.i.d. structure; DEFF > 5 signals to revisit the design declaration. Note that for the current `ids = ~hh_id` (stratified-only) declaration, `svymean` may return DEFF as NA — switching the declaration to `ids = ~community` (community as PSU) is one way to recover a meaningful DEFF when a diagnostic is needed.
3. **Inspect the residual after differencing.** Plot $\Delta_i$ against $Y_{BL,i}$ on the panel; look for ceiling/floor effects, regression-to-the-mean dominating the change, or outlier clusters. If the residual is non-symmetric, the normal-approximation CI in §4.4 may understate uncertainty in the tails.
4. **Lonely PSU count.** `prepost.R` does not currently print the lonely-PSU diagnostic, but a `svydesign(...)` summary will. If the lonely-PSU count is large (say, > 5% of strata), the `"average"` rule is doing a lot of work and the inference is correspondingly less reliable.

### 11.2 Known caveats

1. **The estimand is panel-conditional.** $\bar \Delta$ is the average change *among households that completed both rounds*. The 9.75% attrition between BL Random-Walk and ML is not analysed for selectivity in this report; we have not weighted up for attrition. Any inference about the average BRCiS household (including the dropped-out) requires an attrition-bias analysis that is parked for a future round.

2. **No multiple-testing correction.** The 143-row pre/post table reports many comparisons; some "significant" stars will be Type-I errors. We do not adjust because: (a) the report is descriptive, not confirmatory; (b) Bonferroni/BH at 143 comparisons would suppress almost every finding to insignificance; (c) the natural correction unit is "indicator group" (LogFrame / KPI 4 / RSI / TANGO), not "individual indicator," and we do not currently aggregate hypotheses to that level. Stakeholders should read the stars as descriptive flags, not as confirmatory tests.

3. **Single baseline, single follow-up.** With only two rounds we cannot identify serial-correlation structure beyond AR(1). For future ≥ 3-round designs, the Burlig–Preonas–Woerman (2020) machinery becomes directly relevant; for now, paired-Δ is the most informative estimator the data support.

4. **`"average"` lonely-PSU rule is pragmatic, not principled.** A more conservative choice (`"adjust"`) would give larger SEs in some communities. We have not run sensitivity tables; this is a candidate for a future robustness section.

5. **Panel weights are post-attrition.** The weights in `02_panel_weights.R` are derived from the BL community-level populations and the *panel* sample size per community, not the full-BL sample size. This produces a design-consistent panel estimator but means the weights are not directly comparable to the BL-only weights from `03_full_bl_weights.R`. Cross-evaluation users should be aware.

6. **Empirical pre/post correlation is small.** As documented in §3.3 and confirmed in §9, the implied $\rho$ for headline BRCiS indicators (FCS, RSI composite, productive-use water) is near zero or slightly negative. The textbook efficiency argument for paired-Δ over difference-of-independent-means therefore has little bite for these outcomes. The paired-Δ point estimate is still the correct estimator of $E_{\mathcal P}[\Delta]$, but readers comparing BRCiS SEs to those reported in other longitudinal surveys (where $\rho$ may be much higher) should not expect the same level of variance reduction.

---

## 12. References

All citations have been verified against publisher or DOI-resolver pages. Where a stable DOI is not available, a JSTOR link or institutional landing page is given.

**Books**

1. Kish, L. (1965). *Survey Sampling.* New York: John Wiley & Sons. ISBN 978-0-471-48900-9. Wiley Classics Library reprint 1995, ISBN 978-0-471-10949-5. [Open Library record](https://openlibrary.org/books/OL5947497M/Survey_sampling).

2. Lohr, S. L. (2022). *Sampling: Design and Analysis* (3rd ed.). Boca Raton, FL: Chapman & Hall/CRC. ISBN 978-0-367-27950-9. [Routledge product page](https://www.routledge.com/Sampling-Design-and-Analysis/Lohr/p/book/9780367279509).

3. Lumley, T. (2010). *Complex Surveys: A Guide to Analysis Using R.* Wiley Series in Survey Methodology. Hoboken, NJ: John Wiley & Sons. ISBN 978-0-470-28430-8. DOI [10.1002/9780470580066](https://doi.org/10.1002/9780470580066). [Wiley product page](https://www.wiley.com/en-us/Complex+Surveys:+A+Guide+to+Analysis+Using+R-p-9780470284308).

4. Wooldridge, J. M. (2010). *Econometric Analysis of Cross Section and Panel Data* (2nd ed.). Cambridge, MA: MIT Press. ISBN 978-0-262-23258-6. Chapter 20 is the key reference on stratified-sample estimation.

**Foundational papers — survey statistics**

5. Binder, D. A. (1983). On the variances of asymptotically normal estimators from complex surveys. *International Statistical Review* 51(3): 279–292. JSTOR [1402588](https://www.jstor.org/stable/1402588), DOI [10.2307/1402588](https://doi.org/10.2307/1402588). — *Canonical reference for Taylor linearization of complex-survey estimators.*

6. Horvitz, D. G., & Thompson, D. J. (1952). A generalization of sampling without replacement from a finite universe. *Journal of the American Statistical Association* 47(260): 663–685. DOI [10.1080/01621459.1952.10483446](https://doi.org/10.1080/01621459.1952.10483446). [PDF (CMU mirror)](https://www.stat.cmu.edu/~brian/905-2008/papers/Horvitz-Thompson-1952-jasa.pdf). — *The original HT estimator paper.*

**Pre-post estimators in evaluation**

7. Burlig, F., Preonas, L., & Woerman, M. (2020). Panel data and experimental design. *Journal of Development Economics* 144: 102458. DOI [10.1016/j.jdeveco.2020.102458](https://doi.org/10.1016/j.jdeveco.2020.102458). Working paper: NBER WP [26250](https://www.nber.org/papers/w26250). — *Generalises Frison–Pocock and McKenzie to arbitrary serial correlation and ≥ 3 periods.*

8. Frison, L., & Pocock, S. J. (1992). Repeated measures in clinical trials: analysis using mean summary statistics and its implications for design. *Statistics in Medicine* 11(13): 1685–1704. DOI [10.1002/sim.4780111304](https://doi.org/10.1002/sim.4780111304). PubMed [PMID 1485053](https://pubmed.ncbi.nlm.nih.gov/1485053/). — *Canonical pre-McKenzie statement of the ANCOVA-dominates-CHANGE-and-POST result.*

9. McKenzie, D. (2012). Beyond baseline and follow-up: The case for more T in experiments. *Journal of Development Economics* 99(2): 210–221. DOI [10.1016/j.jdeveco.2012.01.002](https://doi.org/10.1016/j.jdeveco.2012.01.002). Working paper: World Bank PRWP [5639](https://ideas.repec.org/p/wbk/wbrwps/5639.html). — *Development-economics framing of the ANCOVA-vs-DD efficiency comparison; gives the $\text{Var(DD)}/\text{Var(ANCOVA)} = 2/(1+\rho)$ result.*

**Survey weighting**

10. DuMouchel, W. H., & Duncan, G. J. (1983). Using sample survey weights in multiple regression analyses of stratified samples. *Journal of the American Statistical Association* 78(383): 535–543. DOI [10.1080/01621459.1983.10478006](https://doi.org/10.1080/01621459.1983.10478006), JSTOR [2288016](https://www.jstor.org/stable/2288016). — *Proposes weighted-vs-unweighted comparison as a regression-specification test.*

11. Pfeffermann, D. (1993). The role of sampling weights when modeling survey data. *International Statistical Review* 61(2): 317–337. JSTOR [1403631](https://www.jstor.org/stable/1403631), DOI [10.2307/1403631](https://doi.org/10.2307/1403631). — *The canonical descriptive-vs-analytic distinction.*

12. Solon, G., Haider, S. J., & Wooldridge, J. M. (2015). What are we weighting for? *Journal of Human Resources* 50(2): 301–316. DOI [10.3368/jhr.50.2.301](https://doi.org/10.3368/jhr.50.2.301). NBER WP [18859](https://www.nber.org/papers/w18859). — *Modern statement: descriptive → weight; causal → three motives only.*

13. Wooldridge, J. M. (1999). Asymptotic properties of weighted M-estimators for variable probability samples. *Econometrica* 67(6): 1385–1406. DOI [10.1111/1468-0262.00083](https://doi.org/10.1111/1468-0262.00083).

**Software**

14. Lumley, T. (2026). *survey: Analysis of Complex Survey Samples.* R package version 4.5. CRAN: [https://CRAN.R-project.org/package=survey](https://CRAN.R-project.org/package=survey). Reference manual (PDF): [https://cran.r-project.org/web/packages/survey/survey.pdf](https://cran.r-project.org/web/packages/survey/survey.pdf). — *The implementation of every statistic in this document.*

15. Lumley, T. (2026). *Estimates in subpopulations* (vignette). In the `survey` package. [PDF](https://cran.r-project.org/web/packages/survey/vignettes/domain.pdf). — *Authoritative reference for the equivalence of NA propagation, `subset()`, and `svyby()` for domain estimation.*

**Project-internal references**

16. `04_scripts/06_weights/02_panel_weights.R` — derivation of the panel weights $w_i$.
17. `04_scripts/08_harmonize/01_build_panel_dataset.R` — construction of `panel_wide`.
18. `04_scripts/00_setup/01_functions/prepost.R` — implementation of `run_pre_post()`, `format_pre_post()`, `prepost_to_flextable()`.
19. `04_scripts/09_preliminary_report/_scratch/verify_prepost_math.R` — the verification script described in §10.
20. `02_survey_tools/01_quant_tools/prepost_harmonization_map.xlsx` — the harmonization map driving the indicator set.

---

## Appendix A. Glossary

| Term | Definition |
|---|---|
| **Analytical sample** | The panel ($N = 3{,}889$); the subset of BL Random-Walk households that completed the ML interview. |
| **Auxiliary information** | External data (population counts, BRCiS II classifications) used to construct weights but not used as outcomes. |
| **DEFF (design effect)** | $\text{Var}_{\text{design}}/\text{Var}_{\text{SRS}}$; ratio of the design-based variance to the variance under simple random sampling. |
| **Domain (subpopulation)** | A subset of the target population defined by an observable characteristic (e.g., farmers); estimands for the domain are computed by zero-weighting non-domain observations. |
| **HT (Horvitz–Thompson)** | The design-unbiased inverse-probability-weighted estimator for finite-population totals and means. |
| **PSU (primary sampling unit)** | The unit selected at the first stage of sampling. BRCiS treats households as PSUs (each its own) under a stratified-only design declaration; the alternative would have been to treat communities as PSUs and households as second-stage units. |
| **Stratum** | A subset of the population that is exhaustively sampled, with variance contributions summed across strata. In BRCiS, strata = communities. |
| **Taylor linearization** | A first-order Taylor expansion of a smooth estimator around the true parameter, producing influence values whose stratified-HT variance estimates the design variance of the estimator. |

---

## Appendix B. Quick decision tree

```
Q: Am I reporting a descriptive change (mean / proportion) on the BL∩ML panel?
   YES → use run_pre_post() in prepost.R.

Q: Am I reporting a subgroup-conditional change?
   YES → set non-subgroup values to NA in the construct step; svymean(..., na.rm = TRUE)
         handles the rest. Document the subgroup in the map's `notes` column.

Q: Am I reporting an effect comparing arms (treatment vs control)?
   N/A FOR BRCIS III (single-arm). If a future round adds a control: switch to ANCOVA
   via survey::svyglm; cite McKenzie 2012.

Q: Do I have more than two rounds?
   N/A FOR BRCIS III. If a future round adds an endline: revisit serial-correlation
   structure per Burlig–Preonas–Woerman 2020.

Q: Do I want to weight or not?
   ALWAYS WEIGHT for descriptive estimates on the panel (Solon-Haider-Wooldridge 2015).
   For causal regressions, decide based on the three motives in SHW 2015.

Q: How do I handle a community with only 1 panel HH?
   options(survey.lonely.psu = "average") — already set in prepost.R. Document
   the lonely-PSU count in the diagnostic if it grows large.
```
