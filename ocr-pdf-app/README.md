# OCR PDF Purchase Order → Excel Terstruktur

Aplikasi Streamlit untuk:
1. Mengumpulkan banyak file PDF Purchase Order sekaligus (upload atau proses satu folder penuh).
2. OCR otomatis (untuk PDF hasil scan) membaca field-field PO ke kolom terpisah.
3. Menyimpan hasilnya ke tabel yang bisa diunduh sebagai CSV atau Excel — satu baris per item barang/jasa.

Kolom yang dihasilkan: **PO NO, PR NO, Tanggal PO, Tgl Maks Pengiriman, Termin
Pembayaran, Nama Vendor, Alamat Vendor, Deskripsi, Jumlah, Harga, Total, Sub
Total, VAT, Jumlah Total, Spesifikasi** (plus `Nama File` dan `Error`).

## 1. Cara pakai (tanpa buka terminal) — `Jalankan Aplikasi.bat`

Cukup **double-click `Jalankan Aplikasi.bat`** di folder `PDF Extractor` (satu
folder di atas folder ini). Tidak perlu mengetik perintah apa pun.

- Sebuah jendela hitam (command prompt) akan muncul dan menampilkan proses
  startup — **biarkan terbuka**, itu bagian normal dari aplikasi berjalan.
  Jendela browser akan otomatis terbuka ke `http://localhost:8501` begitu siap.
- Untuk menutup aplikasi: tutup jendela command prompt hitam tadi (atau
  tekan Ctrl+C lalu Enter di dalamnya).
- Hasil ekstraksi kumulatif tersimpan di folder `ocr-pdf-app/output/`.
- Prasyarat: **Python** dan **Tesseract OCR** harus sudah terpasang di
  komputer ini (lihat bagian 2 dan 3 di bawah) — keduanya sudah terpasang
  di komputer ini sejak pengaturan awal.

> **Catatan:** Sebelumnya dicoba dibungkus jadi satu file `.exe` standalone
> (pakai PyInstaller) supaya tidak perlu Python sama sekali, tapi di komputer
> ini file .exe hasil build sendiri **diblokir tanpa peringatan** oleh
> antivirus/endpoint-security perusahaan saat dijalankan lewat double-click
> di File Explorer (executable custom & belum bersertifikat memang sering
> kena heuristik seperti ini). File `.bat` ini hanya memanggil `python.exe`
> yang sudah terpasang & dikenali sistem, sehingga tidak terblokir.

## 2. Python
Butuh Python 3.10+. Cek dengan:
```bash
python --version
```
Jika belum ada, install dari https://www.python.org/downloads/ (centang "Add Python to PATH" saat instalasi) atau via winget:
```bash
winget install Python.Python.3.12
```
Lalu install library yang dibutuhkan (sekali saja):
```bash
pip install -r requirements.txt
```

## 3. Tesseract OCR (mesin OCR)
Install via winget:
```bash
winget install UB-Mannheim.TesseractOCR
```
Atau download installer manual dari: https://github.com/UB-Mannheim/tesseract/wiki

Aplikasi otomatis mendeteksi lokasi instalasi standar.

**Bahasa Indonesia untuk OCR (wajib untuk parser PO ini):**
Download `ind.traineddata` dari https://github.com/tesseract-ocr/tessdata_fast
dan taruh di folder `tessdata` instalasi Tesseract
(mis. `%LOCALAPPDATA%\Programs\Tesseract-OCR\tessdata`).

## 4. Menjalankan langsung dari terminal (alternatif untuk pengembangan)
```bash
streamlit run app.py
```

## 5. Build jadi .exe standalone (opsional — tidak disarankan di komputer ini)
`run_app.py` dan `OCR-PO-Extractor.spec` masih tersedia bila suatu saat ingin
dicoba lagi di komputer LAIN yang tidak memblokir executable unsigned:
```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --name "OCR-PO-Extractor" ^
  --add-data "app.py;." --add-data "po_extract.py;." --add-data "ocr_utils.py;." ^
  --collect-all streamlit --collect-all altair --collect-all pyarrow ^
  --hidden-import pytesseract --hidden-import fitz --collect-all fitz ^
  --hidden-import PIL --hidden-import PIL.Image --collect-all PIL ^
  --hidden-import pandas --collect-all pandas ^
  --hidden-import openpyxl --collect-all openpyxl ^
  run_app.py
```
File .exe baru akan muncul di `dist/OCR-PO-Extractor.exe`.

## 6. Cara pakai (di dalam aplikasi)
- Pilih sumber PDF: upload langsung, atau masukkan path folder di komputer
  (berguna untuk memproses ratusan/ribuan file sekaligus tanpa upload manual).
- Klik **Proses OCR**.
- Lihat hasil di tabel (satu baris per item barang/jasa dalam PO; field header
  seperti PO NO/Vendor/Sub Total diulang di tiap baris item pada PO yang sama).
- Download hasil sebagai CSV/Excel, atau simpan ke dataset kumulatif
  (`output/hasil_ocr.xlsx`) yang akan terus bertambah setiap kali diproses.
- Baris dengan isi kolom `Error` berarti PDF tersebut gagal diproses (mis. rusak
  atau bukan PDF) — file lain di batch yang sama tetap diproses normal.

## 7. Struktur file
- `Jalankan Aplikasi.bat` (di folder induk) — cara utama menjalankan aplikasi.
- `app.py` — antarmuka Streamlit (source code).
- `po_extract.py` — parser inti: OCR + regex + deteksi posisi piksel untuk
  memisahkan field-field PO (lihat catatan kalibrasi di bawah).
- `ocr_utils.py` — deteksi lokasi instalasi Tesseract OCR.
- `run_app.py` / `OCR-PO-Extractor.spec` — sisa percobaan build .exe standalone
  (lihat bagian 5) — tidak dipakai oleh jalur `.bat`.
- `output/` — tempat dataset kumulatif hasil OCR disimpan.

## 8. Catatan kalibrasi & keterbatasan
Parser ini dikalibrasi dari 2 contoh PO template **"PT Jalin Pembayaran
Nusantara"** (hasil scan, bukan PDF digital). Beberapa hal yang perlu diketahui:

- **Khusus 1 template.** Jika suatu saat format PO berubah (posisi kotak
  Kepada/PO NO, urutan tabel item, dsb.), regex di `po_extract.py`
  (fungsi `parse_header_block`, `parse_body`) mungkin perlu disesuaikan lagi.
- **Deskripsi item** hanya mengambil baris pertama tiap item (mis. "Lisensi
  Configuration Management"), tidak menyertakan baris rincian lanjutan yang
  terpisah (mis. "Perpetual On Premise (unlimited users)") — detail itu
  biasanya sudah tercakup di kolom Spesifikasi/Termin Pembayaran.
- **Angka romawi** (bulan dalam PO NO/PR NO, mis. "XI") kadang terbaca salah
  oleh OCR sebagai "X1" — periksa ulang untuk nomor PO yang penting.
- Sub Total/VAT/Jumlah Total diambil dari kemunculan pertama masing-masing
  label di seluruh halaman dokumen.

## 9. Rencana pengembangan lanjutan
- Klasifikasi/pengelompokan PO (mis. per vendor atau kategori pengadaan) bisa
  ditambahkan di atas tabel hasil ini.
- Kalibrasi ulang atau parser terpisah untuk template PO dari perusahaan lain.
- Validasi otomatis (mis. Sub Total + VAT harus sama dengan Jumlah Total) untuk
  menandai baris yang OCR-nya mencurigakan.
