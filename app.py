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
