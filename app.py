from flask import Flask, request, send_file
from flask_cors import CORS
import pdfplumber
import fitz

app = Flask(__name__)
CORS(app)

def extract_weights(detail_pdf_path):
    weights = {}
    with pdfplumber.open(detail_pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for line in text.split('\n'):
                for part in line.split():
                    if part.startswith(('F', 'E')):
                        num = part[1:]
                        if num.replace('.', '', 1).isdigit():
                            bay = part.strip()
                            weight = int(float(num))
                            weights[bay] = weight
    print("🎯 DANH SÁCH BAY:", weights)
    return weights

def process_pdf(layout_pdf_path, weights, output_path):
    doc = fitz.open(layout_pdf_path)
    print("✅ Đã mở file layout")

    for page_num, page in enumerate(doc, start=1):
        print(f"📄 Trang {page_num}")
        text = page.get_text("text")
        print("🔍 Nội dung trang:")
        print(text)

        for bay_code, weight in weights.items():
            print(f"➡️ Tìm {bay_code}...")
            found = page.search_for(bay_code)
            if not found:
                found = page.search_for(bay_code + ".0")
            for rect in found:
                print(f"✅ Ghi {weight} tại {rect} cho {bay_code}")
                page.insert_textbox(
                    rect,
                    str(weight),
                    fontname="helv",
                    fontsize=12,
                    color=(1, 0, 0),
                    align=1
                )
    doc.save(output_path)
    print("✅ Đã lưu file kết quả:", output_path)

@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        layout_file = request.files["layout"]
        detail_file = request.files["detail"]

        layout_pdf_path = "/tmp/layout.pdf"
        detail_pdf_path = "/tmp/detail.pdf"
        layout_file.save(layout_pdf_path)
        detail_file.save(detail_pdf_path)

        print("📥 Đã nhận file layout và chi tiết")

        weights = extract_weights(detail_pdf_path)
        output_pdf_path = "/tmp/ket_qua.pdf"
        process_pdf(layout_pdf_path, weights, output_pdf_path)

        return send_file(output_pdf_path, as_attachment=True)
    except Exception as e:
        print("❌ LỖI:", str(e))
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(debug=True)
