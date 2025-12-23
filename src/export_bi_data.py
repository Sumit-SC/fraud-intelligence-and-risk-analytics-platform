"""
Export BI-ready data from feat_transactions_risk to CSV.

This script exports a subset of columns from feat_transactions_risk for Power BI,
keeping all fraud transactions and sampling non-fraud transactions to keep
the dataset manageable (300k-500k rows total).
"""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


def get_mysql_url() -> str:
    """
    Build a SQLAlchemy MySQL connection URL from environment variables.

    Expected env vars (with safe defaults for local dev):
      - MYSQL_HOST (default: localhost)
      - MYSQL_PORT (default: 3306)
      - MYSQL_USER (default: root)
      - MYSQL_PASSWORD (default: sanalyst)
      - MYSQL_DB (default: fraud_db)
    """
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "sanalyst")
    db = os.getenv("MYSQL_DB", "fraud_db")

    if password:
        return f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{db}"
    return f"mysql+mysqlconnector://{user}@{host}:{port}/{db}"


def export_bi_data(
    target_total_rows: int = 400000,
    output_path: str = "data/bi/feat_transactions_risk_bi.csv",
) -> None:
    """
    Export BI-ready data from feat_transactions_risk.

    Args:
        target_total_rows: Target total number of rows (default: 400k)
        output_path: Path to output CSV file
    """
    # Load environment variables
    load_dotenv()

    # Create output directory if it doesn't exist
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Connect to MySQL
    mysql_url = get_mysql_url()
    engine = create_engine(mysql_url)

    print("=" * 60)
    print("BI Data Export")
    print("=" * 60)

    # Define columns to export
    columns = [
        # Identifiers & time
        "txn_id_clean",
        "txn_ts",
        "txn_date",
        # Transaction attributes
        "amount",
        "channel_std",
        "country_std",
        # Fraud & outcomes
        "is_fraud",
        "is_declined",
        # Behavioral features
        "txns_last_24h",
        "amount_vs_card_avg",
        "declined_txns_last_24h",
        # Merchant context
        "merchant_id_clean",
        "merchant_risk_tier",
        "merchant_txn_count_30d",
        "merchant_fraud_rate_30d",
        # Flags
        "is_high_risk_merchant",
        "is_emulator_device",
    ]

    columns_str = ", ".join(columns)

    # Build query: get all fraud + sample non-fraud
    query = f"""
    SELECT {columns_str}
    FROM feat_transactions_risk
    WHERE is_fraud = 1
    
    UNION ALL
    
    SELECT {columns_str}
    FROM feat_transactions_risk
    WHERE is_fraud = 0
    ORDER BY RAND()
    LIMIT :sample_limit
    """

    # First, get counts to determine sampling
    print("\n1. Checking data availability...")
    count_query = """
    SELECT 
        SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) as fraud_count,
        SUM(CASE WHEN is_fraud = 0 THEN 1 ELSE 0 END) as non_fraud_count,
        COUNT(*) as total_count
    FROM feat_transactions_risk
    """
    
    with engine.connect() as conn:
        count_result = pd.read_sql(text(count_query), conn)
        fraud_count = int(count_result.iloc[0]["fraud_count"])
        non_fraud_count = int(count_result.iloc[0]["non_fraud_count"])
        total_count = int(count_result.iloc[0]["total_count"])

    print(f"   Total rows in feat_transactions_risk: {total_count:,}")
    print(f"   Fraud rows: {fraud_count:,}")
    print(f"   Non-fraud rows: {non_fraud_count:,}")

    # Calculate how many non-fraud rows to sample
    target_non_fraud_rows = max(0, target_total_rows - fraud_count)
    
    if target_non_fraud_rows > non_fraud_count:
        print(f"\n   Warning: Target requires {target_non_fraud_rows:,} non-fraud rows,")
        print(f"   but only {non_fraud_count:,} available. Using all non-fraud rows.")
        target_non_fraud_rows = non_fraud_count

    print(f"\n2. Sampling strategy:")
    print(f"   Keeping all fraud rows: {fraud_count:,}")
    print(f"   Sampling non-fraud rows: {target_non_fraud_rows:,}")
    print(f"   Expected total: {fraud_count + target_non_fraud_rows:,}")

    # Build the actual query with proper sampling
    # MySQL doesn't support UNION ALL with different LIMITs easily, so we'll do it in two steps
    print("\n3. Loading fraud transactions...")
    fraud_query = f"""
    SELECT {columns_str}
    FROM feat_transactions_risk
    WHERE is_fraud = 1
    """
    
    fraud_df = pd.read_sql(text(fraud_query), engine)
    print(f"   Loaded {len(fraud_df):,} fraud transactions")

    print("\n4. Sampling non-fraud transactions...")
    non_fraud_query = f"""
    SELECT {columns_str}
    FROM feat_transactions_risk
    WHERE is_fraud = 0
    ORDER BY RAND()
    LIMIT {target_non_fraud_rows}
    """
    
    non_fraud_df = pd.read_sql(text(non_fraud_query), engine)
    print(f"   Sampled {len(non_fraud_df):,} non-fraud transactions")

    # Combine dataframes
    print("\n5. Combining datasets...")
    bi_df = pd.concat([fraud_df, non_fraud_df], ignore_index=True)
    
    # Shuffle the combined dataset
    bi_df = bi_df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    print(f"   Total rows: {len(bi_df):,}")
    print(f"   Fraud rows: {bi_df['is_fraud'].sum():,}")
    print(f"   Non-fraud rows: {(bi_df['is_fraud'] == 0).sum():,}")

    # Export to CSV
    print(f"\n6. Exporting to {output_path}...")
    bi_df.to_csv(output_path, index=False)
    
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"   Export complete! File size: {file_size_mb:.2f} MB")

    print("\n" + "=" * 60)
    print("Export Summary")
    print("=" * 60)
    print(f"Output file: {output_path}")
    print(f"Total rows: {len(bi_df):,}")
    print(f"Fraud rows: {bi_df['is_fraud'].sum():,} ({bi_df['is_fraud'].mean()*100:.2f}%)")
    print(f"Non-fraud rows: {(bi_df['is_fraud'] == 0).sum():,} ({(bi_df['is_fraud'] == 0).mean()*100:.2f}%)")
    print(f"Columns exported: {len(columns)}")
    print("=" * 60)
    
    # Compact tabular preview to verify structure in the console
    print("\nData Preview (first 2 rows):")
    print("-" * 60)
    with pd.option_context(
        "display.max_columns", None,
        "display.width", 120,
        "display.max_colwidth", 30,
    ):
        print(bi_df.head(2))
    print("-" * 60)


if __name__ == "__main__":
    export_bi_data()
    print("\nExport complete!")

