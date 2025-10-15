import os
import io
import pymupdf
import pdfplumber
from pathlib import Path
import argparse
from tqdm import tqdm
import time
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from pathlib import Path
import gc

SRC_DIR = Path("/mnt/x")
DIST_DIR = Path("/mnt/z/GPT")
IMG_DIR = DIST_DIR / "images"
TODO_FILE = DIST_DIR / "todo_files.txt"
IGNORE_FILE = DIST_DIR /"ignore_files.txt"

def split_pdf_by_pages(src_pdf_path: Path, max_size_bytes=1_000_000_000, temp_dir: Path = Path("/tmp")) -> list:
    """
    PDFファイルがmax_size_bytesを超える場合、1ページずつ分割してtemp_dirに保存。
    分割後ファイルのパスリストを返す。
    超えなければ元ファイルのリストを返す。
    """
    size = src_pdf_path.stat().st_size
    if size <= max_size_bytes:
        return [src_pdf_path]

    reader = PdfReader(str(src_pdf_path))
    total_pages = len(reader.pages)
    temp_dir.mkdir(parents=True, exist_ok=True)
    split_files = []

    for i in range(total_pages):
        writer = PdfWriter()
        writer.add_page(reader.pages[i])
        split_pdf_path = temp_dir / f"{src_pdf_path.stem}_part_{i+1}.pdf"
        with open(split_pdf_path, "wb") as f_out:
            writer.write(f_out)
        split_files.append(split_pdf_path)

    return split_files
def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def convert_pdf_with_split(src_pdf: Path, dist_txt_path: Path, max_size_bytes=1_000_000_000):
    temp_dir = dist_txt_path.parent / "temp_split"
    split_files = split_pdf_by_pages(src_pdf, max_size_bytes=max_size_bytes, temp_dir=temp_dir)

    text_parts = []

    for split_pdf in split_files:
        # 元のdist_txt_pathにページ区切りや分割ファイル名を付加して出力先を分ける方法もあり
        # ここでは単純にファイルごとに別名で保存する例
        if len(split_files) == 1:
            out_path = dist_txt_path
        else:
            out_path = dist_txt_path.with_name(dist_txt_path.stem + f"_{split_pdf.stem}" + dist_txt_path.suffix)

        extract_text_and_images(split_pdf, out_path)
        text_parts.append(f"Processed split file: {split_pdf.name}")

    print("\n".join(text_parts))

def write_split_md(text_parts: list[str], base_path: Path, max_size_bytes=15 * 1024 * 1024):
    """
    text_parts（文字列リスト）をmax_size_bytesごとに分割して
    base_pathのファイル名をベースに複数ファイルに分けて保存する。
    """

    part_num = 1
    buffer = []
    buffer_size = 0

    for part in text_parts:
        part_bytes = part.encode("utf-8")
        part_len = len(part_bytes)

        # 現バッファに足すとサイズオーバーならファイル出力してリセット
        if buffer_size + part_len > max_size_bytes and buffer:
            out_path = base_path.with_name(f"{base_path.stem}_part{part_num},{base_path.suffix}")
            with open(out_path, "w", encoding="utf-8") as f_out:
                f_out.write("".join(buffer))
            print(f"分割ファイルを書き出しました: {out_path}")
            part_num += 1
            buffer = []
            buffer_size = 0

        buffer.append(part)
        buffer_size += part_len

    # 残ったバッファを最後のファイルとして書き出し
    if buffer:
        out_path = base_path.with_name(f"{base_path.stem}_part{part_num},{base_path.suffix}")
        with open(out_path, "w", encoding="utf-8") as f_out:
            f_out.write("".join(buffer))
        print(f"分割ファイルを書き出しました: {out_path}")


def write_md_with_size_check(text_parts: list[str], base_path: Path, max_size_bytes=15 * 1024 * 1024):
    """
    text_partsの合計サイズを判定し、max_size_bytesを超えれば分割して書き出し、
    超えなければ単一ファイルにまとめて書き出す。
    """
    # 全体サイズ計算
    total_size = sum(len(part.encode("utf-8")) for part in text_parts)
    if total_size <= max_size_bytes:
        # サイズ以内なので単一ファイルに書き出し
        with open(base_path, "w", encoding="utf-8") as f:
            f.write("".join(text_parts))
        print(f"ファイルを書き出しました（サイズ: {total_size} bytes）: {base_path}")
    else:
        # サイズ超過のため分割書き出し
        print(f"ファイルサイズ {total_size} bytes が上限 {max_size_bytes} bytes を超えたため分割します。")
        part_num = 1
        buffer = []
        buffer_size = 0
        for part in text_parts:
            part_len = len(part.encode("utf-8"))
            if buffer_size + part_len > max_size_bytes and buffer:
                out_path = base_path.with_name(f"{base_path.stem}_part{part_num},{base_path.suffix}")
                with open(out_path, "w", encoding="utf-8") as f_out:
                    f_out.write("".join(buffer))
                print(f"分割ファイルを書き出しました: {out_path}")
                part_num += 1
                buffer = []
                buffer_size = 0
            buffer.append(part)
            buffer_size += part_len
        # 最後のバッファ書き出し
        if buffer:
            out_path = base_path.with_name(f"{base_path.stem}_part{part_num},{base_path.suffix}")
            with open(out_path, "w", encoding="utf-8") as f_out:
                f_out.write("".join(buffer))
            print(f"分割ファイルを書き出しました: {out_path}")

def extract_text_and_images(pdf_path: Path, dist_txt_path: Path):
    ensure_dir(dist_txt_path.parent)
    ensure_dir(IMG_DIR)
    pdf_size_bytes = pdf_path.stat().st_size
    pdf_size_kb = pdf_size_bytes / 1024
    print(f"✅ {dist_txt_path} を生成開始。 元PDFファイルサイズ: {pdf_size_kb:.2f} KB")
    with pdfplumber.open(pdf_path) as pdf, pymupdf.open(pdf_path) as doc, \
        open(dist_txt_path, "w", encoding="utf-8") as f_out:
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
                f_out.write(f"\n\n### 表 {page_num+1}-{idx}\n\n{table_text}\n\n")
            # 2. 画像抽出
            image_list = page_fitz.get_images(full=True)
            for img_idx, img_info in enumerate(image_list, start=1):
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                img_ext = base_image["ext"]
                image = Image.open(io.BytesIO(image_bytes))
                try:
                    ascii_art = image_to_ascii_art(image, width=80)
                except Exception as e:
                    print(f"⚠️ 画像のアスキーアート変換に失敗しました: {e}")
                    ascii_art = "[画像のアスキーアート変換に失敗しました]"
                f_out.write(f"\n\n### 画像 {page_num+1}-{img_idx} (ASCII Art)\n\n```\n{ascii_art}```\n\n")
            # 3. テキスト抽出
            text = page_fitz.get_text("text")
            f_out.write(f"\n\n## Page {page_num+1}\n\n{text}\n")
            # 明示的にオブジェクト解放（必要に応じて）
            del page_plumber
            del page_fitz
            gc.collect()
    print(f"✅ {dist_txt_path} を生成しました。")

def image_to_ascii_art(image: Image.Image, width=80) -> str:
    # グレースケールの文字セット（濃淡に応じて）
    ascii_chars = "@%#*+=-:. "
  
    # 画像のアスペクト比を維持しつつリサイズ
    aspect_ratio = image.height / image.width
    height = int(width * aspect_ratio * 0.55)  # 0.55は文字の縦横比補正
  
    image = image.convert("L").resize((width, height))
  
    pixels = image.getdata()
    chars = []
    for pixel_value in pixels:
        # 0(黒)〜255(白)を文字セットのインデックスに変換
        index = int(pixel_value / 255 * (len(ascii_chars) - 1))
        chars.append(ascii_chars[index])
    # widthごとに改行して文字列に
    ascii_art = ""
    for i in range(0, len(chars), width):
        ascii_art += "".join(chars[i:i+width]) + "\n"
    return ascii_art

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

def add_to_ignore_list(path_str: str):
    ignore_list = load_ignore_list()
    if path_str not in ignore_list:
        ensure_dir(IGNORE_FILE.parent)
        with open(IGNORE_FILE, "a", encoding="utf-8") as f:
            f.write(path_str + "\n")
        print(f"⚠️ メモリ不足のためignoreリストに追加しました: {path_str}")

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
            rel_path = Path(src_pdf.name)
        dist_txt_path = DIST_DIR / rel_path.with_suffix(".md")
        print(f"生成開始({i}/{total}): {dist_txt_path}")
        file_start = time.time()
        try:
            convert_pdf_with_split(src_pdf, dist_txt_path)
            file_elapsed = time.time() - file_start
            print(f"完了({i}/{total}): {dist_txt_path} 処理時間: {file_elapsed:.2f}秒")
            new_todo_list.remove(pdf_path_str)
        except MemoryError as mem_err:
            print(f"⚠️ メモリ不足エラー発生({i}/{total}): {dist_txt_path} エラー: {mem_err}")
            add_to_ignore_list(pdf_path_str)
            if pdf_path_str in new_todo_list:
                new_todo_list.remove(pdf_path_str)
            print("メモリ不足のため処理を中止します。")
            break  # 中止したい場合はbreak、続行したい場合はcontinueに変更可
        except Exception as e:
            print(f"⚠️ 処理失敗({i}/{total}): {dist_txt_path} エラー: {e}")
            continue
        save_todo_list(new_todo_list)
    save_todo_list(new_todo_list)
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
    #extract_text_and_images(file_path, dist_txt_path)
    convert_pdf_with_split(file_path, dist_txt_path)

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