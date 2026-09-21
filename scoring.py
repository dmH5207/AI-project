"""
AI评分模块：负责调用大模型API，给开放式题目的回答打分。
"""

import requests
import json

API_URL = "换成你实际使用的大模型API地址"
API_KEY = "换成你的API密钥"


def score_open_ended(question_text, rubric, user_answer):
    prompt = f"""
    （在这里写你的评分指令模板）
    """

    # TODO：调用大模型API，解析返回结果

    return {"score": 0, "feedback": "还没有实现评分逻辑"}