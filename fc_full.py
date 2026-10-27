# 作用：Function Calling 完整版 —— 两个工具 + 工具分发 + 防御式处理
# 用法：$env:DEEPSEEK_API_KEY="sk-xxx"  然后 python fc_full.py
# 完成：2026-10-27（Day3）
# 踩过的坑：arguments 是字符串要 loads；模型可能不调工具（要判空）

import os
import sys
import json
import datetime
import requests

API_URL = "https://api.deepseek.com/chat/completions"


# ===== ① 你的真函数（模型碰不到它们，执行权在你手里）=====
def get_time(city="北京"):
    now = datetime.datetime.now()
    return f"{city} 现在是 {now:%H:%M:%S}"


def get_weather(city="北京"):
    fake = {"北京": ("晴", 18), "上海": ("多云", 22), "深圳": ("小雨", 26)}
    desc, temp = fake.get(city, ("未知", None))
    if temp is None:
        return f"没有 {city} 的天气数据"
    return f"{city} 今天{desc}，气温 {temp}℃"


# ===== ② 工具清单（用 JSON 描述给模型看）=====
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "查询城市当前时间。用户问几点、现在什么时间时使用。",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "城市名"}},
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询城市今天的天气和气温。用户问天气、下雨、穿什么时使用。",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "城市名"}},
                "required": ["city"],
            },
        },
    },
]


# ===== ③ 工具分发表：名字 → 真函数 =====
# 模型说调哪个，我们就按名字找到对应函数。
# 不写死 get_time，才能支持任意多个工具。
TOOL_MAP = {"get_time": get_time, "get_weather": get_weather}


# ===== ④ 封装一次调用 =====
def chat(messages, with_tools=True):
    """发一轮请求，返回模型的消息（可能含 tool_calls，也可能只有 content）"""
    payload = {"model": "deepseek-chat", "messages": messages}
    if with_tools:
        payload["tools"] = tools        # 第二轮不需要再传 tools

    r = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]


# ===== 主流程 =====
if not os.getenv("DEEPSEEK_API_KEY"):
    print("先设置密钥：$env:DEEPSEEK_API_KEY='sk-xxx'")
    sys.exit(1)

messages = [{"role": "user", "content": "北京今天天气怎么样？"}]

# --- 第一轮：模型决定要不要调工具 ---
msg = chat(messages)
print("=== 第一轮：模型返回 ===")
print(json.dumps(msg, ensure_ascii=False, indent=2))

# 防御：模型可能不调工具，直接用人话回答（这是常态，必须处理）
tool_calls = msg.get("tool_calls")
if not tool_calls:
    print("\n模型没调工具，直接回答：", msg.get("content"))
    sys.exit(0)

# --- 取出要调的函数和参数 ---
tool_call = tool_calls[0]
func_name = tool_call["function"]["name"]
args = json.loads(tool_call["function"]["arguments"])   # 字符串 → 字典

print("\n=== 模型决定调用 ===")
print("函数：", func_name)
print("参数：", args)

# --- 真的执行（工具分发）---
result = TOOL_MAP[func_name](**args)
print("执行结果：", result)

# --- 第二轮：把结果端回给模型 ---
messages.append(msg)                                  # 模型的点菜单必须带上
messages.append({
    "role": "tool",
    "tool_call_id": tool_call["id"],                  # 与上面的 id 配对
    "content": result,
})

final = chat(messages, with_tools=False)
print("\n=== 最终回答 ===")
print(final.get("content", ""))
