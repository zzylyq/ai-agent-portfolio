# Day3 最小版：完整五步 —— 模型写单子 → 你执行 → 结果回传 → 模型说人话
# 用法：$env:DEEPSEEK_API_KEY="sk-xxx"  然后 python fc_min.py

import os
import json
import datetime
import requests

# ① 你的真函数（模型碰不到它）
def get_time(city):
    return f"{city}现在是{datetime.datetime.now():%H:%M}"

def get_date(city):
    today = datetime.date.today()
    return f"今天是{today.year}年{today.month}月{today.day}日"

# 告诉模型：我有这个工具
tools = [
    {
    "type": "function",
    "function": {
        "name": "get_time",
        "description": "查某个城市现在几点",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "get_date",
        "description": "查今天的日期。用户问今天几号、今天星期几时使用",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"]
        }
    }
}


]

messages = [{"role": "user", "content": "今天几号"}]

# ===== ①② 第一轮：模型写单子 =====
r = requests.post("https://api.deepseek.com/chat/completions",
    headers={"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"},
    json={"model": "deepseek-chat", "messages": messages, "tools": tools},
    timeout=60)

msg = r.json()["choices"][0]["message"]
print("模型说的话：", msg.get("content"))
print("模型要调的：", msg.get("tool_calls"))

# ===== ③ 从单子里取出：调什么函数、什么参数 =====
tool_call = msg["tool_calls"][0]
func_name = tool_call["function"]["name"]
args = json.loads(tool_call["function"]["arguments"])   # 字符串 → 字典

# ===== ④ 你的代码真的执行它 =====
# 原来是：result = get_time(**args)
if func_name == "get_time":
    result = get_time(**args)
else:
    result = get_date(**args)

print("\n执行结果：", result)

# ===== ⑤ 把结果端回给模型，让它说人话 =====
messages.append(msg)                                    # 单子必须带上
messages.append({
    "role": "tool",
    "tool_call_id": tool_call["id"],                    # 与单子上的 id 配对
    "content": result,
})

r2 = requests.post("https://api.deepseek.com/chat/completions",
    headers={"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"},
    json={"model": "deepseek-chat", "messages": messages},
    timeout=60)

print("\n最终回答：", r2.json()["choices"][0]["message"]["content"])
