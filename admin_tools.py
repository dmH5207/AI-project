"""
管理员功能
1. 网页端重置密码路由：/api/admin/reset
2. 网页端列出所有用户：/api/admin/users
3. 答题数据统计：/api/admin/stats
4. 命令行重置密码工具：reset_password_cli()
共用核心逻辑：_do_reset()
"""

import os
from flask import request, jsonify, session
from werkzeug.security import generate_password_hash
from storage import load_json, save_json

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")
STATS_FILE = os.path.join(os.path.dirname(__file__), "quiz_stats.json")
WRONG_FILE = os.path.join(os.path.dirname(__file__), "wrong_answers.json")
DIALOG_FILE = os.path.join(os.path.dirname(__file__), "dialog_records.json")
PRACTICE_FILE = os.path.join(os.path.dirname(__file__), "practice_records.json")


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

    @app.route("/api/admin/stats", methods=["GET"])
    def admin_stats():
        if session.get("role") != "admin":
            return jsonify({"success": False, "message": "无权限"})
        try:
            users = _load_users_dict()
            quiz_stats = load_json(STATS_FILE, {})
            wrong_data = load_json(WRONG_FILE, {})
            dialog_data = load_json(DIALOG_FILE, {})
            practice_data = load_json(PRACTICE_FILE, {})

            students = [u for u in users.values() if u.get("role") == "student"]
            student_names = [s["username"] for s in students]

            mode_counts = {"dialog": [], "practice": [], "objective": []}
            mode_last_scores = {"dialog": [], "practice": [], "objective": []}
            for name in student_names:
                us = quiz_stats.get(name, {})
                for mode in ("dialog", "practice", "objective"):
                    m = us.get(mode, {})
                    mode_counts[mode].append(m.get("count", 0))
                    last = m.get("last")
                    mode_last_scores[mode].append(last if last is not None else 0)

            dim_names = ["AI基础认知", "AI工具使用", "提示词工程", "AI结果评估与优化", "AI伦理与安全", "人机协同解决问题"]
            dim_wrong_counts = {d: 0 for d in dim_names}
            for uname, items in wrong_data.items():
                if isinstance(items, list):
                    for it in items:
                        dim = it.get("dimension", "")
                        if dim in dim_wrong_counts:
                            dim_wrong_counts[dim] += 1

            radar_data = {}
            for name in student_names:
                scores = [0] * len(dim_names)
                for records_group in dialog_data.get(name, []):
                    for r in records_group.get("records", []):
                        dk = r.get("dimension", "")
                        if dk in dim_names:
                            idx = dim_names.index(dk)
                            w = r.get("weight", 20)
                            s = r.get("score", 0)
                            scores[idx] = max(scores[idx], round(s / w * 100)) if w else 0
                for records_group in practice_data.get(name, []):
                    for r in records_group.get("records", []):
                        dk = r.get("dimension", "")
                        if dk in dim_names:
                            idx = dim_names.index(dk)
                            w = r.get("weight", 20)
                            s = r.get("score", 0)
                            scores[idx] = max(scores[idx], round(s / w * 100)) if w else 0
                radar_data[name] = scores

            total_wrong = sum(len(v) for v in wrong_data.values() if isinstance(v, list))
            total_dialog = sum(len(v) for v in dialog_data.values() if isinstance(v, list))
            total_practice = sum(len(v) for v in practice_data.values() if isinstance(v, list))

            return jsonify({
                "success": True,
                "student_names": student_names,
                "mode_counts": mode_counts,
                "mode_last_scores": mode_last_scores,
                "dim_names": dim_names,
                "dim_wrong_counts": dim_wrong_counts,
                "radar_data": radar_data,
                "summary": {
                    "student_count": len(students),
                    "total_wrong": total_wrong,
                    "total_dialog": total_dialog,
                    "total_practice": total_practice,
                },
            })
        except Exception as e:
            return jsonify({"success": False, "message": "统计接口错误: " + str(e)})

    @app.route("/api/admin/wrong_list", methods=["GET"])
    def admin_wrong_list():
        if session.get("role") != "admin":
            return jsonify({"success": False, "message": "无权限"})
        try:
            import ai as _ai_mod
            wrong_data = load_json(WRONG_FILE, {})
            _placeholder_keywords = ["对话题", "实操题", "参考AI", "参考答案", "开放题"]
            _need_save = False
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
                        _ref = _ai_mod.generate_reference_answer(_q, _d)
                        _it["correct_answer"] = _ref
                        _need_save = True
            if _need_save:
                save_json(WRONG_FILE, wrong_data)
            dim_map = {}
            for username, items in wrong_data.items():
                if not isinstance(items, list):
                    continue
                for it in items:
                    if not isinstance(it, dict):
                        continue
                    dim = it.get("dimension", "未分类")
                    dim_en = it.get("dimension_en", dim)
                    if dim not in dim_map:
                        dim_map[dim] = {"dimension": dim, "dimension_en": dim_en, "items": []}
                    entry = {
                        "id": it.get("id", ""),
                        "question": it.get("question", ""),
                        "question_en": it.get("question_en", ""),
                        "user_answer": it.get("user_answer", ""),
                        "correct_answer": it.get("correct_answer", ""),
                        "username": username,
                        "time": it.get("time", ""),
                        "mastered": it.get("mastered", False),
                    }
                    dim_map[dim]["items"].append(entry)
            result = sorted(dim_map.values(), key=lambda d: len(d["items"]), reverse=True)
            return jsonify({"success": True, "data": result})
        except Exception as e:
            return jsonify({"success": False, "message": "错题列表接口错误: " + str(e)})


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