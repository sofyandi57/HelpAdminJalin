import re
import io
import fitz
import pytesseract
from PIL import Image

from ocr_utils import configure_tesseract

configure_tesseract()

HEADER_LABEL_RE = re.compile(r"^(PO\.?\s*NO|PR\.?\s*NO|Tanggal\s*PO|Tgl\.?\s*Maks\.?\s*Pengiriman|Kepada|Telephon|Atensi)\b[\s:]*", re.IGNORECASE)
NUM = r"[\d]{1,3}(?:[.,]\s?\d{2,3})*"
ITEM_ROW_RE = re.compile(r"^(\d{1,3})\s+(.+?)\s+(" + NUM + r")\s+IDR\s+(" + NUM + r")\s+IDR\s+(" + NUM + r")\s*$")
NUM_AFTER_LABEL_RE = lambda label: re.compile(label + r"\D{0,15}?(" + NUM + r")", re.IGNORECASE)


def clean_num(s):
    return re.sub(r"\s+", "", s) if s else s


def clean_text(s):
    if not s:
        return s
    s = re.sub(r"[�“”‘’]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def render_page(page, dpi=300):
    zoom = dpi / 72
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    return Image.open(io.BytesIO(pix.tobytes("png")))


def get_lines(img, psm=4, lang="ind+eng"):
    data = pytesseract.image_to_data(img, lang=lang, config=f"--psm {psm}", output_type=pytesseract.Output.DICT)
    groups = {}
    n = len(data["text"])
    for i in range(n):
        text = data["text"][i].strip()
        if not text:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        g = groups.setdefault(key, {"words": [], "top": data["top"][i], "bottom": data["top"][i] + data["height"][i], "left": data["left"][i]})
        g["words"].append(text)
        g["bottom"] = max(g["bottom"], data["top"][i] + data["height"][i])
        g["left"] = min(g["left"], data["left"][i])
    lines = []
    for g in groups.values():
        lines.append({"text": " ".join(g["words"]), "top": g["top"], "bottom": g["bottom"], "left": g["left"]})
    lines.sort(key=lambda l: l["top"])
    return lines


def parse_header_block(page, dpi=300, lang="ind+eng"):
    img = render_page(page, dpi)
    w, h = img.size
    crop = img.crop((int(w * 0.50), int(h * 0.05), w, int(h * 0.42)))
    text = pytesseract.image_to_string(crop, lang=lang, config="--psm 6")

    result = {"PO NO": "", "PR NO": "", "Tanggal PO": "", "Tgl Maks Pengiriman": "", "Nama Vendor": "", "Alamat Vendor": ""}

    def line_value(label_pattern, src_text):
        m = re.search(label_pattern + r"\s*:?\s*([^\n]+)", src_text, re.IGNORECASE)
        return m.group(1).strip() if m else ""

    result["PO NO"] = line_value(r"PO\.?\s*NO", text)
    result["PR NO"] = line_value(r"PR\.?\s*NO", text)
    result["Tanggal PO"] = line_value(r"Tanggal\s*PO", text)
    result["Tgl Maks Pengiriman"] = line_value(r"Tgl\.?\s*Maks\.?\s*Pengiriman", text)

    lines = [l.strip() for l in text.splitlines()]
    vendor_start = None
    for i, l in enumerate(lines):
        if re.match(r"^Kepada\b", l, re.IGNORECASE):
            vendor_start = i
            break
    if vendor_start is not None:
        first = re.sub(r"^Kepada\s*:?\s*", "", lines[vendor_start], flags=re.IGNORECASE).strip()
        result["Nama Vendor"] = first
        addr_lines = []
        for l in lines[vendor_start + 1:]:
            if not l.strip():
                continue
            if re.match(r"^(Telephon|Atensi)\b", l, re.IGNORECASE):
                break
            addr_lines.append(l.strip())
        result["Alamat Vendor"] = ", ".join(addr_lines)

    return result


def parse_body(doc, dpi=300, lang="ind+eng"):
    termin = ""
    spesifikasi = ""
    sub_total = ""
    vat = ""
    jumlah_total = ""
    items = {}

    page_width = None

    for page_index in range(doc.page_count):
        page = doc.load_page(page_index)
        img = render_page(page, dpi)
        w, h = img.size
        page_width = w
        lines = get_lines(img, psm=4, lang=lang)

        item_header_top = None
        for l in lines:
            if re.search(r"Deskripsi", l["text"], re.IGNORECASE) and re.search(r"Jumlah|Harga", l["text"], re.IGNORECASE):
                item_header_top = l["top"]
                break

        # Termin Pembayaran: left-column-only lines, from "Termin Pembayaran" until item header (or next page)
        if not termin:
            start_idx = None
            for idx, l in enumerate(lines):
                if re.search(r"Termin\s*Pembayaran", l["text"], re.IGNORECASE):
                    start_idx = idx
                    break
            if start_idx is not None:
                collected = []
                first_line = re.sub(r"^.*Termin\s*Pembayaran\s*:?\s*", "", lines[start_idx]["text"], flags=re.IGNORECASE)
                if first_line.strip():
                    collected.append(first_line.strip())
                stop_top = item_header_top if item_header_top is not None else h
                for l in lines[start_idx + 1:]:
                    if l["top"] >= stop_top:
                        break
                    if l["left"] > w * 0.52:
                        continue
                    collected.append(l["text"])
                termin = " ".join(collected).strip()

        # Item rows: re-OCR just the item-table band on its own — mixing it in with
        # the full page confuses Tesseract's column detection and scrambles cells.
        if item_header_top is not None:
            items_end_top = h
            for l in lines:
                if l["top"] > item_header_top and re.search(r"^Sub\s*Total", l["text"], re.IGNORECASE):
                    items_end_top = l["top"]
                    break
            band = img.crop((0, item_header_top, w, min(items_end_top + 20, h)))
            band_lines = get_lines(band, psm=4, lang=lang)
            for l in band_lines:
                m = ITEM_ROW_RE.match(l["text"])
                if m:
                    no = int(m.group(1))
                    if no not in items:
                        items[no] = {
                            "Deskripsi": m.group(2).strip(),
                            "Jumlah": clean_num(m.group(3)),
                            "Harga": clean_num(m.group(4)),
                            "Total": clean_num(m.group(5)),
                        }

        for l in lines:
            t = l["text"]
            if not sub_total and re.search(r"^Sub\s*Total", t, re.IGNORECASE):
                m = NUM_AFTER_LABEL_RE(r"Sub\s*Total").search(t)
                if m:
                    sub_total = clean_num(m.group(1))
            if not vat and re.search(r"^VAT\b", t, re.IGNORECASE):
                m = NUM_AFTER_LABEL_RE(r"VAT").search(t)
                if m:
                    vat = clean_num(m.group(1))
            if not jumlah_total and re.search(r"^Jumlah\s*Total", t, re.IGNORECASE):
                m = NUM_AFTER_LABEL_RE(r"Jumlah\s*Total").search(t)
                if m:
                    jumlah_total = clean_num(m.group(1))

        if not spesifikasi:
            start_idx = None
            for idx, l in enumerate(lines):
                if re.search(r"SPESIFIKASI.*RUANG\s*LINGKUP", l["text"], re.IGNORECASE):
                    start_idx = idx
                    break
            if start_idx is not None:
                collected = []
                for l in lines[start_idx:]:
                    if re.search(r"HARAP\s*DI\s*CANTUMKAN|Disclaimer|Syarat\s*&\s*Ketentuan", l["text"], re.IGNORECASE):
                        break
                    collected.append(l["text"])
                spesifikasi = " ".join(collected).strip()

    return {
        "Termin Pembayaran": clean_text(termin),
        "Sub Total": sub_total,
        "VAT": vat,
        "Jumlah Total": jumlah_total,
        "Spesifikasi": clean_text(spesifikasi),
        "items": [items[k] for k in sorted(items)],
    }


COLUMNS = [
    "Nama File", "PO NO", "PR NO", "Tanggal PO", "Tgl Maks Pengiriman",
    "Termin Pembayaran", "Nama Vendor", "Alamat Vendor", "Deskripsi",
    "Jumlah", "Harga", "Total", "Sub Total", "VAT", "Jumlah Total",
    "Spesifikasi", "Error",
]


def extract_po(path_or_bytes, filename, dpi=300, lang="ind+eng"):
    """Ekstrak satu PDF PO menjadi baris-baris (satu baris per item barang/jasa)."""
    try:
        if isinstance(path_or_bytes, (bytes, bytearray)):
            doc = fitz.open(stream=path_or_bytes, filetype="pdf")
        else:
            doc = fitz.open(path_or_bytes)
        header = parse_header_block(doc.load_page(0), dpi=dpi, lang=lang)
        header["Nama Vendor"] = clean_text(header["Nama Vendor"])
        header["Alamat Vendor"] = clean_text(header["Alamat Vendor"])
        body = parse_body(doc, dpi=dpi, lang=lang)
        doc.close()
    except Exception as exc:  # noqa: BLE001 - satu PDF gagal tidak boleh menghentikan batch
        return [{**{c: "" for c in COLUMNS}, "Nama File": filename, "Error": str(exc)}]

    rows = []
    items = body["items"] or [{"Deskripsi": "", "Jumlah": "", "Harga": "", "Total": ""}]
    for item in items:
        row = {"Nama File": filename, "Error": ""}
        row.update(header)
        row["Termin Pembayaran"] = body["Termin Pembayaran"]
        row.update(item)
        row["Sub Total"] = body["Sub Total"]
        row["VAT"] = body["VAT"]
        row["Jumlah Total"] = body["Jumlah Total"]
        row["Spesifikasi"] = body["Spesifikasi"]
        rows.append({c: row.get(c, "") for c in COLUMNS})
    return rows


if __name__ == "__main__":
    import sys
    import json

    for path in sys.argv[1:]:
        print(f"\n===== {path} =====")
        rows = extract_po(path, path)
        for r in rows:
            print(json.dumps(r, ensure_ascii=False, indent=2))
