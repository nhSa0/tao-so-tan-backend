from flask import Flask, request, send_file
from flask_cors import CORS
import fitz
import pdfplumber
import re
import os

app = Flask(__name__)
CORS(app)

def extract_weights(file_path):
    weights = {}
    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if re.match(r'^[FEfe]\d+(\.\d+)?$', line.strip().split()[0]):
                    match = re.match(r'[FEfe](\d+)', line.strip())
                    if not match:
                        continue
                    weight = int(float(match.group(1)))
                    # tìm dòng mã xyz phía dưới
                    for offset in range(1, 4):
                        if i + offset < len(lines):
                            line_below = lines[i + offset].strip()
                            if re.match(r'^\d{6}$', line_below):
                                weights[line_below] = weight
                                break
    return weights

def insert_weights(layout_pdf_path, weights, output_pdf_path):
    doc = fitz.open(layout_pdf_path)
    page = doc[0]  # chỉ 1 trang duy nhất
    blocks = page.get_text("blocks")

    for block in blocks:
        x0, y0, x1, y1, text, *_ = block
        key = text.strip()
        if re.match(r"^[a-zA-Z]$", key):  # chỉ 1 chữ cái tạm thời
            rect = fitz.Rect(x0, y0, x1, y1)
            center_x = (x0 + x1) / 2
            center_y = (y0 + y1) / 2

            # xác định vùng cần xóa + chèn nếu mapping có dữ liệu
            for code, value in weights.items():
                if (abs(center_x - float(code[0:2])) < 1000 and
                    abs(center_y - float(code[2:4])) < 1000):  # đơn giản hóa vị trí
                    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))  # xóa chữ cũ
                    page.insert_textbox(
                        rect,
                        str(value),
                        fontsize=12,
                        fontname="helv",
                        color=(0, 0, 0),
                        align=1
                    )
                    break

    doc.save(output_pdf_path)

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

        weights = extract_weights(detail_path)
        insert_weights(layout_path, weights, result_path)

        return send_file(result_path, as_attachment=True)

    except Exception as e:
        print("❌ Lỗi:", str(e))
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(debug=True)
