import os
from pathlib import Path
import fitz  # PyMuPDF

#
# pdf text 変換
#

SRC_DIR = Path("./src")
DIST_DIR = Path("./dist")
MAX_SIZE_MB = 15
MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024

def extract_text_and_images(pdf_path: Path, dist_dir: Path, base_name: str):
    doc = fitz.open(pdf_path)
    text_parts = []
    img_count = 1

    for page_idx, page in enumerate(doc, 1):
        text_parts.append(f"\n--- Page {page_idx} ---\n")
        text_parts.append(page.get_text("text"))

        # ページ内の画像を抽出
        images = page.get_images(full=True)
        for img in images:
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_data = base_image["image"]
            image_ext = base_image["ext"]
            img_filename = f"{base_name}_image_{img_count:03d}.{image_ext}"
            img_path = dist_dir / img_filename

            with open(img_path, "wb") as f:
                f.write(image_data)

            # テキスト内に画像リンクを挿入
            text_parts.append(f"\n[Image: {img_filename}]\n")
            img_count += 1

    doc.close()
    return "\n".join(text_parts)

def save_split_text(text: str, output_dir: Path, base_name: str):
    """15MB単位で分割保存"""
    output_dir.mkdir(parents=True, exist_ok=True)
    part = 1
    start = 0

    while start < len(text):
        chunk = text[start:start + MAX_SIZE_BYTES]
        encoded = chunk.encode("utf-8", errors="ignore")
        while len(encoded) > MAX_SIZE_BYTES:
            chunk = chunk[:-1000]
            encoded = chunk.encode("utf-8", errors="ignore")

        output_file = output_dir / f"{base_name}_part_{part:03d}.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(chunk)

        print(f"✅ Saved: {output_file} ({len(encoded)/1024/1024:.2f} MB)")
        start += len(chunk)
        part += 1

def process_pdf(pdf_path: Path):
    rel_path = pdf_path.relative_to(SRC_DIR)
    dist_dir = DIST_DIR / rel_path.parent / pdf_path.stem
    dist_dir.mkdir(parents=True, exist_ok=True)

    base_name = pdf_path.stem
    try:
        print(f"🔍 Processing {pdf_path} ...")
        text = extract_text_and_images(pdf_path, dist_dir, base_name)
        save_split_text(text, dist_dir, base_name)
    except Exception as e:
        print(f"⚠️ Error processing {pdf_path}: {e}")

def main():
    for pdf_path in SRC_DIR.rglob("*.pdf"):
        process_pdf(pdf_path)

if __name__ == "__main__":
    main()
