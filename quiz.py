"""
答题：开始、提交、即时报告
（暂时占位，后续填逻辑）
"""
from flask import request, jsonify


def register_quiz_routes(app):

    @app.route("/api/start", methods=["POST"])
    def start():
        # TODO：初始化 session，返回第一题数据
        pass

    @app.route("/api/answer", methods=["POST"])
    def answer():
        data = request.get_json()
        question_id = data.get("question_id")
        user_answer = data.get("answer")

        # TODO：判分逻辑

        pass

    @app.route("/api/report_now")
    def report_now():
        # TODO：返回本次答题的即时报告
        pass