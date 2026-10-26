# 作用：Day2 专项① —— dict 硬取 vs 软取、链式剥洋葱、空值兜底
# 用法：python drill_dict.py
# 坑：模型拒答/限流时字段会缺失，一路用 [] 硬取会让整个服务 KeyError 崩掉

print("=== 1) 硬取 vs 软取 ===")

resp = {
    "choices": [
        {"message": {"role": "assistant", "content": "你好，我是AI助手"}}
    ],
    "usage": {"total_tokens": 42},
}

print("[硬取·键存在]  :", resp["usage"])                  # 正常
print("[软取·键存在]  :", resp.get("usage"))              # 正常
print("[软取·键不存在]:", resp.get("model"))              # None，不崩
print("[软取·带默认值]:", resp.get("model", "未返回"))     # 未返回

try:
    print(resp["model"])                                 # 硬取不存在的键
except KeyError as e:
    print("[硬取·键不存在]: 崩了！KeyError ->", e)

print()
print("=== 2) 空值兜底惯用法：or ===")

bad_resp = {"choices": [], "usage": {"total_tokens": 0}}   # 模型拒答时就是这样

choices = resp.get("choices") or []
print("正常响应的 choices 非空吗:", bool(choices))

choices_bad = bad_resp.get("choices") or []
print("异常响应的 choices 非空吗:", bool(choices_bad), "-> 已被兜成空列表")

print()
print("=== 3) 剥洋葱：每一层都软取 ===")

msg = choices[0].get("message") or {}                     # 第二层
content = msg.get("content", "")                          # 第三层，带默认值
print("content =", content)

print()
print("=== 4) 标准答案（这个函数后天还要用，背下来）===")


def safe_content(d):
    """从大模型响应里安全取回答文本：任何一层缺失都返回空串，绝不崩"""
    choices = d.get("choices") or []
    if not choices:
        return ""
    msg = choices[0].get("message") or {}
    return msg.get("content") or ""


print("正常响应 ->", repr(safe_content(resp)))
print("空响应   ->", repr(safe_content(bad_resp)))
print("空dict   ->", repr(safe_content({})))

print()
print("=== 5) 一行 vs 四行，什么时候用哪个 ===")
print("确定的字段(自己刚写的dict)  : d['usage']")
print("不确定的字段(外部返回的数据): d.get('usage') or {}")
print("记住：外部数据 > 一律软取，自己造的数据 > 硬取没问题")
