import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as path_effects
import matplotlib as mpl
from datetime import datetime
import locale

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="Jadwal Pengawas & Plotter", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; color: #212529; }
    .stSelectbox label, .stTextInput label, .stDateInput label, .stTimeInput label { color: #495057; font-weight: 600; }
    .stDataFrame { border: 1px solid #dee2e6; border-radius: 0.25rem; }
    h1, h2, h3 { color: #343a40; }
    </style>
""", unsafe_allow_html=True)

# --- CONSTANTS ---
MONTH_MAP_ID = {
    'Januari': 1, 'Februari': 2, 'Maret': 3, 'April': 4, 'Mei': 5, 'Juni': 6,
    'Juli': 7, 'Agustus': 8, 'September': 9, 'Oktober': 10, 'November': 11, 'Desember': 12
}

DAY_MAP_ID = {
    'Monday': 'SENIN', 'Tuesday': 'SELASA', 'Wednesday': 'RABU',
    'Thursday': 'KAMIS', 'Friday': 'JUMAT', 'Saturday': 'SABTU', 'Sunday': 'MINGGU'
}

# --- DATA LOADING ---
@st.cache_data
def load_data(file_input):
    try:
        # Determine if file_input is a path string or an uploaded file object
        if isinstance(file_input, str):
            with open(file_input, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            file_source_name = file_input
        else:
            # Assume it's an UploadedFile (BytesIO)
            # Need to decode bytes to string
            content = file_input.getvalue().decode("utf-8", errors='replace')
            lines = content.splitlines(keepends=True)
            file_source_name = file_input.name

        # 1. Find the header row index
        header_idx = -1
        col_names = []
        
        for i, line in enumerate(lines):
            if "Nama Pengawas" in line or "nama pengawas" in line.lower():
                header_idx = i
                # Manually parse columns
                raw_cols = [c.strip().replace('"', '') for c in line.split(';')]
                # Deduplicate columns
                seen = {}
                col_names = []
                for c in raw_cols:
                    if c in seen:
                        seen[c] += 1
                        col_names.append(f"{c}.{seen[c]}")
                    else:
                        seen[c] = 0
                        col_names.append(c)
                break
        
        if header_idx == -1:
            st.error(f"Header 'Nama Pengawas' tidak ditemukan dalam file {file_source_name}.")
            return None

        # 2. Read CSV using the found data
        from io import StringIO
        # Join lines starting from header_idx + 1 (data)
        data_str = "".join(lines[header_idx + 1:])
        
        df = pd.read_csv(
            StringIO(data_str), 
            sep=';', 
            names=col_names, 
            header=None,
            encoding='utf-8', 
            on_bad_lines='skip', 
            dtype=str
        )
        
        # 3. Clean Columns
        df.columns = [str(c).replace('\n', '').replace('\r', '').strip() for c in df.columns]
        
        # 4. Remove empty, Unnamed, or duplicate columns
        df = df.loc[:, ~df.columns.str.contains('^Unnamed', case=False)]
        df = df.loc[:, df.columns != '']
        
        return df
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return None

# --- PARSING HELPERS ---
def parse_indonesian_date(date_str):
    if not isinstance(date_str, str): return None
    try:
        parts = date_str.strip().split()
        if len(parts) >= 3:
            day = int(parts[0])
            month_str = parts[1]
            year = int(parts[2])
            month = MONTH_MAP_ID.get(month_str)
            if month:
                return datetime(year, month, day)
    except:
        pass
    return None

def get_day_name(dt_obj):
    return DAY_MAP_ID.get(dt_obj.strftime("%A"), "UNKNOWN") if dt_obj else "UNKNOWN"

def parse_time_range(time_str):
    if not isinstance(time_str, str): return None, None
    try:
        clean = time_str.replace("WIB", "").strip()
        start_str, end_str = clean.split('-')
        start_str = start_str.strip().replace('.', ':')
        end_str = end_str.strip().replace('.', ':')
        
        # Normalize HH:MM
        def norm(t):
            if len(t) == 4 and ':' not in t: return t[:2] + ":" + t[2:]
            return t
        
        return norm(start_str), norm(end_str)
    except:
        return None, None

def check_conflicts(df_schedule):
    df_schedule['Conflict'] = False
    
    # Simple overlap check
    if 'DateObj' not in df_schedule.columns or df_schedule.empty:
        return df_schedule
        
    dates = df_schedule['DateObj'].dropna().unique()
    
    for date in dates:
        # subset for this date
        day_idxs = df_schedule[df_schedule['DateObj'] == date].index
        
        for i in day_idxs:
            row1 = df_schedule.loc[i]
            if not row1['ValidTime']: continue
            
            try:
                s1 = datetime.strptime(row1['Start'], "%H:%M")
                e1 = datetime.strptime(row1['End'], "%H:%M")
                
                for j in day_idxs:
                    if i == j: continue
                    row2 = df_schedule.loc[j]
                    if not row2['ValidTime']: continue
                    
                    s2 = datetime.strptime(row2['Start'], "%H:%M")
                    e2 = datetime.strptime(row2['End'], "%H:%M")
                    
                    # Overlap: Start1 < End2 AND Start2 < End1
                    if s1 < e2 and s2 < e1:
                        df_schedule.at[i, 'Conflict'] = True
                        break # Found one conflict, enough to mark row
            except:
                continue
                
    return df_schedule

# --- PLOTTING ---
_PALETTE = list(mpl.colormaps['tab20'].colors)

def _posisi_waktu(hhmm, base_hhmm="06:00"):
    try:
        hb, mb = map(int, base_hhmm.split(':'))
        h, m = map(int, hhmm.split(':'))
        return ((h*60 + m) - (hb*60 + mb)) / 60.0
    except:
        return 0

def _best_text_color(rgb):
    return "black" if (0.2126*rgb[0] + 0.7152*rgb[1] + 0.0722*rgb[2]) > 0.6 else "white"

def wrap_text(text, max_length=15):
    text = str(text)
    words = text.split()
    lines = []
    current = []
    curr_len = 0
    for w in words:
        if curr_len + len(w) + len(current) > max_length:
            if current:
                lines.append(' '.join(current))
                current = [w]
                curr_len = len(w)
            else:
                lines.append(w[:max_length])
                current = [w[max_length:]]
        else:
            current.append(w)
            curr_len += len(w)
    if current: lines.append(' '.join(current))
    return '\n'.join(lines)

def plot_jadwal_data(df, title="Jadwal"):
    if df.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Kosong", ha='center')
        return fig
        
    hari_order = ["SENIN","SELASA","RABU","KAMIS","JUMAT","SABTU","MINGGU"]
    hari_idx = {h:i for i,h in enumerate(hari_order)}
    
    df = df[df['Hari'].isin(hari_order)]
    if df.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Tidak ada data hari valid", ha='center')
        return fig

    fig, ax = plt.subplots(figsize=(16, 10))
    
    for _, row in df.iterrows():
        if not row['ValidTime']: continue
        
        start, end = row['Start'], row['End']
        h_idx = hari_idx[row['Hari']]
        
        y_bottom = _posisi_waktu(start)
        y_height = _posisi_waktu(end) - _posisi_waktu(start)
        
        col = _PALETTE[abs(hash(str(row["Activity"]))) % len(_PALETTE)]
        edge = "red" if row.get('Conflict') else "black"
        lw = 3 if row.get('Conflict') else 1
        
        rect = patches.Rectangle((h_idx - 0.45, y_bottom), 0.9, y_height, 
                                 linewidth=lw, edgecolor=edge, facecolor=col, alpha=0.9)
        ax.add_patch(rect)
        
        # Text
        cx, cy = h_idx, y_bottom + y_height/2
        tc = _best_text_color(col)
        
        info = f"{row['Activity']}\n{start}-{end}\n{row['Room']}"
        if row.get('Type') == 'External': info += " (Ext)"
        
        ax.text(cx, cy, wrap_text(info, max_length=15), 
                ha='center', va='center', fontsize=9, 
                color=tc, fontweight='bold', clip_on=True)
        
    ax.set_xlim(-0.5, 6.5)
    ax.set_xticks(range(7))
    ax.set_xticklabels(hari_order)
    
    # Y Axis Time
    start_m, end_m = 6*60, 21*60
    ax.set_ylim(0, (end_m - start_m)/60)
    yticks = range(0, int((end_m - start_m)/60) + 1)
    ax.set_yticks(yticks)
    ax.set_yticklabels([f"{h+6:02d}:00" for h in yticks])
    ax.invert_yaxis()
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.set_title(title, fontsize=14)
    
    return fig

# --- APP LAYOUT ---
header = st.container()
selection = st.container()

with header:
    st.title("📅 Sistem Pengecekan Jadwal Pengawas")

with selection:
    st.sidebar.header("Data Source")
    uploaded_file = st.sidebar.file_uploader("Upload CSV Jadwal (Opsional)", type=["csv"])
    
    if uploaded_file is not None:
        data_source = uploaded_file
        st.sidebar.success("Menggunakan file yang diupload.")
    else:
        data_source = 'UAS(JADWAL JAGA).csv'
        st.sidebar.info("Menggunakan file default.")

data = load_data(data_source)
if data is None: st.stop()

# Find Supervisor Columns
# Case insensitive search including "Nama Pengawas"
sup_cols = [c for c in data.columns if 'nama pengawas' in c.lower()]

if not sup_cols:
    st.error("Kolom 'Nama Pengawas' tidak ditemukan. Cek format file.")
    st.write("Kolom yang terbaca:", data.columns.tolist())
    st.stop()

# Extract unique names
all_names = set()
for c in sup_cols:
    uniqs = data[c].dropna().unique()
    for u in uniqs:
        if isinstance(u, str) and len(u.strip()) > 2:
            all_names.add(u.strip())
            
sorted_names = sorted(list(all_names))

with selection:
    st.sidebar.markdown("---")
    st.sidebar.header("Menu")
    sel_name = st.sidebar.selectbox("Pilih Nama Pengawas", [""] + sorted_names)
    
    st.sidebar.markdown("### Kegiatan External")
    if 'ext_list' not in st.session_state: st.session_state['ext_list'] = []
    
    with st.sidebar.form("ext_form"):
        en = st.text_input("Nama Kegiatan")
        ed = st.date_input("Tanggal", min_value=datetime(2026,1,1))
        es = st.time_input("Mulai")
        ee = st.time_input("Selesai")
        if st.form_submit_button("Tambah") and en:
            st.session_state['ext_list'].append({
                'Activity': en,
                'DateObj': datetime.combine(ed, datetime.min.time()),
                'Start': es.strftime("%H:%M"),
                'End': ee.strftime("%H:%M"),
                'Room': 'External',
                'Hari': get_day_name(datetime.combine(ed, datetime.min.time())),
                'Type': 'External',
                'ValidTime': True
            })
            st.rerun()

    if st.sidebar.button("Reset External"):
        st.session_state['ext_list'] = []
        st.rerun()

if sel_name:
    st.subheader(f"Jadwal: {sel_name}")
    
    # 1. Filter
    subset = pd.DataFrame()
    for c in sup_cols:
        matched = data[data[c].astype(str).str.contains(sel_name, case=False, regex=False, na=False)]
        subset = pd.concat([subset, matched])
    
    subset = subset.drop_duplicates(subset=['NO'] if 'NO' in subset.columns else None)
    
    # 2. Map to Standard Format
    rows = []
    for _, r in subset.iterrows():
        do = parse_indonesian_date(r.get('Tanggal'))
        s, e = parse_time_range(r.get('Pukul'))
        
        rows.append({
            'Activity': r.get('SUBJECTNAME', 'Ujian'),
            'DateObj': do,
            'DateStr': r.get('Tanggal', '-'),
            'Start': s,
            'End': e,
            'Room': r.get('ROOM', '-'),
            'Hari': get_day_name(do),
            'Type': 'Pengawas',
            'ValidTime': (s is not None and e is not None)
        })
    
    # 3. Add External
    rows.extend(st.session_state['ext_list'])
    
    df_show = pd.DataFrame(rows)
    if not df_show.empty:
        df_show = check_conflicts(df_show)
        
        # Table
        st.dataframe(df_show[['Hari', 'DateStr', 'Start', 'End', 'Activity', 'Room', 'Conflict']])
        
        if df_show['Conflict'].any():
            st.error("JADWAL BENTROK TERDETEKSI!")
            
        # Plot
        st.pyplot(plot_jadwal_data(df_show, title=f"Jadwal {sel_name}"))
        
    else:
        st.warning("Belum ada jadwal.")
else:
    st.info("Pilih nama di sebelah kiri.")

# --- FOOTER ---
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #6c757d;'>
        <p>Created by Athila Ramdani Saputra</p>
    </div>
    """, 
    unsafe_allow_html=True
)
