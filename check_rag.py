"""Day5 验收器 · 客观检查 rag_core.py 的三个函数是否正确

用法（在 ai-journey 目录下）：
    python check_rag.py

它只检查离线部分（切片 + 检索），不花 API 钱。
不通过就改 rag_core.py，别改这个文件。
"""
import os
import sys

CORPUS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kb_reimburse.md")

PASS, FAIL = "✅ PASS", "❌ FAIL"
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{PASS if ok else FAIL}  {name}" + (f"\n        {detail}" if detail else ""))


def main():
    if not os.path.exists(CORPUS):
        print("找不到 kb_reimburse.md，请确认语料文件和本脚本在同一目录")
        return 1
    text = open(CORPUS, encoding="utf-8").read()

    try:
        import rag_core
    except Exception as e:
        print(f"{FAIL}  导入 rag_core.py 失败：{e}")
        print("        确认 rag_core.py 在同一目录，且没有语法错误")
        return 1

    for fn in ("chunk_text", "retrieve"):
        if not hasattr(rag_core, fn):
            print(f"{FAIL}  rag_core.py 里没有 {fn}() —— 函数名必须完全一致")
            return 1

    # ---------- 1. 切片 ----------
    chunks = rag_core.chunk_text(text)
    check("切片返回的是列表", isinstance(chunks, list), f"实际类型 {type(chunks).__name__}")
    if not isinstance(chunks, list) or not chunks:
        return 1

    check("切出 6~12 块（按小节切的合理区间）", 6 <= len(chunks) <= 12, f"实际 {len(chunks)} 块")
    check("块数不是 1（说明真的切了，没整篇返回）", len(chunks) > 1, f"实际 {len(chunks)} 块")

    heads = [c.strip().splitlines()[0][:20] for c in chunks if c.strip()]
    titled = sum(1 for h in heads if h.startswith("#"))
    check("每块以标题开头（没有从句子中间劈开）", titled == len(heads),
          f"{titled}/{len(heads)} 块以 # 开头；开头分别是：{heads[:3]}")
    print(f"        共 {len(chunks)} 块：")
    for i, c in enumerate(chunks):
        first = c.strip().splitlines()[0]
        print(f"          [{i}] {first}  ({len(c)} 字)")

    # ---------- 2. 检索 ----------
    def top1(q):
        r = rag_core.retrieve(q, chunks)
        return r[0] if r else None

    r = top1("杭州住宿上限是多少")
    ok = r is not None and "住宿" in r[2]
    check("问「杭州住宿上限是多少」→ Top-1 是住宿费标准那一块", ok,
          f"实际命中：{r[2].splitlines()[0] if r else '无'}")

    r2 = rag_core.retrieve("上海出差住宿能报多少", chunks)
    ok2 = bool(r2) and "住宿" in r2[0][2] and "600" in r2[0][2]
    check("问「上海出差住宿能报多少」→ Top-1 含 600 元", ok2,
          f"实际 Top-1：{r2[0][2].splitlines()[0] if r2 else '无'}")

    r3 = rag_core.retrieve("发票丢了怎么办", chunks)
    ok3 = bool(r3) and "发票" in r3[0][2]
    check("问「发票丢了怎么办」→ Top-1 命中常见问题块", ok3,
          f"实际 Top-1：{r3[0][2].splitlines()[0] if r3 else '无'}")

    r4 = rag_core.retrieve("住一晚最多能花多少钱", chunks)
    check("问「住一晚最多能花多少钱」→ 检索失败（0 命中）※这是要你看见的失败，不是 bug", not r4,
          f"实际命中 {len(r4)} 块 —— 若命中了，说明你的关键词规则太宽，反而掩盖了关键词检索的死穴")

    # ---------- 汇总 ----------
    total, ok_cnt = len(results), sum(results)
    print("\n" + "=" * 52)
    print(f"结果：{ok_cnt}/{total} 通过")
    if ok_cnt == total:
        print("✅ 离线管线合格。接下来：build_prompt → 接 DeepSeek → rag_chat.py → 工具化")
    else:
        print("❌ 先修到全过再往下走，别带着 bug 接 API（接上去只会更难查）")
    print("=" * 52)
    return 0 if ok_cnt == total else 2


if __name__ == "__main__":
    sys.exit(main())
