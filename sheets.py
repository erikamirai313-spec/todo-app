"""Googleスプレッドシートを「データベース」として使うための処理をまとめたファイル"""
import json
import os
import uuid
from datetime import datetime, timedelta, timezone

import gspread

JST = timezone(timedelta(hours=9))

# 課題1の列（A〜F）はそのままにして、新しい列を右側（G・H）に足している
# → 課題1で登録したデータもそのまま使える
HEADERS = [
    "id", "title", "content", "due_date", "created_at", "updated_at",
    "category", "done",
]
COL_CATEGORY = "G"
COL_DONE = "H"

_worksheet = None  # 一度つないだシートを使い回して、表示を速くする


def _get_worksheet():
    """認証してシート（1枚目のタブ）を取得する"""
    global _worksheet
    if _worksheet is not None:
        return _worksheet

    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        # Render などのサーバー上：環境変数にJSONの中身をそのまま入れておく
        gc = gspread.service_account_from_dict(json.loads(creds_json))
    else:
        # 手元のPC：credentials.json ファイルを読む
        gc = gspread.service_account(filename="credentials.json")

    ws = gc.open_by_key(os.environ["SPREADSHEET_ID"]).sheet1

    # 1行目の見出しが最新でなければ書き直す（G・H列が足される）
    if ws.row_values(1) != HEADERS:
        ws.update(range_name="A1:H1", values=[HEADERS])

    _worksheet = ws
    return ws


def now_jst():
    return datetime.now(JST)


def today_jst():
    """日本時間の「今日」（Renderのサーバーは世界標準時なので注意）"""
    return now_jst().date()


def _now_str():
    return now_jst().strftime("%Y-%m-%d %H:%M")


def _normalize(todo):
    """シートから読んだ1行を、アプリで使いやすい形に整える"""
    todo["category"] = (todo.get("category") or "").strip()
    todo["done"] = str(todo.get("done", "")).upper() == "TRUE"
    return todo


def get_all_todos():
    """全件取得（期日が近い順）"""
    ws = _get_worksheet()
    todos = [_normalize(t) for t in ws.get_all_records(numericise_ignore=["all"])]
    return sorted(todos, key=lambda t: t["due_date"] or "9999-12-31")


def get_todo(todo_id):
    for todo in get_all_todos():
        if todo["id"] == todo_id:
            return todo
    return None


def add_todo(title, content, due_date, category):
    ws = _get_worksheet()
    now = _now_str()
    ws.append_row([uuid.uuid4().hex[:8], title, content, due_date, now, now, category, ""])


def _find_row(ws, todo_id):
    cell = ws.find(todo_id, in_column=1)
    return cell.row if cell else None


def update_todo(todo_id, title, content, due_date, category):
    ws = _get_worksheet()
    row = _find_row(ws, todo_id)
    if row is None:
        return False
    ws.batch_update([
        {"range": f"B{row}:D{row}", "values": [[title, content, due_date]]},
        {"range": f"F{row}", "values": [[_now_str()]]},
        {"range": f"{COL_CATEGORY}{row}", "values": [[category]]},
    ])
    return True


def set_done(todo_id, done):
    """完了／未完了を切り替える"""
    ws = _get_worksheet()
    row = _find_row(ws, todo_id)
    if row is None:
        return False
    ws.batch_update([
        {"range": f"F{row}", "values": [[_now_str()]]},
        {"range": f"{COL_DONE}{row}", "values": [["TRUE" if done else ""]]},
    ])
    return True


def delete_todo(todo_id):
    ws = _get_worksheet()
    row = _find_row(ws, todo_id)
    if row is None:
        return False
    ws.delete_rows(row)
    return True
