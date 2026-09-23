"""
错题中心：列表、统计报告、移除
（暂时占位，后续填逻辑）
"""
from flask import request, jsonify


def register_wrong_routes(app):

    @app.route("/api/wrong/list")
    def wrong_list():
        # TODO：返回当前用户的错题列表
        pass

    @app.route("/api/wrong/report")
    def wrong_report():
        # TODO：返回历史汇总报告
        pass

    @app.route("/api/wrong/remove/<int:qid>", methods=["POST"])
    def wrong_remove(qid):
        # TODO：移除某条错题
        pass