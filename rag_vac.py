import os
import requests

# ===== 1. 读取与切片 =====
with open("kb_reimburse.md", "r", encoding="utf-8") as f:
    text = f.read()

def split_by_paragraph(text):
    parts = text.split("\n\n")
    result = []
    for p in parts:
        p = p.strip()
        if p:
            result.append(p)
    return result

chunks = split_by_paragraph(text)

# ===== 2. 向量化 =====
def embed(texts):
    r = requests.post(
        "https://open.bigmodel.cn/api/paas/v4/embeddings",
        headers={"Authorization": f"Bearer {os.getenv('ZHIPU_API_KEY')}"},
        json={"model": "embedding-3", "input": texts},
        timeout=60,
    )
    data = r.json()["data"]
    return [d["embedding"] for d in data]

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

# ===== 3. 建库：一次算完所有块（只做一次）=====
CHUNK_VECS = embed(chunks)
print("建库完成：", len(CHUNK_VECS), "块，每块", len(CHUNK_VECS[0]), "维")

# ===== 4. 检索 =====
def retrieve(query, top_k=2):
    qv = embed([query])[0]          # 把问题也变成向量
    scored = []
    for i in range(len(chunks)):
        s = cosine(qv, CHUNK_VECS[i])   # 算夹角
        scored.append((s, chunks[i]))
    scored.sort(reverse=True)
    return scored[:top_k]

# ===== 5. 拼提示词 =====
def build_prompt(query):
    hits = retrieve(query, top_k=2)
    parts = []
    for s, c in hits:
        parts.append(c)
    context = "\n\n".join(parts)
    return f"""请只根据下面的资料回答问题。如果资料里没有答案，就直接说"资料中没有提到"，不要自己编。

【资料】
{context}

【问题】
{query}"""

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
while True:
    q = input("\n问：")
    if q == "exit":
        break
    print("答：", ask(build_prompt(q)))
