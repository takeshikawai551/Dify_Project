import os
import requests
import time
import json
# ======================
# Dify テキストアップローダ
# ======================
API_KEY = "dataset-c7vK0h9oaUVsTnSJer64VwN7"
KB_ID = "73798bac-66ca-43ea-8817-b6d4065052df"
DIST_DIR = "./dist"

SERVER = "http://161.93.108.55:8890/v1"
UPLOAD_URL = f"{SERVER}/datasets/{KB_ID}/document/create-by-file"
#LIST_URL =  f"{SERVER}/knowledge/{KB_ID}/documents"
#http://161.93.108.55:8890/datasets/73798bac-66ca-43ea-8817-b6d4065052df/documents
LIST_URL =  f"{SERVER}/datasets/{KB_ID}/documents"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# ======================
# 1. 既存ナレッジ取得
# ======================
def get_uploaded_docs():
    resp = requests.get(LIST_URL, headers=HEADERS)
    # if resp.status_code == 200:
    #     print(f"{resp.json()}")
    #     docs = resp.json().get("documents", [])
    # else:
    #     print(f"url:{LIST_URL} error {resp.status_code}")
    # #return {doc["title"] for doc in docs}  # タイトルのセット
    # return {docs["name"] for docs in data}  
    # resp = requests.get(LIST_URL, headers=HEADERS)
    if resp.status_code != 200:
        print("API取得失敗:", resp.status_code, resp.text)
        return set()
    
    data = resp.json().get("data", [])
    return {doc["name"] for doc in data}  # 'name' がファイル名

uploaded_titles = get_uploaded_docs()
print(f"既存アップロード文書: {uploaded_titles}")
# ======================
# 2. /dist 配下のファイル探索
# ======================
files_to_upload = []
ALLOWED_EXTS = ('.md', '.txt')  # 対象拡張子
SKIP_EXTS = ('.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip')
for root, dirs, files in os.walk(DIST_DIR):
    print(f"探索中: {root} ({len(files)} files)")
    for file in files:
        lower_file = file.lower()

        # ❌ バイナリ拡張子をスキップ
        if lower_file.endswith(SKIP_EXTS):
            continue

        # ✅ テキスト/マークダウンのみ対象
        if not lower_file.endswith(ALLOWED_EXTS):
            continue

        path = os.path.join(root, file)
        title = os.path.relpath(path, DIST_DIR)  # dist/ からの相対パス

        # 既存アップロード済みは除外
        if title in uploaded_titles:
            print(f"  ⏩ 既にアップロード済み: {title}")
            continue

        print(f"  ✅ 未アップロード: {title}")
        files_to_upload.append((title, path))

print(f"未アップロードのファイル: {[t for t, _ in files_to_upload]}")

for title, path in files_to_upload:
    try:
        with open(path, "rb") as f:
            # files = {"file": (os.path.basename(path), f, "text/plain")}
            files = {"file": (os.path.basename(path), open(path, "rb"), "text/markdown")}
            headers = {"Authorization": f"Bearer {API_KEY}",}
            data = {
                "name": os.path.basename(path),
                "process_rule": json.dumps({"mode": "automatic"}),
                "indexing_technique": "high_quality"
            }
            resp = requests.post(UPLOAD_URL, headers=headers, files=files, data=data)
            if resp.status_code in (200, 201):
                result = resp.json()
                print(f"✅ アップロード成功: {title} → id={result.get('id')}")
            else:
                print(f"❌ アップロード失敗: {title}, status={resp.status_code}, msg={resp.text}")

    except Exception as e:
        print(f"⚠️ アップロード例外: {title}, error={e}")
