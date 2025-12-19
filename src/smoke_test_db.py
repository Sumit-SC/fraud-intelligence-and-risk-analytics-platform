import os
from sqlalchemy import create_engine, text

host = os.getenv("MYSQL_HOST", "localhost")
port = os.getenv("MYSQL_PORT", "3306")
user = os.getenv("MYSQL_USER", "root")
pwd  = os.getenv("MYSQL_PASSWORD", "sanalyst")
db   = os.getenv("MYSQL_DB", "fraud_db")

if pwd:
    url = f"mysql+mysqlconnector://{user}:{pwd}@{host}:{port}/{db}"
else:
    url = f"mysql+mysqlconnector://{user}@{host}:{port}/{db}"

engine = create_engine(url)

with engine.connect() as conn:
    tables = [row[0] for row in conn.execute(text("SHOW TABLES"))]
    print("Tables found:")
    for t in tables:
        print(" -", t)
