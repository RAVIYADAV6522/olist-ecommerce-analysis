# Power BI build guide

This guide builds a 4-page report from the CSVs in this folder. It takes about 3–4 hours the first time. Save the result as `dashboard/olist_dashboard.pbix`.

**You need a Windows PC.** Power BI Desktop does not run on macOS. Use a college lab PC, a Windows laptop, or Windows 11 in a virtual machine (Parallels or UTM on a Mac). Copy this repo's `dashboard/` folder onto it.

## What is in this folder

| File | Rows | What it is |
|---|---:|---|
| `orders_fact.csv` | 96,211 | One row per delivered order, Jan 2017 – Aug 2018 |
| `dim_customer.csv` | 93,104 | One row per real customer, with state, region and repeat flag |
| `dim_product.csv` | 31,029 | One row per product, with English category |
| `dim_seller.csv` | 2,936 | One row per seller, with state and region |
| `dim_date.csv` | 608 | One row per day, Jan 2017 – Aug 2018 |
| `measures.dax` | — | The DAX measures to paste in, with the expected value of each |
| `olist_theme.json` | — | Colours and fonts that match the notebook charts |

## 1. Load the data (15 min)

1. **Home → Get data → Text/CSV**, pick `orders_fact.csv`, then **Transform Data** (not Load).
2. In Power Query, check these column types and fix any that are wrong:
   - `purchase_date`, `delivered_date`, `estimated_date` → **Date**
   - `revenue`, `product_value`, `freight_value` → **Fixed decimal number**
   - `delivery_days`, `review_score` → **Decimal number**
   - `items`, `sellers`, `payment_installments`, `days_late`, `is_late`, `purchase_hour`, `delay_bucket_order` → **Whole number**
   - all ID columns → **Text**
3. **Home → New Source → Text/CSV** for each of the 4 `dim_` files. In `dim_date`, set `date` and `month_start` to **Date**.
4. **Close & Apply**.

## 2. Build the star schema (15 min)

1. Open **Model view**. Delete any relationships Power BI guessed on its own.
2. Drag to create these 4 relationships. Each one is **one-to-many**, single direction, from the dimension (1) to the fact (*):

   | From (one side) | To (many side) |
   |---|---|
   | `dim_customer[customer_unique_id]` | `orders_fact[customer_unique_id]` |
   | `dim_product[product_id]` | `orders_fact[product_id]` |
   | `dim_seller[seller_id]` | `orders_fact[seller_id]` |
   | `dim_date[date]` | `orders_fact[purchase_date]` |

3. Select `dim_date` → **Table tools → Mark as date table** → column `date`.
4. Set sort orders, so text columns do not sort alphabetically:
   - `dim_date[month_name]` → **Sort by column** → `month_number`
   - `dim_date[weekday_name]` → **Sort by column** → `weekday_number`
   - `orders_fact[delay_bucket]` → **Sort by column** → `delay_bucket_order`
5. Set data categories so the maps work: `dim_customer[customer_map_location]` and `dim_seller[seller_map_location]` → **Column tools → Data category → Place**.
6. Hide the key columns in the fact table (right-click → **Hide in report view**) so report builders use the dimensions.

Take a screenshot of the Model view and save it as `images/powerbi_model.png`. Interviewers like seeing the star schema.

## 3. Add the measures (20 min)

1. **Home → Enter data**, name the table `_Measures`, **Load**.
2. Select `_Measures` → **New measure**, and paste each measure from `measures.dax` one at a time.
3. Format them: `Total Revenue`, `Avg Order Value` → Currency (R$), 0 and 2 decimals. `Late Delivery %`, `Repeat Customer %`, `Low Review %`, `Revenue MoM %` → Percentage, 1 decimal. `Avg Review Score` → 2 decimals.
4. Delete the empty `Column1` from `_Measures`. It then moves to the top of the field list.
5. **Check:** put each measure in a Card with no filters. The numbers must match the comments in `measures.dax` (R$15,373,120 · 96,211 orders · R$159.79 · 6.79% · 4.16 · 3.0%). If one does not match, a column type or relationship is wrong.

## 4. Apply the theme (2 min)

**View → Themes → Browse for themes** → `olist_theme.json`. Blue means normal and orange means late or problem, the same as in the notebook charts.

## 5. Build the 4 pages (2–3 hours)

Use a 1280 × 720 page. Put a title text box at the top of every page that **states the finding**, not the topic. For example: "Late orders get 2 stars fewer", not "Reviews".

### Page 1 · Executive overview

| Visual | Fields |
|---|---|
| 5 Cards across the top | `Total Revenue`, `Orders`, `Avg Order Value`, `Late Delivery %`, `Avg Review Score` |
| Line chart | X: `dim_date[month_start]` (turn off date hierarchy) · Y: `Total Revenue` |
| Filled map | Location: `dim_customer[customer_map_location]` · Tooltips: `Total Revenue`, `Late Delivery %` |
| Slicer (Between) | `dim_date[date]` |

Title: *R$15.4M in 20 months: revenue grew 2.8x, then levelled off at about R$1M a month*

### Page 2 · Sales

| Visual | Fields |
|---|---|
| Clustered bar chart (top 10) | Y: `dim_product[category]` · X: `Total Revenue` · Filter pane → Top N = 10 by `Total Revenue` |
| Treemap | Group: `dim_customer[customer_state]` · Values: `Total Revenue` |
| Donut chart | Legend: `orders_fact[payment_type]` · Values: `Orders` |
| Line chart | X: `dim_date[month_start]` · Y: `Avg Order Value` |

Clicking a category bar should cross-filter the other three visuals. This is the default; check it under **Format → Edit interactions**.

Title: *8 categories bring in 54% of revenue; São Paulo alone brings in 37%*

### Page 3 · Delivery performance

| Visual | Fields |
|---|---|
| Filled map | Location: `dim_customer[customer_map_location]` · Colour saturation: `Late Delivery %` (Format → Fill colours → fx → gradient white to orange) |
| Column chart (histogram) | X: `orders_fact[days_late]` · Y: `Orders` · Filter `days_late` between −40 and 30 |
| Line chart | X: `dim_date[month_start]` · Y: `Late Delivery %` |
| Slicer (dropdown) | `dim_customer[customer_state]` |

Title: *North-east customers get late orders up to 5x as often as São Paulo, and late rates spike after big promotions*

### Page 4 · Customers & reviews

| Visual | Fields |
|---|---|
| Column chart | X: `orders_fact[delay_bucket]` · Y: `Avg Review Score` · data labels on |
| Column chart | X: `orders_fact[review_score]` · Y: `Orders` |
| Card | `Repeat Customer %` |
| Table | `dim_customer[customer_city]`, `Total Revenue`, `Orders` · Top N = 10 by revenue |
| Slicer (tile) | `orders_fact[review_score]` |

Title: *A late order loses 1 to 2.5 stars; late orders cause a third of all 1–2 star reviews*

## 6. Polish (30 min)

- [ ] **Sync slicers:** View → Sync slicers, sync the date slicer across all 4 pages.
- [ ] **Navigation:** Insert → Buttons → Navigator → **Page navigator** at the top of each page.
- [ ] Hide the visual header icons you don't need (Format → Visual header).
- [ ] Every axis title says the unit ("Revenue (R$)", "Orders", "Late %").
- [ ] Save as `dashboard/olist_dashboard.pbix`.

## 7. Publish and share

1. Sign in to Power BI Desktop with your **college email**. Personal Gmail and Outlook addresses are not accepted.
2. **Home → Publish → My workspace**.
3. In the browser, open the report → **File → Embed report → Publish to web (public)**. Copy the link into the main README.
   - Many colleges switch "Publish to web" off. If the option is missing or greyed out, use the fallback below; it is just as good for a portfolio.
4. **Fallback:** export each page as a PNG (File → Export → PDF, or take a screenshot at 100% zoom) and save them as `images/powerbi_page1_overview.png` … `images/powerbi_page4_reviews.png`. Commit the `.pbix` too.
5. Record a 60-second screen capture clicking through the 4 pages and using the slicers. On Windows use **Win + Alt + R** (Xbox Game Bar), or use [Loom](https://www.loom.com). Upload it to YouTube (unlisted) or Loom and put the link in the README.

## Interview questions this dashboard should prepare you for

- **Why a star schema?** Each dimension filters the fact table in one direction, so measures are fast and slicers behave predictably. Customer, product, seller and date can each slice revenue without double counting.
- **Why is Late Delivery % not just AVERAGE(is_late)?** It is, in effect, but writing it with `CALCULATE` and an explicit denominator makes the exclusion of the 8 undelivered orders visible to anyone reading the measure.
- **What does `Repeat Customer %` do differently from a column?** It recalculates for the current filter context: filter to one state and it gives that state's repeat rate. A calculated column would be fixed at load time.
- **What is `DATEADD` doing in `Revenue Prior Month`?** It shifts the date filter back one month, which only works because `dim_date` is marked as a date table with no gaps.
