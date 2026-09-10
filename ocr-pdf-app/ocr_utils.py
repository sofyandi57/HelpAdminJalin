"""Deteksi dan konfigurasi lokasi Tesseract OCR di komputer ini."""

import os
import shutil

import pytesseract


def find_tesseract_cmd():
    """Cari lokasi tesseract.exe: PATH dulu, lalu lokasi instalasi default Windows."""
    found = shutil.which("tesseract")
    if found:
        return found
    default_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    for p in default_paths:
        if os.path.isfile(p):
            return p
    return None


def configure_tesseract():
    cmd = find_tesseract_cmd()
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd
    return cmd
