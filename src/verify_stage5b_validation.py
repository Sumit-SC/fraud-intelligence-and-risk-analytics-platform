"""
Verify Stage 5B validation table.
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
    print("Stage 5B Validation Verification")
    print("=" * 60)
    
    with engine.connect() as conn:
        # Check if validation table exists
        result = conn.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'fraud_db' 
            AND table_name = 'feat_transactions_risk_validation'
        """))
        
        if result.scalar_one() == 0:
            print("\n[ERROR] Validation table does not exist!")
            print("   Please run: SOURCE sql/features/feat_transactions_risk_validation.sql;")
            return
        
        print("\n[OK] Validation table exists")
        
        # Check row counts
        result = conn.execute(text("""
            SELECT COUNT(*) 
            FROM feat_transactions_risk_validation
        """))
        validation_count = result.scalar_one()
        
        result = conn.execute(text("""
            SELECT COUNT(*) 
            FROM feat_transactions
            WHERE txn_ts IS NOT NULL
              AND txn_ts >= DATE_SUB((SELECT MAX(txn_ts) FROM feat_transactions WHERE txn_ts IS NOT NULL), INTERVAL 30 DAY)
        """))
        expected_count = result.scalar_one()
        
        print(f"\nRow counts:")
        print(f"  Validation table: {validation_count:,} rows")
        print(f"  Expected (last 30 days): {expected_count:,} rows")
        
        if validation_count == expected_count:
            print("  [OK] Row counts match!")
        else:
            print(f"  [WARNING] Row counts differ by {abs(validation_count - expected_count)}")
        
        # Check feature columns
        print("\n" + "-" * 60)
        print("Feature Columns Check:")
        print("-" * 60)
        
        required_features = [
            'card_txn_count_30d',
            'card_fraud_rate_30d',
            'card_decline_rate_30d',
            'merchant_txn_count_30d',
            'merchant_fraud_rate_30d',
            'merchant_decline_rate_30d'
        ]
        
        result = conn.execute(text("""
            SELECT COLUMN_NAME 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'fraud_db' 
            AND TABLE_NAME = 'feat_transactions_risk_validation'
        """))
        existing_columns = {row[0] for row in result}
        
        for feature in required_features:
            if feature in existing_columns:
                print(f"  [OK] {feature}")
            else:
                print(f"  [ERROR] {feature} - MISSING!")
        
        # Sample feature values
        print("\n" + "-" * 60)
        print("Sample Feature Values:")
        print("-" * 60)
        
        result = conn.execute(text("""
            SELECT 
                txn_id_clean,
                DATE(txn_ts) as txn_date,
                card_txn_count_30d,
                card_fraud_rate_30d,
                card_decline_rate_30d,
                merchant_txn_count_30d,
                merchant_fraud_rate_30d,
                merchant_decline_rate_30d,
                is_fraud
            FROM feat_transactions_risk_validation
            WHERE txn_ts IS NOT NULL
            ORDER BY txn_ts DESC
            LIMIT 10
        """))
        
        rows = result.fetchall()
        if rows:
            print(f"\n  Sample rows (most recent first):")
            for i, row in enumerate(rows, 1):
                print(f"\n  Row {i}:")
                print(f"    txn_id: {row[0]}")
                print(f"    date: {row[1]}")
                print(f"    card_txn_count_30d: {row[2]}")
                print(f"    card_fraud_rate_30d: {row[3]:.4f}")
                print(f"    card_decline_rate_30d: {row[4]:.4f}")
                print(f"    merchant_txn_count_30d: {row[5]}")
                print(f"    merchant_fraud_rate_30d: {row[6]:.4f}")
                print(f"    merchant_decline_rate_30d: {row[7]:.4f}")
                print(f"    is_fraud: {row[8]}")
        
        # Check feature statistics
        print("\n" + "-" * 60)
        print("Feature Statistics:")
        print("-" * 60)
        
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                AVG(card_txn_count_30d) as avg_card_txn_30d,
                MAX(card_txn_count_30d) as max_card_txn_30d,
                AVG(card_fraud_rate_30d) as avg_card_fraud_rate,
                AVG(merchant_txn_count_30d) as avg_merchant_txn_30d,
                AVG(merchant_fraud_rate_30d) as avg_merchant_fraud_rate
            FROM feat_transactions_risk_validation
            WHERE txn_ts IS NOT NULL
        """))
        
        stats = result.fetchone()
        if stats:
            print(f"  Total rows: {stats[0]:,}")
            print(f"  Avg card_txn_count_30d: {stats[1]:.2f}")
            print(f"  Max card_txn_count_30d: {stats[2]}")
            print(f"  Avg card_fraud_rate_30d: {stats[3]:.4f}")
            print(f"  Avg merchant_txn_count_30d: {stats[4]:.2f}")
            print(f"  Avg merchant_fraud_rate_30d: {stats[5]:.4f}")
        
        print("\n" + "=" * 60)
        print("[OK] Stage 5B validation verification complete!")
        print("=" * 60)


if __name__ == "__main__":
    main()

