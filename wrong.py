"""
错题中心：列表、统计报告、移除、举一反三
"""
import json
import os
from flask import request, jsonify, session
from datetime import datetime

WRONG_FILE = os.path.join(os.path.dirname(__file__), "wrong_answers.json")

def _read_wrong():
    if not os.path.exists(WRONG_FILE) or os.path.getsize(WRONG_FILE) == 0:
        return []
    try:
        with open(WRONG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "wrong_answers" in data:
            return data["wrong_answers"]
        all_items = []
        for username, items in data.items():
            if isinstance(items, list):
                for it in items:
                    if isinstance(it, dict):
                        it.setdefault("user", username)
                        all_items.append(it)
        return all_items
    return []

def _write_wrong(items):
    with open(WRONG_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def _read_wrong_dict():
    if not os.path.exists(WRONG_FILE) or os.path.getsize(WRONG_FILE) == 0:
        return {}
    try:
        with open(WRONG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}
    if isinstance(data, dict):
        return data
    return {}

def _save_wrong_dict(data):
    with open(WRONG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _find_item(all_items, qid):
    for it in all_items:
        if it.get("id") == qid or it.get("question_id") == qid:
            return it
    return None

def register_wrong_routes(app):

    @app.route("/api/wrong/list")
    def wrong_list():
        items = _read_wrong()
        items.sort(key=lambda x: x.get("num", x.get("id", 0)))
        for i, it in enumerate(items):
            it.setdefault("num", i + 1)
        return jsonify({"success": True, "wrong_answers": items})

    @app.route("/api/wrong/report")
    def wrong_report():
        items = _read_wrong()
        mastered = sum(1 for it in items if it.get("mastered"))
        return jsonify({
            "success": True,
            "total": len(items),
            "mastered": mastered,
            "unmastered": len(items) - mastered
        })

    @app.route("/api/wrong/remove/<int:qid>", methods=["POST"])
    def wrong_remove(qid):
        data = _read_wrong_dict()
        if isinstance(data, dict) and "wrong_answers" not in data:
            for username in data:
                data[username] = [it for it in data[username]
                                   if it.get("id") != qid and it.get("question_id") != qid]
            _save_wrong_dict(data)
        else:
            items = _read_wrong()
            items = [it for it in items if it.get("id") != qid and it.get("question_id") != qid]
            _write_wrong(items)
        return jsonify({"success": True})

    @app.route("/api/wrong/master/<int:qid>", methods=["POST"])
    def wrong_master(qid):
        body = request.get_json(silent=True) or {}
        flag = body.get("mastered", True)
        data = _read_wrong_dict()
        if isinstance(data, dict) and "wrong_answers" not in data:
            for username in data:
                for it in data[username]:
                    if it.get("id") == qid or it.get("question_id") == qid:
                        it["mastered"] = flag
            _save_wrong_dict(data)
        else:
            items = _read_wrong()
            for it in items:
                if it.get("id") == qid or it.get("question_id") == qid:
                    it["mastered"] = flag
                    break
            _write_wrong(items)
        return jsonify({"success": True, "mastered": flag})

    @app.route("/api/wrong/analyze/<int:qid>", methods=["POST"])
    def wrong_analyze(qid):
        items = _read_wrong()
        item = _find_item(items, qid)
        if not item:
            return jsonify({"success": False, "message": "错题不存在"})

        question = item.get("question", item.get("text", ""))
        user_answer = item.get("user_answer", item.get("wrong_answer", ""))
        correct_answer = item.get("correct_answer", item.get("answer", ""))
        options = item.get("options", [])
        dimension = item.get("dimension", "")

        analysis = (
            "\u3010\u9898\u76ee\u3011" + question + "\n\n"
            "\u3010\u4f60\u7684\u7b54\u6848\u3011" + str(user_answer) + "\n"
            "\u3010\u6b63\u786e\u7b54\u6848\u3011" + str(correct_answer) + "\n\n"
            "\u3010\u89e3\u6790\u3011\u4f60\u9009\u62e9\u4e86 " + str(user_answer) + "\uff0c\u4f46\u6b63\u786e\u7b54\u6848\u662f " + str(correct_answer) + "\u3002"
            "\u8fd9\u8bf4\u660e\u5bf9" + dimension + "\u76f8\u5173\u77e5\u8bc6\u70b9\u7684\u7406\u89e3\u8fd8\u4e0d\u591f\u6df1\u5165\u3002"
            "\u5efa\u8bae\u56de\u987e\u8be5\u77e5\u8bc6\u70b9\u7684\u6838\u5fc3\u6982\u5ff5\uff0c\u6ce8\u610f\u533a\u5206\u6613\u6df7\u6dc6\u7684\u9009\u9879\uff0c"
            "\u5e76\u901a\u8fc7\u53d8\u5f0f\u8bad\u7ec3\u52a0\u6df1\u7406\u89e3\u3002"
        )

        practice = {
            "question": "\u3010\u53d8\u5f0f\u8bad\u7ec3\u3011\u5173\u4e8e" + dimension + "\uff0c\u4ee5\u4e0b\u54ea\u4e2a\u8bf4\u6cd5\u662f\u6b63\u786e\u7684\uff1f",
            "options": [
                "A. " + dimension + "\u7684\u6838\u5fc3\u6982\u5ff5\u9700\u8981\u7ed3\u5408\u5177\u4f53\u573a\u666f\u7406\u89e3",
                "B. " + dimension + "\u53ea\u9700\u8981\u8bb0\u5fc6\uff0c\u4e0d\u9700\u8981\u7406\u89e3",
                "C. " + dimension + "\u4e0e\u5176\u4ed6\u9886\u57df\u5b8c\u5168\u65e0\u5173",
                "D. " + dimension + "\u53ea\u6709\u4e00\u79cd\u56fa\u5b9a\u7684\u5e94\u7528\u65b9\u5f0f"
            ],
            "answer": "A",
            "hint": "\u53d8\u5f0f\u8bad\u7ec3\u7684\u6838\u5fc3\u601d\u8def\uff1a\u540c\u4e00\u77e5\u8bc6\u70b9\u5728\u4e0d\u540c\u573a\u666f\u4e0b\u7684\u8868\u73b0\u53ef\u80fd\u4e0d\u540c\uff0c"
                    "\u9700\u8981\u7406\u89e3\u672c\u8d28\u800c\u975e\u6b7b\u8bb0\u786c\u80cc\u3002\u6392\u9664\u7edd\u5bf9\u5316\u8868\u8ff0\uff08\u5982\u201c\u53ea\u9700\u8981\u201d\u3001\u201c\u5b8c\u5168\u65e0\u5173\u201d\u3001\u201c\u53ea\u6709\u4e00\u79cd\u201d\uff09\uff0c"
                    "\u9009\u62e9\u5f3a\u8c03\u7406\u89e3\u548c\u573a\u666f\u7684\u9009\u9879\u3002"
        }

        return jsonify({
            "success": True,
            "analysis": analysis,
            "practice": practice
        })
