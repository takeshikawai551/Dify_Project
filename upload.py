import os
import requests
import time

# ======================
# Dify テキストアップローダ
# ======================
API_KEY = "dataset-c7vK0h9oaUVsTnSJer64VwN7"
KB_ID = "73798bac-66ca-43ea-8817-b6d4065052df"
DIST_DIR = "/dist"

SERVER = "http://161.93.108.55:8890/v1"
UPLOAD_URL = f"{SERVER}/knowledge/upload"
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
for root, dirs, files in os.walk(DIST_DIR):
    for file in files:
        path = os.path.join(root, file)
        title = os.path.relpath(path, DIST_DIR)  # 相対パスをタイトルに
        if title not in uploaded_titles:
            files_to_upload.append((title, path))

print(f"未アップロードのファイル: {[t for t, _ in files_to_upload]}")

# ======================
# 3. 未アップロードファイルをアップロード
# ======================
for title, path in files_to_upload:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    payload = {
        "knowledge_id": KB_ID,
        "documents": [
            {"title": title, "content": content}
        ]
    }

    resp = requests.post(UPLOAD_URL, json=payload, headers=HEADERS)
    if resp.status_code == 200:
        task_id = resp.json().get("task_id")
        print(f"アップロード開始: {title} (task_id: {task_id})")

        # 非同期処理完了待ち
        status_url = f"https://api.dify.ai/v1/tasks/{task_id}"
        while True:
            status_resp = requests.get(status_url, headers=HEADERS)
            status = status_resp.json()
            if status["status"] in ["completed", "failed"]:
                break
            time.sleep(1)

        result = status.get("result", {})
        if status["status"] == "completed":
            print(f"アップロード成功: {title}, success_count={result.get('success_count')}")
        else:
            print(f"アップロード失敗: {title}, errors={result.get('errors')}")
    else:
        print(f"アップロードリクエスト失敗: {title}, status_code={resp.status_code}")
