import os, json, datetime, requests

API_URL = "https://api.deepseek.com/chat/completions"

# ① 你的真函数（模型碰不到它）
def get_time(city="北京"):
    now = datetime.datetime.now()
    return f"{city} 现在是 {now:%H:%M:%S}"

# ② 工具清单：用 JSON 告诉模型"我有这个工具"
tools = [{
    "type": "function",
    "function": {
        "name": "get_time",
        "description": "查询城市当前时间。用户问几点、现在什么时间时使用。",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "城市名"}},
            "required": ["city"]
        }
    }
}]

# ③ 发给模型（带上 tools）
messages = [{"role": "user", "content": "现在几点了？"}]
r = requests.post(API_URL,
    headers={"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
             "Content-Type": "application/json"},
    json={"model": "deepseek-chat", "messages": messages, "tools": tools},
    timeout=60)
r.raise_for_status()

# ④ 关键！打印模型返回的完整内容
msg = r.json()["choices"][0]["message"]
print(json.dumps(msg, ensure_ascii=False, indent=2))

# ===== 第二部分：执行函数，把结果端回给模型 =====

# ⑤ 从 tool_calls 里取出"要调什么函数、参数是什么"
tool_call = msg["tool_calls"][0]
func_name = tool_call["function"]["name"]
args_text = tool_call["function"]["arguments"]     # ⚠️ 这是字符串！

# ⑥ 字符串 → 字典（这就是昨天练的 loads）
args = json.loads(args_text)
print("\n要调的函数：", func_name)
print("解析出的参数：", args)

# ⑦ 真的执行你的函数（**args 把字典展开成参数）
result = get_time(**args)
print("函数执行结果：", result)

# ⑧ 把结果发回给模型（第二轮）
messages.append(msg)          # 模型那张点菜单必须原样带回去
messages.append({
    "role": "tool",
    "tool_call_id": tool_call["id"],    # 必须和上面那个 id 对上
    "content": result,
})

r2 = requests.post(API_URL,
    headers={"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
             "Content-Type": "application/json"},
    json={"model": "deepseek-chat", "messages": messages},   # 这轮不用再传 tools
    timeout=60)
r2.raise_for_status()

final = r2.json()["choices"][0]["message"]
print("\n最终回答：", final["content"])
