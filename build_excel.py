"""Build excel/olist_monthly_tracker.xlsx from the delivered_orders view in olist.db.

Run from the project root, after load_data.py:
    python build_excel.py

Every number on the summary tabs is a live formula (SUMIFS, COUNTIFS, AVERAGEIFS,
XLOOKUP) over the Orders table on the Data tab, so the workbook still works if rows
are added. Values computed in pandas are stored alongside each formula so the file
also shows correct numbers in viewers that do not recalculate (e.g. GitHub previews).
"""

import sqlite3
from pathlib import Path

import pandas as pd
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell as cell, xl_col_to_name as col_name

ROOT = Path(__file__).parent
OUT = ROOT / "excel" / "olist_monthly_tracker.xlsx"

BLUE, ORANGE, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e1e0d9"

# ---------------------------------------------------------------- data
con = sqlite3.connect(ROOT / "olist.db")
orders = pd.read_sql_query("""
    SELECT d.order_id, d.purchase_date, d.purchase_month, d.customer_state,
           COALESCE(p.product_category_name, 'unknown') AS category_code,
           d.items, d.product_value, d.freight_value, d.revenue, d.payment_type,
           d.delivery_days, d.days_late, d.is_late, d.review_score
    FROM delivered_orders AS d
    JOIN products AS p ON p.product_id = d.product_id
    ORDER BY d.purchase_timestamp
""", con, parse_dates=["purchase_date"])
lookup = pd.read_sql_query("""
    SELECT product_category_name AS code, product_category_name_english AS english
    FROM category_translation ORDER BY code
""", con)
con.close()

DATA_COLUMNS = [  # (header, source column, width, format key)
    ("Order ID", "order_id", 34, None),
    ("Purchase Date", "purchase_date", 13, "date"),
    ("Month", "purchase_month", 9, None),
    ("Customer State", "customer_state", 9, None),
    ("Category Code", "category_code", 30, None),
    ("Items", "items", 7, None),
    ("Product Value", "product_value", 12, "money2"),
    ("Freight", "freight_value", 10, "money2"),
    ("Revenue", "revenue", 11, "money2"),
    ("Payment Type", "payment_type", 13, None),
    ("Delivery Days", "delivery_days", 10, "one_dp"),
    ("Days Late", "days_late", 9, None),
    ("Late", "is_late", 6, None),
    ("Review Score", "review_score", 9, "one_dp"),
]
months = sorted(orders.purchase_month.unique())
states = sorted(orders.customer_state.unique())

# ---------------------------------------------------------------- workbook + formats
OUT.parent.mkdir(exist_ok=True)
wb = xlsxwriter.Workbook(OUT, {"use_future_functions": True, "nan_inf_to_errors": True})
wb.set_properties({"title": "Olist monthly tracker", "author": "Ravi Yadav"})

base = {"font_name": "Calibri", "font_size": 11, "font_color": INK}
F = {
    "title": wb.add_format({**base, "bold": True, "font_size": 18}),
    "subtitle": wb.add_format({**base, "font_color": MUTED, "italic": True}),
    "header": wb.add_format({**base, "bold": True, "bg_color": "#eef3fb", "bottom": 1, "bottom_color": BLUE,
                             "text_wrap": True, "valign": "vcenter"}),
    "label": wb.add_format({**base, "bold": True}),
    "text": wb.add_format(base),
    "input": wb.add_format({**base, "bold": True, "bg_color": "#fff4d6", "border": 1, "border_color": "#eda100",
                            "align": "center"}),
    "date": wb.add_format({**base, "num_format": "yyyy-mm-dd"}),
    "money": wb.add_format({**base, "num_format": '"R$"#,##0'}),
    "money2": wb.add_format({**base, "num_format": '"R$"#,##0.00'}),
    "int": wb.add_format({**base, "num_format": "#,##0"}),
    "one_dp": wb.add_format({**base, "num_format": "0.0"}),
    "two_dp": wb.add_format({**base, "num_format": "0.00"}),
    "pct": wb.add_format({**base, "num_format": "0.0%"}),
    "growth": wb.add_format({**base, "num_format": '[Color10]▲ 0.0%;[Red]▼ 0.0%;0.0%'}),
    "total_label": wb.add_format({**base, "bold": True, "top": 1}),
    "total_money": wb.add_format({**base, "bold": True, "top": 1, "num_format": '"R$"#,##0'}),
    "total_int": wb.add_format({**base, "bold": True, "top": 1, "num_format": "#,##0"}),
    "total_pct": wb.add_format({**base, "bold": True, "top": 1, "num_format": "0.0%"}),
    "total_two": wb.add_format({**base, "bold": True, "top": 1, "num_format": "0.00"}),
    "kpi_label": wb.add_format({**base, "font_color": MUTED, "align": "center", "top": 2, "top_color": BLUE}),
    "kpi_money": wb.add_format({**base, "bold": True, "font_size": 20, "align": "center", "num_format": '"R$"#,##0'}),
    "kpi_int": wb.add_format({**base, "bold": True, "font_size": 20, "align": "center", "num_format": "#,##0"}),
    "kpi_money2": wb.add_format({**base, "bold": True, "font_size": 20, "align": "center", "num_format": '"R$"#,##0.00'}),
    "kpi_pct": wb.add_format({**base, "bold": True, "font_size": 20, "align": "center", "num_format": "0.0%"}),
    "kpi_two": wb.add_format({**base, "bold": True, "font_size": 20, "align": "center", "num_format": "0.00"}),
    "prev_money": wb.add_format({**base, "font_color": MUTED, "align": "center", "num_format": '"vs R$"#,##0'}),
    "prev_int": wb.add_format({**base, "font_color": MUTED, "align": "center", "num_format": '"vs "#,##0'}),
    "prev_money2": wb.add_format({**base, "font_color": MUTED, "align": "center", "num_format": '"vs R$"#,##0.00'}),
    "prev_pct": wb.add_format({**base, "font_color": MUTED, "align": "center", "num_format": '"vs "0.0%'}),
    "prev_two": wb.add_format({**base, "font_color": MUTED, "align": "center", "num_format": '"vs "0.00'}),
    "chg_up_good": wb.add_format({**base, "bold": True, "align": "center", "num_format": '[Color10]▲ 0.0%;[Red]▼ 0.0%;0.0%'}),
    "chg_up_bad_pts": wb.add_format({**base, "bold": True, "align": "center",
                                     "num_format": '[Red]▲ 0.0" pts";[Color10]▼ 0.0" pts";0.0" pts"'}),
    "chg_up_good_abs": wb.add_format({**base, "bold": True, "align": "center", "num_format": '[Color10]▲ 0.00;[Red]▼ 0.00;0.00'}),
    "red": wb.add_format({"bg_color": "#f8d0cf", "font_color": "#9c1c1b"}),
    "amber": wb.add_format({"bg_color": "#fde7b0", "font_color": "#7a5200"}),
    "green": wb.add_format({"bg_color": "#cdeccd", "font_color": "#005000"}),
}

STATE_CRIT = 'IF(Monthly!$B$3="All","*",Monthly!$B$3)'

# ---------------------------------------------------------------- Summary (first tab, filled last)
ws_sum = wb.add_worksheet("Summary")

# ---------------------------------------------------------------- Monthly
ws = wb.add_worksheet("Monthly")
ws.write("A1", "Monthly performance", F["title"])
ws.write("A2", "Delivered orders by purchase month. Pick a state in the yellow cell to filter the whole tab.", F["subtitle"])
ws.write("A3", "Customer state:", F["label"])
ws.write("B3", "All", F["input"])
ws.data_validation("B3", {"validate": "list", "source": ["All"] + states})

headers = ["Month", "Orders", "Revenue", "Avg Order Value", "Revenue vs Prior Month", "Late %", "Avg Review"]
ws.write_row(4, 0, headers, F["header"])
ws.set_row(4, 32)
m = orders.groupby("purchase_month").agg(orders=("order_id", "count"), revenue=("revenue", "sum"),
                                         late=("is_late", "mean"), review=("review_score", "mean"))
FIRST, LAST = 5, 5 + len(months) - 1
for i, mo in enumerate(months):
    r = FIRST + i
    a = cell(r, 0)
    v = m.loc[mo]
    ws.write_string(r, 0, mo, F["text"])
    ws.write_formula(r, 1, f'=COUNTIFS(Orders[Month],{a},Orders[Customer State],{STATE_CRIT})', F["int"], v.orders)
    ws.write_formula(r, 2, f'=SUMIFS(Orders[Revenue],Orders[Month],{a},Orders[Customer State],{STATE_CRIT})', F["money"], v.revenue)
    ws.write_formula(r, 3, f'=IFERROR({cell(r, 2)}/{cell(r, 1)},"")', F["money2"], v.revenue / v.orders)
    if i == 0:
        ws.write_string(r, 4, "", F["growth"])
    else:
        ws.write_formula(r, 4, f'=IFERROR({cell(r, 2)}/{cell(r - 1, 2)}-1,"")', F["growth"],
                         v.revenue / m.iloc[i - 1].revenue - 1)
    ws.write_formula(r, 5, f'=IFERROR(AVERAGEIFS(Orders[Late],Orders[Month],{a},Orders[Customer State],{STATE_CRIT}),"")',
                     F["pct"], v.late)
    ws.write_formula(r, 6, f'=IFERROR(AVERAGEIFS(Orders[Review Score],Orders[Month],{a},Orders[Customer State],{STATE_CRIT}),"")',
                     F["two_dp"], v.review)
T = LAST + 1
ws.write(T, 0, "Total", F["total_label"])
ws.write_formula(T, 1, f"=SUM(B{FIRST + 1}:B{LAST + 1})", F["total_int"], len(orders))
ws.write_formula(T, 2, f"=SUM(C{FIRST + 1}:C{LAST + 1})", F["total_money"], orders.revenue.sum())
ws.write_formula(T, 3, f'=IFERROR(C{T + 1}/B{T + 1},"")', F["total_money"], orders.revenue.mean())
ws.write(T, 4, "", F["total_label"])
ws.write_formula(T, 5, f'=IFERROR(AVERAGEIFS(Orders[Late],Orders[Customer State],{STATE_CRIT}),"")', F["total_pct"], orders.is_late.mean())
ws.write_formula(T, 6, f'=IFERROR(AVERAGEIFS(Orders[Review Score],Orders[Customer State],{STATE_CRIT}),"")', F["total_two"], orders.review_score.mean())
ws.set_column("A:A", 16)
ws.set_column("B:G", 14)
ws.freeze_panes(5, 1)

chart = wb.add_chart({"type": "column"})
chart.add_series({"name": "Revenue", "categories": ["Monthly", FIRST, 0, LAST, 0],
                  "values": ["Monthly", FIRST, 2, LAST, 2], "fill": {"color": BLUE}, "gap": 60})
chart.set_title({"name": "Revenue by month", "name_font": {"size": 12, "bold": True}})
chart.set_legend({"none": True})
chart.set_y_axis({"num_format": '"R$"#,##0,"k"', "major_gridlines": {"visible": True, "line": {"color": GRID}},
                  "line": {"none": True}})
chart.set_x_axis({"num_font": {"rotation": -45}})
chart.set_size({"width": 620, "height": 330})
ws.insert_chart("I5", chart)

# ---------------------------------------------------------------- Category
ws = wb.add_worksheet("Category")
ws.write("A1", "Revenue by category and month", F["title"])
ws.write("A2", "English names come from the Lookup tab with XLOOKUP. Sorted by total revenue; darker = more revenue.", F["subtitle"])
cat = orders.groupby("category_code").agg(orders=("order_id", "count"), revenue=("revenue", "sum"),
                                          review=("review_score", "mean")).sort_values("revenue", ascending=False)
cat_month = orders.pivot_table(index="category_code", columns="purchase_month", values="revenue", aggfunc="sum").fillna(0)
english = dict(zip(lookup.code, lookup.english))
fixed = ["Category Code", "Category", "Orders", "Total Revenue", "Avg Review", "Trend"]
ws.write_row(3, 0, fixed + months, F["header"])
ws.set_row(3, 32)
C0 = len(fixed)  # first month column
CF, CL = 4, 4 + len(cat) - 1
for i, (code, v) in enumerate(cat.iterrows()):
    r = CF + i
    a = cell(r, 0)
    ws.write_string(r, 0, code, F["text"])
    ws.write_formula(r, 1, f"=XLOOKUP({a},CategoryLookup[Code],CategoryLookup[English],{a})", F["text"], english.get(code, code))
    ws.write_formula(r, 2, f"=COUNTIFS(Orders[Category Code],{a})", F["int"], v.orders)
    ws.write_formula(r, 3, f"=SUM({cell(r, C0)}:{cell(r, C0 + len(months) - 1)})", F["money"], v.revenue)
    ws.write_formula(r, 4, f'=IFERROR(AVERAGEIFS(Orders[Review Score],Orders[Category Code],{a}),"")', F["two_dp"], v.review)
    for j, mo in enumerate(months):
        ws.write_formula(r, C0 + j, f"=SUMIFS(Orders[Revenue],Orders[Category Code],{a},Orders[Month],{cell(3, C0 + j, True, True)})",
                         F["money"], cat_month.loc[code, mo])
    ws.add_sparkline(r, 5, {"range": f"Category!{cell(r, C0)}:{cell(r, C0 + len(months) - 1)}",
                            "series_color": BLUE, "high_point": True, "markers_color": ORANGE, "high_color": ORANGE})
ws.conditional_format(CF, C0, CL, C0 + len(months) - 1,
                      {"type": "2_color_scale", "min_color": "#ffffff", "max_color": "#5598e7"})
ws.conditional_format(CF, 4, CL, 4, {"type": "3_color_scale", "min_color": "#f8d0cf", "mid_color": "#ffffff",
                                     "max_color": "#cdeccd", "mid_type": "num", "mid_value": 4})
ws.set_column("A:A", 30)
ws.set_column("B:B", 26)
ws.set_column("C:E", 11)
ws.set_column("F:F", 16)
ws.set_column(C0, C0 + len(months) - 1, 10)
ws.freeze_panes(4, 2)

# ---------------------------------------------------------------- Delivery
ws = wb.add_worksheet("Delivery")
ws.write("A1", "Delivery performance", F["title"])
ws.write("A2", "Late = delivered on a later day than the estimate given at purchase. Red > 10%, amber 5-10%, green < 5%.", F["subtitle"])
ws.write_row(3, 0, ["Customer State", "Orders", "Late Orders", "Late %", "Avg Delivery Days", "Avg Review"], F["header"])
ws.set_row(3, 32)
st = orders.groupby("customer_state").agg(orders=("order_id", "count"), late_orders=("is_late", "sum"),
                                          late=("is_late", "mean"), days=("delivery_days", "mean"),
                                          review=("review_score", "mean")).sort_values("late", ascending=False)
SF, SL = 4, 4 + len(st) - 1
for i, (s, v) in enumerate(st.iterrows()):
    r = SF + i
    a = cell(r, 0)
    ws.write_string(r, 0, s, F["text"])
    ws.write_formula(r, 1, f"=COUNTIFS(Orders[Customer State],{a})", F["int"], v.orders)
    ws.write_formula(r, 2, f"=COUNTIFS(Orders[Customer State],{a},Orders[Late],1)", F["int"], v.late_orders)
    ws.write_formula(r, 3, f'=IFERROR(AVERAGEIFS(Orders[Late],Orders[Customer State],{a}),"")', F["pct"], v.late)
    ws.write_formula(r, 4, f'=IFERROR(AVERAGEIFS(Orders[Delivery Days],Orders[Customer State],{a}),"")', F["one_dp"], v.days)
    ws.write_formula(r, 5, f'=IFERROR(AVERAGEIFS(Orders[Review Score],Orders[Customer State],{a}),"")', F["two_dp"], v.review)
rng = (SF, 3, SL, 3)
ws.conditional_format(*rng, {"type": "cell", "criteria": ">", "value": 0.10, "format": F["red"]})
ws.conditional_format(*rng, {"type": "cell", "criteria": "between", "minimum": 0.05, "maximum": 0.10, "format": F["amber"]})
ws.conditional_format(*rng, {"type": "cell", "criteria": "<", "value": 0.05, "format": F["green"]})
ws.conditional_format(SF, 5, SL, 5, {"type": "data_bar", "bar_color": "#9ec5f4", "bar_solid": True,
                                     "min_type": "num", "min_value": 3, "max_type": "num", "max_value": 5})
ws.write(SL + 1, 0, "All states", F["total_label"])
ws.write_formula(SL + 1, 1, f"=SUM(B{SF + 1}:B{SL + 1})", F["total_int"], len(orders))
ws.write_formula(SL + 1, 2, f"=SUM(C{SF + 1}:C{SL + 1})", F["total_int"], orders.is_late.sum())
ws.write_formula(SL + 1, 3, "=AVERAGE(Orders[Late])", F["total_pct"], orders.is_late.mean())
ws.write_formula(SL + 1, 4, "=AVERAGE(Orders[Delivery Days])", F["total_two"], orders.delivery_days.mean())
ws.write_formula(SL + 1, 5, "=AVERAGE(Orders[Review Score])", F["total_two"], orders.review_score.mean())

# Review score by how late the order arrived.
B0 = 3
ws.write(B0 - 1, 8, "Review score by days late", F["label"])
ws.write_row(B0, 8, ["Delivery", "From (days late)", "To (days late)", "Orders", "Avg Review", "1-2 Star %"], F["header"])
buckets = [("On time or early", -999, 0), ("1-3 days late", 1, 3), ("4-7 days late", 4, 7),
           ("8-14 days late", 8, 14), ("15+ days late", 15, 999)]
for i, (name, lo, hi) in enumerate(buckets):
    r = B0 + 1 + i
    sel = orders[orders.days_late.between(lo, hi)]
    rated = sel.review_score.dropna()
    rng_crit = f'Orders[Days Late],">="&{cell(r, 9)},Orders[Days Late],"<="&{cell(r, 10)}'
    ws.write_string(r, 8, name, F["text"])
    ws.write_number(r, 9, lo, F["text"])
    ws.write_number(r, 10, hi, F["text"])
    ws.write_formula(r, 11, f"=COUNTIFS({rng_crit})", F["int"], len(sel))
    ws.write_formula(r, 12, f"=AVERAGEIFS(Orders[Review Score],{rng_crit})", F["two_dp"], rated.mean())
    ws.write_formula(r, 13, f'=COUNTIFS({rng_crit},Orders[Review Score],"<=2")/COUNTIFS({rng_crit},Orders[Review Score],">=1")',
                     F["pct"], (rated <= 2).mean())
BF, BL = B0 + 1, B0 + len(buckets)
ws.set_column("A:A", 15)
ws.set_column("B:F", 12)
ws.set_column("I:I", 18)
ws.set_column("J:N", 12)
ws.freeze_panes(4, 0)

# ---------------------------------------------------------------- Data + Lookup
ws = wb.add_worksheet("Data")
rows = orders[[c for _, c, _, _ in DATA_COLUMNS]].astype(object).where(orders.notna(), None).values.tolist()
ws.add_table(0, 0, len(rows), len(DATA_COLUMNS) - 1, {
    "name": "Orders", "style": "Table Style Light 9", "data": rows,
    "columns": [{"header": h, "format": F[f] if f else None} for h, _, _, f in DATA_COLUMNS],
})
for i, (_, _, w, _) in enumerate(DATA_COLUMNS):
    ws.set_column(i, i, w)
ws.freeze_panes(1, 0)

ws = wb.add_worksheet("Lookup")
ws.add_table(0, 0, len(lookup), 1, {"name": "CategoryLookup", "style": "Table Style Light 9",
                                    "data": lookup.values.tolist(),
                                    "columns": [{"header": "Code"}, {"header": "English"}]})
ws.set_column("A:B", 45)
ws.freeze_panes(1, 0)

# ---------------------------------------------------------------- Summary
ws = ws_sum
ws.hide_gridlines(2)
ws.set_column("A:A", 2)
ws.set_column("B:F", 22)
ws.set_column("G:G", 2)
ws.write("B1", "Olist monthly tracker", F["title"])
ws.write("B2", "How did we do last month? Pick a month in the yellow cell; everything below updates.", F["subtitle"])
ws.write("B4", "Month:", F["label"])
default_month = months[-1]
ws.write("C4", default_month, F["input"])
ws.data_validation("C4", {"validate": "list", "source": f"=Monthly!$A${FIRST + 1}:$A${LAST + 1}"})
ws.write("D4", "Compared with:", F["label"])
ws.write_formula("E4", f'=IFERROR(INDEX(Monthly!$A${FIRST + 1}:$A${LAST + 1},MATCH(C4,Monthly!$A${FIRST + 1}:$A${LAST + 1},0)-1),"-")',
                 F["text"], months[-2])

cur, prev = orders[orders.purchase_month == months[-1]], orders[orders.purchase_month == months[-2]]
kpis = [  # label, current formula, previous formula, current value, previous value, formats, change kind
    ("Revenue", 'SUMIFS(Orders[Revenue],Orders[Month],{m})', cur.revenue.sum(), prev.revenue.sum(), "money", "pct"),
    ("Orders", 'COUNTIFS(Orders[Month],{m})', len(cur), len(prev), "int", "pct"),
    ("Avg Order Value", 'SUMIFS(Orders[Revenue],Orders[Month],{m})/COUNTIFS(Orders[Month],{m})',
     cur.revenue.mean(), prev.revenue.mean(), "money2", "pct"),
    ("Late Deliveries", 'AVERAGEIFS(Orders[Late],Orders[Month],{m})', cur.is_late.mean(), prev.is_late.mean(), "pct", "pts"),
    ("Avg Review Score", 'AVERAGEIFS(Orders[Review Score],Orders[Month],{m})',
     cur.review_score.mean(), prev.review_score.mean(), "two", "abs"),
]
trend_cols = {"Revenue": 2, "Orders": 1, "Avg Order Value": 3, "Late Deliveries": 5, "Avg Review Score": 6}
for i, (label, f, vc, vp, kind, chg) in enumerate(kpis):
    c = 1 + i
    ws.write(5, c, label, F["kpi_label"])
    ws.write_formula(6, c, "=" + f.format(m="$C$4"), F[f"kpi_{kind}"], vc)
    ws.write_formula(7, c, f'=IFERROR({f.format(m="$E$4")},"")', F[f"prev_{kind}"], vp)
    cur_ref, prev_ref = cell(6, c), cell(7, c)
    if chg == "pct":
        ws.write_formula(8, c, f'=IFERROR({cur_ref}/{prev_ref}-1,"")', F["chg_up_good"], vc / vp - 1)
    elif chg == "pts":
        ws.write_formula(8, c, f'=IFERROR(({cur_ref}-{prev_ref})*100,"")', F["chg_up_bad_pts"], (vc - vp) * 100)
    else:
        ws.write_formula(8, c, f'=IFERROR({cur_ref}-{prev_ref},"")', F["chg_up_good_abs"], vc - vp)
    tc = trend_cols[label]
    ws.add_sparkline(9, c, {"range": f"Monthly!{cell(FIRST, tc)}:{cell(LAST, tc)}", "series_color": BLUE,
                            "last_point": True, "last_color": ORANGE})
ws.set_row(6, 34)
ws.set_row(9, 30)
ws.write("B11", "Sparklines show all 20 months (Jan 2017 - Aug 2018), following the state filter on the Monthly tab.",
         F["subtitle"])


def small_chart(kind, title):
    ch = wb.add_chart({"type": kind})
    ch.set_title({"name": title, "name_font": {"size": 11, "bold": True}})
    ch.set_legend({"none": True})
    ch.set_size({"width": 470, "height": 290})
    ch.set_chartarea({"border": {"none": True}})
    return ch


ch = small_chart("line", "Revenue by month")
ch.add_series({"categories": ["Monthly", FIRST, 0, LAST, 0], "values": ["Monthly", FIRST, 2, LAST, 2],
               "line": {"color": BLUE, "width": 2}, "marker": {"type": "circle", "size": 4,
               "fill": {"color": BLUE}, "border": {"color": BLUE}}})
ch.set_y_axis({"num_format": '"R$"#,##0,"k"', "major_gridlines": {"visible": True, "line": {"color": GRID}}})
ch.set_x_axis({"num_font": {"rotation": -45}})
ws.insert_chart("B13", ch)

ch = small_chart("bar", "Late deliveries: 10 worst states")
ch.add_series({"categories": ["Delivery", SF, 0, SF + 9, 0], "values": ["Delivery", SF, 3, SF + 9, 3],
               "fill": {"color": ORANGE}, "gap": 50, "data_labels": {"value": True, "num_format": "0%"}})
ch.set_y_axis({"reverse": True})
ch.set_x_axis({"num_format": "0%", "major_gridlines": {"visible": True, "line": {"color": GRID}}})
ws.insert_chart("D13", ch, {"x_offset": 60})

ch = small_chart("column", "Review score by days late")
ch.add_series({"categories": ["Delivery", BF, 8, BL, 8], "values": ["Delivery", BF, 12, BL, 12],
               "points": [{"fill": {"color": BLUE}}] + [{"fill": {"color": ORANGE}}] * 4,
               "gap": 50, "data_labels": {"value": True, "num_format": "0.00"}})
ch.set_y_axis({"min": 0, "max": 5, "major_gridlines": {"visible": True, "line": {"color": GRID}}})
ws.insert_chart("B29", ch)

ws.write("D30", "How to read this", F["label"])
notes = [
    "Revenue = item price + freight, delivered orders only.",
    "Late = delivered on a later day than promised at checkout.",
    "Late orders average about 2.3 stars vs 4.3 on time.",
    "Red/amber/green on the Delivery tab: > 10% / 5-10% / < 5% late.",
    "Raw rows: Data tab (Orders table). Names: Lookup tab.",
]
for i, n in enumerate(notes):
    ws.write(30 + i, 3, "•  " + n, F["text"])
ws.activate()
wb.close()
print(f"Wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1e6:.1f} MB, {len(orders):,} order rows)")
