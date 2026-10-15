"""Run every query in sql/ against olist.db and save each result to data/clean/.

Run from the project root, after load_data.py:
    python run_queries.py              # all queries
    python run_queries.py 05           # only files whose name starts with 05
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
DB_PATH = ROOT / "olist.db"
SQL_DIR = ROOT / "sql"
OUT_DIR = ROOT / "data" / "clean"


def main():
    if not DB_PATH.exists():
        raise SystemExit("olist.db not found. Run `python load_data.py` first.")

    prefix = sys.argv[1] if len(sys.argv) > 1 else ""
    files = sorted(SQL_DIR.glob(f"{prefix}*.sql"))
    if not files:
        raise SystemExit(f"No .sql files in {SQL_DIR} starting with '{prefix}'")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    pd.set_option("display.width", 160)
    pd.set_option("display.max_columns", 20)

    for path in files:
        df = pd.read_sql_query(path.read_text(), con)
        df.to_csv(OUT_DIR / f"{path.stem}.csv", index=False)
        print(f"\n=== {path.name} ({len(df)} rows) ===")
        print(df.head(12).to_string(index=False))

    con.close()


if __name__ == "__main__":
    main()
