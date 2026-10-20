# Todoリストアプリ（Flask × Googleスプレッドシート × LINE）

やること（タイトル・内容・期日・カテゴリ）を登録・編集・完了・削除し、一覧で確認できるWebアプリです。
データはGoogleスプレッドシートに保存され、期日が近づくとLINEにお知らせが届きます。

## ファイル構成

```
todo-app/
├── app.py              # 画面とURLの処理（Flask）
├── sheets.py           # スプレッドシートの読み書き
├── notify.py           # LINE通知（課題2）
├── templates/
│   ├── base.html       # 共通レイアウト（ヘッダー・お知らせ表示・二重送信防止）
│   ├── index.html      # 一覧ページ（絞り込み・完了チェック）
│   └── form.html       # 登録・編集フォーム
├── static/style.css    # デザイン
├── .github/workflows/
│   └── line-notify.yml # 毎朝のLINE通知を動かす設定（GitHub Actions）
├── requirements.txt    # 使うライブラリ
├── .env.example        # 設定ファイルのひな形
└── .gitignore          # GitHubに上げないファイル
```

## 機能

### 課題1
- やることの登録・編集・削除（タイトル・内容・期日）
- 一覧（期日が近い順。期限切れは赤、今日までは黄色）

### 課題2で追加した3つの機能
1. **完了チェック**：丸ボタンで完了／未完了を切り替え。「未完了・完了済み・すべて」のタブで表示を切り替え
2. **カテゴリ＋絞り込み**：「仕事」「学校」「家のこと」などで分類し、カテゴリごとに一覧を絞り込み
3. **LINEに期日通知**：毎朝8時ごろ、未完了のうち「期限切れ・今日まで・明日まで」のやることをLINEに送信。画面の「LINEに通知」ボタンで今すぐ送ることもできる

おまけ：登録ボタンの二重押し防止（保存中はボタンが押せなくなる）

| URL | 内容 |
|---|---|
| `/` | 一覧（`?status=todo/done/all`、`?category=〇〇` で絞り込み） |
| `/new` | 新規登録 |
| `/edit/<id>` | 編集 |
| `/toggle/<id>` | 完了／未完了の切り替え（POST） |
| `/delete/<id>` | 削除（POST） |
| `/notify` | 今すぐLINEに通知（POST） |
| `/cron/notify?key=合言葉` | 毎朝の自動通知用（GitHub Actions から呼ばれる） |

### スプレッドシートの列

| A | B | C | D | E | F | G | H |
|---|---|---|---|---|---|---|---|
| id | title | content | due_date | created_at | updated_at | category | done |

課題1の列（A〜F）はそのままで、G・H列を右に足しています。アプリを起動すると見出しが自動で更新されるので、課題1で登録したデータもそのまま使えます。

---

## セットアップ手順（課題1）

### 1. Google Cloud でサービスアカウントを作る
1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを選ぶ
   - 「組織」に入っているプロジェクトでキーを作れない場合は、「組織: No organization」のプロジェクトを使う
2. 「APIとサービス」→「ライブラリ」で **Google Sheets API** と **Google Drive API** を有効化
3. 「IAMと管理」→「サービスアカウント」→ 作成
4. 作ったサービスアカウントの「鍵」タブ →「鍵を追加」→ **JSON** をダウンロード
5. ダウンロードしたファイルを `credentials.json` という名前で `todo-app` フォルダに置く

### 2. スプレッドシートを用意する
1. Googleスプレッドシートを新規作成
2. 「共有」で、`credentials.json` の中の `client_email` を **編集者** として追加
3. URLの `/d/` と `/edit` の間の文字列が **スプレッドシートID**

### 3. 手元で動かす
```bash
pip install -r requirements.txt
cp .env.example .env             # .env を開いて中身を書き換える
flask --app app run --port 5001 --debug
```
ブラウザで http://localhost:5001 を開く。

### 4. GitHub → Render で公開
- Build Command：`pip install -r requirements.txt`
- Start Command：`gunicorn app:app`
- 環境変数は下の「環境変数まとめ」を参照

---

## セットアップ手順（課題2：LINE通知）

### 1. LINE公式アカウントとチャネルを作る
1. [LINE Official Account Manager](https://manager.line.biz/) で、LINE公式アカウントを作る（名前は「Todo通知」など）
2. 作ったアカウントの「設定」→「Messaging API」→「Messaging APIを利用する」
3. [LINE Developers](https://developers.line.biz/console/) を開き、作ったチャネルを選ぶ
4. 「**Messaging API設定**」タブの一番下で「チャネルアクセストークン（長期）」を**発行**してコピー → `LINE_CHANNEL_ACCESS_TOKEN`
5. 「**チャネル基本設定**」タブの一番下の「あなたのユーザーID」（`U` から始まる）をコピー → `LINE_USER_ID`
6. 「Messaging API設定」タブのQRコードを、スマホのLINEで読み取って**友だち追加**する（追加しないと届きません）

### 2. 合言葉（CRON_SECRET）を作る
```bash
python -c "import secrets; print(secrets.token_hex(16))"
```
出てきた英数字を、Render と GitHub の両方に同じものを設定します。

### 3. 毎朝の自動通知（GitHub Actions）
GitHubのリポジトリ →「Settings」→「Secrets and variables」→「Actions」→「New repository secret」で2つ追加

| Name | Secret |
|---|---|
| `APP_URL` | `https://todo-app-t3ov.onrender.com`（最後に `/` をつけない） |
| `CRON_SECRET` | 2で作った合言葉 |

「Actions」タブ →「毎朝のLINE通知」→「Run workflow」で、手動でも試せます。

---

## 環境変数まとめ

| 名前 | 手元（.env） | Render | 内容 |
|---|---|---|---|
| `SPREADSHEET_ID` | ○ | ○ | スプレッドシートID |
| `SECRET_KEY` | 任意 | ○ | ランダムな長い英数字 |
| `GOOGLE_CREDENTIALS_JSON` | ー | ○ | `credentials.json` の中身まるごと |
| `LINE_CHANNEL_ACCESS_TOKEN` | ○ | ○ | LINEのチャネルアクセストークン（長期） |
| `LINE_USER_ID` | ○ | ○ | 自分のユーザーID（空なら友だち全員に送信） |
| `APP_URL` | 任意 | ○ | 通知に載せる一覧ページのURL |
| `CRON_SECRET` | 任意 | ○ | 自動通知用の合言葉 |

`LINE_CHANNEL_ACCESS_TOKEN` を設定すると、一覧画面に「LINEに通知」ボタンが表示されます。

---

## よくあるエラー

| エラー | 原因と対処 |
|---|---|
| `SpreadsheetNotFound` / `PermissionError` | スプレッドシートをサービスアカウントのメールに共有していない |
| `APIError: ... has not been used` | Sheets API / Drive API が有効になっていない |
| `KeyError: 'SPREADSHEET_ID'` | `.env`（Renderなら環境変数）に設定がない |
| `LINEへの送信に失敗しました（401）` | チャネルアクセストークンが間違っている／貼り付けミス |
| `LINEへの送信に失敗しました（400）` | ユーザーIDが間違っている（`U` から始まる33文字か確認） |
| LINEに届かない（エラーなし） | 公式アカウントを友だち追加していない |
| GitHub Actions が `403` | Render と GitHub の `CRON_SECRET` が一致していない |
