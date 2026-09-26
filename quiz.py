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
    {"key": "dialog",    "nameKey": "modeDialog",    "descKey": "modeDialogDesc"},
    {"key": "practice",  "nameKey": "modePractice",  "descKey": "modePracticeDesc"},
    {"key": "objective", "nameKey": "modeObjective", "descKey": "modeObjectiveDesc"},
]


# ---------- 问候语 ----------

def _make_greeting(username):
    hour = datetime.now().hour
    if 5 <= hour < 11:
        time_key = "morningGreeting"
    elif 11 <= hour < 13:
        time_key = "noonGreeting"
    elif 13 <= hour < 18:
        time_key = "afternoonGreeting"
    else:
        time_key = "eveningGreeting"

    display = username
    try:
        users = load_json(USERS_FILE, [])
        for u in users:
            if u.get("username") == username:
                display = u.get("nickname") or u.get("username") or username
                break
    except Exception:
        pass

    return {"timeKey": time_key, "display": display}


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

def _format_question(q):
    result = {
        "id": q["id"],
        "type": q.get("type", "single"),
        "question": q["question"],
        "options": q.get("options", []),
        "dimension": q.get("dimension", "\u2014"),
    }
    if q.get("question_en"):
        result["question_en"] = q["question_en"]
    if q.get("options_en"):
        result["options_en"] = q["options_en"]
    if q.get("dimension_en"):
        result["dimension_en"] = q["dimension_en"]
    if q.get("analysis"):
        result["analysis"] = q["analysis"]
    if q.get("analysis_en"):
        result["analysis_en"] = q["analysis_en"]
    if q.get("reference"):
        result["reference"] = q["reference"]
    if q.get("scoring_points"):
        result["scoring_points"] = q["scoring_points"]
    return result


def register_quiz_routes(app):

    @app.route("/api/modes", methods=["POST"])
    def modes():
        username = session.get("username") or "anonymous"
        stats = _user_stats(username)
        if not session.get("username"):
            greeting = {"timeKey": "", "display": "", "notLoggedIn": True}
        else:
            greeting = _make_greeting(username)

        result = []
        for m in MODES:
            s = stats[m["key"]]
            result.append({
                "key": m["key"],
                "nameKey": m["nameKey"],
                "descKey": m["descKey"],
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

        total = min(len(questions), 17)
        session["quiz_mode"] = mode
        session["quiz_ids"] = [q["id"] for q in questions[:total]]
        session["quiz_answers"] = []

        first = questions[0]
        return jsonify({
            "success": True,
            "total": total,
            "question": _format_question(first),
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
            "question": _format_question(q),
        })

    @app.route("/api/answer", methods=["POST"])
    def answer():
        data = request.get_json() or {}
        qid = data.get("question_id")
        user_answer = data.get("answer")
        lang = data.get("lang", "zh")

        questions = _get_questions()
        q = next((x for x in questions if x["id"] == qid), None)
        if not q:
            return jsonify({"success": False, "message": "题目不存在"})

        qtype = q.get("type", "single")
        correct_answer = q.get("answer", "")

        if qtype == "multi":
            correct = (sorted(user_answer.upper()) == sorted(correct_answer.upper()))
        elif qtype in ("practice", "scenario", "design"):
            dim_obj = {"key": q.get("dimension", ""), "name": q.get("dimension", ""), "name_en": q.get("dimension_en", q.get("dimension", "")), "weight": 20}
            score, _ = ai.score_answer(dim_obj, user_answer, lang=lang)
            correct = score >= 12
            correct_answer = q.get("reference", "（参考答案见解析）")
        else:
            correct = (user_answer == correct_answer)

        log = session.get("quiz_answers", [])
        log.append({"question_id": qid, "correct": correct})
        session["quiz_answers"] = log

        if not correct:
            username = session.get("username") or "anonymous"
            wrong = _get_wrong()
            wrong_entry = {
                "id": qid,
                "question": q.get("question", q.get("text", "")),
                "options": q.get("options", []),
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "dimension": q.get("dimension", "\u2014"),
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "mastered": False,
            }
            if q.get("question_en"):
                wrong_entry["question_en"] = q["question_en"]
            if q.get("options_en"):
                wrong_entry["options_en"] = q["options_en"]
            if q.get("dimension_en"):
                wrong_entry["dimension_en"] = q["dimension_en"]
            wrong.setdefault(username, []).append(wrong_entry)
            _save_wrong(wrong)

        result = {
            "success": True,
            "correct": correct,
            "correct_answer": correct_answer,
        }
        if q.get("analysis"):
            result["analysis"] = q["analysis"]
        if q.get("analysis_en"):
            result["analysis_en"] = q["analysis_en"]
        if q.get("reference"):
            result["reference"] = q["reference"]
        return jsonify(result)

    @app.route("/api/report_now", methods=["POST"])
    def report_now():
        log = session.get("quiz_answers", [])
        total = len(log)
        correct = sum(1 for x in log if x.get("correct"))
        score = round(correct / total * 100) if total else 0

        username = session.get("username") or "anonymous"
        mode = session.get("quiz_mode", "objective")
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
        question_en = ai.generate_question(d["key"], lang="en")
        return jsonify({
            "success": True,
            "round": 1,
            "dimension": d["name"],
            "dimension_en": d.get("name_en", d["name"]),
            "question": question,
            "question_en": question_en,
        })

    @app.route("/api/dialog/reply", methods=["POST"])
    def dialog_reply():
        data = request.get_json() or {}
        user_answer = (data.get("answer") or "").strip()
        lang = data.get("lang", "zh")

        if not user_answer:
            return jsonify({"success": False, "message": "回答不能为空"})

        index = session.get("dialog_index", 0)
        records = session.get("dialog_records", [])

        d = ai.get_dimension(index)
        if not d:
            return jsonify({"success": False, "message": "会话异常"})

        score, _ = ai.score_answer(d, user_answer, lang=lang)

        records.append({
            "dimension": d["name"],
            "dimension_en": d.get("name_en", d["name"]),
            "dimension_key": d["key"],
            "answer": user_answer,
            "score": score,
            "weight": d["weight"],
        })
        session["dialog_records"] = records
        session["dialog_index"] = index + 1

        if score < d["weight"] * 0.6:
            username = session.get("username") or "anonymous"
            wrong = _get_wrong()
            wrong_entry_2 = {
                "id": f"dialog_{index}_{d['key']}",
                "question": ai.generate_question(d["key"]),
                "options": [],
                "user_answer": user_answer,
                "correct_answer": "（对话题，参考AI点评）",
                "dimension": d["name"],
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "mastered": False,
            }
            if d.get("name_en"):
                wrong_entry_2["dimension_en"] = d["name_en"]
            question_en_text = ai.generate_question(d["key"], lang="en")
            if question_en_text:
                wrong_entry_2["question_en"] = question_en_text
            wrong.setdefault(username, []).append(wrong_entry_2)
            _save_wrong(wrong)

        reply = ai.generate_reply(d["key"], user_answer, lang=lang)

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
        next_question = ai.generate_question(nd["key"], lang=lang)
        next_question_en = ai.generate_question(nd["key"], lang="en")
        if lang == "en":
            full_reply = reply + "\n\n[Next Round · " + nd.get("name_en", nd["name"]) + "]\n" + next_question
        else:
            full_reply = reply + "\n\n【下一轮 · " + nd["name"] + "】\n" + next_question

        return jsonify({
            "success": True,
            "round": next_index,
            "dimension": nd["name"],
            "dimension_en": nd.get("name_en", nd["name"]),
            "reply": full_reply,
            "next_question": next_question,
            "next_question_en": next_question_en,
            "finished": False,
        })

    @app.route("/api/dialog/end", methods=["POST"])
    def dialog_end():
        data = request.get_json() or {}
        lang = data.get("lang", "zh")
        records = session.get("dialog_records", [])
        report = ai.generate_report(records, lang=lang)

        username = session.get("username") or "anonymous"
        total_score = report.get("total_score", 0)
        max_score = report.get("max_score", 1) or 1
        score = round(total_score / max_score * 100)
        _bump_stats(username, "dialog", score)

        return jsonify({
            "success": True,
            "comment": report["comment"],
            "highlights": report["highlights"],
            "suggestions": report["suggestions"],
            "scores": report["scores"],
            "total_score": report["total_score"],
            "max_score": report["max_score"],
        })

    # ================================================================
# 实操式练习接口
# ================================================================

PRACTICE_FILE = os.path.join(os.path.dirname(__file__), "practice_records.json")


def _get_practice_records():
    return load_json(PRACTICE_FILE, {})


def _save_practice_records(data):
    save_json(PRACTICE_FILE, data)


def register_practice_routes(app):

    @app.route("/api/practice/start", methods=["POST"])
    def practice_start():
        # 清空会话
        session["practice_step"] = 0
        session["practice_records"] = []

        task = ai.generate_practice_task()
        session["practice_task"] = task

        return jsonify({
            "success": True,
            "task_title": task["task_title"],
            "task_title_en": task.get("task_title_en", task["task_title"]),
            "task_desc": task["task_desc"],
            "task_desc_en": task.get("task_desc_en", task["task_desc"]),
        })

    @app.route("/api/practice/step", methods=["POST"])
    def practice_step():
        data = request.get_json() or {}
        index = int(data.get("step", 0))
        fetch_only = data.get("fetch_only", False)
        user_answer = (data.get("answer") or "").strip()
        lang = data.get("lang", "zh")

        step = ai.get_practice_step(index)
        if not step:
            return jsonify({"success": False, "message": "步骤不存在"})

        if fetch_only:
            return jsonify({
                "success": True,
                "step": index,
                "dimension": step["dimension"],
                "dimension_en": step.get("dimension_en", step["dimension"]),
                "question": step["question"],
                "question_en": step.get("question_en", step["question"]),
            })

        if not user_answer:
            return jsonify({"success": False, "message": "回答不能为空"})

        score, _ = ai.score_practice_step(step, user_answer, lang=lang)

        records = session.get("practice_records", [])
        records.append({
            "dimension": step["dimension"],
            "dimension_en": step.get("dimension_en", step["dimension"]),
            "dimension_key": step["dimension_key"],
            "answer": user_answer,
            "score": score,
            "weight": step["weight"],
        })
        session["practice_records"] = records
        session["practice_step"] = index + 1

        if score < step["weight"] * 0.6:
            username = session.get("username") or "anonymous"
            wrong = _get_wrong()
            wrong_entry_3 = {
                "id": f"practice_{index}_{step['dimension_key']}",
                "question": step["question"],
                "options": [],
                "user_answer": user_answer,
                "correct_answer": "（实操题，参考AI反馈）",
                "dimension": step["dimension"],
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "mastered": False,
            }
            if step.get("dimension_en"):
                wrong_entry_3["dimension_en"] = step["dimension_en"]
            if step.get("question_en"):
                wrong_entry_3["question_en"] = step["question_en"]
            wrong.setdefault(username, []).append(wrong_entry_3)
            _save_wrong(wrong)

        feedback = ai.generate_practice_feedback(step, user_answer, lang=lang)

        finished = (index + 1 >= len(ai.PRACTICE_STEPS))

        if finished:
            username = session.get("username") or "anonymous"
            all_records = _get_practice_records()
            all_records.setdefault(username, []).append({
                "task": session.get("practice_task", {}),
                "records": records,
            })
            _save_practice_records(all_records)

        return jsonify({
            "success": True,
            "step": index + 1,
            "finished": finished,
            "feedback": feedback,
            "dimension": step["dimension"],
            "dimension_en": step.get("dimension_en", step["dimension"]),
            "question": step["question"],
            "question_en": step.get("question_en", step["question"]),
        })

    @app.route("/api/practice/end", methods=["POST"])
    def practice_end():
        data = request.get_json() or {}
        lang = data.get("lang", "zh")
        records = session.get("practice_records", [])
        report = ai.generate_practice_report(records, lang=lang)

        username = session.get("username") or "anonymous"
        total_score = report.get("total_score", 0)
        max_score = report.get("max_score", 1) or 1
        score = round(total_score / max_score * 100)
        _bump_stats(username, "practice", score)

        return jsonify({
            "success": True,
            "comment": report["comment"],
            "highlights": report["highlights"],
            "suggestions": report["suggestions"],
            "scores": report["scores"],
            "total_score": report["total_score"],
            "max_score": report["max_score"],
        })