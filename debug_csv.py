import pandas as pd
import io

try:
    print("--- Attempting skip 12 ---")
    df = pd.read_csv('UAS(JADWAL JAGA).csv', sep=';', skiprows=12, encoding='utf-8', on_bad_lines='skip')
    print("Columns found (skip 12):")
    print(df.columns.tolist())
    print(f"Row count: {len(df)}")
    
    supervisor_cols = [c for c in df.columns if 'nama pengawas' in str(c).lower()]
    print(f"Supervisor cols matching 'nama pengawas': {supervisor_cols}")
    
    if supervisor_cols:
        print("Sample data from first intfound col:")
        print(df[supervisor_cols[0]].head())

except Exception as e:
    print(f"Error: {e}")
