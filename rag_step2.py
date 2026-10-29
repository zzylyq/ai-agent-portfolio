import os
import requests

# ===== 1. 读取文档 =====
path = "kb_reimburse.md"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
print("总字数：", len(text))

# ===== 2. 按段落切片 =====
def split_by_paragraph(text):
    parts = text.split("\n\n")
    result = []
    for p in parts:
        p = p.strip()
        if p:
            result.append(p)
    return result

# ===== 3. 给一块打分 =====
def score(query, chunk):
    hit = 0
    for i in range(len(query) - 1):
        word = query[i:i+2]
        if word in chunk:
            hit += 1
    return hit

# ===== 4. 检索 top_k =====
def retrieve(query, chunks, top_k=2):
    scored = []
    for c in chunks:
        scored.append((score(query, c), c))
    scored.sort(reverse=True)
    return scored[:top_k]

# ===== 5. 拼提示词 =====
def build_prompt(query, chunks):
    hits = retrieve(query, chunks, top_k=2)
    pieces = []
    for s, c in hits:
        pieces.append(c)
    context = "\n\n".join(pieces)
    prompt = f"""请只根据下面的资料回答问题。如果资料里没有答案，就直接说"资料中没有提到"，不要自己编。

【资料】
{context}

【问题】
{query}"""
    return prompt

# ===== 6. 问模型 =====
def ask(prompt):
    r = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"},
        json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]},
        timeout=60,
    )
    return r.json()["choices"][0]["message"]["content"]

# ===== 7. 主循环 =====
chunks = split_by_paragraph(text)
print("切了", len(chunks), "块")

while True:
    q = input("\n问：")
    if q == "exit":
        break
    p = build_prompt(q, chunks)
    print("答：", ask(p))
