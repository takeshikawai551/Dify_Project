import os
import fitz  # PyMuPDF
import pdfplumber
from pathlib import Path

#
# pdf markdown 変換
#

SRC_DIR = Path("./src")
DIST_DIR = Path("./dist")
IMG_DIR = DIST_DIR / "images"

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def extract_text_and_images(pdf_path: Path, dist_txt_path: Path):
    ensure_dir(dist_txt_path.parent)
    ensure_dir(IMG_DIR)

    text_parts = []

    # --- 1. まずはpdfplumberで表を抽出 ---
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # 表抽出
                tables = page.extract_tables()
                for idx, table in enumerate(tables, start=1):
                    md = []
                    for row in table:
                        md.append("| " + " | ".join(cell or "" for cell in row) + " |")
                    if table and len(table[0]) > 0:
                        header = "| " + " | ".join(["---"] * len(table[0])) + " |"
                        md.insert(1, header)
                    table_text = "\n".join(md)
                    text_parts.append(f"\n\n### 表 {page_num}-{idx}\n\n{table_text}\n\n")
    except Exception as e:
        print(f"⚠️ 表抽出スキップ: {e}")

    # --- 2. PyMuPDFでテキストと画像を抽出 ---
    with fitz.open(pdf_path) as doc:
        for page_index, page in enumerate(doc, start=1):
            text = page.get_text("text")
            text_parts.append(f"\n\n## Page {page_index}\n\n{text}\n")

            # 画像抽出
            # 画像は読み込まないので一時除外
            # for img_index, img in enumerate(page.get_images(full=True), start=1):
            #     xref = img[0]
            #     base_image = doc.extract_image(xref)
            #     image_bytes = base_image["image"]
            #     image_ext = base_image["ext"]
            #     image_name = f"{pdf_path.stem}_p{page_index}_{img_index}.{image_ext}"
            #     image_path = IMG_DIR / image_name
            #     with open(image_path, "wb") as img_file:
            #         img_file.write(image_bytes)
            #     text_parts.append(f"![{image_name}](images/{image_name})\n")

    # --- 3. 出力 ---
    with open(dist_txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(text_parts))
    print(f"✅ {dist_txt_path} を生成しました。")

def main():
    for root, _, files in os.walk(SRC_DIR):
        for file in files:
            if file.lower().endswith(".pdf"):
                src_pdf = Path(root) / file
                rel_path = src_pdf.relative_to(SRC_DIR)
                dist_txt_path = DIST_DIR / rel_path.with_suffix(".md")
                extract_text_and_images(src_pdf, dist_txt_path)

if __name__ == "__main__":
    main()
