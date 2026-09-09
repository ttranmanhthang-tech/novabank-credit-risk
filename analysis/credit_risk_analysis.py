"""
NovaBank credit-risk portfolio - reproducible analysis of the source dataset.

Reads Data/Bank.xlsx (the same star-schema workbook that feeds the Power BI
model) and reproduces the headline KPIs of the dashboard in plain Python, so
every number in the README can be verified independently of Power BI.

Usage:  python analysis/credit_risk_analysis.py
Output: analysis/output/*.png  and  analysis/output/kpi_summary.csv
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "Data" / "Bank.xlsx"
OUT = ROOT / "analysis" / "output"
OUT.mkdir(parents=True, exist_ok=True)

# --- design tokens ---------------------------------------------------------
# Single-hue ordinal ramp (light -> dark), validated for monotone lightness,
# visible step gaps and >= 2:1 contrast against the chart surface.
RAMP = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"]
POS, NEG = "#2a78d6", "#e34948"          # diverging pair: gain / loss
SURFACE = "#fcfcfb"
INK, INK_2, GRID = "#0b0b0b", "#52514e", "#e6e5e1"

mpl.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "font.size": 10,
    "axes.edgecolor": GRID, "axes.labelcolor": INK_2,
    "xtick.color": INK_2, "ytick.color": INK_2,
    "axes.titlecolor": INK, "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False,
})


def de(x, d=1):
    """German number format: 1.234,5"""
    return f"{x:,.{d}f}".replace(",", "\u00a0").replace(".", ",").replace("\u00a0", ".")


def ramp(n):
    """n evenly spread steps from the validated ordinal ramp."""
    if n <= len(RAMP):
        idx = [round(i * (len(RAMP) - 1) / max(n - 1, 1)) for i in range(n)]
        return [RAMP[i] for i in idx]
    return [RAMP[i % len(RAMP)] for i in range(n)]


def bar_chart(labels, values, title, subtitle, fname, colors=None,
              fmt=None, ylabel="Ausfallquote (%)"):
    """Horizontal-baseline bar chart, one series, every bar directly labelled."""
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    bars = ax.bar(labels, values, width=0.62,
                  color=colors or ramp(len(values)))
    top = max(values)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + top * 0.025,
                de(value) + " %", ha="center", va="bottom",
                fontsize=10, fontweight="bold", color=INK)
    ax.set_ylim(0, top * 1.18)
    ax.set_ylabel(ylabel)
    ax.set_title(title, pad=18, loc="left")
    ax.text(0, 1.02, subtitle, transform=ax.transAxes,
            fontsize=9.5, color=INK_2, va="bottom")
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / fname, dpi=170)
    plt.close(fig)


def main():
    xl = pd.ExcelFile(DATA)
    f = xl.parse("fact_loans")
    dim = {name: xl.parse(f"dim_{name}") for name in
           ("grade", "payment", "creditband", "income", "age")}

    f = (f.merge(dim["grade"], on="GradeKey", how="left")
           .merge(dim["payment"], on="PaymentKey", how="left")
           .merge(dim["creditband"], on="CreditBandKey", how="left"))

    n = len(f)
    overall = 100 * f["DefaultFlag"].mean()
    exposure = f["LoanAmount"].sum()
    exp_loss = f["ExpectedLoss"].sum()
    exp_rev = f["ExpectedInterestRevenue"].sum()
    net = exp_rev - exp_loss

    def rate_by(col, order=None):
        g = f.groupby(col)["DefaultFlag"].agg(["mean", "size"])
        g["rate"] = 100 * g["mean"]
        return g.reindex(order) if order else g.sort_values("rate")

    # 1 - loan grade -------------------------------------------------------
    grades = rate_by("LoanGrade", order=list("ABCDE"))
    bar_chart(grades.index.tolist(), grades["rate"].round(1).tolist(),
              "Ausfallquote nach Loan Grade",
              f"n = {de(n, 0)} Kredite  |  Gesamtausfallquote {de(overall)} %",
              "01_default_rate_by_grade.png")

    # 2 - debt-to-income band ---------------------------------------------
    bands = [(0, 20), (20, 30), (30, 40), (40, 50), (50, 200)]
    labels = ["< 20 %", "20-30 %", "30-40 %", "40-50 %", "> 50 %"]
    f["DTI_Band"] = pd.cut(f["DTI_RatioPct"], [b[0] for b in bands] + [200],
                           labels=labels, right=False)
    dti = f.groupby("DTI_Band", observed=True)["DefaultFlag"].mean().mul(100)
    bar_chart(labels, dti.reindex(labels).round(1).tolist(),
              "Ausfallquote nach Debt-to-Income-Band",
              "Höhere Schuldenlast geht mit höherer Ausfallquote einher",
              "02_default_rate_by_dti.png")

    # 3 - payment history --------------------------------------------------
    order = ["Clean History", "Single Late Payment",
             "Multiple Issues", "Chronic Problems"]
    hist = rate_by("PaymentHistory", order=order)
    bar_chart(order, hist["rate"].round(1).tolist(),
              "Ausfallquote nach Zahlungshistorie",
              "Stärkster Einzeltreiber im Modell",
              "03_default_rate_by_payment_history.png")

    # 4 - portfolio economics ---------------------------------------------
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    items = ["Erwartete\nZinserträge", "Expected\nLoss", "Nettoergebnis"]
    vals = [exp_rev / 1e6, -exp_loss / 1e6, net / 1e6]
    bars = ax.bar(items, vals, width=0.55,
                  color=[POS if v >= 0 else NEG for v in vals])
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2,
                v + (2.5 if v >= 0 else -2.5),
                ("+" if v >= 0 else "\u2212") + de(abs(v)) + " Mio.",
                ha="center", va="bottom" if v >= 0 else "top",
                fontsize=10, fontweight="bold", color=INK)
    ax.axhline(0, color=INK_2, linewidth=1)
    ax.set_ylabel("Mio. (Modellwährung)")
    ax.set_ylim(min(vals) * 1.35, max(vals) * 1.35)
    ax.set_title("Portfolio-Ökonomie", pad=18, loc="left")
    ax.text(0, 1.02,
            f"Exposure {de(exposure/1e6)} Mio.  |  Expected Loss übersteigt die erwarteten Zinserträge",
            transform=ax.transAxes, fontsize=9.5, color=INK_2, va="bottom")
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "04_portfolio_economics.png", dpi=170)
    plt.close(fig)

    # KPI table ------------------------------------------------------------
    prior = f.groupby("PriorDefault")["DefaultFlag"].mean().mul(100)
    kpis = pd.DataFrame([
        ("Kredite (Zeilen)", de(n, 0)),
        ("Ausfallquote gesamt", de(overall) + " %"),
        ("Ausfallquote mit Vorausfall", de(prior["Yes"]) + " %"),
        ("Ausfallquote ohne Vorausfall", de(prior["No"]) + " %"),
        ("Schlechtester Loan Grade", "E \u2013 " + de(grades.loc["E", "rate"]) + " %"),
        ("Exposure", de(exposure/1e6) + " Mio."),
        ("Expected Loss", de(exp_loss/1e6) + " Mio."),
        ("Erwartete Zinserträge", de(exp_rev/1e6) + " Mio."),
        ("Nettoergebnis", "\u2212" + de(abs(net)/1e6) + " Mio."),
    ], columns=["KPI", "Wert"])
    kpis.to_csv(OUT / "kpi_summary.csv", index=False)
    print(kpis.to_string(index=False))
    print(f"\nCharts and kpi_summary.csv written to {OUT}")


if __name__ == "__main__":
    main()
