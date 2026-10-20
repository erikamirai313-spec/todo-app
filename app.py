"""Todoリストアプリ（Flask）"""
import hmac
import os

from dotenv import load_dotenv
from flask import (Flask, abort, flash, jsonify, redirect, render_template,
                   request, url_for)

load_dotenv()  # 手元で動かすときに .env を読み込む

import notify  # noqa: E402
import sheets  # noqa: E402  (.env を読んだあとに読み込む)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# カテゴリ入力欄に最初から出しておく候補
DEFAULT_CATEGORIES = ["仕事", "学校", "家のこと"]


def _read_form():
    """フォームの入力値を取り出して、空欄チェックをする"""
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    due_date = request.form.get("due_date", "").strip()
    category = request.form.get("category", "").strip()
    errors = []
    if not title:
        errors.append("タイトルを入力してください")
    if not due_date:
        errors.append("期日を入力してください")
    return title, content, due_date, category, errors


def _category_choices(todos):
    """候補 ＝ 最初からある候補 ＋ これまでに使ったカテゴリ"""
    used = sorted({t["category"] for t in todos if t["category"]})
    return DEFAULT_CATEGORIES + [c for c in used if c not in DEFAULT_CATEGORIES]


def _back_to_list():
    """一覧に戻る（絞り込みの状態を保ったまま）"""
    next_url = request.form.get("next", "")
    # 他のサイトに飛ばされないように、このアプリ内のURLだけを許可する
    if not next_url.startswith("/") or next_url.startswith("//"):
        next_url = url_for("index")
    return redirect(next_url)


@app.route("/")
def index():
    """一覧ページ（完了状態とカテゴリで絞り込みできる）"""
    status = request.args.get("status", "todo")  # todo / done / all
    category = request.args.get("category", "")

    all_todos = sheets.get_all_todos()

    todos = all_todos
    if category:
        todos = [t for t in todos if t["category"] == category]
    counts = {
        "todo": sum(not t["done"] for t in todos),
        "done": sum(t["done"] for t in todos),
        "all": len(todos),
    }
    if status == "todo":
        todos = [t for t in todos if not t["done"]]
    elif status == "done":
        todos = [t for t in todos if t["done"]]

    categories = sorted({t["category"] for t in all_todos if t["category"]})

    return render_template(
        "index.html",
        todos=todos,
        today=sheets.today_jst().isoformat(),
        status=status,
        category=category,
        categories=categories,
        counts=counts,
        line_enabled=bool(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")),
    )


@app.route("/new", methods=["GET", "POST"])
def new():
    """新規登録"""
    if request.method == "POST":
        title, content, due_date, category, errors = _read_form()
        if errors:
            for e in errors:
                flash(e, "error")
            todo = {"title": title, "content": content, "due_date": due_date, "category": category}
            return render_template("form.html", todo=todo, mode="new",
                                   choices=_category_choices(sheets.get_all_todos()))
        sheets.add_todo(title, content, due_date, category)
        flash("やることを登録しました", "success")
        return redirect(url_for("index"))
    # 一覧で絞り込んでいたカテゴリを、最初から入れておく
    todo = {"category": request.args.get("category", "")}
    return render_template("form.html", todo=todo, mode="new",
                           choices=_category_choices(sheets.get_all_todos()))


@app.route("/edit/<todo_id>", methods=["GET", "POST"])
def edit(todo_id):
    """編集"""
    all_todos = sheets.get_all_todos()
    todo = next((t for t in all_todos if t["id"] == todo_id), None)
    if todo is None:
        abort(404)

    if request.method == "POST":
        title, content, due_date, category, errors = _read_form()
        if errors:
            for e in errors:
                flash(e, "error")
            todo.update(title=title, content=content, due_date=due_date, category=category)
            return render_template("form.html", todo=todo, mode="edit",
                                   choices=_category_choices(all_todos))
        sheets.update_todo(todo_id, title, content, due_date, category)
        flash("やることを更新しました", "success")
        return redirect(url_for("index"))
    return render_template("form.html", todo=todo, mode="edit",
                           choices=_category_choices(all_todos))


@app.route("/toggle/<todo_id>", methods=["POST"])
def toggle(todo_id):
    """完了／未完了の切り替え"""
    done = request.form.get("done") == "1"
    sheets.set_done(todo_id, done)
    flash("おつかれさまでした！完了にしました 🎉" if done else "未完了に戻しました", "success")
    return _back_to_list()


@app.route("/delete/<todo_id>", methods=["POST"])
def delete(todo_id):
    """削除"""
    sheets.delete_todo(todo_id)
    flash("やることを削除しました", "success")
    return _back_to_list()


@app.route("/notify", methods=["POST"])
def notify_now():
    """画面のボタンから、今すぐLINEに通知する（テスト用）"""
    todos = sheets.get_all_todos()
    message = notify.build_message(todos, sheets.today_jst())
    if message is None:
        message = "📋 やることリスト\n\n期限切れ・今日・明日が期日のやることはありません 🎉"
    try:
        notify.send_line(message)
        flash("LINEに通知を送りました", "success")
    except Exception as e:  # noqa: BLE001
        flash(str(e), "error")
    return _back_to_list()


@app.route("/cron/notify")
def cron_notify():
    """毎朝の自動通知用（GitHub Actions から呼ばれる）。
    ?key= に合言葉（CRON_SECRET）がないと動かない"""
    secret = os.environ.get("CRON_SECRET", "")
    key = request.args.get("key", "")
    if not secret or not hmac.compare_digest(key, secret):
        abort(403)

    todos = sheets.get_all_todos()
    message = notify.build_message(todos, sheets.today_jst())
    if message is None:
        # 該当なしの日は送らない（LINEの無料送信数を節約）
        return jsonify(sent=False, reason="no todos due")
    notify.send_line(message)
    return jsonify(sent=True)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
