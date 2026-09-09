# NovaBank – Credit Risk Dashboard (Power BI)

A credit-risk portfolio dashboard on a **synthetic** consumer-loan dataset
(32,581 loans): a star-schema model built in Power Query, ~186 DAX measures, and
a six-page report covering portfolio economics, risk demographics, financial
risk drivers, market segments and single-customer scoring.

The repository also contains a **standalone Python analysis** that recomputes the
dashboard's headline KPIs directly from the source workbook, so every number
below can be verified without opening Power BI.

---

## Key findings

| KPI | Value |
|---|---|
| Loans analysed | 32,581 |
| Overall default rate | 21.8 % |
| Default rate — with prior default / without | 27.8 % / 20.5 % |
| Default rate — worst loan grade (E) | 27.0 % |
| Default rate — "Chronic Problems" payment history | 28.6 % |
| Exposure | 371.0 M |
| Expected loss | 60.9 M |
| Expected interest revenue | 32.1 M |
| **Net result** | **−28.8 M** |

**The portfolio does not pay for its own risk.** At the modelled interest rates,
expected loss (60.9 M) is roughly **1.9×** expected interest revenue (32.1 M) —
a structurally negative net result. The risk is not evenly spread: it
concentrates in the lower loan grades, in borrowers with a prior default, and
above all in the payment-history dimension. That points at repricing or a
cut-off rule for the worst segments rather than at across-the-board tightening.

Amounts are in the dataset's own currency units; the data is synthetic, so the
figures illustrate the method, not a real institution.

---

## Data model

Star schema, built entirely in Power Query (M) from a single Excel workbook:

- **Fact:** `fact_loans` — one row per loan, carrying exposure, expected loss,
  expected interest revenue and a `DefaultFlag`
- **Dimensions (11):** age group, credit-score band, education, employment type,
  geography, home ownership, income group, marital status, payment history,
  loan purpose, loan grade
- Cleaning, typing and surrogate-key assignment happen in the ETL layer, not in
  DAX; measures live in dedicated measure tables grouped by report page

~186 DAX measures cover default rate, expected loss, portfolio at risk, net
revenue and margin, plus dynamic metric selection and HTML/SVG-driven KPI cards.

## Report pages

| Page | What it answers |
|---|---|
| **Overview** | Portfolio KPIs: exposure, expected revenue vs. expected loss, portfolio quality score |
| **Risk Demographics** | Default rate by age, income, education, marital status and employment — incl. an income×age risk matrix that flags the highest-risk cell |
| **Financial Risk Analysis** | Default behaviour across DTI, LTI, credit-utilisation, interest-rate bands and credit-history length |
| **Market Insights** | Loan purpose, loan grade and geographic concentration |
| **Individual Credit Risk** | Client search + single-customer risk profile and scoring |
| **Metrix Explorer** | Free metric selection (e.g. Portfolio Quality Score) sliced by any dimension |

---

## Repository layout

```
Data/
  Bank.xlsx                   source workbook: fact table + 11 dimensions
Dashboard/
  Master Bank.pbix            the Power BI report
analysis/
  credit_risk_analysis.py     reproducible KPI + chart script
  output/                     generated charts and kpi_summary.csv
```

## Reproducing the analysis

```bash
python3 -m pip install pandas matplotlib openpyxl
python3 analysis/credit_risk_analysis.py
```

Writes the four charts and `kpi_summary.csv` to `analysis/output/`.

## Opening the report

Open `Dashboard/Master Bank.pbix` in Power BI Desktop. The Power Query source
points at a local copy of `Bank.xlsx` — set it to this repository's
`Data/Bank.xlsx` via *Transform data → Data source settings* before refreshing.

## Tech stack

Power BI Desktop · DAX · Power Query (M) · Python (pandas, matplotlib) · Git
