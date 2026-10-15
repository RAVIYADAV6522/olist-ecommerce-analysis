"""Build olist_summary.pdf: a one-page A4 summary of the findings for recruiters.

Run from the project root, after the notebooks have produced images/:
    python build_summary_pdf.py
"""

import sqlite3
import textwrap
from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).parent
OUT = ROOT / "olist_summary.pdf"
REPO_URL = "github.com/RAVIYADAV6522/olist-ecommerce-analysis"

BLUE, ORANGE, INK, MUTED, RULE = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#c3c2b7"

FINDINGS = [
    "Late delivery drives bad reviews: on-time orders average 4.29 stars, 4+ days late about 2. "
    "Late orders are 6.7% of reviewed orders but 32.6% of all 1-2 star reviews.",
    "North-east customers get late orders up to 5x as often as São Paulo (Alagoas 21.5% vs 4.5%).",
    "The late rate tripled after Black Friday 2017 (12.4%) and peaked at 19.0% in March 2018.",
    "Orders split across several sellers score 1.3 stars lower (2.85 vs 4.17), though almost never late.",
    "Revenue grew 2.8x from early 2017 and has held at about R$1M a month since March 2018.",
    "Only 3.0% of customers ordered twice; São Paulo state brings in 37% of revenue.",
]
RECOMMENDATIONS = [
    "Lengthen delivery estimates or change carriers for north-east routes.",
    "Book extra carrier capacity before big promotions like Black Friday.",
    "Warn customers about split parcels at checkout, or consolidate shipments.",
    "Send a repeat-purchase voucher after every on-time delivery.",
]


def kpis():
    con = sqlite3.connect(ROOT / "olist.db")
    d = pd.read_sql_query("SELECT revenue, is_late, review_score, customer_unique_id FROM delivered_orders", con)
    con.close()
    return [
        (f"R${d.revenue.sum() / 1e6:.1f}M", "revenue"),
        (f"{len(d):,}", "delivered orders"),
        (f"R${d.revenue.mean():.0f}", "avg order value"),
        (f"{d.is_late.mean():.1%}", "delivered late"),
        (f"{d.review_score.mean():.2f}", "avg review (1-5)"),
    ]


def bullets(fig, items, x, y, width_chars, marker, color, size=9.2, line_h=0.0165, gap=0.006):
    for i, item in enumerate(items, 1):
        lines = textwrap.wrap(item, width_chars)
        fig.text(x, y, marker.format(i=i), color=color, fontsize=size, fontweight="bold", va="top")
        fig.text(x + 0.022, y, "\n".join(lines), color=INK, fontsize=size, va="top", linespacing=1.35)
        y -= line_h * len(lines) + gap
    return y


def main():
    fig = plt.figure(figsize=(8.27, 11.69))  # A4 portrait
    L, R = 0.06, 0.94

    fig.text(L, 0.955, "What drives bad reviews in Brazilian e-commerce?", fontsize=17, fontweight="bold", color=INK)
    fig.text(L, 0.932, "Analysis of 96,211 delivered Olist orders, Jan 2017 – Aug 2018 · SQL, Python, Excel, Power BI",
             fontsize=9.5, color=MUTED)

    for i, (value, label) in enumerate(kpis()):
        x = L + i * (R - L) / 5
        fig.add_artist(plt.Line2D([x, x + (R - L) / 5 - 0.012], [0.912, 0.912], color=BLUE, lw=2.5,
                                  transform=fig.transFigure))
        fig.text(x, 0.903, value, fontsize=16, fontweight="bold", color=INK, va="top")
        fig.text(x, 0.875, label, fontsize=8.5, color=MUTED, va="top")

    fig.text(L, 0.838, "Late delivery is the biggest driver of bad reviews", fontsize=12, fontweight="bold", color=INK)
    for img, rect in [("07_review_score_by_delay.png", [L - 0.01, 0.6, 0.46, 0.225]),
                      ("06_late_rate_by_month.png", [0.505, 0.6, 0.445, 0.2])]:
        ax = fig.add_axes(rect)
        ax.set_anchor("N")
        ax.imshow(mpimg.imread(ROOT / "images" / img))
        ax.axis("off")

    y = 0.6
    fig.text(L, y, "Key findings", fontsize=12, fontweight="bold", color=INK)
    y = bullets(fig, FINDINGS, L, y - 0.025, 95, "{i}", BLUE)

    y -= 0.02
    fig.text(L, y, "Recommendations", fontsize=12, fontweight="bold", color=INK)
    y = bullets(fig, RECOMMENDATIONS, L, y - 0.025, 95, "→", ORANGE)

    y -= 0.02
    fig.text(L, y, "How it was built", fontsize=12, fontweight="bold", color=INK)
    built = [
        ("SQL", "SQLite database with keys; 15 queries using CTEs, window functions and data-quality checks."),
        ("Python", "pandas data-quality pass (26 checks, 19 issues documented) and exploratory analysis notebook."),
        ("Excel", "Monthly tracker: SUMIFS/XLOOKUP summaries, dropdown filters, conditional formatting, sparklines."),
        ("Power BI", "Star-schema model with DAX measures for revenue, late rate, reviews and repeat customers."),
    ]
    y -= 0.025
    for tool, text in built:
        fig.text(L, y, tool, fontsize=9.2, fontweight="bold", color=INK, va="top")
        fig.text(L + 0.09, y, text, fontsize=9.2, color=INK, va="top")
        y -= 0.02

    fig.add_artist(plt.Line2D([L, R], [0.04, 0.04], color=RULE, lw=0.8, transform=fig.transFigure))
    fig.text(L, 0.025, "Ravi Yadav", fontsize=9, color=INK, fontweight="bold")
    fig.text(L + 0.1, 0.025, "·  Data: Olist dataset on Kaggle", fontsize=8.5, color=MUTED)
    fig.text(R, 0.025, REPO_URL, fontsize=9, color=BLUE, ha="right")

    fig.savefig(OUT)
    fig.savefig(ROOT / "images" / "summary_preview.png", dpi=110)
    print(f"Wrote {OUT.name}")


if __name__ == "__main__":
    main()
