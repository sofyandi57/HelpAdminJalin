# OCR PO Extractor — Lite (versi .exe ringkas, <50MB)

Versi ringan dari aplikasi OCR PDF PO, dibuat khusus supaya bisa dibungkus jadi
satu file `.exe` di bawah 50MB — cocok dikirim lewat email/chat.

## Apa yang beda dari versi utama (`ocr-pdf-app/`)

| | Versi utama (Streamlit) | Versi Lite (ini) |
|---|---|---|
| Tampilan | Halaman web (browser) | Jendela aplikasi desktop biasa (Tkinter) |
| Ukuran .exe | Tidak dibungkus jadi .exe (pakai .bat) | **34MB** (`OCR-PO-Extractor-Lite.exe`) |
| pandas/numpy | Dipakai | **Tidak dipakai** — export CSV/Excel manual (`csv` + `openpyxl`) |
| Tesseract OCR | Deteksi otomatis, atau ikut di paket offline | **Wajib sudah terpasang terpisah** di komputer (lihat di bawah) — tidak ikut dibundel ke exe |
| Logika ekstraksi PO | `po_extract.py` | **Sama persis** (file yang sama) |

Hasil ekstraksi (kolom PO NO, PR NO, Vendor, item, dll) identik dengan versi
utama — hanya cara pakai & pembungkusannya yang beda.

## Cara pakai

1. Pastikan **Tesseract OCR** sudah terpasang di komputer (lihat README utama
   di `../ocr-pdf-app/README.md` bagian instalasi Tesseract — perintahnya:
   `winget install UB-Mannheim.TesseractOCR`, lalu tambahkan data bahasa
   Indonesia). Ini WAJIB — versi Lite tidak membawa Tesseract di dalam .exe.
2. Double-click `OCR-PO-Extractor-Lite.exe` (di folder induk `PDF Extractor`).
3. Klik **Tambah File PDF...** atau **Tambah dari Folder...**.
4. Klik **Proses OCR**, tunggu sampai selesai.
5. Klik **Simpan sebagai CSV** / **Simpan sebagai Excel**, atau **Tambahkan ke
   dataset kumulatif** (tersimpan di folder `output/` di sebelah .exe).

## ⚠️ Catatan penting: risiko diblokir antivirus tetap ada

Ini tetap sebuah **.exe hasil PyInstaller yang tidak bersertifikat (unsigned)**.
Percobaan sebelumnya (`OCR-PO-Extractor.exe`, versi lama) sempat **diblokir
diam-diam** oleh antivirus/endpoint-security saat di-double-click langsung dari
File Explorer — bukan karena ukurannya, tapi karena heuristik terhadap
executable custom yang di-pack. Mengecilkan ukuran **tidak menjamin** masalah
itu tidak terulang di sini.

**Jika di-double-click dan tidak ada reaksi sama sekali** (seperti kejadian
sebelumnya): kemungkinan besar terblokir lagi, dan solusi yang sudah terbukti
jalan adalah pakai `Jalankan Aplikasi.bat` di `ocr-pdf-app/` (memanggil Python
biasa, bukan .exe custom).

## Build ulang
```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --name "OCR-PO-Extractor-Lite" ^
  --hidden-import pytesseract --hidden-import fitz --collect-all fitz ^
  --hidden-import PIL --hidden-import PIL.Image --collect-all PIL ^
  --hidden-import openpyxl --collect-all openpyxl ^
  --exclude-module pandas --exclude-module numpy --exclude-module pyarrow ^
  --exclude-module streamlit --exclude-module altair --exclude-module matplotlib ^
  --exclude-module scipy ^
  gui_app.py
```
**Penting:** flag `--exclude-module` di atas wajib ada kalau lingkungan Python
yang dipakai build juga punya pandas/numpy/streamlit terpasang (mis. karena
komputer yang sama dipakai untuk versi utama) — tanpa itu, PyInstaller ikut
membundel pandas/numpy/pyarrow (~100MB) walau kodenya tidak butuh sama sekali,
dan ukuran akan balik ke ~85MB.
