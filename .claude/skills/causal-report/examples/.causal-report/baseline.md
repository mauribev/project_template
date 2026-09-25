# EXECUTIVE SUMMARY

The executive summary opens the report and carries the findings. It uses Heading 1, like every top-level section, and therefore starts its own page.

# 1.0 HEADINGS AND TEXT

Body text is Arial 10. Section numbers are typed into the heading, not generated — Quarto's automatic numbering is switched off, because the front matter's table of contents is a live Word field that reads the heading text.

## 1.1 A second-level heading

Second-level headings take the house blue at 15 point.

### 1.1.1 A third-level heading

Third level is the same blue at 13 point.

#### A fourth-level heading

Fourth level is the accent red, bold, in small capitals. It takes no number.

##### A fifth-level heading

Fifth level is black, bold, underlined, in small capitals.

## 1.2 Lists

Unordered:

- Leadership and governance systems that plan and respond to crises;
- Ecosystems that provide sustainable access to land, water and natural resources; and
- Market systems that support inclusive access to finance, livelihoods and services.

Ordered:

1.  First step.
2.  Second step.
3.  Third step.

# 2.0 TABLES

A table needs no special markup. Write an ordinary pipe table and it picks up the house look from the Word table style: a blue header row with white bold type, and body rows banded white and pale blue.

The title is a **bold line above the table**, numbered by hand. Keep the numbering sequential with `renumber_titles.py`.

**Table 1. Household composition at baseline and midline**

| Indicator                                    | BL mean (SE) | ML mean (SE) |
|----------------------------------------------|--------------|--------------|
| Average household size                       | 7.92 (0.16)  | 8.33 (0.19)  |
| Average number of female members             | 3.97 (0.08)  | 4.08 (0.11)  |
| Average number of children under 5           | 1.85 (0.07)  | 1.79 (0.07)  |
| % female-headed households                   | 61.5% (2.42) | 61.0% (2.41) |
| % households with a farmer                   | 37.1% (1.69) | 46.7% (1.98) |
| % households with a member with a disability | 19.2% (2.05) | 26.7% (2.35) |

Text after the table. Note that the prose never cites a table by its number — numbers are reassigned when sections move, so references to them go stale silently. Write "the table above" instead. The lint pass in `render.py` refuses to build a report that breaks this rule.

## 2.1 A wider table

**Table 2. Indicator values by round and region**

| Indicator               | North BL | North ML | South BL | South ML | Change |
|-------------------------|----------|----------|----------|----------|--------|
| Food consumption score  | 41.2     | 46.8     | 38.9     | 44.1     | +5.4   |
| Coping strategies index | 12.6     | 9.4      | 14.1     | 10.2     | −3.6   |
| Households with savings | 18%      | 31%      | 15%      | 27%      | +12pp  |

# 3.0 FIGURES

Figures follow the same convention: a bold numbered title above the image.

**Figure 1. Illustrative trend**

*\[An image would sit here, inserted as* `![](path/to/figure.png){width=6.5in}`*. Figures belong in the project's own outputs folder and are produced by a script, not drawn by hand.\]*

# 4.0 MATHEMATICS

Inline mathematics works: the design effect is $1 + (m - 1)\rho$, where $\rho$ is the intra-cluster correlation.

Display equations render as native, editable Word equations rather than images:

$$MDE = (t_{1 - \kappa} + t_{\alpha/2})\sqrt{\frac{1}{P(1 - P)} \cdot \frac{\sigma^{2}}{N}}$$

# 5.0 OTHER ELEMENTS

A block quotation:

> Evidence from the first phase shows the approach is ready for replication.

A footnote reference sits at the end of a sentence.[^1]

Bold, *italic*, and `inline code` all behave normally.

[^1]: Footnote text appears at the foot of the page.
