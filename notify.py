"""LINEに期日のお知らせを送る処理（LINE Messaging API）"""
import os
from datetime import timedelta

import requests

PUSH_URL = "https://api.line.me/v2/bot/message/push"
BROADCAST_URL = "https://api.line.me/v2/bot/message/broadcast"


def build_message(todos, today):
    """未完了のやることから「期限切れ・今日・明日」を集めて通知文を作る。
    該当がなければ None を返す"""
    tomorrow = (today + timedelta(days=1)).isoformat()
    today_s = today.isoformat()

    overdue, due_today, due_tomorrow = [], [], []
    for t in todos:
        if t["done"] or not t["due_date"]:
            continue
        if t["due_date"] < today_s:
            overdue.append(t)
        elif t["due_date"] == today_s:
            due_today.append(t)
        elif t["due_date"] == tomorrow:
            due_tomorrow.append(t)

    if not (overdue or due_today or due_tomorrow):
        return None

    def line(t):
        cat = f"［{t['category']}］" if t["category"] else ""
        return f"・{cat}{t['title']}"

    parts = [f"📋 やることリスト（{today.month}/{today.day}）"]
    if overdue:
        parts.append("\n⚠️ 期限切れ")
        parts += [line(t) + f"（{t['due_date'][5:].replace('-', '/')}）" for t in overdue]
    if due_today:
        parts.append("\n🔴 今日まで")
        parts += [line(t) for t in due_today]
    if due_tomorrow:
        parts.append("\n🟡 明日まで")
        parts += [line(t) for t in due_tomorrow]

    app_url = os.environ.get("APP_URL")
    if app_url:
        parts.append(f"\n▶ 一覧を見る\n{app_url}")
    return "\n".join(parts)


def send_line(text):
    """LINEにメッセージを送る。
    LINE_USER_ID があれば自分だけに送信（push）、なければ友だち全員に送信（broadcast）"""
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("LINE_CHANNEL_ACCESS_TOKEN が設定されていません")

    user_id = os.environ.get("LINE_USER_ID")
    body = {"messages": [{"type": "text", "text": text[:5000]}]}
    if user_id:
        url = PUSH_URL
        body["to"] = user_id
    else:
        url = BROADCAST_URL

    res = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json=body,
        timeout=10,
    )
    if res.status_code != 200:
        raise RuntimeError(f"LINEへの送信に失敗しました（{res.status_code}）: {res.text}")
