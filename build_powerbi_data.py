"""Export star-schema CSVs for the Power BI dashboard into dashboard/.

Run from the project root, after load_data.py:
    python build_powerbi_data.py

orders_fact.csv          one row per delivered order (Jan 2017 – Aug 2018)
dim_customer.csv         one row per real customer (customer_unique_id)
dim_product.csv          one row per product, with English category
dim_seller.csv           one row per seller
dim_date.csv             one row per calendar day, Jan 2017 – Aug 2018
"""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
OUT = ROOT / "dashboard"

REGIONS = {
    "North": ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
    "Northeast": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "Center-West": ["DF", "GO", "MT", "MS"],
    "Southeast": ["ES", "MG", "RJ", "SP"],
    "South": ["PR", "RS", "SC"],
}
REGION_OF = {state: region for region, states in REGIONS.items() for state in states}
STATE_NAMES = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia", "CE": "Ceará",
    "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul", "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
    "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina",
    "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins",
}


def add_geo(df, state_col, prefix):
    df[f"{prefix}_state_name"] = df[state_col].map(STATE_NAMES)
    df[f"{prefix}_region"] = df[state_col].map(REGION_OF)
    # "São Paulo, Brazil" lets the Power BI map place the state without guessing the country.
    df[f"{prefix}_map_location"] = df[f"{prefix}_state_name"] + ", Brazil"
    return df


def main():
    con = sqlite3.connect(ROOT / "olist.db")
    fact = pd.read_sql_query("SELECT * FROM delivered_orders", con)

    fact_cols = ["order_id", "customer_unique_id", "product_id", "seller_id", "purchase_date",
                 "purchase_timestamp", "items", "sellers", "product_value", "freight_value", "revenue",
                 "payment_type", "payment_installments", "delivered_date", "estimated_date",
                 "delivery_days", "days_late", "is_late", "review_score"]
    fact = fact[fact_cols].assign(
        purchase_hour=pd.to_datetime(fact.purchase_timestamp).dt.hour,
        delay_bucket=pd.cut(fact.days_late, [-10_000, 0, 3, 7, 14, 10_000],
                            labels=["On time or early", "1-3 days late", "4-7 days late",
                                    "8-14 days late", "15+ days late"]),
    ).drop(columns="purchase_timestamp").astype({"days_late": "Int64", "is_late": "Int64"})
    # Power BI sorts text alphabetically; "Sort by column" on this keeps the buckets in order.
    fact["delay_bucket_order"] = fact.delay_bucket.cat.codes.replace(-1, pd.NA).astype("Int64") + 1

    customers = pd.read_sql_query("""
        SELECT customer_unique_id, MIN(customer_city) AS customer_city, MIN(customer_state) AS customer_state
        FROM customers GROUP BY customer_unique_id
    """, con)
    customers = customers[customers.customer_unique_id.isin(fact.customer_unique_id)]
    orders_per_customer = fact.groupby("customer_unique_id").size()
    customers["is_repeat_customer"] = customers.customer_unique_id.map(orders_per_customer).gt(1).astype(int)
    customers = add_geo(customers, "customer_state", "customer")

    products = pd.read_sql_query("""
        SELECT p.product_id,
               COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
               p.product_photos_qty, p.product_weight_g
        FROM products AS p
        LEFT JOIN category_translation AS t ON t.product_category_name = p.product_category_name
    """, con)
    products = products[products.product_id.isin(fact.product_id)]
    products["category"] = products.category.str.replace("_", " ").str.capitalize()

    sellers = pd.read_sql_query("SELECT seller_id, seller_city, seller_state FROM sellers", con)
    sellers = add_geo(sellers[sellers.seller_id.isin(fact.seller_id)], "seller_state", "seller")
    con.close()

    dates = pd.DataFrame({"date": pd.date_range("2017-01-01", "2018-08-31", freq="D")})
    dates = dates.assign(
        year=dates.date.dt.year,
        quarter="Q" + dates.date.dt.quarter.astype(str),
        month_number=dates.date.dt.month,
        month_name=dates.date.dt.strftime("%b"),
        year_month=dates.date.dt.strftime("%Y-%m"),
        month_start=dates.date.dt.to_period("M").dt.start_time.dt.date,
        weekday_number=dates.date.dt.dayofweek + 1,  # 1 = Monday
        weekday_name=dates.date.dt.strftime("%a"),
        is_weekend=(dates.date.dt.dayofweek >= 5).astype(int),
    )
    dates["date"] = dates.date.dt.date

    OUT.mkdir(exist_ok=True)
    for name, df in [("orders_fact", fact), ("dim_customer", customers), ("dim_product", products),
                     ("dim_seller", sellers), ("dim_date", dates)]:
        df.to_csv(OUT / f"{name}.csv", index=False)
        print(f"{name:<14} {len(df):>7,} rows  {(OUT / f'{name}.csv').stat().st_size / 1e6:5.1f} MB")

    # Every fact key must exist in its dimension, or Power BI shows a blank member.
    assert fact.customer_unique_id.isin(customers.customer_unique_id).all()
    assert fact.product_id.isin(products.product_id).all()
    assert fact.seller_id.isin(sellers.seller_id).all()
    assert pd.to_datetime(fact.purchase_date).dt.date.isin(dates.date).all()
    assert customers.customer_unique_id.is_unique and products.product_id.is_unique and sellers.seller_id.is_unique


if __name__ == "__main__":
    main()
