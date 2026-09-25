"""
用户认证：登录、注册、忘记密码
用户数据从 users.json 读写
"""
import os
from flask import session, request, jsonify
from storage import load_json, save_json

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")


# ---------- 用户读写 ----------

def load_users():
    """读 users.json，返回 {username: {...}}"""
    return {u["username"]: u for u in load_json(USERS_FILE, [])}


def save_users(users_dict):
    """写回 users.json"""
    save_json(USERS_FILE, list(users_dict.values()))


# ---------- 路由 ----------

def register_auth_routes(app):

    @app.route("/api/login", methods=["POST"])
    def login():
        users = load_users()
        data = request.get_json()
        username = data.get("username", "")
        phone = data.get("phone", "")
        password = data.get("password", "")
        role = data.get("role", "student")

        # 手机号登录
        if phone:
            for uname, uinfo in users.items():
                if (uinfo.get("phone") == phone
                        and uinfo.get("password") == password
                        and uinfo.get("role") == role):
                    session["username"] = uname
                    session["role"] = role
                    redirect = "/quiz" if role == "student" else "/wrong"
                    return jsonify({"success": True, "redirect": redirect})
            return jsonify({"success": False, "message": "手机号、密码或身份错误"})

        # 账号登录
        user = users.get(username)
        if user and user.get("password") == password and user.get("role") == role:
            session["username"] = username
            session["role"] = role
            redirect = "/quiz" if role == "student" else "/wrong"
            return jsonify({"success": True, "redirect": redirect})
        return jsonify({"success": False, "message": "账号或密码错误"})

    @app.route("/api/register", methods=["POST"])
    def register():
        users = load_users()
        data = request.get_json()
        username = data.get("username", "").strip()
        phone = data.get("phone", "").strip()
        password = data.get("password", "")
        role = data.get("role", "student")

        if not username or not phone or not password:
            return jsonify({"success": False, "message": "请填写完整信息"})
        if username in users:
            return jsonify({"success": False, "message": "该账号已存在"})
        for u in users.values():
            if u.get("phone") == phone:
                return jsonify({"success": False, "message": "该手机号已注册"})

        users[username] = {
            "username": username,
            "password": password,
            "role": role,
            "phone": phone,
        }
        save_users(users)

        return jsonify({"success": True, "message": "注册成功"})

    @app.route("/api/forgot_password", methods=["POST"])
    def forgot_password():
        users = load_users()
        data = request.get_json()
        username = data.get("username", "").strip()
        if username in users:
            users[username]["reset_requested"] = True
            save_users(users)
            return jsonify({"success": True, "message": "已记录，请联系管理员重置密码"})
        return jsonify({"success": False, "message": "该账号不存在"})