import pandas as pd

try:
    # Try finding header row dynamically
    with open('UAS(JADWAL JAGA).csv', 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    header_row = -1
    for i, line in enumerate(lines):
        if "Nama Pengawas 1" in line:
            header_row = i
            print(f"Header found at index {i}")
            break
            
    if header_row != -1:
        # Read with that header row
        df = pd.read_csv('UAS(JADWAL JAGA).csv', sep=';', header=header_row, encoding='utf-8', on_bad_lines='skip')
        print(f"Columns: {df.columns.tolist()}")
        sup_cols = [c for c in df.columns if 'Nama Pengawas' in str(c)]
        print(f"Supervisor Cols: {sup_cols}")
    else:
        print("Header not found in lines.")

except Exception as e:
    print(e)
