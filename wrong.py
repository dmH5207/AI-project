"""
错题中心：列表、统计报告、移除、举一反三
"""
import json
import os
from flask import request, jsonify, session
from datetime import datetime
import ai

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

def _ai_analyze(question, user_answer, correct_answer, options, dimension, lang="zh"):
    if lang == "en":
        opts_text = "\n".join(options) if options else "N/A"
        prompt = (
            f"Question: {question}\n"
            f"Options:\n{opts_text}\n"
            f"Student answer: {user_answer}\n"
            f"Correct answer: {correct_answer}\n"
            f"Dimension: {dimension}\n\n"
            f"Analyze why the student chose the wrong answer. Explain the correct answer and the key concept.\n"
            f"Be specific and educational. Reply in English."
        )
        sys_msg = "You are an AI literacy assessment teacher. Analyze wrong answers clearly and helpfully. Reply in English."
    else:
        opts_text = "\n".join(options) if options else "无"
        prompt = (
            f"题目：{question}\n"
            f"选项：\n{opts_text}\n"
            f"学生答案：{user_answer}\n"
            f"正确答案：{correct_answer}\n"
            f"维度：{dimension}\n\n"
            f"请分析学生为什么选错了，解释正确答案的原理和关键知识点。\n"
            f"要求具体、有教育意义，用中文回复。"
        )
        sys_msg = "你是AI素养评估老师，分析错题要具体、有建设性，用中文回复。"

    result = ai._call_spark(sys_msg, prompt, max_tokens=384, temperature=0.3)
    if result:
        if lang == "en":
            header = f"[Question] {question}\n\n[Your Answer] {user_answer}\n[Correct Answer] {correct_answer}\n\n[Analysis]\n"
        else:
            header = f"【题目】{question}\n\n【你的答案】{user_answer}\n【正确答案】{correct_answer}\n\n【解析】\n"
        return header + result

    if lang == "en":
        return (
            f"[Question] {question}\n\n"
            f"[Your Answer] {user_answer}\n"
            f"[Correct Answer] {correct_answer}\n\n"
            f"[Analysis] You chose {user_answer}, but the correct answer is {correct_answer}. "
            f"This suggests your understanding of {dimension} needs deepening. "
            f"Review the core concepts and try the variant practice below."
        )
    return (
        f"【题目】{question}\n\n"
        f"【你的答案】{user_answer}\n"
        f"【正确答案】{correct_answer}\n\n"
        f"【解析】你选择了 {user_answer}，但正确答案是 {correct_answer}。"
        f"这说明对{dimension}相关知识点的理解还不够深入。"
        f"建议回顾该知识点的核心概念，注意区分易混淆的选项，"
        f"并通过变式训练加深理解。"
    )


def _ai_variants(question, user_answer, correct_answer, options, dimension, lang="zh"):
    if lang == "en":
        opts_text = "\n".join(options) if options else "N/A"
        prompt = (
            f"Original question: {question}\n"
            f"Options:\n{opts_text}\n"
            f"Correct answer: {correct_answer}\n"
            f"Dimension: {dimension}\n\n"
            f"Generate a variant question on the same topic but from a different angle.\n"
            f"Strictly reply in JSON format:\n"
            f'{{"question": "...", "options": ["A. ...", "B. ...", "C. ...", "D. ..."], "answer": "X", "hint": "..."}}\n'
            f"The hint should explain the reasoning. Reply in English."
        )
        sys_msg = "You are an AI literacy assessment teacher. Generate variant questions for practice. Reply only in JSON, in English."
    else:
        opts_text = "\n".join(options) if options else "无"
        prompt = (
            f"原题：{question}\n"
            f"选项：\n{opts_text}\n"
            f"正确答案：{correct_answer}\n"
            f"维度：{dimension}\n\n"
            f"请生成一道同知识点但不同角度的变式题，帮助学生举一反三。\n"
            f"严格按 JSON 格式回复：\n"
            f'{{"question": "...", "options": ["A. ...", "B. ...", "C. ...", "D. ..."], "answer": "X", "hint": "..."}}\n'
            f"hint 为解题思路。用中文回复。"
        )
        sys_msg = "你是AI素养评估老师，生成变式题帮助学生举一反三。只回复JSON。"

    result = ai._call_spark(sys_msg, prompt, max_tokens=384, temperature=0.4)
    if result:
        try:
            clean = result.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[-1].rsplit("```", 1)[0]
            clean = clean.strip()
            if clean.startswith("json"):
                clean = clean[4:].strip()
            data = json.loads(clean)
            if data.get("question") and data.get("options") and data.get("answer"):
                return data
        except (json.JSONDecodeError, KeyError):
            pass

    if lang == "en":
        return {
            "question": f"[Variant] About {dimension}, which statement is correct?",
            "options": [
                f"A. The core concept of {dimension} requires understanding in context",
                f"B. {dimension} only requires memorization, not understanding",
                f"C. {dimension} is completely unrelated to other fields",
                f"D. {dimension} has only one fixed application method"
            ],
            "answer": "A",
            "hint": "The same concept may appear differently in different contexts. Understand the essence rather than memorize. Exclude absolute statements (like 'only', 'completely', 'one fixed')."
        }
    return {
        "question": f"【变式训练】关于{dimension}，以下哪个说法是正确的？",
        "options": [
            f"A. {dimension}的核心概念需要结合具体场景理解",
            f"B. {dimension}只需要记忆，不需要理解",
            f"C. {dimension}与其他领域完全无关",
            f"D. {dimension}只有一种固定的应用方式"
        ],
        "answer": "A",
        "hint": "变式训练的核心思路：同一知识点在不同场景下的表现可能不同，需要理解本质而非死记硬背。排除绝对化表述（如「只需要」、「完全无关」、「只有一种」），选择强调理解和场景的选项。"
    }


def register_wrong_routes(app):

    @app.route("/api/wrong/list")
    def wrong_list():
        items = _read_wrong()
        items.sort(key=lambda x: x.get("num", x.get("id", 0)))
        result = []
        for i, it in enumerate(items):
            copy = dict(it)
            copy.setdefault("num", i + 1)
            result.append(copy)
        return jsonify({"success": True, "wrong_answers": result})

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

    @app.route("/api/wrong/remove/<path:qid>", methods=["POST"])
    def wrong_remove(qid):
        data = _read_wrong_dict()
        if isinstance(data, dict) and "wrong_answers" not in data:
            for username in data:
                if isinstance(data[username], list):
                    data[username] = [it for it in data[username]
                                       if it.get("id") != qid and it.get("question_id") != qid]
            _save_wrong_dict(data)
        else:
            items = _read_wrong()
            items = [it for it in items if it.get("id") != qid and it.get("question_id") != qid]
            _write_wrong(items)
        return jsonify({"success": True})

    @app.route("/api/wrong/master/<path:qid>", methods=["POST"])
    def wrong_master(qid):
        body = request.get_json(silent=True) or {}
        flag = body.get("mastered", True)
        data = _read_wrong_dict()
        if isinstance(data, dict) and "wrong_answers" not in data:
            for username in data:
                if not isinstance(data[username], list):
                    continue
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

    @app.route("/api/wrong/analyze/<path:qid>", methods=["POST"])
    def wrong_analyze(qid):
        data = request.get_json(silent=True) or {}
        lang = data.get("lang", "zh")

        items = _read_wrong()
        item = _find_item(items, qid)
        if not item:
            msg = "Wrong answer not found" if lang == "en" else "错题不存在"
            return jsonify({"success": False, "message": msg})

        question = item.get("question", item.get("text", ""))
        user_answer = item.get("user_answer", item.get("wrong_answer", ""))
        correct_answer = item.get("correct_answer", item.get("answer", ""))
        options = item.get("options", [])
        dimension = item.get("dimension", "")

        analysis = _ai_analyze(question, user_answer, correct_answer, options, dimension, lang)
        practice = _ai_variants(question, user_answer, correct_answer, options, dimension, lang)

        return jsonify({
            "success": True,
            "analysis": analysis,
            "practice": practice
        })