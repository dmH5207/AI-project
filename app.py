"""
后端主程序（Python / Flask）
只负责：创建 app、页面路由、注册各模块、启动
"""

from flask import Flask, render_template, session
from auth import register_auth_routes, migrate_passwords
from quiz import (
    register_quiz_routes,
    register_dialog_routes,
    register_practice_routes,
)
from wrong import register_wrong_routes
from profile import register_profile_routes
from admin_tools import register_admin_routes

app = Flask(__name__)
app.secret_key = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/quiz")
def quiz():
    return render_template("quiz.html", role=session.get("role", "student"))


@app.route("/dialog")
def dialog():
    return render_template("dialog.html")


@app.route("/practice")
def practice():
    return render_template("practice.html")


@app.route("/wrong")
def wrong():
    return render_template("wrong.html", role=session.get("role", "student"))


@app.route("/me")
def me():
    return render_template("me.html", role=session.get("role", "student"))


@app.route("/admin")
def admin():
    return render_template("admin.html", role=session.get("role", "student"))


# 启动时迁移明文密码为哈希
migrate_passwords()

# 注册各模块
register_auth_routes(app)
register_quiz_routes(app)
register_dialog_routes(app)
register_practice_routes(app)
register_wrong_routes(app)
register_profile_routes(app)
register_admin_routes(app)


def _fix_placeholder_answers():
    import os as _os
    import ai as _ai_mod
    from storage import load_json, save_json
    _wrong_file = _os.path.join(_os.path.dirname(__file__), "wrong_answers.json")
    _placeholder_keywords = ["对话题", "实操题", "参考AI", "参考答案", "开放题"]
    wrong_data = load_json(_wrong_file, {})
    if not isinstance(wrong_data, dict):
        return
    _need_save = False
    _count = 0
    for _uname in wrong_data:
        if not isinstance(wrong_data[_uname], list):
            continue
        for _it in wrong_data[_uname]:
            if not isinstance(_it, dict):
                continue
            _ca = _it.get("correct_answer", "")
            if any(kw in _ca for kw in _placeholder_keywords):
                _q = _it.get("question", "")
                _d = _it.get("dimension", "")
                print(f"    Generating reference answer for: {_q[:30]}...")
                _ref = _ai_mod.generate_reference_answer(_q, _d)
                _it["correct_answer"] = _ref
                _need_save = True
                _count += 1
    if _need_save:
        save_json(_wrong_file, wrong_data)
        print(f"    Updated {_count} placeholder answers with AI-generated references.")
    else:
        print("    No placeholder answers found. All good.")


if __name__ == "__main__":
    import sys
    import os
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        from admin_tools import reset_password_cli
        reset_password_cli()
    else:
        port = int(os.environ.get("PORT", 5000))
        if len(sys.argv) > 1:
            try:
                port = int(sys.argv[1])
            except ValueError:
                pass
        print(f"\n  AI Assessment System running at:")
        print(f"    -> Local:   http://127.0.0.1:{port}")
        print(f"    -> Network: http://<your-ip>:{port}")
        print(f"\n  Checking placeholder answers in wrong_answers.json...")
        _fix_placeholder_answers()
        print(f"    -> Press CTRL+C to quit\n")
        app.run(host="0.0.0.0", port=port, debug=True)


if __name__ == "__main__":
    import sys
    import os
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        from admin_tools import reset_password_cli
        reset_password_cli()
    else:
        port = int(os.environ.get("PORT", 5000))
        if len(sys.argv) > 1:
            try:
                port = int(sys.argv[1])
            except ValueError:
                pass
        print(f"\n  AI Assessment System running at:")
        print(f"    -> Local:   http://127.0.0.1:{port}")
        print(f"    -> Network: http://<your-ip>:{port}")
        print(f"    -> Press CTRL+C to quit\n")
        app.run(host="0.0.0.0", port=port, debug=True)