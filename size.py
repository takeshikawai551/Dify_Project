from pathlib import Path
IGNORE_FILE = Path("/mnt/z/GPT2/ignore_files.txt")
SIZE_FILE = Path("/mnt/z/GPT/size.txt")
def normalize_path(path_str):
    return Path(path_str).resolve()
def main():
    if not IGNORE_FILE.exists():
        print(f"Ignore file not found: {IGNORE_FILE}")
        return
    sizes = []
    with open(IGNORE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            path_str = line.strip()
            if not path_str:
                continue
            file_path = normalize_path(path_str)
            if file_path.exists() and file_path.is_file():
                size = file_path.stat().st_size
                sizes.append(f"{file_path}\t{size}")
            else:
                sizes.append(f"{file_path}\tNOT FOUND")
    with open(SIZE_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sizes))
    print(f"サイズ情報を {SIZE_FILE} に書き込みました。")
if __name__ == "__main__":
    main()