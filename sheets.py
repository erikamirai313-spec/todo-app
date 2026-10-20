"""Googleスプレッドシートを「データベース」として使うための処理をまとめたファイル"""
import json
import os
import uuid
from datetime import datetime, timedelta, timezone

import gspread

JST = timezone(timedelta(hours=9))
HEADERS = ["id", "title", "content", "due_date", "created_at", "updated_at"]


def _get_worksheet():
    """認証してシート（1枚目のタブ）を取得する"""
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        # Render などのサーバー上：環境変数にJSONの中身をそのまま入れておく
        gc = gspread.service_account_from_dict(json.loads(creds_json))
    else:
        # 手元のPC：credentials.json ファイルを読む
        gc = gspread.service_account(filename="credentials.json")

    sheet = gc.open_by_key(os.environ["SPREADSHEET_ID"])
    ws = sheet.sheet1

    # 1行目に見出しがなければ作る
    if ws.row_values(1) != HEADERS:
        ws.update(range_name="A1:F1", values=[HEADERS])
    return ws


def _now():
    return datetime.now(JST).strftime("%Y-%m-%d %H:%M")


def get_all_todos():
    """全件取得（期日が近い順）"""
    ws = _get_worksheet()
    todos = ws.get_all_records(numericise_ignore=["all"])
    return sorted(todos, key=lambda t: t["due_date"] or "9999-12-31")


def get_todo(todo_id):
    for todo in get_all_todos():
        if todo["id"] == todo_id:
            return todo
    return None


def add_todo(title, content, due_date):
    ws = _get_worksheet()
    now = _now()
    ws.append_row([uuid.uuid4().hex[:8], title, content, due_date, now, now])


def update_todo(todo_id, title, content, due_date):
    ws = _get_worksheet()
    cell = ws.find(todo_id, in_column=1)
    if cell is None:
        return False
    row = cell.row
    ws.update(range_name=f"B{row}:D{row}", values=[[title, content, due_date]])
    ws.update(range_name=f"F{row}", values=[[_now()]])
    return True


def delete_todo(todo_id):
    ws = _get_worksheet()
    cell = ws.find(todo_id, in_column=1)
    if cell is None:
        return False
    ws.delete_rows(cell.row)
    return True
