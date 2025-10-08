import os
import pymupdf
import pdfplumber
from pathlib import Path
import argparse
from tqdm import tqdm
import time
#
# pdf markdown 変換
#

# WSLでのマウント手順
# windows側で
# sudo mkdir -p /mnt/x
# sudo mount -t drvfs X: /mnt/x

SRC_DIR = Path("/mnt/x")
#SRC_DIR = Path("./src")
DIST_DIR = Path("/mnt/z/GPT")
#DIST_DIR = Path("./dist")
IMG_DIR = DIST_DIR / "images"


ignore_files = ["/mnt/z/GPT/002_ｱﾋﾟｽﾃ_APISTE/ENC-GRシリーズ取扱説明書(側面取付).md"]

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)
def extract_text_and_images(pdf_path: Path, dist_txt_path: Path):
    ensure_dir(dist_txt_path.parent)
    ensure_dir(IMG_DIR)
    text_parts = []
    print(f"✅ {dist_txt_path} を生成開始。")
    # --- 1. まずはpdfplumberで表を抽出 ---
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(tqdm(pdf.pages, desc="表抽出中", unit="ページ"), start=1):
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
    with pymupdf.open(pdf_path) as doc:
        for page_index, page in enumerate(tqdm(doc, desc="テキスト抽出中", unit="ページ"), start=1):
            text = page.get_text("text")
            text_parts.append(f"\n\n## Page {page_index}\n\n{text}\n")
            # 画像抽出はコメントアウトのまま
    # --- 3. 出力 ---
    with open(dist_txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(text_parts))
    print(f"✅ {dist_txt_path} を生成しました。")
    # パスを正規化する関数
def normalize_path(path):
    return os.path.normpath(os.path.abspath(path))

def convert_all_unprocessed():
    pdf_files = []
    for root, _, files in os.walk(SRC_DIR):
        for file in files:
            if file.lower().endswith(".pdf"):
                src_pdf = Path(root) / file
                rel_path = src_pdf.relative_to(SRC_DIR)
                dist_txt_path = DIST_DIR / rel_path.with_suffix(".md")
                if dist_txt_path.exists():
                    print(f"⏩ 既に変換済み: {dist_txt_path}")
                    continue
                pdf_files.append((src_pdf, dist_txt_path))
    total = len(pdf_files)
    print(f"▶️ 変換対象PDFファイル数: {total}")
    norm_ignore_files = [normalize_path(p) for p in ignore_files]
    start_time = time.time()
    for i, (src_pdf, dist_txt_path) in enumerate(pdf_files, start=1):
        norm_dist_txt_path = normalize_path(dist_txt_path)
        if norm_dist_txt_path in norm_ignore_files:
            print(f"無視対象: {dist_txt_path}")
            continue
        if "270_ﾌｧﾅｯｸ_FANUC" in norm_dist_txt_path:
            print(f"fanuc をスキップ: {norm_dist_txt_path}")
            continue
        print(f"生成開始({i}/{total}): {dist_txt_path}")
        file_start = time.time()
        extract_text_and_images(src_pdf, dist_txt_path)
        file_elapsed = time.time() - file_start
        print(f"完了({i}/{total}): {dist_txt_path} 処理時間: {file_elapsed:.2f}秒")
    elapsed = time.time() - start_time
    print(f"✅ 全処理完了 時間: {elapsed:.2f}秒")
    
def convert_single_file(file_path: Path):
    if not file_path.exists():
        print(f"⚠️ 指定ファイルが存在しません: {file_path}")
        return
    if file_path.suffix.lower() != ".pdf":
        print(f"⚠️ PDFファイルを指定してください: {file_path}")
        return
    # distフォルダ内の対応するmdパスを計算
    try:
        rel_path = file_path.relative_to(SRC_DIR)
    except ValueError:
        # src外のファイルならdist直下に配置
        rel_path = file_path.name
    dist_txt_path = DIST_DIR / Path(rel_path).with_suffix(".md")
    extract_text_and_images(file_path, dist_txt_path)
def main():
    parser = argparse.ArgumentParser(description="PDF→Markdown変換")
    parser.add_argument("file", nargs="?", help="変換したいPDFファイルのパス（省略時はsrc内全PDF処理）")
    args = parser.parse_args()
    if args.file:
        convert_single_file(Path(args.file))
    else:
        convert_all_unprocessed()
if __name__ == "__main__":
    main()