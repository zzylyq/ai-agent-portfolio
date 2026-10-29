import requests
import os


path="kb_reimburse.md"
with open(path,"r",encoding="utf-8") as f:
    text=f.read()
print("总字数：",(len(text)))

def split_text(text, size=200, overlap=50):
    """
    将文本按指定大小和重叠大小进行分割
    """
    chunks=[]
    step = size - overlap                      # 每次前进多少
    for i in range(0, len(text), step):        # range 三参数：起点、终点、步长
        chunks.append(text[i:i+size])                         # 切片，注意终点可能越界也没事
    return chunks



def score(query, chunk):
    hit = 0
    for i in range(len(query) - 1):
        word = query[i:i+2]        # 取两个连续字
        if word in chunk:          # 这一组在片段里出现过
            hit += 1
    return hit

def retrieve(query, chunks, top_k=3):
    scored = []                        # ① 准备篮子
    for c in chunks:
        s = score(query, c)
        scored.append((s, c))          # ② 装成 (分数, 片段) 的元组

    scored.sort(reverse=True)          # ③ 按分数从高到低排
    return scored[:top_k]    

def split_by_paragraph(text):
    parts = text.split("\n\n")        # 按空行切
    result = []
    for p in parts:
        p = p.strip()                  # 去掉首尾空白
        if p:                          # 空块不要
            result.append(p)
    return result

def build_prompt(query, chunks):
    hits = retrieve(query, chunks, top_k=2)   # 取最相关的 2 块

    pieces = []                               # 把片段收集起来
    for s, c in hits:
        pieces.append(c)

    context = "\n\n".join(pieces)             # 用空行拼成一大段

    prompt = f"""请只根据下面的资料回答问题。如果资料里没有答案，就直接说"资料中没有提到"，不要自己编。

【资料】
{context}

【问题】
{query}"""
    return prompt

chunks = split_by_paragraph(text)
print("切了", len(chunks), "块")

for c in chunks:
    print("---", c[:30])
          # ④ 取前 top_k 个

result = retrieve("住宿费标准是多少", chunks)
for s, c in result:
    print("分数", s, "|", c[:40])


p = build_prompt("公司年假有几天", chunks)
print(p)





r = requests.post(
    "https://api.deepseek.com/chat/completions",
    headers={"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"},
    json={"model": "deepseek-chat", "messages": [{"role": "user", "content": p}]},
    timeout=60,
)
print("\n【模型回答】")
print(r.json()["choices"][0]["message"]["content"])
