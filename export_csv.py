import sqlite3
import pandas as pd
import os

DB_FILE = "phonepe_pulse.db"
EXPORT_DIR = "csv_export"

def export_tables_to_csv():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Fetch all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall()]
    
    print("Starting CSV export for Power BI...")
    for table in tables:
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
        csv_path = os.path.join(EXPORT_DIR, f"{table}.csv")
        df.to_csv(csv_path, index=False)
        print(f"Exported '{table}' -> {csv_path} ({len(df)} rows)")
        
    conn.close()
    print("\nAll database tables successfully exported to the 'csv_export' folder!")

if __name__ == "__main__":
    export_tables_to_csv()
