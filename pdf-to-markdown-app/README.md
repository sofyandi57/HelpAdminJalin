# PDF → Markdown

Aplikasi Streamlit untuk mengubah file PDF langsung menjadi Markdown (.md):
1. Upload satu atau banyak PDF sekaligus.
2. PDF dengan text layer (PDF digital biasa, bukan hasil scan) dikonversi
   langsung dengan deteksi heading, tabel, dan teks tebal (via `pymupdf4llm`).
3. PDF hasil scan/foto (tidak ada text layer) otomatis di-OCR dulu dengan
   Tesseract sebelum digabung jadi Markdown.
4. Hasilnya bisa dilihat langsung (preview + markdown mentah) dan diunduh
   sebagai `.md` satuan atau `.zip` jika lebih dari satu file.

## 1. Instalasi

### a. Python
Butuh Python 3.10+. Cek dengan:
```bash
python --version
```

### b. Tesseract OCR (WAJIB untuk PDF hasil scan/foto)
Install via winget:
```bash
winget install UB-Mannheim.TesseractOCR
```
Atau download installer manual dari: https://github.com/UB-Mannheim/tesseract/wiki

**Bahasa Indonesia untuk OCR:**
Download `ind.traineddata` dari https://github.com/tesseract-ocr/tessdata_fast
dan taruh di folder `tessdata` instalasi Tesseract
(mis. `%LOCALAPPDATA%\Programs\Tesseract-OCR\tessdata`).

Jika PDF kamu semuanya PDF digital (bukan hasil scan), Tesseract tidak wajib —
aplikasi tetap bisa jalan, hanya fitur OCR yang tidak aktif.

### c. Library Python
Di folder proyek ini, jalankan:
```bash
pip install -r requirements.txt
```

## 2. Menjalankan aplikasi

**Cara paling gampang (tanpa install Python sama sekali):** double-click
`dist\PDF-to-Markdown.exe`. Ini versi standalone hasil build — semua library
sudah dibundel di dalamnya. Akan muncul jendela terminal (biarkan terbuka
selama pakai aplikasi) lalu browser otomatis terbuka ke
`http://localhost:8501`. Tutup jendela terminal untuk mematikan aplikasi.
Tesseract OCR **tetap perlu diinstall terpisah** di komputer (lihat bagian
b di atas) kalau mau proses PDF hasil scan — .exe ini tidak membundel
Tesseract-nya.

**Cara double-click (perlu Python & library terpasang):** buka folder ini di
File Explorer lalu double-click `jalankan.bat`. Script ini otomatis pasang
library yang kurang lalu menjalankan aplikasinya — tidak perlu setting PATH
Python manual.

**Cara manual (terminal):**
```bash
streamlit run app.py
```
Kalau muncul error `python`/`streamlit` tidak dikenali, berarti Python belum
ada di PATH — pakai path lengkap ke `python.exe` kamu, misalnya:
```bash
"C:\Users\sofyandi.sedar\AppData\Local\Programs\Python\Python312\python.exe" -m streamlit run app.py
```
Browser akan terbuka otomatis (biasanya di `http://localhost:8501`).

## 3. Cara pakai
- Upload PDF (bisa pilih banyak file sekaligus).
- Klik **Konversi ke Markdown**.
- Lihat hasil per file: badge menunjukkan apakah file diproses lewat text
  layer langsung atau lewat OCR, beserta jumlah halaman.
- Tab **Preview** menampilkan hasil Markdown yang sudah dirender, tab
  **Markdown mentah** menampilkan teks `.md` apa adanya.
- Download tiap file sebagai `.md`, atau download semua sekaligus sebagai
  `.zip` kalau lebih dari satu file diproses.
- File yang gagal diproses akan menampilkan pesan error tanpa menghentikan
  file lain di batch yang sama.

## 4. Struktur file
- `app.py` — antarmuka Streamlit.
- `pdf_to_markdown.py` — logika inti: deteksi text layer, OCR fallback,
  konversi ke Markdown, dan pembersihan hasil.
- `ocr_utils.py` — deteksi lokasi instalasi Tesseract OCR.
- `run_app.py` — launcher yang dipakai saat dibungkus jadi `.exe`.
- `PDF-to-Markdown.spec` — konfigurasi build PyInstaller.
- `dist\PDF-to-Markdown.exe` — hasil build standalone (~46 MB, satu file).

## 5. Build ulang .exe (kalau ada perubahan kode)
```bash
"C:\Users\sofyandi.sedar\AppData\Local\Programs\Python\Python312\python.exe" -m PyInstaller PDF-to-Markdown.spec --noconfirm
```
Hasilnya ada di `dist\PDF-to-Markdown.exe`.

## 6. Catatan & keterbatasan
- PDF hasil OCR tidak mendapat deteksi struktur (heading/tabel) — hanya teks
  polos per halaman (ditandai komentar `<!-- page N -->` yang tidak muncul
  saat Markdown dirender).
- Deteksi "punya text layer atau tidak" berdasarkan rata-rata jumlah karakter
  per halaman; PDF hasil scan yang sudah punya text layer tersembunyi (mis.
  dari OCR sebelumnya) akan dianggap sebagai PDF digital.
- Untuk deploy online: cara paling stabil adalah **Streamlit Community
  Cloud** (gratis, tinggal hubungkan ke GitHub) karena Streamlit butuh server
  Python yang jalan terus — Vercel (serverless/static) tidak cocok untuk
  aplikasi Streamlit biasa.
