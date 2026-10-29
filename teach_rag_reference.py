"""Day5 参考实现（离线部分）· teach_rag_reference.py

⚠️ 规矩：**三个函数自己写完、check_rag.py 全过之后，再打开这个文件对照。**
现在就打开 = 今天白学，明天测评照样写不出。

它和 check_rag.py 校验通过的版本完全一致。
"""

import re
def chunk_text(text, size=400):
    sections = re.split(r"\n(?=## )", text.strip())
    chunks = []
    for sec in sections:
        sec = sec.strip()
        if not sec: continue
        if len(sec) <= size:
            chunks.append(sec)
        else:
            buf = ""
            for p in sec.split("\n\n"):
                if buf and len(buf) + len(p) > size:
                    chunks.append(buf.strip()); buf = ""
                buf += p + "\n\n"
            if buf.strip(): chunks.append(buf.strip())
    return chunks
def keywords(q, k=2):
    words = [w for w in re.split(r"[，。？！、\s]+", q) if len(w) >= 2]
    out = set()
    for w in words:
        out.add(w)
        for i in range(len(w) - k + 1): out.add(w[i:i+k])
    return out
def retrieve(question, chunks, top_k=2):
    kws = keywords(question); scored = []
    for i, c in enumerate(chunks):
        s = sum(len(w) * c.count(w) for w in kws if w in c)
        if s: scored.append((s, i, c))
    scored.sort(key=lambda x: -x[0])
    return scored[:top_k]
