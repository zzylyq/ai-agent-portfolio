import os, json, datetime, requests
from fastapi import FastAPI
from pydantic import BaseModel


from dotenv import load_dotenv      # ← 加
load_dotenv()                        # ← 加

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

def embed(texts):
    result = []
    for t in texts:
        r = requests.post(
            "https://open.bigmodel.cn/api/paas/v4/embeddings",
            headers={"Authorization": f"Bearer {os.getenv('ZHIPU_API_KEY')}"},
            json={"model": "embedding-3", "input": [t]},
            timeout=60,
        )
        j = r.json()
        if "data" not in j:
            print("接口报错：", j)
            print("出错的那块：", t[:60])
            raise SystemExit
        result.append(j["data"][0]["embedding"])
    return result


def cosine(a, b):
    dot = 0
    for x, y in zip(a, b):
        dot += x * y
    na = 0
    for x in a:
        na += x * x
    nb = 0
    for y in b:
        nb += y * y
    return dot / ((na ** 0.5) * (nb ** 0.5))


def retrieve(query, chunks, top_k=2):
    qv = embed([query])[0]
    scored = []
    for i in range(len(chunks)):
        s = cosine(qv, KB_VECS[i])
        scored.append((s, chunks[i]))
    scored.sort(reverse=True)
    return scored[:top_k]


# 启动时加载一次知识库
with open("kb_reimburse.md", "r", encoding="utf-8") as f:
    KB_CHUNKS = split_by_paragraph(f.read())
    KB_VECS = embed(KB_CHUNKS)                      # ← 新增
    print("知识库建库完成：", len(KB_VECS), "块")     # ← 新增


def search_kb(query):
    hits = retrieve(query, KB_CHUNKS, top_k=2)
    if not hits or hits[0][0] < 0.45:
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

# ===== 7. HTTP 接口 =====
def answer_question(question):
    msgs = [{"role": "user", "content": question}]

    r = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"},
        json={"model": "deepseek-chat", "messages": msgs, "tools": tools},
        timeout=60,
    )
    msg = r.json()["choices"][0]["message"]
    calls = msg.get("tool_calls") or []

    if not calls:
        return msg.get("content")

    msgs.append(msg)
    for c in calls:
        name = c["function"]["name"]
        args = json.loads(c["function"]["arguments"])
        result = run_tool(name, args)
        msgs.append({"role": "tool", "tool_call_id": c["id"], "content": result})

    r2 = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"},
        json={"model": "deepseek-chat", "messages": msgs},
        timeout=60,
    )
    return r2.json()["choices"][0]["message"]["content"]


app = FastAPI(title="星辰科技 AI 助手")

class AskRequest(BaseModel):
    question: str

@app.post("/chat")
def chat_api(req: AskRequest):
    answer = answer_question(req.question)
    return {"question": req.question, "answer": answer}

