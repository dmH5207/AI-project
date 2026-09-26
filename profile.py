"""
我的：用户信息、改密码、退出、头像上传
"""
import os
import uuid
from flask import session, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from storage import load_json, save_json

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")
AVATAR_DIR = os.path.join(os.path.dirname(__file__), "static", "avatars")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_AVATAR_SIZE = 2 * 1024 * 1024

os.makedirs(AVATAR_DIR, exist_ok=True)


def _load_users():
    return {u["username"]: u for u in load_json(USERS_FILE, [])}


def _save_users(users_dict):
    save_json(USERS_FILE, list(users_dict.values()))


def register_profile_routes(app):

    @app.route("/api/me/info")
    def me_info():
        username = session.get("username")
        if not username:
            return jsonify({"success": False, "message": "未登录"}), 401
        users = _load_users()
        user = users.get(username)
        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 404
        avatar = user.get("avatar", "")
        if not avatar:
            avatar = "/static/avatar.png"
        return jsonify({
            "success": True,
            "data": {
                "username": user["username"],
                "phone": user.get("phone", ""),
                "role": user.get("role", "student"),
                "avatar": avatar
            }
        })

    @app.route("/api/me/change_password", methods=["POST"])
    def me_change_password():
        username = session.get("username")
        if not username:
            return jsonify({"success": False, "message": "未登录"}), 401
        data = request.get_json()
        old_pwd = data.get("old_password", "")
        new_pwd = data.get("new_password", "")
        if not old_pwd or not new_pwd:
            return jsonify({"success": False, "message": "请填写完整"})
        if len(new_pwd) < 6:
            return jsonify({"success": False, "message": "新密码至少6位"})
        users = _load_users()
        user = users.get(username)
        if not user:
            return jsonify({"success": False, "message": "用户不存在"})
        if not check_password_hash(user.get("password", ""), old_pwd):
            return jsonify({"success": False, "message": "原密码错误"})
        users[username]["password"] = generate_password_hash(new_pwd)
        _save_users(users)
        return jsonify({"success": True, "message": "密码修改成功"})

    @app.route("/api/me/upload_avatar", methods=["POST"])
    def me_upload_avatar():
        username = session.get("username")
        if not username:
            return jsonify({"success": False, "message": "未登录"}), 401
        if "avatar" not in request.files:
            return jsonify({"success": False, "message": "请选择图片"})
        file = request.files["avatar"]
        if file.filename == "":
            return jsonify({"success": False, "message": "请选择图片"})
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            return jsonify({"success": False, "message": "仅支持 png/jpg/jpeg/gif/webp 格式"})
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > MAX_AVATAR_SIZE:
            return jsonify({"success": False, "message": "图片大小不能超过 2MB"})
        filename = f"{username}_{uuid.uuid4().hex[:8]}.{ext}"
        filepath = os.path.join(AVATAR_DIR, filename)
        file.save(filepath)
        avatar_url = f"/static/avatars/{filename}"
        users = _load_users()
        if username not in users:
            return jsonify({"success": False, "message": "用户不存在"})
        old_avatar = users[username].get("avatar", "")
        users[username]["avatar"] = avatar_url
        _save_users(users)
        if old_avatar and old_avatar.startswith("/static/avatars/"):
            old_path = os.path.join(os.path.dirname(__file__), old_avatar.lstrip("/"))
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except OSError:
                    pass
        return jsonify({"success": True, "message": "头像更新成功", "avatar": avatar_url})

    @app.route("/api/logout", methods=["POST"])
    def logout():
        session.clear()
        return jsonify({"success": True, "message": "已退出登录"})