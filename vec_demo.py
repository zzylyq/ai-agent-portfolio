import os
import requests

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

texts = [
    "住宿费标准",
    "住店能报多少钱",
    "今天天气怎么样",
]
vecs = embed(texts)
print("向量维度：", len(vecs[0]))

print("\n住宿费标准  vs 住店能报多少钱 ：", round(cosine(vecs[0], vecs[1]), 4))
print("住宿费标准  vs 今天天气怎么样 ：", round(cosine(vecs[0], vecs[2]), 4))
