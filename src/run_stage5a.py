"""
Run Stage 5A SQL script and verify results.
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


def run_sql_file(engine, filepath: str):
    """Execute SQL file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Split by semicolons and execute each statement
    statements = [s.strip() for s in sql_content.split(';') if s.strip()]
    
    with engine.begin() as conn:
        for i, statement in enumerate(statements, 1):
            if statement.upper().startswith('USE '):
                # Skip USE statements (already connected to DB)
                continue
            try:
                conn.execute(text(statement))
                print(f"  Executed statement {i}/{len(statements)}")
            except Exception as e:
                print(f"  Error in statement {i}: {e}")
                raise


def main():
    engine = create_engine(get_mysql_url())
    
    print("=" * 60)
    print("Running Stage 5A: Creating feat_transactions table")
    print("=" * 60)
    
    sql_file = "sql/features/feat_transactions.sql"
    
    if not os.path.exists(sql_file):
        print(f"\n[ERROR] SQL file not found: {sql_file}")
        return
    
    print(f"\nReading SQL file: {sql_file}")
    
    try:
        run_sql_file(engine, sql_file)
        print("\n[OK] SQL script executed successfully!")
    except Exception as e:
        print(f"\n[ERROR] Failed to execute SQL: {e}")
        return
    
    # Now verify
    print("\n" + "=" * 60)
    print("Verifying feat_transactions table")
    print("=" * 60)
    
    with engine.connect() as conn:
        # Check table exists
        result = conn.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'fraud_db' 
            AND table_name = 'feat_transactions'
        """))
        
        if result.scalar_one() > 0:
            print("\n[OK] feat_transactions table created successfully!")
            
            # Check row counts
            result = conn.execute(text("SELECT COUNT(*) FROM stg_transactions_enriched"))
            enriched_count = result.scalar_one()
            
            result = conn.execute(text("SELECT COUNT(*) FROM feat_transactions"))
            feature_count = result.scalar_one()
            
            print(f"\nRow counts:")
            print(f"  stg_transactions_enriched: {enriched_count:,} rows")
            print(f"  feat_transactions:         {feature_count:,} rows")
            
            if enriched_count == feature_count:
                print("  [OK] Row counts match!")
            else:
                print(f"  [WARNING] Row counts differ by {abs(enriched_count - feature_count)}")
            
            # Sample a few rows
            result = conn.execute(text("""
                SELECT 
                    txn_id_clean,
                    amount,
                    txns_last_24h,
                    distinct_merchants_last_24h,
                    is_fraud
                FROM feat_transactions
                WHERE txn_ts IS NOT NULL
                LIMIT 5
            """))
            
            rows = result.fetchall()
            if rows:
                print("\nSample feature values:")
                for i, row in enumerate(rows, 1):
                    print(f"\n  Row {i}:")
                    print(f"    txn_id: {row[0]}")
                    print(f"    amount: {row[1]}")
                    print(f"    txns_last_24h: {row[2]}")
                    print(f"    distinct_merchants_last_24h: {row[3]}")
                    print(f"    is_fraud: {row[4]}")
        else:
            print("\n[ERROR] Table was not created!")


if __name__ == "__main__":
    main()

