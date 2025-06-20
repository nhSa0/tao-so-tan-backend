from flask import Flask, request, send_file
from flask_cors import CORS
import fitz
from PIL import Image
import pytesseract
import io
import re
from decimal import Decimal, ROUND_HALF_UP

app = Flask(__name__)
CORS(app)

def extract_weights_ocr(file_path):
    weights = {}
    doc = fitz.open(file_path)

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img)
        lines = text.splitlines()
        lines = [line.strip() for line in lines if line.strip()]

        for i, line in enumerate(lines):
            match = re.search(r'[FEfe](\d+\.\d+)', line)
            if match:
                raw_value = match.group(1)
                try:
                    rounded = int(Decimal(raw_value).quantize(0, ROUND_HALF_UP))
                except:
                    continue
                for j in range(1, 4):
                    if i + j < len(lines):
                        line_below = lines[i + j]
                        if re.match(r'^\d{6}$', line_below):
                            weights[line_below] = rounded
                            print(f"✅ Trang {page_num+1} | {line_below} → {rounded} tấn")
                            break
    return weights

# Hàm xác định vị trí xyz → vị trí (x, y) trong layout
def estimate_bay(x):
    bay_ranges = {
        (0, 100): 1, (100, 200): 3, (200, 300): 5,
        (300, 400): 7, (400, 500): 9, (500, 600): 11,
        (600, 700): 13, (700, 800): 15, (800, 900): 17,
        (900, 1000): 19, (1000, 1100): 21, (1100, 1200): 23,
        (1200, 1300): 25, (1300, 1400): 27
    }
    for (xmin, xmax), bay in bay_ranges.items():
        if xmin <= x < xmax:
            return bay
    return None

def estimate_row(x):
    row_positions = {
        (0, 20): 14, (20, 40): 12, (40, 60): 10, (60, 80): 8,
        (80, 100): 6, (100, 120): 4, (120, 140): 2, (140, 160): 0,
        (160, 180): 1, (180, 200): 3, (200, 220): 5, (220, 240): 7,
        (240, 260): 9, (260, 280): 11, (280, 300): 13
    }
    for (xmin, xmax), row in row_positions.items():
        if xmin <= x < xmax:
            return row
    return None

def estimate_tier(y):
    tier_positions = {
        (100, 115): 2, (115, 130): 4, (130, 145): 6,
        (145, 160): 8, (160, 175): 10, (175, 190): 12,
        (200, 215): 82, (215, 230): 84, (230, 245): 86,
        (245, 260): 88, (260, 275): 90, (275, 290): 92,
        (290, 305): 94
    }
    for (ymin, ymax), tier in tier_positions.items():
        if ymin <= y < ymax:
            return tier
    return None

def insert_weights(layout_pdf_path, weights, output_pdf_path):
    doc = fitz.open(layout_pdf_path)
    page = doc[0]

    print("📥 Đang xử lý layout...")

    for block in page.get_text("blocks"):
        x0, y0, x1, y1, text, *_ = block
        text = text.strip()
        if not re.match(r"^[a-zA-Z]$", text):
            continue

        rect = fitz.Rect(x0, y0, x1, y1)
        center_x = (x0 + x1) / 2
        center_y = (y0 + y1) / 2

        bay = estimate_bay(center_x)
        row = estimate_row(center_x)
        tier = estimate_tier(center_y)

        if bay is None or row is None or tier is None:
            continue

        xyz = f"{bay:02}{row:02}{tier:02}"
        if xyz in weights:
            value = str(weights[xyz])
            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
            page.insert_textbox(
                rect,
                value,
                fontsize=12,
                fontname="helv",
                color=(0, 0, 0),
                align=1
            )
            print(f"✅ Ghi {value} tấn vào {xyz}")

    doc.save(output_pdf_path)
    print("✅ Đã lưu file kết quả.")

@app.route("/upload", methods=["POST"])
def upload():
    try:
        layout_file = request.files["layout"]
        detail_file = request.files["detail"]

        layout_path = "/tmp/layout.pdf"
        detail_path = "/tmp/detail.pdf"
        result_path = "/tmp/ket_qua.pdf"

        layout_file.save(layout_path)
        detail_file.save(detail_path)

        weights = extract_weights_ocr(detail_path)
        insert_weights(layout_path, weights, result_path)

        return send_file(result_path, as_attachment=True)

    except Exception as e:
        print("❌ Lỗi:", str(e))
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(debug=True)
