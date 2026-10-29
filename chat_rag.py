import os, json, datetime, requests

# ===== 1. 普通工具 =====
def get_time(city):
    return f"{city}现在是{datetime.datetime.now():%H:%M}"

def get_date(city):
    today = datetime.date.today()
    return f"今天是{today.year}年{today.month}月{today.day}日"

def get_weather(city):
    return f"{city}：晴，26℃"

# ===== 2. 知识库工具的内部零件 =====
def split_by_paragraph(text):
    parts = text.split("\n\n")
    result = []
    for p in parts:
        p = p.strip()
        if p:
            result.append(p)
    return result

def score(query, chunk):
    hit = 0
    for i in range(len(query) - 1):
        word = query[i:i+2]
        if word in chunk:
            hit += 1
    return hit

def retrieve(query, chunks, top_k=2):
    scored = []
    for c in chunks:
        scored.append((score(query, c), c))
    scored.sort(reverse=True)
    return scored[:top_k]

# 启动时加载一次知识库
with open("kb_reimburse.md", "r", encoding="utf-8") as f:
    KB_CHUNKS = split_by_paragraph(f.read())

def search_kb(query):
    hits = retrieve(query, KB_CHUNKS, top_k=2)
    if not hits or hits[0][0] == 0:
        return "知识库里没有找到相关内容"
    parts = []
    for s, c in hits:
        parts.append(c)
    return "\n\n".join(parts)

# ===== 3. 工具清单 =====
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
            "description": "查今天的日期。用户问今天几号、今天星期几时使用",
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
            "description": "查某个城市今天的天气",
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
            "name": "search_kb",
            "description": "检索流程等规定。用户询问公司制度、报销、出差相关问题时必须使用",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "检索关键词，例如：住宿标准"}},
                "required": ["query"]
            }
        }
    }
]

TOOL_MAP = {
    "get_time": get_time,
    "get_date": get_date,
    "get_weather": get_weather,
    "search_kb": search_kb,
}

def run_tool(name, args):
    func = TOOL_MAP.get(name)
    if not func:
        return "没有这个工具"
    return func(**args)

# ===== 4. 流式打印 =====
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

# ===== 5. 调度：先用工具，再说话 =====
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
        print("[结果]", result[:80], "..." if len(result) > 80 else "")
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
