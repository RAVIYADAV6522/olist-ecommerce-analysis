# Olist E-commerce Analysis

What drives bad reviews in Brazilian e-commerce? An end-to-end analysis of ~100k Olist orders (2016–2018) using SQL, Python, Excel and Power BI.

> Work in progress. Findings and dashboard will be added here as each phase is completed.

## Dataset

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) on Kaggle: 9 linked CSVs covering orders, order items, customers, sellers, products, payments, reviews, geolocation and category translations.

The raw files are not committed. Download the zip from Kaggle and extract the CSVs into `data/raw/`.

## Business questions

- How did revenue and order volume trend month by month?
- Which product categories and states bring in the most revenue?
- Where are deliveries late, and which sellers and regions are responsible?
- How much does a late delivery hurt the review score?
- How many customers come back for a second order?
- How do customers pay, and how often do they use instalments?

## Project structure

```
data/raw/      Kaggle CSVs (not committed)
data/clean/    Query results and cleaned extracts
sql/           SQL query library, one business question per file
load_data.py   Builds the SQLite database from the raw CSVs
run_queries.py Runs the SQL library and saves each result as a CSV
notebooks/     Data-quality and exploratory analysis notebooks
excel/         Monthly tracker workbook
dashboard/     Power BI report and its source tables
images/        Charts and dashboard screenshots
```

## Tools

SQLite · Python (pandas, matplotlib) · Excel · Power BI Desktop

## How to run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python load_data.py     # builds olist.db from data/raw/ (about 6 seconds)
python run_queries.py   # runs every query in sql/ and saves results to data/clean/
```

See [`sql/schema.md`](sql/schema.md) for the tables, how they join, and the rules every query follows.
