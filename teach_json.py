# ==========================================================
# Day2 教学版：json 四兄弟（每个方法都有中文注释）
# 用法：python teach_json.py
# 学法：先整段抄一遍跑通 → 再改一处 → 再改一处
#
# 记忆口诀：带 s 的跟【字符串】打交道，不带 s 的跟【文件】打交道
#   loads  = load  + s(string)  ：字符串 → 字典    （读模型返回）
#   dumps  = dump  + s(string)  ：字典   → 字符串  （发给模型）
#   load   =              读文件：文件   → 字典
#   dump   =              写文件：字典   → 文件
# ==========================================================

import json

# ============ 第1组：loads / dumps —— 处理"字符串" ============

# 这是模型返回的原始文本。注意：它是一段【字符串】，不是字典！
# 长得像字典，但外面有引号，程序只把它当文字
text = '{"name": "小明", "skills": ["Python", "AI"], "age": 25}'

# loads：把这段"字符串"解析成能操作的字典
obj = json.loads(text)

print("=== 第1组：loads / dumps ===")
print("转换前 type：", type(text))        # <class 'str'>
print("转换后 type：", type(obj))         # <class 'dict'>
print("现在可以按键取值：", obj["name"])   # 小明
print("列表也能取：", obj["skills"][1])    # AI

# dumps：把字典变回字符串。为什么要变回去？
# 因为发给模型的 HTTP 请求体，只能是字符串
back = json.dumps(obj, ensure_ascii=False)   # ensure_ascii=False 让中文正常显示
print("变回字符串 type：", type(back))
print("变回的内容：", back)


# ============ 第2组：dump / load —— 处理"文件" ============

print()
print("=== 第2组：dump / load 文件读写 ===")

data = {"project": "ai-agent-portfolio", "day": 2, "skills": ["Python"]}

# dump：把字典【写进文件】
# encoding="utf-8" 必须写，否则中文在 Windows 上会乱码或报错
# indent=2 让文件有缩进、人能看懂；ensure_ascii=False 保留中文
with open("demo2.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# load：把文件【读成字典】
with open("demo2.json", "r", encoding="utf-8") as f:
    loaded = json.load(f)

print("从文件读回来的 type：", type(loaded))
print("内容：", loaded)
print("能直接取值：", loaded["project"])


# ============ 第3组：转不出来怎么办（实战必用） ============

print()
print("=== 第3组：坏数据不会让程序崩 ===")

# 模型有时会返回这种不是 JSON 的东西（尤其是它说话的时候）
bad_text = "我觉得这个问题很好，答案是42"     # 这不是 JSON！

try:
    result = json.loads(bad_text)
except json.JSONDecodeError:
    # 捕获到"解析失败"，给个兜底值，程序继续跑
    result = {}
    print("这段文本不是合法JSON，已兜底为空字典")

print("最终拿到的 result：", result)
print("后续代码可以正常继续，不会崩")
