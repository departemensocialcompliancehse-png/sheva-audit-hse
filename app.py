import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests  # Ditambahkan untuk integrasi ke Webhook Make.com

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

# Tambahan daftar Factory sesuai dengan operasional perusahaan
FACTORY_OPTIONS = {
    "FACTORY-A": "Factory A",
    "FACTORY-B": "Factory B",
    "FACTORY-F": "Factory F",
    "FACTORY-K": "Factory K (IHP)"
}

AREA_OPTIONS = {
    "MT-LINE": "MT Line",
    "MT-RND": "MT R&D",
    "PRD-SEWING": "Produksi - Sewing",
    "PRD-CUTTING": "Produensing - Cutting",
    "PRD-ACCESSORIES": "Produksi - Accessories",
    "PRD-DISTRIBUSI": "Produksi - Distribusi",
    "PRD-GUDANGJADI": "Produksi - Gudang Jadi",
}

# 3. INFORMASI UMUM (SEKARANG ADA 3 KOLOM INPUT)
st.subheader("📋 1. Informasi Umum Inspeksi")
col1, col2, col3 = st.columns(3)
with col1:
    auditor = st.text_input("Nama Auditor/Inspektur:", placeholder="Contoh: Tim HSE")
with col2:
    factory_select = st.selectbox(
        "Pilih Lokasi Factory:",
        options=list(FACTORY_OPTIONS.keys()),
        format_func=lambda code: FACTORY_OPTIONS[code]
    )
with col3:
    area_select = st.selectbox(
        "Pilih Area Kerja / Fasilitas:",
        options=list(AREA_OPTIONS.keys()),
        format_func=lambda code: AREA_OPTIONS[code],
    )
    periode = "Juli 2026"  # Di-hardcode internal atau bisa disesuaikan nanti

st.markdown("---")
st.subheader("🔍 2. Parameter Kepatuhan K3 & Sosial")
st.write("Isi evaluasi kondisi riil di lantai pabrik saat ini:")

def hitung_skor_kepatuhan(persen: float) -> int:
    if persen >= 90: return 5
    if persen >= 80: return 4
    if persen >= 70: return 3
    if persen >= 60: return 2
    return 1

# --- PERTANYAAN 1 ---
st.markdown("### **P1. Aspek K3 - Proteksi Kebakaran**")
st.write("Apakah semua APAR di area kerja terpasang jelas, tidak terhalang barang, dan kartu inspeksi bulanan dalam kondisi aktif?")

total_apar_p1 = st.number_input("Total APAR yang diperiksa:", min_value=1, value=10, step=1, key="total_p1")

if "temuan_p1" not in st.session_state:
    st.session_state.temuan_p1 = 0

st.write("Temuan: APAR terhalang / rusak / kartu kontrol mati")
c1_p1, c2_p1, c3_p1 = st.columns([1, 2, 1])
with c1_p1:
    if st.button("➖", key="minus_p1"):
        st.session_state.temuan_p1 = max(0, st.session_state.temuan_p1 - 1)
with c2_p1:
    st.session_state.temuan_p1 = st.number_input(
        "Jumlah temuan P1", 
        min_value=0, 
        max_value=total_apar_p1, 
        value=st.session_state.temuan_p1, 
        step=1, 
        label_visibility="collapsed",
        key="input_manual_p1"
    )
with c3_p1:
    if st.button("➕", key="plus_p1"):
        st.session_state.temuan_p1 = min(total_apar_p1, st.session_state.temuan_p1 + 1)

temuan_p1 = st.session_state.temuan_p1
apar_patuh_p1 = total_apar_p1 - temuan_p1
persen_p1 = (apar_patuh_p1 / total_apar_p1) * 100
skor_1 = hitung_skor_kepatuhan(persen_p1)

mcol1_p1, mcol2_p1 = st.columns(2)
mcol1_p1.metric("Kepatuhan APAR", f"{persen_p1:.0f}%")
mcol2_p1.metric("Skor otomatis P1", skor_1)

catatan_1 = st.text_input("Catatan Temuan Lapangan P1 (Wajib jika skor < 4):", key="catat_p1", placeholder="Isi detail jika ada pelanggaran...")
foto_1 = None
if skor_1 < 4:
    st.warning("⚠️ **SHEVA AI Warning:** Kepatuhan di bawah standar! AI Agent akan otomatis menandai ini sebagai 'OPEN target' its dan memicu alert perbaikan.")
    foto_1 = st.file_uploader("📸 Unggah Foto Bukti Pelanggaran (Maks 5MB):", type=["jpg", "png", "jpeg"], key="foto_p1")

st.markdown("---")

# --- PERTANYAAN 2 ---
st.markdown("### **P2. Aspek K3 - Keamanan Mesin Produksi**")
st.write("Apakah seluruh mesin jahit (Sewing Machine) telah dilengkapi dengan komponen keselamatan standar seperti *finger guard* dan *pulley guard*?")

total_mesin_p2 = st.number_input("Total mesin sewing yang diperiksa:", min_value=1, value=100, step=1, key="total_p2")

if "temuan_p2" not in st.session_state:
    st.session_state.temuan_p2 = 0

st.write("Temuan: mesin tanpa needle guard / pulley guard yang sesuai")
c1_p2, c2_p2, c3_p2 = st.columns([1, 2, 1])
with c1_p2:
    if st.button("➖", key="minus_p2"):
        st.session_state.temuan_p2 = max(0, st.session_state.temuan_p2 - 1)
with c2_p2:
    st.session_state.temuan_p2 = st.number_input(
        "Jumlah temuan P2", 
        min_value=0, 
        max_value=total_mesin_p2, 
        value=st.session_state.temuan_p2, 
        step=1, 
        label_visibility="collapsed",
        key="input_manual_p2"
    )
with c3_p2:
    if st.button("➕", key="plus_p2"):
        st.session_state.temuan_p2 = min(total_mesin_p2, st.session_state.temuan_p2 + 1)

temuan_p2 = st.session_state.temuan_p2
mesin_patuh_p2 = total_mesin_p2 - temuan_p2
persen_p2 = (mesin_patuh_p2 / total_mesin_p2) * 100
skor_2 = hitung_skor_kepatuhan(persen_p2)

mcol1_p2, mcol2_p2 = st.columns(2)
mcol1_p2.metric("Kepatuhan Mesin", f"{persen_p2:.0f}%")
mcol2_p2.metric("Skor otomatis P2", skor_2)

catatan_2 = st.text_input("Catatan Temuan Lapangan P2 (Wajib jika skor < 4):", key="catat_p2", placeholder="Isi detail jika ada pelanggaran...")
foto_2 = None
if skor_2 < 4:
    st.warning(f"⚠️ **SHEVA AI Warning:** Kepatuhan {persen_p2:.0f}% (skor {skor_2}) — di bawah standar! AI Agent akan otomatis menandai ini sebagai 'OPEN target' dan memicu alert perbaikan.")
    foto_2 = st.file_uploader("📸 Unggah Foto Bukti Pelanggaran Mesin:", type=["jpg", "png", "jpeg"], key="foto_p2")

st.markdown("---")

# 4. LOGIKA SUBMIT
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
                waktu_submisi = datetime.now()
                timestamp_now = waktu_submisi.strftime("%Y-%m-%d %H:%M:%S")
                string_id_waktu = waktu_submisi.strftime("%Y%m%d%H%M%S")

                evidence_1 = foto_1.name if foto_1 is not None else ""
                evidence_2 = foto_2.name if foto_2 is not None else ""

                # FORMULASI KUNCI: Gabungkan kode factory dan kode area
                area_gabungan = f"{factory_select} / {area_select}"

                id_audit_1 = f"AUD-{string_id_waktu}-01"
                status_1 = "Closed" if skor_1 >= 4 else "Open"
                row_1 = [id_audit_1, timestamp_now, auditor, "Juli 2026", area_gabungan,
                         "I. HEALTH, SAFETY, ENVIRONMENT (HSE)", "1", "Proteksi APAR Lapangan",
                         str(apar_patuh_p1), str(total_apar_p1), str(skor_1), str(skor_1), "GOV-11", catatan_1, evidence_1,
                         status_1, ""]

                id_audit_2 = f"AUD-{string_id_waktu}-02"
                status_2 = "Closed" if skor_2 >= 4 else "Open"
                row_2 = [id_audit_2, timestamp_now, auditor, "Juli 2026", area_gabungan,
                         "I. HEALTH, SAFETY, ENVIRONMENT (HSE)", "2", "Finger Guard Mesin Sewing",
                         str(mesin_patuh_p2), str(total_mesin_p2), str(skor_2), str(skor_2), "SYS-04", catatan_2, evidence_2,
                         status_2, ""]

                # 1. Kirim data ke Google Sheets
                db_sheet.append_rows([row_1, row_2])

                # 2. INTEGRASI PERMANEN KE MAKE.COM WEBHOOK
                # Gantilah URL di bawah ini dengan URL asli dari modul Webhooks 1 Anda
                URL_WEBHOOK_MAKE = "https://hook.eu1.make.com/v0scqi2q6hjurane29w6i6yviohv1jke" 
                
                payload_webhook = {
                    "sumber_data": "STREAMLIT_AUDIT_APP",
                    "auditor": auditor,
                    "factory": factory_select,
                    "area": area_select,
                    "status_p1": status_1,
                    "status_p2": status_2
                }
                
                try:
                    requests.post(URL_WEBHOOK_MAKE, json=payload_webhook, timeout=5)
                except Exception:
                    pass  # Agar aplikasi tidak crash jika koneksi internet lokal ke Webhook tidak stabil

                st.balloons()
                st.success("🎉 BERHASIL! Data sukses terekam dengan klasifikasi Factory. Dashboard eksekutif siap disinkronkan.")
            except Exception as err:
                st.error(f"Gagal mengirim data: {err}")
