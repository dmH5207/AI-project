"""
后端主程序（Python / Flask）
负责：接收前端发来的请求 -> 处理逻辑（判分、调用AI等）-> 把结果返回给前端
"""

from flask import Flask, render_template, session, request, jsonify

app = Flask(__name__)
app.secret_key = "换成任意一串随机字符串"

USERS = {
    "admin": {"password": "admin123", "role": "admin", "phone": "13800000001"},
    "student": {"password": "student123", "role": "student", "phone": "13800000002"},
}

# TODO 1：在这里加载题库数据


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/quiz")
def quiz():
    return render_template("quiz.html")


@app.route("/report")
def report():
    return render_template("report.html")


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username", "")
    phone = data.get("phone", "")
    password = data.get("password", "")
    role = data.get("role", "student")

    if phone:
        for uname, uinfo in USERS.items():
            if uinfo.get("phone") == phone and uinfo["password"] == password and uinfo["role"] == role:
                session["username"] = uname
                session["role"] = role
                redirect = "/quiz" if role == "student" else "/report"
                return jsonify({"success": True, "redirect": redirect})
        return jsonify({"success": False, "message": "手机号、密码或身份错误"})

    user = USERS.get(username)
    if user and user["password"] == password and user["role"] == role:
        session["username"] = username
        session["role"] = role
        redirect = "/quiz" if role == "student" else "/report"
        return jsonify({"success": True, "redirect": redirect})
    else:
        return jsonify({"success": False, "message": "账号或密码错误"})


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username", "")
    phone = data.get("phone", "")
    password = data.get("password", "")
    role = data.get("role", "student")

    if not username or not phone or not password:
        return jsonify({"success": False, "message": "请填写完整信息"})
    if username in USERS:
        return jsonify({"success": False, "message": "该账号已存在"})
    for u in USERS.values():
        if u.get("phone") == phone:
            return jsonify({"success": False, "message": "该手机号已注册"})

    USERS[username] = {"password": password, "role": role, "phone": phone}
    return jsonify({"success": True, "message": "注册成功"})


@app.route("/api/forgot_password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    username = data.get("username", "")
    if username in USERS:
        return jsonify({"success": True, "message": "已记录，请联系管理员重置密码"})
    else:
        return jsonify({"success": False, "message": "该账号不存在"})


@app.route("/api/start", methods=["POST"])
def start():
    # TODO：初始化session，返回第一题数据
    pass


@app.route("/api/answer", methods=["POST"])
def answer():
    data = request.get_json()
    question_id = data.get("question_id")
    user_answer = data.get("answer")

    # TODO：判分逻辑

    pass


@app.route("/api/report_data")
def report_data():
    # TODO：返回汇总得分
    pass


if __name__ == "__main__":
    app.run(debug=True)