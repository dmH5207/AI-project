"""
答题：客观题 / 实操题接口
对话：对话式练习接口
"""
import os
from datetime import datetime
from flask import session, request, jsonify
from storage import load_json, save_json
import ai

QUESTIONS_FILE = os.path.join(os.path.dirname(__file__), "questions.json")
WRONG_FILE = os.path.join(os.path.dirname(__file__), "wrong_answers.json")
STATS_FILE = os.path.join(os.path.dirname(__file__), "quiz_stats.json")
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")
DIALOG_FILE = os.path.join(os.path.dirname(__file__), "dialog_records.json")


MODES = [
    {"key": "dialog",    "name": "对话式练习", "desc": "与 AI 对话，锻炼表达与理解"},
    {"key": "practice",  "name": "实操式练习", "desc": "动手操作，模拟真实任务"},
    {"key": "objective", "name": "客观题练习", "desc": "选择题，快速检测掌握程度"},
]


# ---------- 问候语 ----------

def _make_greeting(username):
    hour = datetime.now().hour
    if 5 <= hour < 11:
        time_word = "早上好"
    elif 11 <= hour < 13:
        time_word = "中午好"
    elif 13 <= hour < 18:
        time_word = "下午好"
    else:
        time_word = "晚上好"

    display = username
    try:
        users = load_json(USERS_FILE, [])
        for u in users:
            if u.get("username") == username:
                display = u.get("nickname") or u.get("username") or username
                break
    except Exception:
        pass

    return time_word + "，" + display + "！\n选一种模式开始吧"


# ---------- 数据读写 ----------

def _get_questions():
    return load_json(QUESTIONS_FILE, [])


def _get_wrong():
    return load_json(WRONG_FILE, {})


def _save_wrong(data):
    save_json(WRONG_FILE, data)


def _get_stats():
    return load_json(STATS_FILE, {})


def _save_stats(data):
    save_json(STATS_FILE, data)


def _bump_stats(username, mode, score):
    stats = _get_stats()
    stats.setdefault(username, {}).setdefault(mode, {"count": 0, "last": None})
    stats[username][mode]["count"] += 1
    stats[username][mode]["last"] = score
    _save_stats(stats)


def _user_stats(username):
    stats = _get_stats().get(username, {})
    result = {}
    for m in MODES:
        s = stats.get(m["key"], {"count": 0, "last": None})
        result[m["key"]] = {"count": s.get("count", 0), "last": s.get("last")}
    return result


def _get_dialog_records():
    return load_json(DIALOG_FILE, {})


def _save_dialog_records(data):
    save_json(DIALOG_FILE, data)


# ================================================================
# 答题接口（客观题 / 实操题）
# ================================================================

def register_quiz_routes(app):

    @app.route("/api/modes", methods=["POST"])
    def modes():
        username = session.get("username")

        if not username:
            stats = {m["key"]: {"count": 0, "last": None} for m in MODES}
            greeting = "请先登录"
        else:
            stats = _user_stats(username)
            greeting = _make_greeting(username)

        result = []
        for m in MODES:
            s = stats[m["key"]]
            result.append({
                "key": m["key"],
                "name": m["name"],
                "desc": m["desc"],
                "count": s["count"],
                "last": s["last"],
            })

        return jsonify({
            "success": True,
            "greeting": greeting,
            "modes": result,
        })

    @app.route("/api/start", methods=["POST"])
    def start():
        data = request.get_json() or {}
        mode = data.get("mode", "objective")

        questions = _get_questions()
        if not questions:
            return jsonify({"success": False, "message": "题库为空"})

        total = min(len(questions), 10)
        session["quiz_mode"] = mode
        session["quiz_ids"] = [q["id"] for q in questions[:total]]
        session["quiz_answers"] = []

        first = questions[0]
        return jsonify({
            "success": True,
            "total": total,
            "question": {
                "id": first["id"],
                "question": first["question"],
                "options": first["options"],
                "dimension": first.get("dimension", "—"),
            },
        })

    @app.route("/api/next", methods=["POST"])
    def next_question():
        data = request.get_json() or {}
        index = int(data.get("index", 0))

        questions = _get_questions()
        ids = session.get("quiz_ids", [])

        if index < 0 or index >= len(ids):
            return jsonify({"success": False, "message": "越界"})

        qid = ids[index]
        q = next((x for x in questions if x["id"] == qid), None)
        if not q:
            return jsonify({"success": False, "message": "题目不存在"})

        return jsonify({
            "success": True,
            "question": {
                "id": q["id"],
                "question": q["question"],
                "options": q["options"],
                "dimension": q.get("dimension", "—"),
            },
        })

    @app.route("/api/answer", methods=["POST"])
    def answer():
        data = request.get_json() or {}
        qid = data.get("question_id")
        user_answer = data.get("answer")

        questions = _get_questions()
        q = next((x for x in questions if x["id"] == qid), None)
        if not q:
            return jsonify({"success": False, "message": "题目不存在"})

        correct_answer = q.get("answer")
        correct = (user_answer == correct_answer)

        log = session.get("quiz_answers", [])
        log.append({"question_id": qid, "correct": correct})
        session["quiz_answers"] = log

        if not correct:
            username = session.get("username") or "anonymous"
            wrong = _get_wrong()
            wrong.setdefault(username, []).append({
                "question_id": qid,
                "wrong_answer": user_answer,
                "correct_answer": correct_answer,
                "dimension": q.get("dimension", "—"),
            })
            _save_wrong(wrong)

        return jsonify({
            "success": True,
            "correct": correct,
            "correct_answer": correct_answer,
        })

    @app.route("/api/report_now", methods=["POST"])
    def report_now():
        log = session.get("quiz_answers", [])
        total = len(log)
        correct = sum(1 for x in log if x.get("correct"))
        score = round(correct / total * 100) if total else 0

        username = session.get("username")
        mode = session.get("quiz_mode", "objective")
        if username:
            _bump_stats(username, mode, score)

        return jsonify({
            "success": True,
            "total": total,
            "correct": correct,
            "score": score,
        })


# ================================================================
# 对话式练习接口
# ================================================================

def register_dialog_routes(app):

    @app.route("/api/dialog/start", methods=["POST"])
    def dialog_start():
        session["dialog_index"] = 0
        session["dialog_records"] = []

        d = ai.get_dimension(0)
        if not d:
            return jsonify({"success": False, "message": "维度配置错误"})

        question = ai.generate_question(d["key"])
        return jsonify({
            "success": True,
            "round": 1,
            "dimension": d["name"],
            "question": question,
        })

    @app.route("/api/dialog/reply", methods=["POST"])
    def dialog_reply():
        data = request.get_json() or {}
        user_answer = (data.get("answer") or "").strip()

        if not user_answer:
            return jsonify({"success": False, "message": "回答不能为空"})

        index = session.get("dialog_index", 0)
        records = session.get("dialog_records", [])

        d = ai.get_dimension(index)
        if not d:
            return jsonify({"success": False, "message": "会话异常"})

        # 按 rubric 评分
        score, _ = ai.score_answer(d, user_answer)

        # 记录这一轮
        records.append({
            "dimension": d["name"],
            "dimension_key": d["key"],
            "answer": user_answer,
            "score": score,
            "weight": d["weight"],
        })
        session["dialog_records"] = records
        session["dialog_index"] = index + 1

        # 生成点评 + 追问
        reply = ai.generate_reply(d["key"], user_answer)

        next_index = index + 1
        finished = (next_index >= len(ai.DIMENSIONS))

        if finished:
            username = session.get("username") or "anonymous"
            all_records = _get_dialog_records()
            all_records.setdefault(username, []).append({
                "records": records,
            })
            _save_dialog_records(all_records)

            return jsonify({
                "success": True,
                "round": next_index,
                "dimension": d["name"],
                "reply": reply,
                "finished": True,
            })

        nd = ai.get_dimension(next_index)
        next_question = ai.generate_question(nd["key"])
        full_reply = reply + "\n\n【下一轮 · " + nd["name"] + "】\n" + next_question

        return jsonify({
            "success": True,
            "round": next_index,
            "dimension": nd["name"],
            "reply": full_reply,
            "finished": False,
        })

    @app.route("/api/dialog/end", methods=["POST"])
    def dialog_end():
        records = session.get("dialog_records", [])
        report = ai.generate_report(records)
        return jsonify({
            "success": True,
            "comment": report["comment"],
            "highlights": report["highlights"],
            "suggestions": report["suggestions"],
            "scores": report["scores"],
            "total_score": report["total_score"],
            "max_score": report["max_score"],
        })