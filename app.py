import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# 1. SETUP KONFIGURASI HALAMAN
st.set_page_config(page_title="SHEVA HSE COMPLIANCE", page_icon="🛡️", layout="centered")

st.markdown("""
    <style>
    .stRadio p { font-size: 13pt !important; font-weight: bold !important; color: #1a365d !important; }
    .stButton button { width: 100%; height: 50px; font-size: 13pt !important; background-color: #1a365d !important; color: white !important; font-weight: bold; border-radius: 8px; }
    .success-text { color: #2f855a; font-weight: bold; font-size: 14pt; }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ SHEVA HSE & Social Compliance Digital Tools")
st.caption("PT Adira Semesta Industry - Integrated with SHEVA AI Agent System")
st.markdown("---")

# 2. KONEKSI KE GOOGLE SHEETS
try:
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(dict(creds_dict), scopes=scope)
    client = gspread.authorize(creds)

    sheet = client.open("SHEVA - AUDIT DIGITAL")
    db_sheet = sheet.worksheet("AUDIT_CHECKLIST_DATABASE")
except Exception as e:
    st.error(f"❌ Gagal koneksi ke database: {e}")
    st.stop()

# Kode area HARUS sama persis dengan tab Area_Reference, supaya nanti bisa
# di-join untuk routing PIC dan dashboard otomatis.
AREA_OPTIONS = {
    "MT-LINE": "MT Line",
    "MT-RND": "MT R&D",
    "PRD-SEWING": "Produksi - Sewing",
    "PRD-CUTTING": "Produksi - Cutting",
    "PRD-ACCESSORIES": "Produksi - Accessories",
    "PRD-DISTRIBUSI": "Produksi - Distribusi",
    "PRD-GUDANGJADI": "Produksi - Gudang Jadi",
}

# 3. INFORMASI UMUM (di luar form — boleh, ini tidak butuh reaksi dinamis)
st.subheader("📋 1. Informasi Umum Inspeksi")
col1, col2 = st.columns(2)
with col1:
    auditor = st.text_input("Nama Auditor/Inspektur:", placeholder="Contoh: Tim HSE")
    periode = st.selectbox("Periode Evaluasi:", ["Juli 2026", "Agustus 2026", "September 2026"])
with col2:
    area = st.selectbox(
        "Pilih Area Kerja / Fasilitas Pabrik:",
        options=list(AREA_OPTIONS.keys()),
        format_func=lambda code: f"{code} — {AREA_OPTIONS[code]}",
    )

st.markdown("---")
st.subheader("🔍 2. Parameter Kepatuhan K3 & Sosial")
st.write("Isi evaluasi kondisi riil di lantai pabrik saat ini:")

# PENTING: skor DILETAKKAN DI LUAR st.form(). Widget di dalam st.form tidak
# memicu rerun saat diubah, sehingga warning + uploader foto baru muncul
# bersamaan dengan klik submit — terlambat untuk benar-benar melampirkan
# bukti. Di luar form, tiap perubahan skor langsung memicu rerun, sehingga
# "AI Warning Logic" muncul dinamis persis saat auditor memilih skor rendah.

# --- PERTANYAAN 1 ---
st.markdown("### **P1. Aspek K3 - Proteksi Kebakaran**")
st.write("Apakah semua APAR di area kerja terpasang jelas, tidak terhalang barang, dan kartu inspeksi bulanan dalam kondisi aktif?")
skor_1 = st.radio("Skor Kepatuhan P1:", options=[1, 2, 3, 4, 5], index=4, key="skor_p1", horizontal=True)
catatan_1 = st.text_input("Catatan Temuan Lapangan P1 (Wajib jika skor < 4):", key="catat_p1", placeholder="Isi detail jika ada pelanggaran...")
foto_1 = None
if skor_1 < 4:
    st.warning("⚠️ **SHEVA AI Warning:** Skor di bawah standar! AI Agent akan otomatis menandai ini sebagai 'OPEN target' dan memicu alert perbaikan.")
    foto_1 = st.file_uploader("📸 Unggah Foto Bukti Pelanggaran (Maks 5MB):", type=["jpg", "png", "jpeg"], key="foto_p1")

st.markdown("---")

# --- PERTANYAAN 2 ---
st.markdown("### **P2. Aspek K3 - Keamanan Mesin Produksi**")
st.write("Apakah seluruh mesin jahit (Sewing Machine) telah dilengkapi dengan komponen keselamatan standar seperti *finger guard* dan *pulley guard*?")
skor_2 = st.radio("Skor Kepatuhan P2:", options=[1, 2, 3, 4, 5], index=4, key="skor_p2", horizontal=True)
catatan_2 = st.text_input("Catatan Temuan Lapangan P2 (Wajib jika skor < 4):", key="catat_p2", placeholder="Isi detail jika ada pelanggaran...")
foto_2 = None
if skor_2 < 4:
    st.warning("⚠️ **SHEVA AI Warning:** Skor kritis terdeteksi di area mesin produksi!")
    foto_2 = st.file_uploader("📸 Unggah Foto Bukti Pelanggaran Mesin:", type=["jpg", "png", "jpeg"], key="foto_p2")

st.markdown("---")

# 4. SUBMIT (tombol biasa, bukan form_submit_button — semua nilai di atas
# sudah "hidup" di rerun ini karena tidak dibungkus st.form)
submit_btn = st.button("🚀 SUBMIT DATA KE SHEVA AI DATABASE")

if submit_btn:
    errors = []
    if not auditor:
        errors.append("Nama Auditor tidak boleh kosong.")
    if skor_1 < 4 and not catatan_1:
        errors.append("Catatan Temuan P1 wajib diisi karena skor < 4.")
    if skor_1 < 4 and foto_1 is None:
        errors.append("Foto bukti P1 wajib diunggah karena skor < 4.")
    if skor_2 < 4 and not catatan_2:
        errors.append("Catatan Temuan P2 wajib diisi karena skor < 4.")
    if skor_2 < 4 and foto_2 is None:
        errors.append("Foto bukti P2 wajib diunggah karena skor < 4.")

    if errors:
        for e in errors:
            st.error(f"❌ {e}")
    else:
        with st.spinner("Mengirim data ke database sentral..."):
            try:
                timestamp_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Catatan: untuk versi Golden Path besok, nama file dicatat
                # sebagai bukti bahwa foto sudah dilampirkan auditor. Upload
                # fisik ke Google Drive (agar Link_Evidence berisi URL asli)
                # bisa ditambahkan setelah demo — lihat catatan di bagian
                # bawah file ini untuk kode opsionalnya.
                evidence_1 = foto_1.name if foto_1 is not None else ""
                evidence_2 = foto_2.name if foto_2 is not None else ""

                id_audit_1 = f"AUD-{datetime.now().strftime('%Y%m%d%H%M%S')}-01"
                status_1 = "Closed" if skor_1 >= 4 else "Open"
                row_1 = [id_audit_1, timestamp_now, auditor, periode, area,
                          "I. HEALTH, SAFETY, ENVIRONMENT (HSE)", "1", "Proteksi APAR Lapangan",
                          "", "", str(skor_1), str(skor_1), "GOV-11", catatan_1, evidence_1,
                          status_1, ""]

                id_audit_2 = f"AUD-{datetime.now().strftime('%Y%m%d%H%M%S')}-02"
                status_2 = "Closed" if skor_2 >= 4 else "Open"
                row_2 = [id_audit_2, timestamp_now, auditor, periode, area,
                          "I. HEALTH, SAFETY, ENVIRONMENT (HSE)", "2", "Finger Guard Mesin Sewing",
                          "", "", str(skor_2), str(skor_2), "SYS-04", catatan_2, evidence_2,
                          status_2, ""]

                db_sheet.append_rows([row_1, row_2])

                st.balloons()
                st.success("🎉 BERHASIL! Data sukses terekam. SHEVA AI Agent sedang memproses sinkronisasi dasbor eksekutif.")
            except Exception as err:
                st.error(f"Gagal mengirim data: {err}")

# ---------------------------------------------------------------------------
# CATATAN UNTUK PENGEMBANGAN SETELAH DEMO (tidak perlu dikerjakan malam ini):
#
# 1. Upload foto fisik ke Google Drive: scope "drive" sudah ada di atas,
#    jadi bisa pakai googleapiclient.discovery.build("drive", "v3",
#    credentials=creds) untuk upload file dari foto_1/foto_2, lalu simpan
#    URL-nya (bukan cuma nama file) ke kolom Link_Evidence.
# 2. Ganti client.open("SHEVA - AUDIT DIGITAL") jadi client.open_by_key(ID)
#    — lebih tahan terhadap kemungkinan nama file duplikat di Drive.
# 3. Kode Regulatory_Source ("GOV-11", "SYS-04") sudah disamakan format
#    dengan tab Master_Regulatory — pastikan kode ini memang ada persis di
#    tab tersebut, sesuaikan kalau nomornya beda.
# ---------------------------------------------------------------------------
