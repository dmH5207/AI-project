"""
后端主程序（Python / Flask）
负责：接收前端发来的请求 -> 处理逻辑（判分、调用AI等）-> 把结果返回给前端
"""

from flask import Flask, render_template, session, request, jsonify

app = Flask(__name__)
app.secret_key = "换成任意一串随机字符串"

# TODO 1：在这里加载题库数据


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/quiz")
def quiz():
    return render_template("quiz.html")


@app.route("/report")
def report():
    return render_template("report.html")


@app.route("/api/start", methods=["POST"])
def start():
    # TODO：初始化session，返回第一题数据
    pass


@app.route("/api/answer", methods=["POST"])
def answer():
    data = request.get_json()
    question_id = data.get("question_id")
    user_answer = data.get("answer")

    # TODO：判分逻辑

    pass


@app.route("/api/report_data")
def report_data():
    # TODO：返回汇总得分
    pass


if __name__ == "__main__":
    app.run(debug=True)