# oracle_test.py
from dotenv import load_dotenv
import os
import oracledb  # no cx_Oracle needed

# Load .env
load_dotenv()

user = os.getenv("ORACLE_USER")
pwd  = os.getenv("ORACLE_PASS")
dsn = os.getenv("ORACLE_DSN")  # localhost/orclpdb

try:
    # Thin mode, no Oracle Instant Client needed
    conn = oracledb.connect(user=user, password=pwd, dsn=dsn)
    
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM DUAL")
    print("Query result:", cur.fetchone())
    
    cur.close()
    conn.close()
    print("Oracle connection OK")
except Exception as e:
    print("Oracle connection failed:", e)
