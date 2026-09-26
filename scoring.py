"""
AI评分模块：负责调用大模型API，给开放式题目的回答打分。
"""

import os
import requests
import json

API_URL = os.environ.get("AI_API_URL", "")
API_KEY = os.environ.get("AI_API_KEY", "")


def score_open_ended(question_text, rubric, user_answer):
    prompt = f"""
    （在这里写你的评分指令模板）
    """

    # TODO：调用大模型API，解析返回结果

    return {"score": 0, "feedback": "还没有实现评分逻辑"}