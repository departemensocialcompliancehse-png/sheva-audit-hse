import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime

# 1. SETUP KONFIGURASI HALAMAN (RAMAH MOBILE)
st.set_page_config(page_title="SHEVA HSE Audit", page_icon="📱", layout="centered")

st.title("📱 SHEVA HSE Audit Checklist")
st.write("Sistem Digitalisasi Audit Compliance PT Adira Semesta Industry")
st.markdown("---")

# 2. KONEKSI KE GOOGLE SHEETS VIA STREAMLIT SECRETS
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Mengambil kredensial dari sistem rahasia Streamlit (nanti kita setup di akhir)
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # Membuka Spreadsheet Utama Anda (Ganti teks di bawah jika nama file di Drive berbeda)
    sheet = client.open("RENCANA PENGEMBANGAN SHEVA")
    db_sheet = sheet.worksheet("AUDIT_CHECKLIST_DATABASE")
    q_sheet = sheet.worksheet("Question_Bank")
except Exception as e:
    st.error(f"❌ Gagal koneksi ke database: {e}")
    st.stop()

# 3. FORM IDENTITAS AWAL AUDITOR
with st.form("form_audit"):
    st.subheader("📋 Informasi Umum Audit")
    auditor = st.text_input("Nama Auditor", placeholder="Contoh: Budi Santoso")
    
    # Dropdown bulan berjalan di 2026
    periode = st.selectbox("Periode/Bulan Audit", ["Juli 2026", "Agustus 2026", "September 2026"])
    
    # Pilihan area uji coba (Pilot Project)
    area = st.selectbox("Pilih Area Kerja Pabrik", ["PRD-SEWING", "PRD-CUTTING", "MAINTENANCE", "WAREHOUSE"])
    
    st.markdown("---")
    st.subheader("🔍 Pertanyaan Evaluasi Lapangan")
    
    # Simulasi pertanyaan (di fase rincian nanti ini ditarik otomatis dari tab Question_Bank)
    st.write("**Pertanyaan 1 (HSE):** Apakah semua mesin jahit telah dilengkapi dengan finger guard?")
    skor_1 = st.radio("Skor Kepatuhan P1:", options=[1, 2, 3, 4, 5], index=4, key="p1", horizontal=True)
    catatan_1 = st.text_input("Catatan Temuan P1 (Opsional)", key="c1")
    
    # Logika efisiensi foto: Muncul hanya jika ada temuan (skor di bawah 4)
    foto_link_1 = ""
    if skor_1 < 4:
        st.warning("⚠️ Skor di bawah 4 wajib mencantumkan catatan detail temuan.")
        file_foto = st.file_uploader("📸 Ambil Foto Bukti Temuan P1:", type=["jpg", "png", "jpeg"], key="f1")
        if file_foto:
            foto_link_1 = "https://drive.google.com/mock_link_uploaded" # Simulasi link
            st.success("✅ Foto berhasil direkam!")

    st.markdown("---")
    
    # Tombol Kirim Data Besar
    submit_btn = st.form_submit_button("🚀 SUBMIT HASIL AUDIT")
    
    if submit_btn:
        if not auditor:
            st.error("❌ Nama Auditor tidak boleh kosong!")
        else:
            # Menyusun data sesuai susunan 17 kolom spreadsheet Anda
            # ['ID_Audit', 'Timestamp', 'Auditor', 'Periode', 'Area_Kode', 'Aspek', 'No_Pertanyaan', 'Pertanyaan', ...]
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            id_audit = f"AUD-{datetime.now().strftime('%Y%m%d')}-001"
            status_tl = "Closed" if skor_1 >= 4 else "Open"
            
            baris_data = [
                id_audit, timestamp, auditor, periode, area, 
                "HSE", "1", "Apakah semua mesin jahit telah dilengkapi dengan finger guard?", 
                "", "", str(skor_1), str(skor_1), "REG-001", catatan_1, foto_link_1, status_tl, ""
            ]
            
            # Memasukkan data ke Google Sheets
            db_sheet.append_row(baris_data)
            st.balloons()
            st.success("🎉 Data Berhasil Disimpan Ke Google Sheets!")
