# 作用：Day2 专项② —— json.loads / load / dumps / dump 四兄弟 + 模型返回的"假JSON"清洗
# 用法：python drill_json.py（会在当前目录生成一个 demo.json，跑完可以删掉）
# 坑：模型说"返回JSON"，实际给的是字符串，还常常带 ```json 围栏，直接 loads 必崩

import json

print("=== 记这一句 ===")
print("带 s 的跟【字符串】打交道；不带 s 的跟【文件】打交道")
print()

print("=== 1) loads：字符串 -> dict ===")
raw = '{"role": "user", "content": "你好"}'
d = json.loads(raw)
print("结果:", d, "| 类型:", type(d).__name__)

print()
print("=== 2) dumps：dict -> 字符串 ===")
s = json.dumps(d, ensure_ascii=False, indent=2)
print("带 ensure_ascii=False（能看清中文）:")
print(s)
print("不带 ensure_ascii 的效果:", json.dumps({"content": "你好"}))

print()
print("=== 3) dump：dict -> 文件（要 with + encoding）===")
with open("demo.json", "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
print("已写入 demo.json")

print()
print("=== 4) load：文件 -> dict ===")
with open("demo.json", "r", encoding="utf-8") as f:
    back = json.load(f)
print("读回来:", back)

print()
print("=== 5) 真实场景：清洗模型返回的围栏 JSON ===")
llm_output = '```json\n{"answer": "RAG", "confidence": 0.9}\n```'

try:
    json.loads(llm_output)          # 不清洗直接转
except json.JSONDecodeError as e:
    print("不清洗直接 loads -> 崩了:", str(e)[:45])

clean = (
    llm_output.strip()
    .removeprefix("```json")
    .removeprefix("```")
    .removesuffix("```")
    .strip()
)
print("清洗后:", clean)
parsed = json.loads(clean)
print("能用啦 -> answer =", parsed["answer"], "| confidence =", parsed["confidence"])
print("（这一步是后天 Function Calling 的必备操作，模型返回的参数就长这样）")

print()
print("=== 6) 顺手记：文件/README 里最常见的两个参数 ===")
print("indent=2            -> 缩进好看，人能读")
print("ensure_ascii=False  -> 中文不被转成 \\uXXXX")
