"""
Aplikasi sederhana: kumpulkan banyak PDF -> OCR -> tabel CSV/Excel.
Jalankan dengan: streamlit run app.py
"""

import glob
import os
import sys

import pandas as pd
import streamlit as st

from ocr_utils import configure_tesseract
from po_extract import COLUMNS, extract_po

# Saat dibungkus jadi .exe (PyInstaller), __file__ mengarah ke folder ekstraksi
# sementara yang hilang tiap tutup aplikasi — simpan output di sebelah .exe-nya.
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CUMULATIVE_XLSX = os.path.join(OUTPUT_DIR, "hasil_ocr.xlsx")
CUMULATIVE_CSV = os.path.join(OUTPUT_DIR, "hasil_ocr.csv")

st.set_page_config(page_title="OCR PDF Massal", layout="wide")
st.title("📄 Kumpulkan PDF PO → OCR → Excel Terstruktur")
st.caption(
    "Upload banyak PDF Purchase Order sekaligus (atau proses seluruh folder), "
    "OCR otomatis membaca PO NO, PR NO, tanggal, vendor, item barang/jasa, "
    "sampai Sub Total/VAT/Jumlah Total ke dalam tabel siap diunduh sebagai CSV/Excel."
)

# --- Cek Tesseract ---
tesseract_cmd = configure_tesseract()
if not tesseract_cmd:
    st.warning(
        "⚠️ Tesseract OCR tidak ditemukan di komputer ini. PDF hasil scan/gambar "
        "tidak akan bisa di-OCR (PDF teks digital tetap bisa diekstrak langsung). "
        "Lihat README.md untuk cara instalasi Tesseract OCR."
    )
else:
    st.success(f"Tesseract OCR terdeteksi: {tesseract_cmd}")

# --- Sidebar pengaturan ---
st.sidebar.header("Pengaturan")
lang = st.sidebar.selectbox(
    "Bahasa OCR",
    options=["ind+eng", "ind", "eng"],
    index=0,
    help="Butuh file bahasa 'ind' (Indonesia) terpasang di Tesseract. Lihat README.",
)
dpi = st.sidebar.slider("Resolusi render (DPI) untuk OCR", 150, 400, 300, step=50)
st.sidebar.caption(
    "Parser ini dikalibrasi untuk template PO 'PT Jalin Pembayaran Nusantara' "
    "(hasil scan). Format PO lain kemungkinan perlu penyesuaian regex di po_extract.py."
)

st.sidebar.divider()
mode = st.sidebar.radio("Sumber PDF", ["Upload file", "Folder di komputer"])

pdf_inputs = []  # list of (filename, bytes_or_path)

if mode == "Upload file":
    uploaded_files = st.file_uploader(
        "Upload PDF (bisa pilih banyak sekaligus)", type=["pdf"], accept_multiple_files=True
    )
    if uploaded_files:
        pdf_inputs = [(f.name, f.read()) for f in uploaded_files]
else:
    folder_path = st.text_input(
        "Path folder berisi PDF (akan diproses semua PDF di dalamnya, termasuk sub-folder)",
        placeholder=r"contoh: C:\Users\nama\Documents\ArsipPDF",
    )
    if folder_path and os.path.isdir(folder_path):
        found = sorted(glob.glob(os.path.join(folder_path, "**", "*.pdf"), recursive=True))
        st.info(f"Ditemukan {len(found)} file PDF di folder tersebut.")
        pdf_inputs = [(os.path.relpath(p, folder_path), p) for p in found]
    elif folder_path:
        st.error("Folder tidak ditemukan.")

st.divider()

if pdf_inputs:
    st.write(f"**{len(pdf_inputs)} file siap diproses.**")
    process_clicked = st.button("🚀 Proses OCR", type="primary")
else:
    process_clicked = False

if process_clicked:
    progress = st.progress(0.0, text="Memulai...")
    rows = []
    for i, (name, source) in enumerate(pdf_inputs):
        progress.progress(i / len(pdf_inputs), text=f"Memproses: {name}")
        rows.extend(extract_po(source, name, dpi=dpi, lang=lang))
    progress.progress(1.0, text="Selesai.")

    df = pd.DataFrame(rows)[COLUMNS]
    st.session_state["hasil_df"] = df

if "hasil_df" in st.session_state:
    df = st.session_state["hasil_df"]
    st.subheader("Hasil")

    n_error = (df["Error"] != "").sum()
    if n_error:
        st.warning(f"{n_error} file gagal diproses sepenuhnya — lihat kolom Error.")

    st.dataframe(
        df,
        use_container_width=True,
        height=min(450, 60 + 35 * len(df)),
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "⬇️ Download CSV",
            df.to_csv(index=False).encode("utf-8-sig"),
            file_name="hasil_ocr.csv",
            mime="text/csv",
        )
    with col2:
        buf = pd.io.common.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Hasil OCR")
        st.download_button(
            "⬇️ Download Excel",
            buf.getvalue(),
            file_name="hasil_ocr.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with col3:
        if st.button("💾 Tambahkan ke dataset kumulatif (output/hasil_ocr.xlsx)"):
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            if os.path.isfile(CUMULATIVE_XLSX):
                existing = pd.read_excel(CUMULATIVE_XLSX)
                combined = pd.concat([existing, df], ignore_index=True)
            else:
                combined = df
            combined.to_excel(CUMULATIVE_XLSX, index=False)
            combined.to_csv(CUMULATIVE_CSV, index=False, encoding="utf-8-sig")
            st.success(f"Tersimpan. Total baris di dataset kumulatif: {len(combined)}")
