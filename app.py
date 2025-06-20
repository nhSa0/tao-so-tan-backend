from flask import Flask, request, send_file
from flask_cors import CORS
import pdfplumber
import fitz

app = Flask(__name__)
CORS(app)

def extract_weights(file_path):
    weights = {}
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split('\n')
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 4:
                    bay, row, tier = parts[0:3]
                    weight_candidate = parts[3]
                    try:
                        weight = int(float(weight_candidate))
                        if all(p.isdigit() and len(p) == 2 for p in (bay, row, tier)):
                            key = f"{bay}{row}{tier}"
                            weights[key] = weight
                    except:
                        continue
    return weights

def insert_weights(layout_pdf_path, weights, output_pdf_path):
    doc = fitz.open(layout_pdf_path)
    print("📥 Đang chèn số tấn...")

    for page_num, page in enumerate(doc, start=1):
        print(f"📄 Trang {page_num}")
        blocks = page.get_text("blocks")
        for block in blocks:
            x0, y0, x1, y1, text, *_ = block
            print(f"🔎 Dòng đọc được: {text.strip()}")
            parts = text.strip().split()
            if len(parts) >= 3:
                bay, row, tier = parts[0:3]
                if all(p.isdigit() and len(p) == 2 for p in (bay, row, tier)):
                    key = f"{bay}{row}{tier}"
                    print(f"🔍 Ghép được mã: {key}")
                    if key in weights:
                        value = str(weights[key])
                        rect = fitz.Rect(x0, y0, x1, y1)
                        page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))  # xóa chữ cũ
                        page.insert_textbox(
                            rect,
                            value,
                            fontsize=12,
                            fontname="helv",
                            color=(0, 0, 0),
                            align=1
                        )
                        print(f"✅ Ghi {value} tấn vào {key}")
    doc.save(output_pdf_path)
    print("✅ Đã lưu file PDF kết quả.")

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
