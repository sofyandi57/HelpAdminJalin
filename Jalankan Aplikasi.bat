@echo off
cd /d "%~dp0ocr-pdf-app"
echo Menjalankan OCR PDF PO... Jangan tutup jendela ini selagi memakai aplikasinya.
"C:\Users\sofyandi.sedar\AppData\Local\Programs\Python\Python312\python.exe" -m streamlit run app.py
pause
