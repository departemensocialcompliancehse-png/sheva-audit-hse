import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json
import os

# ============================================================
# SHEVA HSE — VERSI DINAMIS (SEMUA 113 PERTANYAAN, 7 AREA)
# ============================================================
# File ini TERPISAH dari app.py (Golden Path 2 pertanyaan).
# Wajib diuji end-to-end dulu sebelum dipakai menggantikan Golden
# Path. Kalau ada kendala waktu, app.py tetap jadi cadangan aman.
# ============================================================

st.set_page_config(page_title="SHEVA HSE COMPLIANCE", page_icon="🛡️", layout="centered")

st.markdown("""
    <style>
    .stRadio p { font-size: 12pt !important; font-weight: bold !important; color: #1a365d !important; }
    .stButton button { font-weight: bold; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ SHEVA HSE & Social Compliance Digital Tools")
st.caption("PT Adira Semesta Industry - Integrated with SHEVA AI Agent System")
st.markdown("---")

# ------------------------------------------------------------
# 1. KONEKSI KE GOOGLE SHEETS
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# 2. MUAT QUESTION BANK (file lokal, tidak perlu baca Sheets
#    tiap kali form dibuka — lebih cepat & lebih sedikit titik gagal)
# ------------------------------------------------------------
QB_PATH = os.path.join(os.path.dirname(__file__), "question_bank.json")
try:
    with open(QB_PATH, encoding="utf-8") as f:
        QUESTION_BANK = json.load(f)
except Exception as e:
    st.error(f"❌ Gagal memuat question_bank.json: {e}. Pastikan file ini ada di folder yang sama dengan app_full_dynamic.py di repo GitHub.")
    st.stop()

AREA_LABELS = {
    "MT-LINE": "MT Line",
    "MT-RND": "MT R&D",
    "PRD-SEWING": "Produksi - Sewing",
    "PRD-CUTTING": "Produksi - Cutting",
    "PRD-ACCESSORIES": "Produksi - Accessories",
    "PRD-DISTRIBUSI": "Produksi - Distribusi",
    "PRD-GUDANGJADI": "Produksi - Gudang Jadi",
}

# ------------------------------------------------------------
# 3. INFORMASI UMUM
# ------------------------------------------------------------
st.subheader("📋 1. Informasi Umum Inspeksi")
col1, col2 = st.columns(2)
with col1:
    auditor = st.text_input("Nama Auditor/Inspektur:", placeholder="Contoh: Tim HSE")
    periode = st.selectbox("Periode Evaluasi:", ["Juli 2026", "Agustus 2026", "September 2026"])
with col2:
    area = st.selectbox(
        "Pilih Area Kerja / Fasilitas Pabrik:",
        options=list(AREA_LABELS.keys()),
        format_func=lambda code: f"{code} — {AREA_LABELS[code]}",
    )

questions = QUESTION_BANK.get(area, []) + QUESTION_BANK.get("ALL", [])

st.markdown("---")
st.subheader(f"🔍 2. Checklist ({len(questions)} pertanyaan — {AREA_LABELS.get(area, area)})")
st.caption("Semua pertanyaan di bawah wajib diisi. Skor kepatuhan (%) dihitung otomatis; pertanyaan lain dinilai dari deskripsi rubrik resmi, bukan pilih angka bebas.")

# ------------------------------------------------------------
# 4. FUNGSI BANTUAN
# ------------------------------------------------------------
def hitung_skor_dari_persen(rubrik, persen):
    # rubrik = list of {'skor','desc','pct'} terurut dari skor besar ke kecil
    for tingkat in rubrik:
        if tingkat["pct"] is not None and persen >= tingkat["pct"]:
            return tingkat["skor"]
    return 1

# ------------------------------------------------------------
# 5. RENDER SEMUA PERTANYAAN (di luar st.form — supaya warning
#    & uploader foto muncul REAL-TIME, bukan telat, sama seperti
#    yang sudah diperbaiki di app.py)
# ------------------------------------------------------------
jawaban = []  # menampung hasil tiap pertanyaan untuk disubmit nanti

for i, q in enumerate(questions):
    key_prefix = f"q{i}_{q['no']}"
    with st.container(border=True):
        badge = q["reg"] if q["reg"] else "—"
        st.markdown(f"**{q['pertanyaan']}**  \n<span style='font-size:11px;color:gray'>{q['aspek']} · Ref: {badge}</span>", unsafe_allow_html=True)

        skor = None
        numerator = ""
        denominator = ""

        if q["mode"] == "counter":
            total = st.number_input("Total unit/objek diperiksa:", min_value=1, value=10, step=1, key=f"total_{key_prefix}")
            count_key = f"temuan_{key_prefix}"
            if count_key not in st.session_state:
                st.session_state[count_key] = 0
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                if st.button("➖", key=f"minus_{key_prefix}"):
                    st.session_state[count_key] = max(0, st.session_state[count_key] - 1)
            with c2:
                st.markdown(f"<div style='text-align:center;font-size:22px;font-weight:bold'>{st.session_state[count_key]} temuan</div>", unsafe_allow_html=True)
            with c3:
                if st.button("➕", key=f"plus_{key_prefix}"):
                    st.session_state[count_key] = min(total, st.session_state[count_key] + 1)

            temuan = st.session_state[count_key]
            patuh = total - temuan
            persen = (patuh / total) * 100
            skor = hitung_skor_dari_persen(q["rubrik"], persen)
            numerator, denominator = patuh, total

            m1, m2 = st.columns(2)
            m1.metric("Kepatuhan", f"{persen:.0f}%")
            m2.metric("Skor otomatis", skor)

        else:  # mode "pilih" — dipandu deskripsi rubrik resmi, bukan pilih angka bebas
            opsi = [f"{t['skor']} — {t['desc']}" for t in sorted(q["rubrik"], key=lambda x: -x["skor"])]
            pilihan = st.radio("Pilih kondisi yang paling sesuai temuan lapangan:", options=opsi, index=0, key=f"pilih_{key_prefix}")
            skor = int(pilihan.split(" — ")[0])

        catatan = st.text_input("Catatan temuan (wajib jika skor < 4):", key=f"catatan_{key_prefix}")
        foto = None
        if skor < 4:
            st.warning(f"⚠️ **SHEVA AI Warning:** Skor {skor} — di bawah standar. Wajib lampirkan bukti foto & catatan.")
            foto = st.file_uploader("📸 Unggah foto bukti:", type=["jpg", "jpeg", "png"], key=f"foto_{key_prefix}")

        jawaban.append({
            "no": q["no"], "aspek": q["aspek"], "pertanyaan": q["pertanyaan"], "reg": q["reg"],
            "skor": skor, "numerator": numerator, "denominator": denominator,
            "catatan": catatan, "foto": foto,
        })

st.markdown("---")
submit_btn = st.button("🚀 SUBMIT SELURUH AUDIT KE SHEVA AI DATABASE", use_container_width=True)

if submit_btn:
    errors = []
    if not auditor:
        errors.append("Nama Auditor tidak boleh kosong.")
    for j in jawaban:
        if j["skor"] < 4:
            if not j["catatan"]:
                errors.append(f"Catatan wajib diisi untuk: {j['pertanyaan'][:60]}...")
            if j["foto"] is None:
                errors.append(f"Foto bukti wajib diunggah untuk: {j['pertanyaan'][:60]}...")

    if errors:
        for e in errors:
            st.error(f"❌ {e}")
    else:
        with st.spinner(f"Mengirim {len(jawaban)} baris data ke database sentral..."):
            try:
                timestamp_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                rows = []
                for idx, j in enumerate(jawaban, start=1):
                    id_audit = f"AUD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{idx:03d}"
                    status = "Closed" if j["skor"] >= 4 else "Open"
                    evidence = j["foto"].name if j["foto"] is not None else ""
                    rows.append([
                        id_audit, timestamp_now, auditor, periode, area,
                        j["aspek"], str(j["no"]), j["pertanyaan"],
                        str(j["numerator"]), str(j["denominator"]),
                        str(j["skor"]), str(j["skor"]), j["reg"],
                        j["catatan"], evidence, status, "",
                    ])
                db_sheet.append_rows(rows)
                st.balloons()
                st.success(f"🎉 BERHASIL! {len(rows)} baris data audit tersimpan. SHEVA AI Agent sedang memproses sinkronisasi dasbor eksekutif.")
            except Exception as err:
                st.error(f"Gagal mengirim data: {err}")
