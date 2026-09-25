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
# 答题接口
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

        score, _ = ai.score_answer(d, user_answer)

        records.append({
            "dimension": d["name"],
            "dimension_key": d["key"],
            "answer": user_answer,
            "score": score,
            "weight": d["weight"],
        })
        session["dialog_records"] = records
        session["dialog_index"] = index + 1

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
    # ================================================================
# 实操式练习（假 AI）
# ================================================================

PRACTICE_STEPS = [
    {
        "step": 1,
        "dimension_key": "basic",
        "dimension": "AI基础认知",
        "weight": 20,
        "question": "第 1 步：请先梳理这个任务的目标。用 3–5 句话说明：你打算解决什么问题、面向谁、希望达到什么效果。",
        "keywords": ["目标", "对象", "效果", "问题", "任务"],
    },
    {
        "step": 2,
        "dimension_key": "tools",
        "dimension": "AI工具使用",
        "weight": 20,
        "question": "第 2 步：针对这个任务，你打算用哪些 AI 工具？请列出 2–3 个，并说明它们各自能帮上什么忙。",
        "keywords": ["工具", "通义", "ChatGPT", "Copilot", "插件", "数据分析"],
    },
    {
        "step": 3,
        "dimension_key": "prompt",
        "dimension": "提示词工程",
        "weight": 20,
        "question": "第 3 步：请写出你会给 AI 的完整提示词，要求包含：角色、任务、输出格式。",
        "keywords": ["角色", "任务", "格式", "提示词", "步骤"],
    },
    {
        "step": 4,
        "dimension_key": "evaluate",
        "dimension": "AI结果评估与优化",
        "weight": 20,
        "question": "第 4 步：假设 AI 已经给了你一份初步结果。你会怎么核实它？请说出你的步骤，并指出可能出现的问题。",
        "keywords": ["核实", "验证", "来源", "幻觉", "偏见", "改进"],
    },
    {
        "step": 5,
        "dimension_key": "collab",
        "dimension": "人机协同解决问题",
        "weight": 20,
        "question": "第 5 步：写出你最终的成果（可以是简报、方案或一段说明）。同时说明：哪些是 AI 做的，哪些是你做的，为什么这样分工。",
        "keywords": ["分工", "我负责", "AI负责", "步骤", "协同", "总结"],
    },
]

PRACTICE_TASKS = [
    {
        "task_title": "帮班级做一份 AI 使用情况小调查",
        "task_desc": "你需要设计并完成一次关于班级 AI 使用情况的小调查，最后形成一份简短说明。",
    },
    {
        "task_title": "用 AI 辅助完成一次文献速览",
        "task_desc": "围绕一个你感兴趣的主题，借助 AI 快速浏览 2–3 篇资料，并整理成一段要点。",
    },
    {
        "task_title": "设计一份 AI 辅助的学习计划",
        "task_desc": "为一门你正在学的课，借助 AI 制定一份 2 周的学习计划，并说明执行方式。",
    },
]


def generate_practice_task():
    return random.choice(PRACTICE_TASKS)


def get_practice_step(index):
    if 0 <= index < len(PRACTICE_STEPS):
        return PRACTICE_STEPS[index]
    return None


def score_practice_step(step, user_answer):
    """按步骤 rubric 评分（0 ~ weight），复用 score_answer 的思路"""
    text = (user_answer or "").strip()
    weight = step["weight"]

    if not text:
        return 0, "没有作答。"

    score = 0.0
    reasons = []

    example_words = ["比如", "例如", "举个例子", "举例", "譬如"]
    if any(w in text for w in example_words):
        score += weight * 0.3
        reasons.append("有具体例子")

    reason_words = ["因为", "所以", "理由", "因此", "由于"]
    if any(w in text for w in reason_words):
        score += weight * 0.25
        reasons.append("有理由推导")

    hit = [k for k in step.get("keywords", []) if k in text]
    if hit:
        score += weight * 0.35
        reasons.append("涉及关键词：" + "、".join(hit[:3]))

    if len(text) >= 100:
        score += weight * 0.1
    elif len(text) < 25:
        score -= weight * 0.15

    score = max(0, min(weight, round(score)))

    if score >= weight * 0.8:
        comment = "这一步完成得很好，内容具体、有支撑。"
    elif score >= weight * 0.5:
        comment = "基本达到要求，可以再补充一些细节。"
    else:
        comment = "这一步还需要展开，建议补充具体做法或例子。"

    if reasons:
        comment += "（" + "、".join(reasons) + "）"

    return score, comment


def generate_practice_feedback(step, user_answer):
    score, comment = score_practice_step(step, user_answer)

    tips = [
        "如果换一个场景，你的做法会变吗？",
        "这一步里，你觉得最容易出问题的地方在哪？",
        "如果只能保留一句话，你会留下哪一句？",
        "有没有更好的方式来表达你的想法？""有没有更简单的方式达到同样的效果？",
    ]

    return (
        "【" + step["dimension"] + " · 反馈】\n"
        + comment + "\n\n"
        + "【想一想】\n" + random.choice(tips)
    )


def generate_practice_report(records):
    if not records:
        return {
            "comment": "本次练习没有记录。",
            "highlights": [],
            "suggestions": ["下次记得每步都写一点内容。"],
            "scores": [],
            "total_score": 0,
            "max_score": 100,
        }

    total_score = sum(r.get("score", 0) for r in records)
    max_score = sum(r.get("weight", 0) for r in records)
    ratio = total_score / max_score if max_score else 0

    if ratio >= 0.8:
        comment = "本次实操练习表现优秀。你在各步骤都能给出具体做法，有目标、有工具、有验证意识，整体完成度很高。"
    elif ratio >= 0.6:
        comment = "本次实操练习表现良好。多数步骤都能按要求完成，个别步骤可以再细化。"
    elif ratio >= 0.4:
        comment = "本次实操练习完成度一般。建议在每一步都补充具体操作细节，让方案更落地。"
    else:
        comment = "本次实操练习完成度偏低。建议先从明确任务目标开始，再逐步补齐工具、提示词和验证方法。"

    sorted_records = sorted(
        records,
        key=lambda r: r.get("score", 0) / (r.get("weight", 1) or 1),
        reverse=True,
    )

    highlights = []
    for r in sorted_records[:2]:
        highlights.append(
            "「" + r["dimension"] + "」表现较好，得分 "
            + str(r.get("score", 0)) + " / " + str(r.get("weight", 0))
        )
    highlights.append("完整走完了 5 步实操流程")

    suggestions = []
    for r in sorted_records[-2:]:
        suggestions.append(
            "「" + r["dimension"] + "」还可加强，建议补充具体操作细节"
        )
    suggestions.append("执行复杂任务时，先写目标，再配工具，最后想验证方法")

    scores = []
    for r in records:
        scores.append({
            "dimension": r["dimension"],
            "score": r.get("score", 0),
            "weight": r.get("weight", 0),
        })

    return {
        "comment": comment,
        "highlights": highlights,
        "suggestions": suggestions,
        "scores": scores,
        "total_score": total_score,
        "max_score": max_score,
    }