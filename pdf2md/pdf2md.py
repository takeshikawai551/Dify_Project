import os
import pymupdf
import pdfplumber
from pathlib import Path
import argparse
from tqdm import tqdm
import time
SRC_DIR = Path("/mnt/x")
DIST_DIR = Path("/mnt/z/GPT")
IMG_DIR = DIST_DIR / "images"
TODO_FILE = DIST_DIR / "todo_files.txt"
IGNORE_FILE = DIST_DIR /"ignore_files.txt"

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)
def extract_text_and_images(pdf_path: Path, dist_txt_path: Path):
    ensure_dir(dist_txt_path.parent)
    ensure_dir(IMG_DIR)
    text_parts = []
    print(f"✅ {dist_txt_path} を生成開始。")
    with pdfplumber.open(pdf_path) as pdf, pymupdf.open(pdf_path) as doc:
        page_count = len(pdf.pages)
        for page_num in tqdm(range(page_count), desc="ページ処理中", unit="ページ"):
            page_plumber = pdf.pages[page_num]
            page_fitz = doc.load_page(page_num)
            # 1. 表抽出
            tables = page_plumber.extract_tables()
            for idx, table in enumerate(tables, start=1):
                md = []
                for row in table:
                    md.append("| " + " | ".join(cell or "" for cell in row) + " |")
                if table and len(table[0]) > 0:
                    header = "| " + " | ".join(["---"] * len(table[0])) + " |"
                    md.insert(1, header)
                table_text = "\n".join(md)
                text_parts.append(f"\n\n### 表 {page_num+1}-{idx}\n\n{table_text}\n\n")
            # 2. テキスト抽出
            text = page_fitz.get_text("text")
            text_parts.append(f"\n\n## Page {page_num+1}\n\n{text}\n")
    with open(dist_txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(text_parts))
    print(f"✅ {dist_txt_path} を生成しました。")
def normalize_path(path):
    return os.path.normpath(os.path.abspath(path))
def load_todo_list():
    if TODO_FILE.exists():
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        # 空行除去
        return [line for line in lines if line.strip()]
    else:
        return []
def save_todo_list(paths):
    ensure_dir(TODO_FILE.parent)
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        f.writelines(p + "\n" for p in paths)
def load_ignore_list():
    if IGNORE_FILE.exists():
        with open(IGNORE_FILE, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        # 空行除去し正規化
        return [normalize_path(p) for p in lines if p.strip()]
    else:
        return []
def make_todo_list():
    ignore_list = load_ignore_list()
    pdf_files = []
    for root, _, files in os.walk(SRC_DIR):
        for file in files:
            if file.lower().endswith(".pdf"):
                src_pdf = Path(root) / file
                norm_src_pdf = normalize_path(str(src_pdf))
                if norm_src_pdf in ignore_list:
                    # 無視リストにあるのでスキップ
                    continue
                rel_path = src_pdf.relative_to(SRC_DIR)
                dist_txt_path = DIST_DIR / rel_path.with_suffix(".md")
                if dist_txt_path.exists():
                    continue
                pdf_files.append(norm_src_pdf)
    return pdf_files
def convert_all_unprocessed():
    todo_list = load_todo_list()
    if not todo_list:
        print("todoファイルが空または存在しません。新規作成します。")
        todo_list = make_todo_list()
        save_todo_list(todo_list)
    total = len(todo_list)
    if total == 0:
        print("変換対象のPDFファイルはありません。")
        return
    print(f"▶️ 変換対象PDFファイル数: {total}")
    start_time = time.time()
    new_todo_list = todo_list.copy()
    for i, pdf_path_str in enumerate(todo_list, start=1):
        src_pdf = Path(pdf_path_str)
        try:
            rel_path = src_pdf.relative_to(SRC_DIR)
        except ValueError:
            rel_path = src_pdf.name
        dist_txt_path = DIST_DIR / rel_path.with_suffix(".md")
        print(f"生成開始({i}/{total}): {dist_txt_path}")
        file_start = time.time()
        try:
            extract_text_and_images(src_pdf, dist_txt_path)
            file_elapsed = time.time() - file_start
            print(f"完了({i}/{total}): {dist_txt_path} 処理時間: {file_elapsed:.2f}秒")
            # 成功したのでtodoから削除
            new_todo_list.remove(pdf_path_str)
        except Exception as e:
            print(f"⚠️ 処理失敗({i}/{total}): {dist_txt_path} エラー: {e}")
            # 失敗してもtodoに残す
            continue
        # 途中でtodoファイルを更新（任意）
        save_todo_list(new_todo_list)
    save_todo_list(new_todo_list)  # 最終更新
    elapsed = time.time() - start_time
    print(f"✅ 全処理完了 時間: {elapsed:.2f}秒")
    if new_todo_list:
        print(f"⚠️ 未処理ファイルが残っています。todoファイルを確認してください: {TODO_FILE}")
    else:
        print("すべてのファイルを処理完了しました。todoファイルを空にします。")
def convert_single_file(file_path: Path):
    if not file_path.exists():
        print(f"⚠️ 指定ファイルが存在しません: {file_path}")
        return
    if file_path.suffix.lower() != ".pdf":
        print(f"⚠️ PDFファイルを指定してください: {file_path}")
        return
    try:
        rel_path = file_path.relative_to(SRC_DIR)
    except ValueError:
        rel_path = file_path.name
    dist_txt_path = DIST_DIR / rel_path.with_suffix(".md")
    extract_text_and_images(file_path, dist_txt_path)
def main():
    parser = argparse.ArgumentParser(description="PDF→Markdown変換")
    parser.add_argument("file", nargs="?", help="変換したいPDFファイルのパス（省略時はtodoファイルのPDFを処理）")
    args = parser.parse_args()
    if args.file:
        convert_single_file(Path(args.file))
    else:
        convert_all_unprocessed()
if __name__ == "__main__":
    main()