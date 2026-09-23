"""
我的：用户信息、改密码、退出
（暂时占位，后续填逻辑）
"""
from flask import request, jsonify


def register_profile_routes(app):

    @app.route("/api/me/info")
    def me_info():
        # TODO：返回当前用户信息
        pass

    @app.route("/api/me/change_password", methods=["POST"])
    def me_change_password():
        # TODO：修改当前用户密码
        pass

    @app.route("/api/logout", methods=["POST"])
    def logout():
        # TODO：清 session
        pass