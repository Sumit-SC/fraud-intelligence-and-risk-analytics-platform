"""
Stage 5A Verification Script
Verifies that feat_transactions table is created correctly with all features.
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
    print("Stage 5A Verification: feat_transactions")
    print("=" * 60)
    
    with engine.connect() as conn:
        # Check if table exists
        result = conn.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'fraud_db' 
            AND table_name = 'feat_transactions'
        """))
        table_exists = result.scalar_one() > 0
        
        if not table_exists:
            print("\n[ERROR] feat_transactions table does not exist!")
            print("   Please run: SOURCE sql/features/feat_transactions.sql;")
            return
        
        print("\n[OK] feat_transactions table exists")
        
        # Check row counts
        print("\n" + "-" * 60)
        print("Row Count Verification:")
        print("-" * 60)
        
        result = conn.execute(text("SELECT COUNT(*) FROM stg_transactions_enriched"))
        enriched_count = result.scalar_one()
        
        result = conn.execute(text("SELECT COUNT(*) FROM feat_transactions"))
        feature_count = result.scalar_one()
        
        print(f"  stg_transactions_enriched: {enriched_count:,} rows")
        print(f"  feat_transactions:         {feature_count:,} rows")
        
        if enriched_count == feature_count:
            print("  [OK] Row counts match!")
        else:
            print(f"  [WARNING] Row counts don't match (diff: {abs(enriched_count - feature_count)})")
        
        # Check feature columns exist
        print("\n" + "-" * 60)
        print("Feature Columns Check:")
        print("-" * 60)
        
        required_features = [
            'txns_last_1h',
            'txns_last_24h',
            'amt_last_24h',
            'declined_txns_last_24h',
            'amount_vs_card_avg',
            'distinct_merchants_last_24h'
        ]
        
        result = conn.execute(text("""
            SELECT COLUMN_NAME 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'fraud_db' 
            AND TABLE_NAME = 'feat_transactions'
        """))
        existing_columns = {row[0] for row in result}
        
        for feature in required_features:
            if feature in existing_columns:
                print(f"  [OK] {feature}")
            else:
                print(f"  [ERROR] {feature} - MISSING!")
        
        # Sample feature values
        print("\n" + "-" * 60)
        print("Feature Value Samples (first 10 rows with valid timestamps):")
        print("-" * 60)
        
        result = conn.execute(text("""
            SELECT 
                txn_id_clean,
                amount,
                txns_last_1h,
                txns_last_24h,
                amt_last_24h,
                declined_txns_last_24h,
                amount_vs_card_avg,
                distinct_merchants_last_24h,
                is_fraud
            FROM feat_transactions
            WHERE txn_ts IS NOT NULL
            LIMIT 10
        """))
        
        rows = result.fetchall()
        if rows:
            print(f"\n  Found {len(rows)} sample rows:")
            for i, row in enumerate(rows, 1):
                print(f"\n  Row {i}:")
                print(f"    txn_id: {row[0]}")
                print(f"    amount: {row[1]}")
                print(f"    txns_last_1h: {row[2]}")
                print(f"    txns_last_24h: {row[3]}")
                print(f"    amt_last_24h: {row[4]}")
                print(f"    declined_txns_last_24h: {row[5]}")
                print(f"    amount_vs_card_avg: {row[6]}")
                print(f"    distinct_merchants_last_24h: {row[7]}")
                print(f"    is_fraud: {row[8]}")
        else:
            print("  [WARNING] No rows with valid timestamps found")
        
        # Check NULL percentages
        print("\n" + "-" * 60)
        print("NULL Value Analysis:")
        print("-" * 60)
        
        for feature in required_features:
            result = conn.execute(text(f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN {feature} IS NULL THEN 1 ELSE 0 END) as null_count
                FROM feat_transactions
            """))
            row = result.fetchone()
            total = row[0]
            null_count = row[1]
            null_pct = (null_count / total * 100) if total > 0 else 0
            
            status = "[OK]" if null_pct < 50 else "[WARN]"
            print(f"  {status} {feature}: {null_pct:.1f}% NULL ({null_count:,} / {total:,})")
        
        # Check feature distributions
        print("\n" + "-" * 60)
        print("Feature Statistics:")
        print("-" * 60)
        
        stats_query = text("""
            SELECT 
                COUNT(*) as total,
                AVG(txns_last_24h) as avg_txns_24h,
                MAX(txns_last_24h) as max_txns_24h,
                AVG(amt_last_24h) as avg_amt_24h,
                AVG(amount_vs_card_avg) as avg_amount_vs_card,
                AVG(distinct_merchants_last_24h) as avg_distinct_merchants
            FROM feat_transactions
            WHERE txn_ts IS NOT NULL
        """)
        
        result = conn.execute(stats_query)
        stats = result.fetchone()
        
        if stats and stats[0] > 0:
            print(f"  Total rows with timestamps: {stats[0]:,}")
            print(f"  Avg txns_last_24h: {stats[1]:.2f}")
            print(f"  Max txns_last_24h: {stats[2]}")
            print(f"  Avg amt_last_24h: {stats[3]:.2f}")
            print(f"  Avg amount_vs_card_avg: {stats[4]:.2f}")
            print(f"  Avg distinct_merchants_last_24h: {stats[5]:.2f}")
        
        print("\n" + "=" * 60)
        print("[OK] Stage 5A verification complete!")
        print("=" * 60)


if __name__ == "__main__":
    main()

