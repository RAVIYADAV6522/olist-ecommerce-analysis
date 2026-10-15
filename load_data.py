"""Build olist.db (SQLite) from the 9 Olist CSVs in data/raw/.

Run from the project root:
    python load_data.py

Rebuilds the database from scratch every time, so it is safe to re-run.
"""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
RAW = ROOT / "data" / "raw"
DB_PATH = ROOT / "olist.db"

SCHEMA = """
CREATE TABLE category_translation (
    product_category_name          TEXT PRIMARY KEY,
    product_category_name_english  TEXT NOT NULL
);

CREATE TABLE customers (
    customer_id               TEXT PRIMARY KEY,
    customer_unique_id        TEXT NOT NULL,
    customer_zip_code_prefix  TEXT,
    customer_city             TEXT,
    customer_state            TEXT
);

CREATE TABLE sellers (
    seller_id               TEXT PRIMARY KEY,
    seller_zip_code_prefix  TEXT,
    seller_city             TEXT,
    seller_state            TEXT
);

-- No foreign key to category_translation: a few categories have no translation
-- (checked in the data-quality notebook), and some products have no category at all.
CREATE TABLE products (
    product_id                  TEXT PRIMARY KEY,
    product_category_name       TEXT,
    product_name_length         INTEGER,
    product_description_length  INTEGER,
    product_photos_qty          INTEGER,
    product_weight_g            REAL,
    product_length_cm           REAL,
    product_height_cm           REAL,
    product_width_cm            REAL
);

CREATE TABLE orders (
    order_id                       TEXT PRIMARY KEY,
    customer_id                    TEXT NOT NULL REFERENCES customers (customer_id),
    order_status                   TEXT NOT NULL,
    order_purchase_timestamp       TEXT NOT NULL,
    order_approved_at              TEXT,
    order_delivered_carrier_date   TEXT,
    order_delivered_customer_date  TEXT,
    order_estimated_delivery_date  TEXT
);

CREATE TABLE order_items (
    order_id             TEXT NOT NULL REFERENCES orders (order_id),
    order_item_id        INTEGER NOT NULL,
    product_id           TEXT NOT NULL REFERENCES products (product_id),
    seller_id            TEXT NOT NULL REFERENCES sellers (seller_id),
    shipping_limit_date  TEXT,
    price                REAL NOT NULL,
    freight_value        REAL NOT NULL,
    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE payments (
    order_id              TEXT NOT NULL REFERENCES orders (order_id),
    payment_sequential    INTEGER NOT NULL,
    payment_type          TEXT NOT NULL,
    payment_installments  INTEGER,
    payment_value         REAL NOT NULL,
    PRIMARY KEY (order_id, payment_sequential)
);

-- review_id alone is not unique in Olist: the same review can be attached to several orders.
CREATE TABLE reviews (
    review_id                TEXT NOT NULL,
    order_id                 TEXT NOT NULL REFERENCES orders (order_id),
    review_score             INTEGER NOT NULL,
    review_comment_title     TEXT,
    review_comment_message   TEXT,
    review_creation_date     TEXT,
    review_answer_timestamp  TEXT,
    PRIMARY KEY (review_id, order_id)
);

-- One row per (zip prefix, lat/lng) sample, so there is no natural key.
CREATE TABLE geolocation (
    geolocation_zip_code_prefix  TEXT NOT NULL,
    geolocation_lat              REAL,
    geolocation_lng              REAL,
    geolocation_city             TEXT,
    geolocation_state            TEXT
);

CREATE INDEX idx_orders_customer     ON orders (customer_id);
CREATE INDEX idx_orders_purchase     ON orders (order_purchase_timestamp);
CREATE INDEX idx_items_product       ON order_items (product_id);
CREATE INDEX idx_items_seller        ON order_items (seller_id);
CREATE INDEX idx_reviews_order       ON reviews (order_id);
CREATE INDEX idx_customers_unique    ON customers (customer_unique_id);
CREATE INDEX idx_geolocation_zip     ON geolocation (geolocation_zip_code_prefix);

-- One row per delivered order in the analysis window (Jan 2017 – Aug 2018), with
-- everything the notebooks, Excel tracker and Power BI dashboard need. The rules
-- behind each column are in sql/schema.md.
CREATE VIEW delivered_orders AS
WITH item_totals AS (
    SELECT
        order_id,
        COUNT(*)                        AS items,
        COUNT(DISTINCT seller_id)       AS sellers,
        SUM(price)                      AS product_value,
        SUM(freight_value)              AS freight_value,
        SUM(price + freight_value)      AS revenue
    FROM order_items
    GROUP BY order_id
),
first_item AS (
    SELECT order_id, product_id, seller_id
    FROM order_items
    WHERE order_item_id = 1
),
first_payment AS (
    SELECT p.order_id, p.payment_type, p.payment_installments
    FROM payments AS p
    WHERE p.payment_sequential = (SELECT MIN(payment_sequential) FROM payments WHERE order_id = p.order_id)
),
order_scores AS (
    SELECT order_id, AVG(review_score) AS review_score
    FROM reviews
    GROUP BY order_id
)
SELECT
    o.order_id,
    c.customer_unique_id,
    c.customer_city,
    c.customer_state,
    fi.seller_id,
    s.seller_state,
    fi.product_id,
    COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
    o.order_purchase_timestamp                                                    AS purchase_timestamp,
    date(o.order_purchase_timestamp)                                              AS purchase_date,
    strftime('%Y-%m', o.order_purchase_timestamp)                                 AS purchase_month,
    it.items,
    it.sellers,
    ROUND(it.product_value, 2)                                                    AS product_value,
    ROUND(it.freight_value, 2)                                                    AS freight_value,
    ROUND(it.revenue, 2)                                                          AS revenue,
    fp.payment_type,
    fp.payment_installments,
    date(o.order_delivered_customer_date)                                         AS delivered_date,
    date(o.order_estimated_delivery_date)                                         AS estimated_date,
    ROUND(julianday(o.order_delivered_customer_date)
        - julianday(o.order_purchase_timestamp), 1)                               AS delivery_days,
    CAST(julianday(date(o.order_delivered_customer_date))
        - julianday(date(o.order_estimated_delivery_date)) AS INTEGER)            AS days_late,
    CASE WHEN o.order_delivered_customer_date IS NULL THEN NULL
         WHEN date(o.order_delivered_customer_date)
            > date(o.order_estimated_delivery_date) THEN 1 ELSE 0 END             AS is_late,
    sc.review_score
FROM orders AS o
JOIN customers AS c                 ON c.customer_id = o.customer_id
JOIN item_totals AS it              ON it.order_id = o.order_id
JOIN first_item AS fi               ON fi.order_id = o.order_id
JOIN sellers AS s                   ON s.seller_id = fi.seller_id
JOIN products AS p                  ON p.product_id = fi.product_id
LEFT JOIN category_translation AS t ON t.product_category_name = p.product_category_name
LEFT JOIN first_payment AS fp       ON fp.order_id = o.order_id
LEFT JOIN order_scores AS sc        ON sc.order_id = o.order_id
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp <  '2018-09-01';
"""

# Load order matters: parent tables before the tables that reference them.
# (table name, CSV file, date columns, column renames)
TABLES = [
    ("category_translation", "product_category_name_translation.csv", [], {}),
    ("customers", "olist_customers_dataset.csv", [], {}),
    ("sellers", "olist_sellers_dataset.csv", [], {}),
    ("products", "olist_products_dataset.csv", [], {
        "product_name_lenght": "product_name_length",
        "product_description_lenght": "product_description_length",
    }),
    ("orders", "olist_orders_dataset.csv", [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ], {}),
    ("order_items", "olist_order_items_dataset.csv", ["shipping_limit_date"], {}),
    ("payments", "olist_order_payments_dataset.csv", [], {}),
    ("reviews", "olist_order_reviews_dataset.csv", [
        "review_creation_date",
        "review_answer_timestamp",
    ], {}),
    ("geolocation", "olist_geolocation_dataset.csv", [], {}),
]

# Zip prefixes have leading zeros ("01037"), so they must stay text.
TEXT_COLUMNS = {
    "customer_zip_code_prefix": str,
    "seller_zip_code_prefix": str,
    "geolocation_zip_code_prefix": str,
}


def read_csv(filename, date_columns, renames):
    # utf-8-sig strips the byte-order mark at the start of the translation file.
    df = pd.read_csv(RAW / filename, dtype=TEXT_COLUMNS, encoding="utf-8-sig")
    df = df.rename(columns=renames)
    for col in date_columns:
        # Store dates as ISO text ("2017-10-02 10:56:33") so SQLite's date functions work on them.
        df[col] = pd.to_datetime(df[col]).dt.strftime("%Y-%m-%d %H:%M:%S")
    return df.astype(object).where(df.notna(), None)


def main():
    missing = [f for _, f, _, _ in TABLES if not (RAW / f).exists()]
    if missing:
        raise SystemExit(f"Missing files in {RAW}: {', '.join(missing)}")

    DB_PATH.unlink(missing_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)

    for table, filename, date_columns, renames in TABLES:
        df = read_csv(filename, date_columns, renames)
        columns = ", ".join(df.columns)
        placeholders = ", ".join("?" * len(df.columns))
        con.executemany(
            f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
            df.itertuples(index=False, name=None),
        )
        print(f"{table:<22} {len(df):>9,} rows")

    con.commit()
    con.close()
    print(f"\nBuilt {DB_PATH.name}")


if __name__ == "__main__":
    main()
