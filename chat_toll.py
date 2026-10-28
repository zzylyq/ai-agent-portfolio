import os, json, datetime, requests

# ===== 1. 工具的真实实现 =====
def get_time(city):
    return f"{city}现在是{datetime.datetime.now():%H:%M}"

def get_date(city):
    today = datetime.date.today()
    return f"今天是{today.year}年{today.month}月{today.day}日"

def get_weather(city):
    return f"{city}：晴，26℃"

# ===== 2. 工具清单（给模型看）=====
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "查某个城市现在几点",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "城市名"}},
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_date",
            "description": "查今天的日期。用户问今天几号时使用",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "城市名"}},
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
	        "description":"查询当地天气",
	        "parameters": {
		        "type":"object",
		        "properties":{"city":{"type":"string","descrition":"城市名"}},
	            "required":["city"]
    }
    }
    }
]

# ===== 3. 登记表 + 分发 =====
TOOL_MAP = {"get_time": get_time, "get_date": get_date, "get_weather": get_weather}

def run_tool(name, args):
    func = TOOL_MAP.get(name)
    if not func:
        return "没有这个工具"
    return func(**args)

# ===== 4. 流式打印（你的原函数，不动）=====
def stream_chat(messages):
    r = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"},
        json={"model": "deepseek-chat", "messages": messages, "stream": True},
        stream=True,
        timeout=60,
    )
    full = ""
    for line in r.iter_lines():
        if not line:
            continue
        text = line.decode("utf-8")
        if not text.startswith("data: "):
            continue
        payload = text[6:]
        if payload == "[DONE]":
            break
        data = json.loads(payload)
        piece = (data["choices"][0].get("delta") or {}).get("content")
        if piece:
            print(piece, end="", flush=True)
            full += piece
    print()
    messages.append({"role": "assistant", "content": full})

# ===== 5. 新增：先问要不要用工具 =====
def chat(messages):
    r = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"},
        json={"model": "deepseek-chat", "messages": messages, "tools": tools},
        timeout=60,
    )
    msg = r.json()["choices"][0]["message"]
    calls = msg.get("tool_calls") or []

    if not calls:
        print(msg.get("content"))
        messages.append(msg)
        return

    print("[要调工具]", [c["function"]["name"] for c in calls])
    messages.append(msg)
    for c in calls:
        name = c["function"]["name"]
        args = json.loads(c["function"]["arguments"])
        result = run_tool(name, args)
        print("[结果]", result)
        messages.append({"role": "tool", "tool_call_id": c["id"], "content": result})

    stream_chat(messages)

# ===== 6. 主循环 =====
messages = []
while True:
    q = input("\n你：")
    if q == "exit":
        break
    messages.append({"role": "user", "content": q})
    chat(messages)
