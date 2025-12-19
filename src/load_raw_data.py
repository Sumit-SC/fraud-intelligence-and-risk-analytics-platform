import os
from typing import Dict

import pandas as pd
from sqlalchemy import create_engine, text


def get_mysql_url() -> str:
    """
    Build a SQLAlchemy MySQL connection URL from environment variables.

    Expected env vars (with safe defaults for local dev):
      - MYSQL_HOST (default: localhost)
      - MYSQL_PORT (default: 3306)
      - MYSQL_USER (default: root)
      - MYSQL_PASSWORD (default: empty)
      - MYSQL_DB (default: fraud_db)
    """
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "sanalyst")
    db = os.getenv("MYSQL_DB", "fraud_db")

    # mysql-connector-python driver
    if password:
        return f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{db}"
    return f"mysql+mysqlconnector://{user}@{host}:{port}/{db}"


def load_csv_to_table(engine, csv_path: str, table_name: str) -> int:
    """
    Load a CSV file into a MySQL table using pandas.to_sql (append mode).

    No cleaning, casting, or transformations are applied.
    """
    df = pd.read_csv(csv_path)
    df.to_sql(table_name, con=engine, if_exists="append", index=False)
    return len(df)


def main() -> None:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(base_dir, "data", "raw")

    mysql_url = get_mysql_url()
    engine = create_engine(mysql_url)

    # Ensure raw tables exist (DDL should already have been run separately)
    # We only append data here.

    file_table_map: Dict[str, str] = {
        os.path.join(raw_dir, "merchants", "merchants.csv"): "raw_merchants",
        os.path.join(raw_dir, "devices", "devices.csv"): "raw_devices",
        os.path.join(raw_dir, "cards", "cards.csv"): "raw_cards",
        os.path.join(raw_dir, "rules", "rule_hits.csv"): "raw_rule_hits",
        os.path.join(
            raw_dir, "investigations", "investigator_notes.csv"
        ): "raw_investigator_notes",
    }

    # Transactions: all monthly files in data/raw/transactions
    transactions_dir = os.path.join(raw_dir, "transactions")
    for filename in sorted(os.listdir(transactions_dir)):
        if filename.lower().endswith(".csv"):
            path = os.path.join(transactions_dir, filename)
            file_table_map[path] = "raw_transactions"

    row_counts: Dict[str, int] = {}

    with engine.begin() as conn:
        # Optional: clear existing data in raw tables before load
        for table in [
            "raw_transactions",
            "raw_merchants",
            "raw_devices",
            "raw_cards",
            "raw_rule_hits",
            "raw_investigator_notes",
        ]:
            conn.execute(text(f"TRUNCATE TABLE {table}"))

        for csv_path, table_name in file_table_map.items():
            if not os.path.exists(csv_path):
                print(f"[WARN] File not found, skipping: {csv_path}")
                continue

            print(f"[INFO] Loading {csv_path} into {table_name} ...")
            df = pd.read_csv(csv_path)
            df.to_sql(table_name, con=conn, if_exists="append", index=False)
            loaded = len(df)
            row_counts[table_name] = row_counts.get(table_name, 0) + loaded

    # Log final row counts from the database for verification
    with engine.connect() as conn:
        print("\n[INFO] Row counts after load:")
        for table in sorted(
            {
                "raw_transactions",
                "raw_merchants",
                "raw_devices",
                "raw_cards",
                "raw_rule_hits",
                "raw_investigator_notes",
            }
        ):
            result = conn.execute(text(f"SELECT COUNT(*) AS cnt FROM {table}"))
            db_count = result.scalar_one()
            loaded_count = row_counts.get(table, 0)
            print(
                f"  - {table}: db_count={db_count}, loaded_in_this_run={loaded_count}"
            )


if __name__ == "__main__":
    main()


