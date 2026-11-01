# rag_core.py
"""RAG 核心纯函数：不依赖网络、不依赖全局状态，可独立测试。"""


def split_by_paragraph(text):
    """把长文本按空行切成段落列表，过滤空块。"""
    parts = text.split("\n\n")
    result = []
    for p in parts:
        p = p.strip()
        if p:
            result.append(p)
    return result


def score(query, chunk):
    """字面打分：把 query 切成相邻两字，统计在 chunk 中出现的个数（关键词检索用）。"""
    hit = 0
    for i in range(len(query) - 1):
        word = query[i:i + 2]
        if word in chunk:
            hit += 1
    return hit


def cosine(a, b):
    """余弦相似度：只看方向，不看长度。范围 -1 ~ 1。

    零向量没有方向，直接返回 0，避免除零崩溃。
    """
    dot = 0
    for x, y in zip(a, b):
        dot += x * y
    na = 0
    for x in a:
        na += x * x
    nb = 0
    for y in b:
        nb += y * y

    if na == 0 or nb == 0:
        return 0.0

    return dot / ((na ** 0.5) * (nb ** 0.5))


def rank_by_vectors(qv, chunks, vecs, top_k=2):
    """给每块算与 qv 的余弦相似度，按分数从高到低返回前 top_k 个。

    返回 [(分数, 片段), ...]
    """
    scored = []
    for i in range(len(chunks)):
        s = cosine(qv, vecs[i])
        scored.append((s, chunks[i]))
    scored.sort(reverse=True)
    return scored[:top_k]
