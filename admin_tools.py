"""
管理员功能
1. 网页端重置密码路由：/api/admin/reset
2. 网页端列出所有用户：/api/admin/users
3. 命令行重置密码工具：reset_password_cli()
共用核心逻辑：_do_reset()
"""

import os
from flask import request, jsonify, session
from werkzeug.security import generate_password_hash
from storage import load_json, save_json

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")


# ---------- 核心逻辑（网页端和命令行共用） ----------

def _load_users_dict():
    """读 users.json，返回 {username: {...}}"""
    return {u["username"]: u for u in load_json(USERS_FILE, [])}


def _save_users_dict(users):
    """写回 users.json"""
    save_json(USERS_FILE, list(users.values()))


def _do_reset(username, new_password):
    """
    重置某个用户的密码
    返回 (成功?, 提示信息)
    """
    username = (username or "").strip()
    new_password = (new_password or "").strip()

    if not username:
        return False, "请输入账号"
    if not new_password:
        return False, "密码不能为空"

    users = _load_users_dict()
    if username not in users:
        return False, "账号不存在"

    users[username]["password"] = generate_password_hash(new_password)
    users[username].pop("reset_requested", None)   # 清掉申请重置的标记
    _save_users_dict(users)

    return True, f"已重置 {username} 的密码"


# ---------- 网页端入口 ----------

def register_admin_routes(app):

    @app.route("/api/admin/reset", methods=["POST"])
    def admin_reset():
        # 权限检查：必须是管理员
        if session.get("role") != "admin":
            return jsonify({"success": False, "message": "无权限"})

        data = request.get_json() or {}
        ok, msg = _do_reset(data.get("username"), data.get("new_password"))
        return jsonify({"success": ok, "message": msg})

    @app.route("/api/admin/users", methods=["GET"])
    def admin_users():
        """列出所有用户（管理员可见），方便前端展示谁申请了重置"""
        if session.get("role") != "admin":
            return jsonify({"success": False, "message": "无权限"})

        users = _load_users_dict()
        result = []
        for uname, uinfo in users.items():
            result.append({
                "username": uname,
                "role": uinfo.get("role"),
                "phone": uinfo.get("phone"),
                "reset_requested": bool(uinfo.get("reset_requested")),
            })
        return jsonify({"success": True, "users": result})


# ---------- 命令行入口 ----------

def reset_password_cli():
    """在终端运行：python app.py reset"""
    users = _load_users_dict()

    print("当前所有账号：")
    for uname, uinfo in users.items():
        flag = " [已申请重置]" if uinfo.get("reset_requested") else ""
        print(f"  - {uname}（{uinfo.get('role')}，{uinfo.get('phone')}）{flag}")

    print()
    username = input("请输入要重置密码的账号：").strip()
    new_pwd = input("请输入新密码：").strip()

    ok, msg = _do_reset(username, new_pwd)
    print(msg)