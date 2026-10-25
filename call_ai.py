import os
import requests

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    print("错误：没读到密钥，请先在同一窗口执行 $env:DEEPSEEK_API_KEY='sk-xxx'")
    exit()

url = "https://api.deepseek.com/chat/completions"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
payload = {
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "用一句话鼓励一个刚转行学AI的人"}],
    "stream": False
}

try:
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    print(r.json()["choices"][0]["message"]["content"])
except requests.Timeout:
    print("请求超时，检查网络后重试")
except Exception as e:
    print(f"出错了：{e}")
