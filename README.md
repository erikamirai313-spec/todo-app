# Todoリストアプリ（Flask × Googleスプレッドシート）

やること（タイトル・内容・期日）を登録・編集・削除し、一覧で確認できるWebアプリです。
データはGoogleスプレッドシートに保存されます。

## ファイル構成

```
todo-app/
├── app.py              # 画面とURLの処理（Flask）
├── sheets.py           # スプレッドシートの読み書き
├── templates/
│   ├── base.html       # 共通レイアウト（ヘッダー・お知らせ表示）
│   ├── index.html      # 一覧ページ
│   └── form.html       # 登録・編集フォーム
├── static/style.css    # デザイン
├── requirements.txt    # 使うライブラリ
├── .env.example        # 設定ファイルのひな形
└── .gitignore          # GitHubに上げないファイル
```

## 機能

| URL | 内容 |
|---|---|
| `/` | 一覧（期日が近い順。期限切れは赤、今日までは黄色で表示） |
| `/new` | 新規登録 |
| `/edit/<id>` | 編集 |
| `/delete/<id>` | 削除（POSTのみ・確認ダイアログあり） |

---

## セットアップ手順

### 1. Google Cloud でサービスアカウントを作る
1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成（既存のものでもOK）
2. 「APIとサービス」→「ライブラリ」で **Google Sheets API** と **Google Drive API** を有効化
3. 「IAMと管理」→「サービスアカウント」→ 作成
4. 作ったサービスアカウントの「鍵」タブ →「鍵を追加」→ **JSON** をダウンロード
5. ダウンロードしたファイルを `credentials.json` という名前で `todo-app` フォルダに置く

### 2. スプレッドシートを用意する
1. Googleスプレッドシートを新規作成（名前は自由。例：Todoリスト）
2. 右上の「共有」で、`credentials.json` の中の `client_email`（`〜@〜.iam.gserviceaccount.com`）を **編集者** として追加
3. URLの `/d/` と `/edit` の間の文字列が **スプレッドシートID**
   `https://docs.google.com/spreadsheets/d/【ここ】/edit`

※ 見出し行（id, title, content, due_date, created_at, updated_at）はアプリが自動で作ります。

### 3. 手元で動かす
```bash
cd todo-app
python -m venv .venv
source .venv/bin/activate        # Windowsは .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # .env を開いて SPREADSHEET_ID を書き換える
python app.py
```
ブラウザで http://localhost:5000 を開く。登録したらスプレッドシートに行が増えるのを確認。

### 4. GitHub に上げる
```bash
git init
git add .
git commit -m "Todoアプリ作成"
```
GitHubで新しいリポジトリを作り、表示されるコマンドで push。
⚠️ `.gitignore` で `credentials.json` と `.env` は除外しています。**絶対に上げないこと。**

### 5. Render で公開する
1. [Render](https://render.com/) →「New」→「Web Service」→ GitHubのリポジトリを選択
2. 設定
   - Runtime：**Python 3**
   - Build Command：`pip install -r requirements.txt`
   - Start Command：`gunicorn app:app`
   - Instance Type：Free
3. 「Environment Variables」に以下を追加

| Key | Value |
|---|---|
| `SPREADSHEET_ID` | スプレッドシートID |
| `SECRET_KEY` | 適当な長い英数字 |
| `GOOGLE_CREDENTIALS_JSON` | `credentials.json` の中身を**まるごと**コピーして貼り付け |

4. 「Create Web Service」→ デプロイ完了後に表示される `https://〜.onrender.com` が公開URL

※ 無料プランは15分ほどアクセスがないとスリープし、次に開くとき起動に少し時間がかかります。

---

## よくあるエラー

| エラー | 原因と対処 |
|---|---|
| `SpreadsheetNotFound` / `PermissionError` | スプレッドシートをサービスアカウントのメールに共有していない |
| `APIError: ... has not been used` | Sheets API / Drive API が有効になっていない |
| `KeyError: 'SPREADSHEET_ID'` | `.env`（Renderなら環境変数）に設定がない |
| `FileNotFoundError: credentials.json` | 手元：ファイル名・置き場所を確認／Render：`GOOGLE_CREDENTIALS_JSON` が未設定 |
