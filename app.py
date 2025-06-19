from flask import Flask, request, send_file
from flask_cors import CORS
import pdfplumber
import fitz  # PyMuPDF
import os

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
    return weights

def process_pdf(layout_pdf_path, weights, output_path):
    doc = fitz.open(layout_pdf_path)
    for page in doc:
        annots = list(page.annots() or [])
        for annot in annots:
            content = annot.info.get("content", "")
            if content in weights:
                rect = annot.rect
                page.delete_annot(annot)
                page.insert_textbox(
                    rect,
                    str(weights[content]),
                    fontname="helv",
                    fontsize=10,
                    color=(0, 0, 0),
                    align=1
                )
    doc.save(output_path)

@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        layout_file = request.files["layout"]
        detail_file = request.files["detail"]

        layout_pdf_path = "/tmp/layout.pdf"
        detail_pdf_path = "/tmp/detail.pdf"
        layout_file.save(layout_pdf_path)
        detail_file.save(detail_pdf_path)

        weights = extract_weights(detail_pdf_path)
        if not weights:
            return {"error": "Không tìm thấy số tấn hợp lệ trong file chi tiết."}, 400

        output_pdf_path = "/tmp/ket_qua.pdf"
        process_pdf(layout_pdf_path, weights, output_pdf_path)

        if not os.path.exists(output_pdf_path):
            return {"error": "Không tạo được file kết quả."}, 500

        return send_file(output_pdf_path, as_attachment=True)
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(debug=True)
