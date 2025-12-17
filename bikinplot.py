import sys, subprocess

def ensure_package(pkg: str, import_name: str | None = None):
    """Import pkg; kalau belum ada, install lalu import lagi."""
    name = import_name or pkg
    try:
        __import__(name)
    except ModuleNotFoundError:
        print(f"Installing {pkg} ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
        __import__(name)

ensure_package("matplotlib")  # ini cukup, submodul tinggal di-import di bawah
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib as mpl
import matplotlib.patheffects as path_effects
from pathlib import Path

# ================== FIX: ganti titik -> titik dua, hapus "WIB" ==================

# UJIAN → replace matkulKelas (keys lama, shift pakai :)
matkulKelas = [
    {
        "hari": "SENIN",
        "shift": "08:00 - 10:15",
        "ruangan": "IF3.02.01",
        "mata_kuliah": "KECERDASAN ARTIFISIAL",
        "kelas": "IF-47-08",
        "kode_dosen": "BMG",
        "keterangan": "ujian"
    },
    {
        "hari": "SELASA",
        "shift": "10:45 - 13:00",
        "ruangan": "E302",
        "mata_kuliah": "KEAMANAN SIBER",
        "kelas": "IF-47-08",
        "kode_dosen": "UIR",
        "keterangan": "ujian"
    },
    {
        "hari": "KAMIS",
        "shift": "14:00 - 16:15",
        "ruangan": "(A203B) KU1.02.06",
        "mata_kuliah": "MANAJEMEN PROJEK TIK",
        "kelas": "IF-47-GABUP.07",
        "kode_dosen": "IDL",
        "keterangan": "ujian"
    },
    {
        "hari": "RABU",
        "shift": "10:45 - 13:00",
        "ruangan": "TULT 0602",
        "mata_kuliah": "KOMPUTASI AWAN DAN TERDISTRIBUSI",
        "kelas": "IF-47-GABUP.01",
        "kode_dosen": "ISB",
        "keterangan": "ujian"
    },
    {
        "hari": "RABU",
        "shift": "14:00 - 16:15",
        "ruangan": "(A304B) KU1.03.08",
        "mata_kuliah": "JARINGAN KOMPUTER",
        "kelas": "IF-47-GAB.07",
        "kode_dosen": "FAZ",
        "keterangan": "ujian"
    },
    {
        "hari": "SABTU",
        "shift": "10:30 - 12:10",
        "ruangan": "ONLINE",
        "mata_kuliah": "IMPAL",
        "kelas": "IF-47-08",
        "kode_dosen": "BRV",
        "keterangan": "ujian"
    },
]


# ATAS → tetap kosong sesuai brief lo
matkulAtas = []

# NGAWAS → replace jadwalAsprak (keys lama, shift pakai :)
jadwalAsprak = [
    {
        "hari": "JUMAT",
        "shift": "08:00 - 10:15",
        "ruangan": "KU3.03.02",
        "mata_kuliah": "NGAWAS APPL",
        "kelas": "IF-48-01",
        "kode_dosen": "SWD",
        "keterangan": "ngawas"
    },
    {
        "hari": "SENIN",
        "shift": "10:45 - 13:00",
        "ruangan": "KU1.03.12",
        "mata_kuliah": "NGAWAS STATISTIKA",
        "kelas": "IF-49-05",
        "kode_dosen": "HYL",
        "keterangan": "ngawas"
    },
    {
        "hari": "KAMIS",
        "shift": "08:00 - 10:15",
        "ruangan": "(A307A) KU1.03.13",
        "mata_kuliah": "NGAWAS STRUKTUR DATA",
        "kelas": "DS-48-03",
        "kode_dosen": "BTG",
        "keterangan": "ngawas"
    },
    {
        "hari": "JUMAT",
        "shift": "14:00 - 16:15",
        "ruangan": "(A203B) KU1.02.06",
        "mata_kuliah": "NGAWAS TEORI BAHASA DAN AUTOMATA",
        "kelas": "IF-48-01",
        "kode_dosen": "AIH",
        "keterangan": "ngawas"
    },
    {
        "hari": "SABTU",
        "shift": "08:00 - 10:15",
        "ruangan": "KU3.05.02",
        "mata_kuliah": "NGAWAS KALKULUS",
        "kelas": "IF-49-09",
        "kode_dosen": "SSI",
        "keterangan": "ngawas"
    },
    {
        "hari": "SELASA",
        "shift": "14:00 - 16:15",
        "ruangan": "(A310) KU1.03.14",
        "mata_kuliah": "NGAWAS PBO",
        "kelas": "IT-47-05",
        "kode_dosen": "TRK",
        "keterangan": "ngawas"
    }
]

matkulKelas

# Cell 2 - Helper Functions
def parse_shift(shift_str: str):
    """Parse shift time string to get start and end times"""
    start, end = [s.strip() for s in shift_str.split('-')]
    def trim(hhmm):
        parts = hhmm.split(':')
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
    return trim(start), trim(end)

def _posisi_waktu(hhmm, base_hhmm="06:00"):
    """Convert time to position on y-axis"""
    hb, mb = map(int, base_hhmm.split(':'))
    h, m = map(int, hhmm.split(':'))
    return ((h*60 + m) - (hb*60 + mb)) / 60.0

# Palet warna stabil (tab20) + kontras teks
_PALETTE = list(mpl.colormaps['tab20'].colors)

def _color_for(name: str):
    """Get consistent color for course name"""
    idx = abs(hash(name)) % len(_PALETTE)
    return _PALETTE[idx]

def _best_text_color(rgb):
    """Determine best text color (black/white) based on background"""
    r, g, b = rgb
    luminance = 0.2126*r + 0.7152*g + 0.0722*b
    return "black" if luminance > 0.6 else "white"

def wrap_text(text, max_length=15):
    """Wrap text to fit in rectangle"""
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + len(current_line) > max_length:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
            else:
                # Word too long, split it
                lines.append(word[:max_length])
                current_line = [word[max_length:]] if len(word) > max_length else []
                current_length = len(current_line[0]) if current_line else 0
        else:
            current_line.append(word)
            current_length += len(word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return '\n'.join(lines)

# Cell 3 - Plot Function
def plot_jadwal(items, title="Jadwal Mingguan"):
    """Create schedule plot with improved text fitting"""
    hari_order = ["SENIN","SELASA","RABU","KAMIS","JUMAT","SABTU","MINGGU"]
    hari_idx = {h:i for i,h in enumerate(hari_order)}
    fig, ax = plt.subplots(figsize=(16, 10))

    for row in items:
        start, end = parse_shift(row["shift"])
        height = _posisi_waktu(end) - _posisi_waktu(start)
        bottom = _posisi_waktu(start)
        x = hari_idx[row["hari"]] - 0.45

        face = _color_for(row["mata_kuliah"])
        rect = patches.Rectangle(
            (x, bottom), 0.9, height,
            linewidth=1, edgecolor="black",
            facecolor=face, alpha=0.9
        )
        ax.add_patch(rect)

        cx = hari_idx[row["hari"]]
        cy = bottom + height/2
        txt_color = _best_text_color(face)

        # Calculate text size based on rectangle height
        base_fontsize = min(16, max(9, height * 2.2))
        # Wrap and display course name
        wrapped_course = wrap_text(row["mata_kuliah"], max_length=int(height * 8))
        course_text = ax.text(cx, cy + height*0.15, wrapped_course, 
                             ha="center", va="center",
                             fontsize=base_fontsize, fontweight="bold", 
                             color="white", clip_on=True)
        course_text.set_path_effects([
            path_effects.Stroke(linewidth=1.5, foreground="black"),
            path_effects.Normal()
        ])
        
        # Class code
        ax.text(cx, cy, row["kelas"], ha="center", va="center",
                fontsize=base_fontsize-1, color=txt_color, clip_on=True)
        
        # Time, room, and instructor code
        time_room_text = f"{start} - {end}"
        if row["kode_dosen"]:
            time_room_text += f" | {row['kode_dosen']}"
        time_room_text += f"\n{row['ruangan']}"
        
        ax.text(cx, cy - height*0.15, time_room_text,
                ha="center", va="center", fontsize=base_fontsize-2, 
                color=txt_color, clip_on=True)

    ax.set_xlim(-0.5, 6.5)
    ax.set_xticks(range(7))
    ax.set_xticklabels(hari_order)
    
    # Time labels from 06:30 to 20:30
    start_min = 6*60
    end_min   = 18*60
    step      = 15

    yticks = [(m - start_min)/60 for m in range(start_min, end_min+1, step)]
    ylabs  = [f"{m//60:02d}:{m%60:02d}" for m in range(start_min, end_min+1, step)]

    ax.set_ylim(0, (end_min - start_min)/60)
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabs)
    ax.invert_yaxis()
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_xlabel("Hari", fontsize=12)
    ax.set_ylabel("Waktu", fontsize=12)
    ax.set_title(title, pad=16, fontsize=14)
    plt.tight_layout()
    return fig


"""Generate all schedule plots"""

# Plot 1: Jadwal Kuliah Saja
print("Membuat plot jadwal kuliah...")
all_kuliah = matkulKelas + matkulAtas
fig1 = plot_jadwal(all_kuliah, title="Jadwal UJIAN (created by athila)")
fig1.savefig("jadwal_UJIAN.png", dpi=150, bbox_inches='tight')
plt.show()

# Plot 2: Jadwal Asprak Saja
print("Membuat plot jadwal asprak...")
fig2 = plot_jadwal(jadwalAsprak, title="Jadwal NGAWAS (created by athila)")
fig2.savefig("jadwal_NGAWAS.png", dpi=150, bbox_inches='tight')
plt.show()

# Plot 3: Jadwal Lengkap (Kuliah + Asprak)
print("Membuat plot jadwal lengkap...")
all_schedule = matkulKelas + matkulAtas + jadwalAsprak
fig3 = plot_jadwal(all_schedule, title="Jadwal Lengkap ujian + ngawas (created by athila)")
fig3.savefig("jadwal_lengkap_ujian_ngawas.png", dpi=150, bbox_inches='tight')
plt.show()

print("Selesai! File PNG tersimpan:")
print("- jadwal_UJIAN.png")
print("- jadwal_NGAWAS.png") 
print("- jadwal_lengkap_ujian_ngawas.png")