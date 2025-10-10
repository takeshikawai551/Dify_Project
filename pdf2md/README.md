# PDF→Markdown変換ツール 使い方ドキュメント
---
## 概要
このツールはPDFファイルをMarkdown形式に変換し、テキストや表を抽出します。
Windows + WSLまたはLinux環境で動作確認済みです。
---
## 環境について
- Windows + WSL環境またはLinux環境で利用可能です。
- 元PDFファイルのあるディレクトリ（`SRC_DIR`）や変換後Markdownの出力先（`DIST_DIR`）は、ネットワーク共有や外部ストレージとしてマウント可能なパスに設定できます。
- これにより、変換結果をホストOSや他の環境から簡単にアクセス・管理できます。
---
## ネットワーク共有フォルダのマウント例（Windows + WSLの場合）
1. WSLを起動し、マウントポイントを作成します。
```bash
sudo mkdir -p /mnt/x
```
2. Windowsのネットワーク共有フォルダをWSL内にマウントします。
```bash
sudo mount -t drvfs '\\\\windows-hostname\\share-name' /mnt/x
```
- `windows-hostname`: Windowsマシンの名前またはIPアドレス
- `share-name`: 共有フォルダ名
3. マウント成功後、`/mnt/x`配下で共有フォルダのファイルにアクセスできます。
---
## マウントを使わずに利用する場合（ローカルディレクトリで完結）
1. スクリプトを配置したディレクトリ内に以下のディレクトリを作成します。
```bash
mkdir src
mkdir dist
```
2. PDFファイルを`src`ディレクトリにコピーします。
3. スクリプト内のパス設定を以下のように変更します。
```python
SRC_DIR = Path("./src")      # srcディレクトリを元PDFの場所に設定
DIST_DIR = Path("./dist")    # distディレクトリを出力先に設定
```
4. 以降は通常通りスクリプトを実行して変換してください。
---
## 事前準備（Python環境構築）
### 1. 仮想環境（venv）を作成・有効化
```bash
python3 -m venv venv
source venv/bin/activate   # Linux / WSLの場合
venv\Scripts\activate      # Windowsコマンドプロンプトの場合
```
### 2. 必要なパッケージを一括インストール
以下コマンドでインストールします。
```bash
pip install -r requirements.txt
```
---
## 実行方法
- **todoリストに基づく一括変換（引数なし）**
```bash
python pdf2md.py
```
- **単一PDFファイルを指定して変換**
```bash
python pdf2md.py ./src/sample.pdf
```
---
## まとめ
| 操作                         | コマンド例                      | 説明                             |
|------------------------------|--------------------------------|----------------------------------|
| 仮想環境作成・有効化         | `python3 -m venv venv`<br>`source venv/bin/activate` | Python環境の分離管理              |
| パッケージ一括インストール   | `pip install -r requirements.txt` | 必要なパッケージをまとめて導入   |
| ネットワーク共有フォルダのマウント | `sudo mount -t drvfs '\\\\host\\share' /mnt/x` | Windows共有をWSLにマウント        |
| ローカルディレクトリ利用     | `mkdir src dist`<br>PDFを`src`にコピー<br>スクリプト内パス修正 | マウント不要でローカル完結        |
| 一括変換                     | `python pdf2md.py`              | todoファイルに基づいて変換       |
| 単一ファイル変換             | `python pdf2md.py ./src/file.pdf` | 指定ファイルのみ変換              |
---
## 注意事項
- ネットワーク共有のマウントはWSL再起動で解除される場合があるため、自動マウント設定を推奨します。
- `SRC_DIR`や`DIST_DIR`のパスは環境に合わせて調整してください。
- 画像抽出用ディレクトリは作成されますが、画像の保存処理は追加実装が必要です。
---
ご不明点があればお気軽にお問い合わせください。