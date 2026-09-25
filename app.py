"""
后端主程序（Python / Flask）
只负责：创建 app、页面路由、注册各模块、启动
"""

from flask import Flask, render_template
from auth import register_auth_routes
from quiz import (
    register_quiz_routes,
    register_dialog_routes,
    register_practice_routes,
)
from wrong import register_wrong_routes
from profile import register_profile_routes
from admin_tools import register_admin_routes

app = Flask(__name__)
app.secret_key = "换成任意一串随机字符串"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/quiz")
def quiz():
    return render_template("quiz.html")


@app.route("/dialog")
def dialog():
    return render_template("dialog.html")


@app.route("/practice")
def practice():
    return render_template("practice.html")


@app.route("/wrong")
def wrong():
    return render_template("wrong.html")


@app.route("/me")
def me():
    return render_template("me.html")


# 注册各模块
register_auth_routes(app)
register_quiz_routes(app)
register_dialog_routes(app)
register_practice_routes(app)
register_wrong_routes(app)
register_profile_routes(app)
register_admin_routes(app)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        from admin_tools import reset_password_cli
        reset_password_cli()
    else:
        app.run(debug=True)