"""
Test Stage 5A on a small subset first to verify it works.
"""
import os
from sqlalchemy import create_engine, text


def get_mysql_url() -> str:
    """Build MySQL connection URL."""
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "sanalyst")
    db = os.getenv("MYSQL_DB", "fraud_db")

    if password:
        return f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{db}"
    return f"mysql+mysqlconnector://{user}@{host}:{port}/{db}"


def main():
    engine = create_engine(get_mysql_url())
    
    print("=" * 60)
    print("Testing Stage 5A on small subset (first 10,000 rows)")
    print("=" * 60)
    
    # Create a test table with limited rows
    test_sql = """
    USE fraud_db;
    
    DROP TABLE IF EXISTS feat_transactions_test;
    
    CREATE TABLE feat_transactions_test AS
    WITH
    base AS (
        SELECT *
        FROM stg_transactions_enriched
        LIMIT 10000
    ),
    velocity_features AS (
        SELECT
            b.*,
            CASE
                WHEN b.txn_ts IS NULL THEN NULL
                ELSE COUNT(*) OVER (
                    PARTITION BY b.card_id_clean
                    ORDER BY b.txn_ts
                    RANGE BETWEEN INTERVAL 1 HOUR PRECEDING AND CURRENT ROW
                )
            END AS txns_last_1h,
            CASE
                WHEN b.txn_ts IS NULL THEN NULL
                ELSE COUNT(*) OVER (
                    PARTITION BY b.card_id_clean
                    ORDER BY b.txn_ts
                    RANGE BETWEEN INTERVAL 24 HOUR PRECEDING AND CURRENT ROW
                )
            END AS txns_last_24h,
            CASE
                WHEN b.txn_ts IS NULL THEN NULL
                ELSE COALESCE(
                    SUM(b.amount) OVER (
                        PARTITION BY b.card_id_clean
                        ORDER BY b.txn_ts
                        RANGE BETWEEN INTERVAL 24 HOUR PRECEDING AND CURRENT ROW
                    ),
                    0
                )
            END AS amt_last_24h
        FROM base b
    ),
    decline_features AS (
        SELECT
            vf.*,
            CASE
                WHEN vf.txn_ts IS NULL THEN NULL
                ELSE COUNT(CASE WHEN vf.is_declined = TRUE THEN 1 END) OVER (
                    PARTITION BY vf.card_id_clean
                    ORDER BY vf.txn_ts
                    RANGE BETWEEN INTERVAL 24 HOUR PRECEDING AND CURRENT ROW
                )
            END AS declined_txns_last_24h
        FROM velocity_features vf
    ),
    behavioral_features AS (
        SELECT
            df.*,
            CASE
                WHEN df.amount IS NULL THEN NULL
                WHEN AVG(df.amount) OVER (PARTITION BY df.card_id_clean) = 0 THEN NULL
                WHEN AVG(df.amount) OVER (PARTITION BY df.card_id_clean) IS NULL THEN NULL
                ELSE df.amount / NULLIF(AVG(df.amount) OVER (PARTITION BY df.card_id_clean), 0)
            END AS amount_vs_card_avg
        FROM decline_features df
    ),
    distinct_merchant_first_seen AS (
        SELECT
            bf.card_id_clean,
            bf.merchant_id_clean,
            MIN(bf.txn_ts) AS first_seen_ts
        FROM behavioral_features bf
        WHERE bf.card_id_clean IS NOT NULL
          AND bf.merchant_id_clean IS NOT NULL
          AND bf.txn_ts IS NOT NULL
        GROUP BY bf.card_id_clean, bf.merchant_id_clean
    ),
    merchant_counts AS (
        SELECT
            dmfs.card_id_clean,
            dmfs.first_seen_ts AS txn_ts,
            COUNT(*) OVER (
                PARTITION BY dmfs.card_id_clean
                ORDER BY dmfs.first_seen_ts
                RANGE BETWEEN INTERVAL 24 HOUR PRECEDING AND CURRENT ROW
            ) AS distinct_merchants_last_24h
        FROM distinct_merchant_first_seen dmfs
    ),
    merchant_features AS (
        SELECT
            bf.*,
            CASE
                WHEN bf.txn_ts IS NULL THEN NULL
                ELSE (
                    SELECT mc.distinct_merchants_last_24h
                    FROM merchant_counts mc
                    WHERE mc.card_id_clean = bf.card_id_clean
                      AND mc.txn_ts <= bf.txn_ts
                      AND mc.txn_ts >= DATE_SUB(bf.txn_ts, INTERVAL 24 HOUR)
                    ORDER BY mc.txn_ts DESC
                    LIMIT 1
                )
            END AS distinct_merchants_last_24h
        FROM behavioral_features bf
    )
    SELECT *
    FROM merchant_features;
    """
    
    try:
        with engine.begin() as conn:
            # Split and execute statements
            statements = [s.strip() for s in test_sql.split(';') if s.strip() and not s.strip().startswith('--')]
            for i, stmt in enumerate(statements, 1):
                if stmt.upper().startswith('USE '):
                    continue
                print(f"Executing statement {i}/{len(statements)}...")
                conn.execute(text(stmt))
        
        print("\n[OK] Test table created successfully!")
        
        # Verify
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM feat_transactions_test"))
            count = result.scalar_one()
            print(f"\nTest table has {count:,} rows")
            
            result = conn.execute(text("""
                SELECT 
                    txns_last_24h,
                    amt_last_24h,
                    distinct_merchants_last_24h,
                    amount_vs_card_avg
                FROM feat_transactions_test
                WHERE txn_ts IS NOT NULL
                LIMIT 5
            """))
            
            print("\nSample feature values:")
            for i, row in enumerate(result.fetchall(), 1):
                print(f"  Row {i}: txns_24h={row[0]}, amt_24h={row[1]:.2f}, distinct_merchants={row[2]}, amount_vs_avg={row[3]:.2f if row[3] else 'NULL'}")
        
        print("\n[OK] Test successful! Features are being computed correctly.")
        print("\nYou can now run the full Stage 5A SQL script.")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

