"""
Test notebook connection and data loading to diagnose errors.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import polars as pl

# Load environment variables
load_dotenv()

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

print("Testing notebook connection...")
print("=" * 60)

# Test 1: Connection
try:
    mysql_url = get_mysql_url()
    engine = create_engine(mysql_url)
    print("[OK] Database connection established")
except Exception as e:
    print(f"[ERROR] Connection failed: {e}")
    exit(1)

# Test 2: Check if table exists
try:
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'fraud_db' 
            AND table_name = 'feat_transactions_risk'
        """))
        table_exists = result.scalar_one() > 0
        
        if table_exists:
            print("[OK] feat_transactions_risk table exists")
        else:
            print("[ERROR] feat_transactions_risk table does NOT exist!")
            print("   Please run: SOURCE sql/features/feat_transactions_risk.sql;")
            exit(1)
except Exception as e:
    print(f"[ERROR] Table check failed: {e}")
    exit(1)

# Test 3: Try Polars read_database
try:
    query = "SELECT * FROM feat_transactions_risk LIMIT 10"
    df = pl.read_database(query, connection=engine.connect())
    print(f"[OK] Polars read_database works! Loaded {df.shape[0]} rows")
    print(f"     Columns: {df.shape[1]}")
except Exception as e:
    print(f"[ERROR] Polars read_database failed: {e}")
    print(f"     Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    
    # Try alternative: pandas then convert
    print("\nTrying alternative: pandas -> polars...")
    try:
        import pandas as pd
        df_pd = pd.read_sql(query, engine)
        df = pl.from_pandas(df_pd)
        print(f"[OK] Alternative method works! Loaded {df.shape[0]} rows via pandas")
    except Exception as e2:
        print(f"[ERROR] Alternative method also failed: {e2}")

print("\n" + "=" * 60)
print("Test complete!")

