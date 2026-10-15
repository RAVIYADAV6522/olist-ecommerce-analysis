# Database schema

`olist.db` is a SQLite database built by `load_data.py` from the 9 Olist CSVs. Rebuild it any time with `python load_data.py`.

## Tables

| Table | Rows | Primary key | Joins to |
|---|---:|---|---|
| `orders` | 99,441 | `order_id` | `customers` on `customer_id` |
| `order_items` | 112,650 | `order_id`, `order_item_id` | `orders`, `products`, `sellers` |
| `payments` | 103,886 | `order_id`, `payment_sequential` | `orders` |
| `reviews` | 99,224 | `review_id`, `order_id` | `orders` |
| `customers` | 99,441 | `customer_id` | `geolocation` on zip prefix |
| `sellers` | 3,095 | `seller_id` | `geolocation` on zip prefix |
| `products` | 32,951 | `product_id` | `category_translation` on `product_category_name` |
| `category_translation` | 71 | `product_category_name` | — |
| `geolocation` | 1,000,163 | none (many rows per zip prefix) | — |

## View: `delivered_orders`

One row per delivered order purchased Jan 2017 – Aug 2018 (96,211 rows, R$15.37M revenue), with the rules below already applied. The notebooks, the Excel tracker and the Power BI tables are all built from it, so every tool reports the same numbers.

| Column | Meaning |
|---|---|
| `customer_unique_id`, `customer_city`, `customer_state` | The real customer and where they live |
| `seller_id`, `seller_state`, `product_id`, `category` | From the order's first item (English category name, else Portuguese, else `unknown`) |
| `purchase_timestamp`, `purchase_date`, `purchase_month` | When the order was placed |
| `items`, `sellers` | Number of items and of distinct sellers in the order |
| `product_value`, `freight_value`, `revenue` | Sum of item prices, of freight, and of both (R$) |
| `payment_type`, `payment_installments` | From the order's first payment |
| `delivered_date`, `estimated_date` | Calendar dates the order arrived and was promised |
| `delivery_days` | Days from purchase to delivery |
| `days_late` | Delivered date minus estimated date; negative = early |
| `is_late` | 1 if delivered on a later day than estimated, 0 if not, blank if no delivery date (8 orders) |
| `review_score` | Average review score for the order; blank for 643 orders with no review |

## How the tables join

```
customers ──< orders ──< order_items >── products >── category_translation
                 │             │
                 │             └──────>── sellers
                 ├──< payments
                 └──< reviews
```

`──<` means one-to-many: one customer ID has many orders (in practice one, see below), one order has many items, payments and reviews.

## Rules every query follows

| Rule | Why |
|---|---|
| Revenue = `price + freight_value` from `order_items` | What the customer paid for the goods and shipping. Close to `payments.payment_value`, but available per item and per seller. |
| Only `order_status = 'delivered'` | The other 3% are cancelled, unavailable or still in transit, so they were never real sales. |
| Only purchases from **Jan 2017 to Aug 2018** | 2016 has 329 orders across 3 months and Sep–Oct 2018 has 20. Including them makes trends spike at the edges. |
| Count people with `customer_unique_id` | `customer_id` is created fresh for every order, so counting it makes every customer look new. |
| Late = `date(delivered) > date(estimated)` | The estimated date has no time of day; comparing timestamps would mark same-day deliveries late. |
| Average reviews per order before averaging across orders | 547 orders have more than one review. |

## Gotchas in the raw data

- Zip prefixes have leading zeros (`01037`), so they are stored as text.
- The products CSV misspells `product_name_lenght` and `product_description_lenght`; the loader renames them to `..._length`.
- `review_id` is not unique on its own: the same review can be attached to several orders.
- 610 products have no category, and 13 products use 2 categories with no English name (`pc_gamer`, `portateis_cozinha_e_preparadores_de_alimentos`).
- 775 orders have no items at all; they drop out of every revenue query automatically through the inner join.

## Query library

| File | Business question | SQL shown |
|---|---|---|
| `01_monthly_revenue.sql` | Monthly revenue and order count | JOIN, GROUP BY, `strftime` |
| `02_top_categories.sql` | Top 10 categories by revenue | 3 JOINs incl. LEFT JOIN, COALESCE, LIMIT |
| `03_revenue_by_state.sql` | Revenue and average order value by state | JOIN, aggregates, HAVING |
| `04_late_delivery_by_state.sql` | Late-delivery rate by state | CASE WHEN inside aggregates, `julianday` |
| `05_review_score_by_delay.sql` | Review score by how late the order was | CTEs, CASE buckets, GROUP BY derived column |
| `06_repeat_customers.sql` | Share of customers with more than one order | CTE, COUNT DISTINCT |
| `07_top_sellers_by_state.sql` | Top 3 sellers in each state | `RANK() OVER (PARTITION BY ...)` |
| `08_cumulative_revenue.sql` | Running total and month-on-month growth | `SUM() OVER (ORDER BY ...)`, `LAG()` |
| `09_payment_mix.sql` | Payment methods and instalment use | Percent of total with `SUM() OVER ()` |
| `10_data_quality_checks.sql` | What is wrong in the raw data | UNION ALL, NOT EXISTS |
| `11_freight_share_by_category.sql` | Where shipping is the biggest share of the bill | Ratio of sums, HAVING threshold |
| `12_delivery_by_seller_state.sql` | Shipping speed and late rate by seller state | SELECT DISTINCT in a CTE, date arithmetic |
| `13_review_by_sellers_in_order.sql` | Reviews for single- vs multi-seller orders | Two CTEs joined, COUNT DISTINCT per order |
| `14_orders_by_weekday_hour.sql` | Orders by day of week and hour | `strftime('%w')`, `strftime('%H')`, CAST |
| `15_worst_reviewed_categories.sql` | Categories with the most 1-star reviews | Join condition on first item, two CTEs |

Run them all and save results to `data/clean/` with `python run_queries.py`.
