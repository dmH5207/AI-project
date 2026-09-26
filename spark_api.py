"""
讯飞星火 Spark API 封装
支持两种调用方式：
  1. HTTP（OpenAI 兼容接口）— 推荐用于星辰 MaaS 平台的 Spark-X2.5
  2. WebSocket — 用于标准星火模型（Lite / v3.5 / v4.0 等）
"""
import os
import json
import hashlib
import hmac
import base64
import requests
from datetime import datetime, timezone
from urllib.parse import urlencode, urlparse


# ================================================================
# 配置项（优先读环境变量，否则用这里的默认值）
# ================================================================

# 方式一：星辰 MaaS 平台（OpenAI 兼容 HTTP 接口，推荐用于 Spark-X2.5）
SPARK_API_KEY  = os.environ.get("SPARK_API_KEY", "ak-32157f45086dbc550b2f5df3c448e254")
SPARK_BASE_URL = os.environ.get("SPARK_BASE_URL", "https://maas-api.cn-huabei-1.xf-yun.com/v2")
SPARK_MODEL    = os.environ.get("SPARK_MODEL", "spark-x2.5-1.7b")

# 方式二：标准星火 WebSocket 接口（用于 Spark-Lite / v3.5 / v4.0 等）
# 需要在星火开放平台控制台获取 APP_ID / API_KEY / API_SECRET
SPARK_APP_ID     = os.environ.get("SPARK_APP_ID", "")
SPARK_API_SECRET = os.environ.get("SPARK_API_SECRET", "")
SPARK_WS_URL     = os.environ.get("SPARK_WS_URL", "wss://spark-api.xf-yun.com/v4.0/chat")
SPARK_DOMAIN     = os.environ.get("SPARK_DOMAIN", "4.0Ultra")

# 默认调用方式："http" 或 "ws"
SPARK_API_MODE = os.environ.get("SPARK_API_MODE", "http")


def is_configured():
    """检查是否已配置 API 凭证"""
    if SPARK_API_MODE == "http":
        return bool(SPARK_API_KEY and SPARK_BASE_URL)
    return bool(SPARK_APP_ID and SPARK_API_KEY and SPARK_API_SECRET)


def chat(messages, temperature=0.5, max_tokens=1024, timeout=30):
    """
    调用星火大模型（统一入口）

    Args:
        messages: 消息列表，[{"role": "user", "content": "xxx"}]
        temperature: 温度 (0~1)
        max_tokens: 最大输出 token 数
        timeout: 超时秒数

    Returns:
        模型回复文本；失败返回 None
    """
    if SPARK_API_MODE == "http":
        return _chat_http(messages, temperature, max_tokens, timeout)
    return _chat_ws(messages, temperature, max_tokens, timeout)


# ================================================================
# HTTP 方式（OpenAI 兼容接口）
# ================================================================

def _chat_http(messages, temperature, max_tokens, timeout):
    try:
        url = f"{SPARK_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {SPARK_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": SPARK_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[Spark HTTP] 调用失败: {e}")
        return None


# ================================================================
# WebSocket 方式（标准星火接口）
# ================================================================

def _chat_ws(messages, temperature, max_tokens, timeout):
    try:
        import websocket
    except ImportError:
        print("[Spark WS] 请安装依赖: pip install websocket-client")
        return None

    try:
        # 星火 WS API 不支持 system 角色，将其合并到首条 user 消息
        ws_messages = []
        system_content = ""
        for m in messages:
            if m["role"] == "system":
                system_content = m["content"]
            else:
                ws_messages.append(m)
        if system_content and ws_messages and ws_messages[0]["role"] == "user":
            ws_messages[0]["content"] = system_content + "\n" + ws_messages[0]["content"]
        elif system_content:
            ws_messages.insert(0, {"role": "user", "content": system_content})

        auth_url = _create_auth_url(SPARK_API_KEY, SPARK_API_SECRET, SPARK_WS_URL)
        body = {
            "header": {"app_id": SPARK_APP_ID, "uid": "ai-project"},
            "parameter": {
                "chat": {
                    "domain": SPARK_DOMAIN,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
            },
            "payload": {"message": {"text": ws_messages}},
        }
        ws = websocket.create_connection(auth_url, timeout=timeout)
        ws.send(json.dumps(body))

        result = []
        while True:
            response = ws.recv()
            if not response:
                break
            data = json.loads(response)
            code = data.get("header", {}).get("code", -1)
            if code != 0:
                print(f"[Spark WS] 错误码: {code}")
                break
            for item in data.get("payload", {}).get("choices", {}).get("text", []):
                result.append(item.get("content", ""))
            if data.get("header", {}).get("status", 0) == 2:
                break

        ws.close()
        return "".join(result)
    except Exception as e:
        print(f"[Spark WS] 调用失败: {e}")
        return None


def _create_auth_url(api_key, api_secret, url):
    """生成 WebSocket 鉴权 URL（HMAC-SHA256 签名）"""
    parsed = urlparse(url)
    host = parsed.hostname
    path = parsed.path
    now = datetime.now(timezone.utc)
    date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")

    signature_origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
    signature = base64.b64encode(
        hmac.new(
            api_secret.encode(), signature_origin.encode(), hashlib.sha256
        ).digest()
    ).decode()

    authorization = base64.b64encode(
        (
            f'api_key="{api_key}", algorithm="hmac-sha256", '
            f'headers="host date request-line", signature="{signature}"'
        ).encode()
    ).decode()

    params = {"authorization": authorization, "date": date, "host": host}
    return f"{url}?{urlencode(params)}"