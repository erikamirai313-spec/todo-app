"""Todoリストアプリ（Flask）"""
import os
from datetime import date

from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, url_for

load_dotenv()  # 手元で動かすときに .env を読み込む

import sheets  # noqa: E402  (.env を読んだあとに読み込む)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")


def _read_form():
    """フォームの入力値を取り出して、空欄チェックをする"""
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    due_date = request.form.get("due_date", "").strip()
    errors = []
    if not title:
        errors.append("タイトルを入力してください")
    if not due_date:
        errors.append("期日を入力してください")
    return title, content, due_date, errors


@app.route("/")
def index():
    """一覧ページ"""
    todos = sheets.get_all_todos()
    return render_template("index.html", todos=todos, today=date.today().isoformat())


@app.route("/new", methods=["GET", "POST"])
def new():
    """新規登録"""
    if request.method == "POST":
        title, content, due_date, errors = _read_form()
        if errors:
            for e in errors:
                flash(e, "error")
            todo = {"title": title, "content": content, "due_date": due_date}
            return render_template("form.html", todo=todo, mode="new")
        sheets.add_todo(title, content, due_date)
        flash("やることを登録しました", "success")
        return redirect(url_for("index"))
    return render_template("form.html", todo={}, mode="new")


@app.route("/edit/<todo_id>", methods=["GET", "POST"])
def edit(todo_id):
    """編集"""
    todo = sheets.get_todo(todo_id)
    if todo is None:
        abort(404)

    if request.method == "POST":
        title, content, due_date, errors = _read_form()
        if errors:
            for e in errors:
                flash(e, "error")
            todo.update(title=title, content=content, due_date=due_date)
            return render_template("form.html", todo=todo, mode="edit")
        sheets.update_todo(todo_id, title, content, due_date)
        flash("やることを更新しました", "success")
        return redirect(url_for("index"))
    return render_template("form.html", todo=todo, mode="edit")


@app.route("/delete/<todo_id>", methods=["POST"])
def delete(todo_id):
    """削除（おまけ機能）"""
    sheets.delete_todo(todo_id)
    flash("やることを削除しました", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
