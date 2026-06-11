<!--
  Methodology reference — Survey standard errors for proportions and small subgroups.
  Companion to methodology_prepost_weights.md (which covers the paired-Δ estimator
  for prepost.R). This doc covers the *multiple-choice / subgroup* figures used in
  the Contribution Analysis and Context sections of the long report (3.2, 3.4).
  Audience: written as course notes — clean math first, then a plain step-by-step
  explanation. All worked numbers are from the BRCiS III midline panel and are
  reproducible via 04_scripts/10_long_report/_scratch/numbers_for_se_doc.R.
-->

# Methodology — Standard Errors for Proportions and Small Subgroups

**Status:** reference / teaching note. **Companion to:** [`methodology_prepost_weights.md`](methodology_prepost_weights.md) (the paired-Δ estimator). **Code it explains:** the survey-weighted *share* figures in long-report Sections 3.2 (Context) and 3.4 (Contribution Analysis) — the `ml_share_one()`, `ml_share_multi()`, and `shock_share_compare()` helpers.

---

## 0. Preface

### 0.1 Why this document exists

Most of the long report compares a baseline (BL) and midline (ML) value of a single indicator — household size, the share of households with an acceptable Food Consumption Score, the Resilience Spectrum Score. The companion document [`methodology_prepost_weights.md`](methodology_prepost_weights.md) explains exactly how those estimates and their standard errors are built, and §7 of that document explains how it handles **subgroups** (e.g. "among farmers").

But Sections 3.2 and 3.4 ask a different *kind* of question. They take a **multiple-choice survey item** — "Which coping strategy did you use?", "How helpful was it?" — and report the **share of households choosing each option**, sometimes **inside a small subgroup** (e.g. only the households whose main shock was drought). When those subgroups are small, the confidence intervals can become enormous, and one reasonable reaction is "are these even right?".

This note answers that. It explains, from first principles:

1. how a standard error (SE) is built for a simple mean and a simple proportion;
2. what a *complex survey* (weights, clusters, strata) changes;
3. what changes again for **multiple-choice** questions (`select_one`, `select_multiple`);
4. and — the heart of it — what happens in **small subgroups**, why the intervals get so wide, and how to compute the SE *correctly* (a thing our report code was, until recently, doing wrong).

### 0.2 How to read it

Each section states the **math** compactly, then walks through it **in words** with a worked number from our own data. If you read only the prose and the worked boxes, you will get the whole argument. The math is there so the prose is not hand-waving.

### 0.3 The running examples (all real, all reproducible)

| Example | What it is | Where it appears |
|---|---|---|
| **Household size** | a simple **mean**, full panel ($n=3{,}889$) | §1, §2, §3 |
| **% of households with a farmer** | a simple **proportion**, full panel | §1, §2, §3 |
| **"How helpful was the strategy?"** (`strat_helpful`) | a 5-option **`select_one`** in a **small subgroup** ($N=82$ drought-affected households) | §4, §5, §6, §7 |
| **Coping strategies** (`cope1*`) | a **`select_multiple`** | §4 |

Reproduce every number with `04_scripts/10_long_report/_scratch/numbers_for_se_doc.R`.

---

## 1. Start simple: one mean and one proportion

Before subgroups and multiple-choice questions, fix the simplest case firmly, because **everything else is built on top of it**.

### 1.1 A mean — average household size

Suppose we just want the average household size at midline. We have $n = 3{,}889$ households. Call household $i$'s size $y_i$. The estimate is the average:

$$\bar y = \frac{1}{n}\sum_{i=1}^{n} y_i .$$

In our data $\bar y = 8.335$ people. But $\bar y$ is computed from *a sample*. If we had drawn a different 3,889 households we would have gotten a slightly different number. The **standard error** is our estimate of how much $\bar y$ would bounce around from sample to sample. For a simple random sample,

$$\widehat{\mathrm{SE}}(\bar y) = \frac{s}{\sqrt{n}}, \qquad s = \text{sample standard deviation of } y .$$

With $s = 3.07$ and $n = 3{,}889$, that is $3.07/\sqrt{3889} = 0.049$. So a naïve reading is "$8.335 \pm 0.096$ people" (using $\pm 1.96\,\mathrm{SE}$).

### 1.2 A proportion *is* a mean

Now a yes/no question: does the household have a farmer? Code "yes" as $1$ and "no" as $0$. The **share** of households with a farmer is just the **average of that 0/1 column**:

$$\hat p = \frac{1}{n}\sum_{i=1}^{n} x_i, \qquad x_i \in \{0,1\}.$$

This is the single most important idea in the whole document:

> **A proportion is the mean of a 0/1 variable.** Everything we know about the SE of a mean applies directly to proportions.

For a 0/1 variable the standard deviation has a special form, $s = \sqrt{\hat p(1-\hat p)}$, so the SE formula specializes to the one you may remember from an intro stats class:

$$\widehat{\mathrm{SE}}(\hat p) = \sqrt{\frac{\hat p(1-\hat p)}{n}} .$$

In our data $\hat p = 0.467$ ("46.7% of households have a farmer"), and $\sqrt{0.467 \cdot 0.533 / 3882} = 0.0080$, i.e. $\pm 1.6$ percentage points.

### 1.3 Comparing two numbers — baseline vs midline

The report almost never reports one number; it reports a **change**. There are two ways to compare:

- **Paired** (within the same households, measured twice). This is what `prepost.R` does for indicators present in both rounds; it is more precise because it cancels stable household differences. The full theory is in [`methodology_prepost_weights.md`](methodology_prepost_weights.md) §3.
- **Independent two-sample** (two different groups, or the same item where pairing is not meaningful). The change is $\hat p_{ML} - \hat p_{BL}$, and because the two estimates are independent their variances **add**:

$$\widehat{\mathrm{SE}}(\hat p_{ML} - \hat p_{BL}) = \sqrt{\widehat{\mathrm{SE}}(\hat p_{BL})^2 + \widehat{\mathrm{SE}}(\hat p_{ML})^2}.$$

The Context/Contribution figures use the **independent two-sample** version (the shock mix inverts between rounds, so the same household rarely faces the same shock twice — pairing would be near-empty). That combined-SE formula is exactly what `shock_share_compare()` and the Table 8/9 helpers compute.

### 1.4 The roadmap from here

Our actual questions differ from §1.1–1.3 in three ways, and the rest of the document adds them one at a time:

1. **The survey is not a simple random sample.** It has **weights**, **clusters** (communities), and **strata**. → §2–§3.
2. **The questions are multiple-choice**, not a single yes/no. → §4.
3. **We often look inside a small subgroup.** → §5–§7.

Each one *inflates* the standard error relative to the simple formulas above. Understanding by how much, and why, is the point.

---

## 2. The simple-random-sample baseline, stated carefully

Keep the two formulas from §1 as the **reference point** ("what the SE *would* be if we had a simple random sample of independent, equally-important households"):

$$\widehat{\mathrm{SE}}_{\text{SRS}}(\bar y) = \frac{s}{\sqrt n}, \qquad \widehat{\mathrm{SE}}_{\text{SRS}}(\hat p) = \sqrt{\frac{\hat p(1-\hat p)}{n}}.$$

A 95% confidence interval is $\hat\theta \pm 1.96\,\widehat{\mathrm{SE}}(\hat\theta)$. The $1.96$ comes from the Normal distribution: an interval built this way contains the true value in about 95% of repeated samples (Lohr, 2022, ch. 2). The whole game in the rest of the document is: **the real SE is bigger than the SRS SE**, and we need to know by how much, because the CI width — and therefore whether a finding is "real" — depends entirely on it.

The ratio that captures "by how much" has a name.

> **Design effect (DEFF).** $\;\mathrm{DEFF} = \dfrac{\text{variance under the actual design}}{\text{variance under SRS with the same } n}.$ A DEFF of 4 means the real variance is 4× the textbook variance, so the real SE is $\sqrt 4 = 2\times$ as wide (Kish, 1965).

Equivalently, define the **effective sample size**

$$n_{\text{eff}} = \frac{n}{\mathrm{DEFF}} .$$

This is the single most useful number in the document. It says: *a complex-survey estimate with sample size $n$ carries as much information as a simple random sample of size $n_{\text{eff}}$.* When $n_{\text{eff}}$ is small, the estimate is imprecise — no matter how big the raw $n$ looks.

---

## 3. What a real survey changes: three forces

The BRCiS panel is not a simple random sample. Three features of the design move the SE away from the textbook value. We take them one at a time and then combine.

### 3.1 Weights → a smaller *effective* sample

Each household $i$ carries a **survey weight** $w_i$ (how many households in the target population it represents; see [`methodology_prepost_weights.md`](methodology_prepost_weights.md) §6 and `04_scripts/06_weights/`). The weighted mean is

$$\bar y_w = \frac{\sum_i w_i\, y_i}{\sum_i w_i}, \qquad \hat p_w = \frac{\sum_i w_i\, x_i}{\sum_i w_i}.$$

Weighting changes the **point estimate** (it corrects for unequal selection/response), but it also **costs precision**: a few households with large weights dominate the estimate, so you effectively have fewer "independent votes". Kish (1965) quantified the loss with a famous formula for the **effective sample size under unequal weighting**:

$$n_{\text{eff}}^{\,w} = \frac{\left(\sum_i w_i\right)^2}{\sum_i w_i^{\,2}} .$$

If all weights are equal this returns $n$ exactly; the more unequal the weights, the smaller it gets.

> **Worked box — the full panel.** Raw $n = 3{,}889$. Plugging the panel weights into Kish's formula gives $n_{\text{eff}}^{\,w} = 413$. So the *weighting alone* throws away about **89%** of the nominal sample size — the weighted mean of household size carries roughly as much information as a simple random sample of **413** households, not 3,889. (This is the dominant reason the survey SE of household size, $0.186$, is so much bigger than the naïve $0.049$.)

### 3.2 Clustering → correlated neighbours

Households were enumerated **within communities**. Households in the same community resemble each other (same market, same rains, same water point), so two households in the same village carry **less than two villages' worth** of independent information. This positive within-cluster correlation (the *intraclass correlation* $\rho$) inflates the variance. For a cluster of size $b$, Kish's clustering design effect is approximately

$$\mathrm{DEFF}_{\text{cluster}} \approx 1 + (b-1)\,\rho .$$

Even a small $\rho$ matters when clusters are big, and — crucially for §5 — clustering interacts badly with small subgroups, where a single community can dominate.

### 3.3 Stratification → usually a small help

The design also **stratifies** by community (in `svydesign(..., strata = ~community)`). Stratification typically *reduces* variance, because it removes between-stratum variation from the error. It is the one force that works in our favour, and it is usually a second-order effect here.

### 3.4 Putting the forces together

The `survey` package does not multiply these by hand; it computes the variance directly from the design (by **Taylor linearization** — see [`methodology_prepost_weights.md`](methodology_prepost_weights.md) §4.2 and Binder, 1983). The DEFF is then just the ratio of that design-based variance to the SRS variance.

> **Worked box — the two simple estimates, design-based.**
>
> | Estimate | SRS SE | survey SE | DEFF | reading |
> |---|---|---|---|---|
> | Household size (mean) | 0.049 | **0.186** | 14.3 | real CI is $\sqrt{14.3}\approx 3.8\times$ wider |
> | % with a farmer (proportion) | 0.0080 | **0.0198** | 6.1 | real CI is $\sqrt{6.1}\approx 2.5\times$ wider |
>
> Even on the **full panel**, the honest SE is several times the textbook one. The DEFF is driven mostly by the unequal weights (§3.1), with clustering adding more for size than for farmer status.

The key message of §3: **report the survey SE, never the textbook SRS SE.** Our code does this — every estimate goes through `survey::svymean()` on a declared `svydesign`. The SRS formulas are only a teaching reference point.

---

## 4. Multiple-choice questions

So far, one yes/no or one mean. The Context/Contribution figures ask questions with **several options**. There are two questionnaire types, and they behave differently.

### 4.1 `select_one` — choose exactly one of K options

"How helpful was the strategy?" has five mutually exclusive answers (Not / Slightly / Moderately / Very / Extremely helpful). This is a **multinomial**: each household lands in exactly one category, and the five shares sum to 100%.

In code we compute it as `svymean(~factor(answer), design)`. Mechanically this is just **K proportions at once** — one 0/1 indicator per category ("is this household in category $k$?"). So §1.2 still applies: each share is the mean of a 0/1 column, and each gets its own survey SE. The only addition is that the categories are **negatively correlated** (if you're "Very helpful" you can't also be "Moderately"), which the multinomial covariance captures; we rarely need the off-diagonal terms because we report and test one category at a time.

### 4.2 `select_multiple` — check all that apply

"Which coping strategies did you use?" lets a household tick several boxes. In the data this is stored as **one 0/1 column per option** (`cope11`, `cope12`, …). So a `select_multiple` is **not** a multinomial — it is just a **bundle of independent yes/no questions**, and the shares **can sum to more than 100%**. Each option's share is, again, the mean of a 0/1 column (§1.2), with its own survey SE, computed independently (`ml_share_multi()` loops over the option columns).

> **The denominator (gate) question.** For a `select_multiple` nested under a parent question — e.g. the "how did you reduce expenditure?" options are only asked of households that *said* they reduced expenditure — the **denominator** is "households for whom the question applies", not all households. Getting this denominator consistent across rounds is a real trap in our data (baseline filled the skip with 0, midline left it missing); it is documented and fixed in `decision_log.md [2026-05-31]` and is conceptually separate from the SE machinery here.

### 4.3 Why two options in the *same* question can have very different SEs

This surprises people, so it is worth stating plainly. In a single `select_one` question, "Moderately helpful" might have a tight CI while "Extremely helpful" has a huge one. How can the same $N$ give such different precision?

Because the SE of a proportion depends on **the proportion itself and on how its supporters are distributed across weights and clusters** — not just on $N$. A category that (a) sits near $p=0.5$, (b) is concentrated in a few high-weight households, or (c) clusters in a few communities, will have a much larger SE than a category that is rare and evenly spread. We will see this dramatically in §6.

---

## 5. Subgroups (domains) — the heart of your question

Now the real case: we don't report "how helpful" over all households — we report it **among the households whose main shock was drought** ($N = 82$). This is a **subpopulation**, or in survey jargon a **domain**.

### 5.1 The estimand: a *conditional* proportion

The quantity is "**among drought-affected households**, the share who found the strategy very helpful." It is a proportion *conditional* on being in the subgroup. This is the correct estimand for the sentence we write in the report ("of households whose main shock was drought, X% …"). We are **not** trying to estimate an unconditional population total, so we do **not** multiply by the probability of being drought-affected, of having received a warning, and so on. (More on that intuition in §5.4.)

### 5.2 The right way and the wrong way to compute the SE

Here is the subtle part, and it is where our report code had a genuine bug.

**The wrong way (intuitive but incorrect):** take the 82 drought households, *pretend they are a fresh little survey*, and build a new design on just them:

```r
# WRONG — subset the data, then build the design on the subset
d   <- panel_wide[drought_main, ]
des <- svydesign(~hh_id, strata = ~community, weights = ~w, data = d)
svymean(~factor(strat_helpful), des)
```

**The right way (domain estimation):** build the design **once on the full sample**, then restrict to the domain:

```r
# RIGHT — full design, then subset() the DESIGN (zero-weights the others)
des <- svydesign(~hh_id, strata = ~community, weights = ~w, data = panel_wide)
svymean(~factor(strat_helpful), subset(des, drought_main))
```

Why does it matter? The official `survey` domain-estimation vignette (Lumley, *Estimates in subpopulations*) is blunt about it:

> "Estimating a mean or total in a subpopulation (domain) from a survey … is **not** done simply by taking the subset of data in that subpopulation and pretending it is a new survey. This approach would give **correct point estimates but incorrect standard errors**."

The reason: when you slice the data first, you **destroy the stratum/cluster bookkeeping**. Communities that had several households now have one or none; the variance estimator suddenly sees a pile of "lonely" clusters and mis-estimates the between-cluster variation. The correct domain estimator keeps the full design and simply sets the non-domain households' weights to zero, so the strata and clusters are still accounted for. This is the same point made for *means* in [`methodology_prepost_weights.md`](methodology_prepost_weights.md) §7.2–§7.3 — here we apply it to *proportions*.

### 5.3 Worked: the wrong way is genuinely wrong (both directions)

For `strat_helpful` among the 82 drought households, here is the SE computed both ways:

| Category | Wrong way (subset-then-design) | Right way (domain) |
|---|---|---|
| Moderately helpful | **1.8 pp** (far too *small*) | 8.0 pp |
| Very helpful | **44.5 pp** (absurdly *large*) | 20.5 pp |
| Extremely helpful | **44.5 pp** | 20.9 pp |

The wrong method does not just shift the SE — it produces **nonsense in both directions**: some SEs collapse to almost zero, others explode to 44 percentage points (a "confidence interval" wider than the entire 0–100% scale is possible). These are artifacts of the broken variance bookkeeping, not real precision. The domain method gives sane, if still wide, numbers.

> **This was a real bug in our code.** The report-side helpers (`ml_share_one`, `ml_share_multi`, `ssc_cell`, the Table 8/9 `svm`) all used the *wrong* pattern — subset the data, rebuild the design. `prepost.R` always used the right pattern. The fix and its blast radius are in §8.

### 5.4 Your intuition, made precise

A natural worry: *"in the whole population, only a subset would have chosen drought as their main shock, and only a subset of those would have a strategy, and only a subset of those would find it very helpful — shouldn't the uncertainty reflect that whole chain?"*

The answer has two parts:

1. **For the sentence we actually write** — "among drought-affected households, X% found it very helpful" — the relevant uncertainty is the sampling variability of that **conditional** proportion, and the domain SE captures it exactly. We condition on "drought-affected", so we don't re-inflate for the chance of being drought-affected.
2. **But your intuition is exactly right about *why* the interval is wide.** The conditional estimate is imprecise *because the subgroup is a small, random slice of the sample* — and the domain SE already accounts for the fact that the subgroup size is itself random (that is precisely what slicing the *design* rather than the *data* preserves). So the wide interval is the honest price of conditioning on a small group, not a mistake.

If you ever did want the **unconditional** statement — "Y% of *all* households were drought-affected **and** found a strategy very helpful" — that is a different, smaller number ($Y = P(\text{drought}) \times P(\text{very helpful}\mid\text{drought})$), with its own SE. We don't report it because it answers a less useful question, but it is available on request.

---

## 6. Why small subgroups are so imprecise — the whole picture

Now combine everything. The subgroup is small ($N=82$), **and** it inherits the weighting and clustering forces of §3, **and** those forces are *worse* in a small group because a single heavy or clustered household is a bigger share of the total.

### 6.1 The effective sample size collapses

Recall $n_{\text{eff}} = n / \mathrm{DEFF}$. For the drought subgroup:

- Raw $N = 82$ households, scattered across **56 communities**, **36 of them with a single household**.
- Kish's weighting formula ($\big(\sum w\big)^2 / \sum w^2$) over just these 82 households gives $n_{\text{eff}}^{\,w} = \mathbf{6.7}$.

> **The punchline.** You have 82 households on paper, but after honest accounting for unequal weights and clustering, you have the statistical information of a simple random sample of **about 7**. That is why the bars wobble. A survey of 7 people simply cannot pin down a five-way split.

A quick sanity check that this is the right intuition: the SE of a proportion behaves like $\sqrt{p(1-p)/n_{\text{eff}}}$. For "Very helpful" ($\hat p_w = 0.32$) with $n_{\text{eff}} \approx 6.7$, that is $\sqrt{0.32 \cdot 0.68 / 6.7} \approx 0.18$ — about **18 pp**, right in line with the design-based 20.5 pp. The effective-sample-size view *predicts* the wide interval.

### 6.2 The full worked table

`strat_helpful` (How helpful was the strategy?), among the $N=82$ drought-affected households, weighted, domain SEs:

| Category | weighted share | domain SE | 95% CI |
|---|---|---|---|
| Not helpful | 8.4% | 6.1 pp | (−3.5, 20.3) |
| Slightly | 11.7% | 5.1 pp | (1.7, 21.7) |
| Moderately | 18.6% | 8.0 pp | (2.9, 34.3) |
| Very | 32.3% | 20.5 pp | (−7.9, 72.5) |
| Extremely | 29.0% | 20.9 pp | (−12.0, 70.0) |

Two things to notice, both now explainable:

- **The CIs are wide** (and two even spill below 0%, a sign the Normal approximation itself is straining at this $N$ — see §7). This is the $n_{\text{eff}} \approx 7$ story.
- **"Very" and "Extremely" are far less precise than "Moderately."** Why? Because the *weighting* does heavy lifting for those two: their **unweighted** shares are 15.9% and 3.7%, but their **weighted** shares are 32.3% and 29.0%. A handful of **high-weight** drought households happen to sit in those two categories and pull the estimate up — and an estimate that rests on a handful of influential households is, correctly, reported as very uncertain. This is exactly the §4.3 phenomenon, amplified by the small group.

---

## 7. When is a subgroup estimate trustworthy?

If 82 gives an effective 7, how big is big enough? There is a respected, concrete answer. The U.S. **National Center for Health Statistics (NCHS) Data Presentation Standards for Proportions** (Parker et al., 2017) set criteria for whether a survey proportion is reliable enough to publish. An estimate is flagged as **unreliable** (and normally suppressed) if **any** of the following hold:

1. the denominator sample size $n < 30$, **or the *effective* sample size $n_{\text{eff}} < 30$**;
2. the (Korn–Graubard) confidence-interval **absolute width $\ge 0.30$** (i.e. ≥ 30 percentage points);
3. the CI is moderately wide **and** its **relative** width exceeds 130% of the estimate;
4. it rests on **fewer than 8 degrees of freedom** (≈ number of clusters minus number of strata), which triggers a manual review.

Hold our `strat_helpful` figure up to this yardstick:

- effective $n \approx 6.7$ → **fails (1)** ($< 30$);
- "Very"/"Extremely" CI widths $\approx 40$ pp → **fail (2)** ($\ge 30$ pp).

So by a standard built for exactly this purpose, the per-category breakdown for the 82 drought households **would not be published as point estimates** — it would be suppressed or shown only with a prominent "indicative, small sample" flag. That is the honest answer to "are these even right?": the *method* is right, but the *data* in that subgroup is too thin to support a five-way breakdown.

**Practical options when a subgroup is this small** (in rough order of preference):

1. **Collapse categories** — e.g. report "Very + Extremely helpful" as one "helpful" bar. Fewer, larger cells → smaller SEs, fewer degenerate intervals.
2. **Report the subgroup size and a caveat**, and let the reader see the wide CIs (what the report currently does, with an "indicative" note).
3. **Don't break the small group down at all** — report the headline ("X% of drought households implemented *some* strategy") without the option-level split.
4. **Pool** across a broader, defensible group if the question allows.

Which to choose is an editorial call for the report; the statistics only tell you the five-way split is not supportable at $N=82$.

---

## 8. What this means for our code

### 8.1 The bug

The report-side share helpers built the survey design **on subset data** (the §5.2 "wrong way"):

```r
# ml_share_one(), ml_share_multi(), ssc_cell(), and the Table 8/9 svm() — all did:
d <- data.frame(...)[keep, ]                       # subset the DATA
svymean(~..., svydesign(~hh_id, strata=~community, weights=~w, data = d))
```

This is the exact anti-pattern that [`methodology_prepost_weights.md`](methodology_prepost_weights.md) §7.3 warns against. Point estimates are unaffected; **standard errors, confidence intervals, and significance stars are wrong** wherever a real subset is involved — most visibly in the small-$N$ Contribution-Analysis figures (3.2.2 Figs 10–12, the 3.4.1 referral/awareness figures), and to a much smaller degree (because the subset is nearly the whole sample) in the full-panel figures.

### 8.2 The fix

Route every share/CI helper through **one** domain-correct pattern: build the design once on the full `panel_wide`, then `subset(design, keep)`:

```r
des <- survey::svydesign(~hh_id, strata = ~community, weights = ~w, data = panel_wide)
svymean(~factor(var_ml), subset(des, keep), na.rm = TRUE)   # keep = the domain mask
```

This is what `prepost.R` already does for means and paired Δ. Bringing the report-side helpers in line removes a whole class of latent SE bugs and makes 3.2/3.4 consistent with 3.1/3.3. The change re-renders standard errors and significance stars in those sections; **point estimates do not move**.

### 8.3 Status

**Applied (2026-05-31).** All six report-side helpers — `ml_share_one`, `ml_share_multi`, `ml_table` (shared chunk), and `svm`, `ssc_cell`, `sev_cell` (Section 3.2 chunks) — now use the §5.2 NA-propagation pattern: the design is built on the full sample and the subgroup is selected by setting the analysis variable to `NA` outside it (`svymean(..., na.rm = TRUE)`). Verified: **point estimates are unchanged** (e.g. the `cope_exp` frame has `max |Δ| = 0`); standard errors and significance change only where a real subset is involved — the small-$N$ `strat_*` figures now show correct domain CIs (e.g. "Very helpful" ±40 pp instead of the broken ±87 pp), and the subset rows of Tables 8–9 shifted slightly, while the full-panel rows are identical. The reproducible check is `04_scripts/10_long_report/_scratch/test_domain_fix.R`. The figures most affected are the small-subgroup ones, which §7 suggests we should *also* consider collapsing or flagging regardless of the (now correct) SE method.

---

## 9. One-page summary

1. **A proportion is the mean of a 0/1 variable.** Everything follows from the SE of a mean.
2. **Textbook SE** (SRS): $s/\sqrt n$ for a mean, $\sqrt{p(1-p)/n}$ for a proportion. This is only a *reference point*.
3. **Real surveys inflate the SE** through **weights** (a few heavy households → fewer effective observations), **clustering** (correlated neighbours), partly offset by **stratification**. The inflation factor is the **design effect**; the honest sample size is $n_{\text{eff}} = n/\mathrm{DEFF}$. Always report the survey SE (`svymean` on a declared design), never the textbook one.
4. **`select_one`** = a multinomial = K proportions at once; **`select_multiple`** = K independent yes/no columns that can sum past 100%. Each option's SE is just a proportion's SE — and two options in the same question can have very different SEs.
5. **Subgroups must use *domain estimation***: full design, then `subset(design, …)` — **never** subset the data and rebuild the design (that gives correct points but wrong SEs).
6. **Small subgroups are imprecise** because $n_{\text{eff}}$ collapses (our $N=82$ drought group ≈ **7** effective). By the **NCHS standard** ($n_{\text{eff}}<30$, or CI width ≥ 30 pp ⇒ suppress), a five-way split of that group is not publishable as point estimates — **collapse categories, caveat, or don't split**.
7. **The conditional estimand is the right one** for "among drought households, X% …"; its wide CI is the honest cost of a small group, not an error.

---

## References

All citations verified against publisher / DOI-resolver pages. References shared with the companion document are repeated here for self-containment.

**Books**

1. Kish, L. (1965). *Survey Sampling.* New York: John Wiley & Sons. ISBN 978-0-471-48900-9. — *Origin of the design effect and the effective-sample-size formula $n_{\text{eff}} = (\sum w)^2/\sum w^2$.*
2. Lumley, T. (2010). *Complex Surveys: A Guide to Analysis Using R.* Hoboken, NJ: Wiley. ISBN 978-0-470-28430-8. DOI [10.1002/9780470580066](https://doi.org/10.1002/9780470580066). — *Domain estimation, design effects, and the implementation behind the `survey` package.*
3. Lohr, S. L. (2022). *Sampling: Design and Analysis* (3rd ed.). Boca Raton, FL: Chapman & Hall/CRC. ISBN 978-0-367-27950-9. — *Textbook treatment of SEs, CIs, design effects, and domain estimation.*
4. Korn, E. L., & Graubard, B. I. (1999). *Analysis of Health Surveys.* New York: Wiley. ISBN 978-0-471-13773-7. DOI [10.1002/9781118032619](https://doi.org/10.1002/9781118032619). — *The Korn–Graubard confidence interval and guidance on reliability of small-subgroup proportions.*

**Papers / standards**

5. Binder, D. A. (1983). On the variances of asymptotically normal estimators from complex surveys. *International Statistical Review* 51(3): 279–292. DOI [10.2307/1402588](https://doi.org/10.2307/1402588). — *Taylor linearization for complex-survey estimators.*
6. Parker, J. D., Talih, M., Malec, D. J., et al. (2017). *National Center for Health Statistics Data Presentation Standards for Proportions.* National Center for Health Statistics. *Vital and Health Statistics* 2(175). [CDC stacks](https://stacks.cdc.gov/view/cdc/47786), [PubMed 30248016](https://pubmed.ncbi.nlm.nih.gov/30248016/). — *Concrete reliability criteria for survey proportions (effective sample size, CI width, degrees of freedom).*

**Software**

7. Lumley, T. *survey: Analysis of Complex Survey Samples.* R package. CRAN: [package=survey](https://CRAN.R-project.org/package=survey).
8. Lumley, T. *Estimates in subpopulations* (vignette, `survey` package). [PDF](https://cran.r-project.org/web/packages/survey/vignettes/domain.pdf). — *Authoritative statement that subsetting-then-rebuilding gives wrong SEs and that domain estimation (zero-weighting) is correct.*

**Project-internal**

9. [`methodology_prepost_weights.md`](methodology_prepost_weights.md) — the companion document (paired-Δ estimator; §6 weights, §7 subgroup conditioning for means).
10. `04_scripts/10_long_report/_scratch/numbers_for_se_doc.R` — reproduces every worked number in this document.
11. `04_scripts/00_setup/01_functions/prepost.R` and the long-report QMD helpers (`ml_share_one`, `ml_share_multi`, `shock_share_compare`) — the code this document explains.

---

## Appendix A. Formula quick-reference

| Quantity | Formula | Note |
|---|---|---|
| Mean | $\bar y = \frac1n\sum y_i$ | weighted: $\sum w_i y_i / \sum w_i$ |
| Proportion | $\hat p = \frac1n\sum x_i,\; x_i\in\{0,1\}$ | a proportion **is** a mean |
| SRS SE (mean) | $s/\sqrt n$ | reference point only |
| SRS SE (proportion) | $\sqrt{\hat p(1-\hat p)/n}$ | reference point only |
| Independent-change SE | $\sqrt{\mathrm{SE}_{BL}^2 + \mathrm{SE}_{ML}^2}$ | variances add |
| Design effect | $\mathrm{DEFF} = \mathrm{Var}_{\text{design}} / \mathrm{Var}_{\text{SRS}}$ | SE ratio $= \sqrt{\mathrm{DEFF}}$ |
| Effective sample size | $n_{\text{eff}} = n/\mathrm{DEFF}$ | "information equals an SRS of this size" |
| Kish weighting $n_{\text{eff}}$ | $(\sum w_i)^2 / \sum w_i^2$ | the weighting part of the loss |
| Domain estimate | `svymean(~y, subset(design, dom))` | **not** a rebuilt design |

## Appendix B. Glossary

- **Domain / subpopulation** — a subgroup defined *after* sampling (e.g. drought-affected households). Estimated by restricting the *design*, not the data.
- **Design effect (DEFF)** — how many times bigger the real variance is than the textbook (SRS) variance.
- **Effective sample size ($n_{\text{eff}}$)** — the SRS size that would carry the same information; $n/\mathrm{DEFF}$.
- **`select_one`** — a question with mutually exclusive options (a multinomial); shares sum to 100%.
- **`select_multiple`** — "check all that apply"; stored as one 0/1 column per option; shares can sum past 100%.
- **Lonely PSU** — a stratum/cluster with a single sampled unit, so within-cluster variance can't be estimated locally; handled by the `survey.lonely.psu = "average"` rule (see companion doc §4.3).
- **Taylor linearization** — the method `survey` uses to get a variance for a ratio/mean estimator (Binder, 1983).
