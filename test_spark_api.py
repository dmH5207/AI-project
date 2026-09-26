"""测试星火 Spark API 是否成功接入"""
import spark_api

print("=" * 50)
print("星火 Spark API 连通性测试")
print("=" * 50)

# 1. 检查配置
print(f"\n[1] API 模式: {spark_api.SPARK_API_MODE}")
print(f"    API Key:  {spark_api.SPARK_API_KEY[:8]}...（已隐藏后半段）")
print(f"    Base URL: {spark_api.SPARK_BASE_URL}")
print(f"    Model:    {spark_api.SPARK_MODEL}")

configured = spark_api.is_configured()
print(f"\n[2] is_configured() → {configured}")
if not configured:
    print("    ❌ 凭证未配置，请检查环境变量或 spark_api.py 中的默认值")
    exit(1)
else:
    print("    ✅ 凭证已配置")

# 2. 发送测试请求
print("\n[3] 发送测试请求...")
result = spark_api.chat(
    messages=[{"role": "user", "content": "你好，请用一句话回复我。"}],
    temperature=0.5,
    max_tokens=64,
    timeout=15,
)

if result:
    print(f"    ✅ API 调用成功！")
    print(f"    模型回复: {result}")
else:
    print(f"    ❌ API 调用失败，返回了 None")
    print(f"    可能原因：")
    print(f"    - API Key 无效或已过期")
    print(f"    - Base URL 不正确")
    print(f"    - 网络无法访问星火服务器")
    print(f"    - 模型名称 {spark_api.SPARK_MODEL} 不存在")

print("\n" + "=" * 50)