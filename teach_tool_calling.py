# 作用：Function Calling 完整参考实现 —— 让模型自己决定调用 get_time / get_weather，并流式输出最终答案
# 用法：python teach_tool_calling.py          离线：演示 tools 结构 + 解析 tool_calls 的逻辑（不需要密钥）
#       python teach_tool_calling.py --call   联网：真实两轮调用，流式打印最终答案
# 完成：2026-10-27（Day3）参考实现，学员需照着手敲进 tool_calling.py
# 踩过的坑：arguments 是 JSON 字符串不是字典；工具那一轮 content 是 None；流式字段叫 delta 不叫 message

import os
import sys
import json
import datetime

API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"


# ===== 1. 工具清单：告诉模型「你有什么工具、参数长什么样」=====
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "查询某个城市当前的日期和时间。用户问现在几点、今天几号时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名，例如 北京"}
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询某个城市今天的天气和气温。用户问天气、下雨、穿什么时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名，例如 上海"}
                },
                "required": ["city"],
            },
        },
    },
]


# ===== 2. 本地真函数：模型只会「说」要调用，真正执行靠这里 =====
def get_time(city="北京"):
    now = datetime.datetime.now()
    return f"{city} 现在是 {now:%Y-%m-%d %H:%M:%S}"


def get_weather(city="北京"):
    # 假数据，但返回值的形式和真接口一致；以后换成真 API 只改这个函数
    fake = {"北京": ("晴", 18), "上海": ("多云", 22), "深圳": ("小雨", 26)}
    desc, temp = fake.get(city, ("未知", None))
    if temp is None:
        return f"没有 {city} 的天气数据"
    return f"{city} 今天{desc}，气温 {temp}℃"


# 名字 → 函数的映射表，模型给名字，我们查表执行
TOOL_MAP = {"get_time": get_time, "get_weather": get_weather}


# ===== 3. 执行工具：任何异常都变成一句话回给模型，不许崩 =====
def run_tool(name, args):
    fn = TOOL_MAP.get(name)
    if not fn:
        return f"没有名为 {name} 的工具"
    try:
        return str(fn(**args))          # args 是字典，**args 拆成关键字参数
    except Exception as e:
        return f"工具执行失败：{e}"


# ===== 4. 解析 tool_calls：全程软取，缺哪层都不崩 =====
def parse_tool_calls(resp):
    choices = resp.get("choices") or []
    if not choices:
        return []
    msg = choices[0].get("message") or {}
    calls = msg.get("tool_calls") or []
    result = []
    for c in calls:
        fn = c.get("function") or {}
        name = fn.get("name") or ""
        raw = fn.get("arguments") or "{}"
        try:
            args = json.loads(raw)      # 关键：arguments 是「JSON 字符串」，必须 loads 才能当字典用
        except json.JSONDecodeError:
            args = {}
        result.append({"id": c.get("id"), "name": name, "args": args})
    return result


# ===== 5. 一次 HTTP 请求（普通 / 流式共用）=====
def call_api(messages, tools=None, stream=False, timeout=60):
    """返回 (响应对象, 错误说明)。成功时错误说明为 None"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return None, "错误：没读到 DEEPSEEK_API_KEY，先执行 $env:DEEPSEEK_API_KEY='sk-xxx'"

    import requests

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": MODEL, "messages": messages, "temperature": 0.3, "stream": stream}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"     # auto = 让模型自己决定调不调

    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=timeout, stream=stream)
        r.raise_for_status()
    except requests.Timeout:
        return None, "请求超时，检查网络后重试"
    except requests.HTTPError:
        return None, f"HTTP错误：{r.status_code}"
    except Exception as e:
        return None, f"出错了：{e}"

    if stream:
        return r, None
    try:
        return r.json(), None
    except ValueError:
        return None, "JSON解析错误"


# ===== 6. 流式收字：边打边收，返回完整文本 =====
def stream_answer(resp):
    buf = []
    for line in resp.iter_lines():
        if not line:
            continue
        text = line.decode("utf-8") if isinstance(line, bytes) else line
        if not text.startswith("data: "):
            continue
        data = text[6:].strip()             # 去掉 "data: " 前缀
        if data == "[DONE]":
            break
        try:
            chunk = json.loads(data)
        except json.JSONDecodeError:
            continue
        choices = chunk.get("choices") or []
        if not choices:
            continue
        delta = choices[0].get("delta") or {}   # 流式里叫 delta，不叫 message
        piece = delta.get("content") or ""      # 最后一块没有 content，跳过
        if piece:
            buf.append(piece)
            print(piece, end="", flush=True)
    print()
    return "".join(buf)


# ===== 7. 主流程：请求 → 要工具 → 执行 → 回填 → 再请求（流式）=====
def chat_with_tools(question, max_rounds=3):
    messages = [
        {"role": "system", "content": "你是生活助手。需要实时信息时必须调用工具，不要凭记忆编造。"},
        {"role": "user", "content": question},
    ]

    for round_no in range(1, max_rounds + 1):
        data, err = call_api(messages, tools=TOOLS)
        if err:
            return err

        choices = data.get("choices") or []
        if not choices:
            return "模型没有返回内容"

        calls = parse_tool_calls(data)

        # 情况A：模型不要工具，直接给答案
        if not calls:
            msg = choices[0].get("message") or {}
            return msg.get("content") or ""

        # 情况B：模型要调工具。把它这条 assistant 消息原样记进对话
        messages.append(choices[0].get("message") or {})

        for c in calls:
            print(f"[第{round_no}轮] 模型想调用 {c['name']}({c['args']})")
            out = run_tool(c["name"], c["args"])
            print(f"  → 本地执行：{out}")
            # 回填工具结果：role 必须是 tool，tool_call_id 必须原样带回
            messages.append({"role": "tool", "tool_call_id": c["id"], "content": out})

    # 轮次用完，强制它直接回答，并且这一次用流式
    messages.append({"role": "user", "content": "请直接根据上面的工具结果回答我，不要再调用工具。"})
    resp, err = call_api(messages, stream=True)
    if err:
        return err
    return stream_answer(resp)


# ===== 8. 离线演示：不用密钥也能验证解析逻辑写对了 =====
def offline_demo():
    print("===== 交给模型的工具清单 =====")
    print(json.dumps(TOOLS, ensure_ascii=False, indent=2))

    # 伪造一个「模型想调工具」的响应，形状和真响应完全一致
    fake_resp = {
        "choices": [
            {
                "finish_reason": "tool_calls",
                "message": {
                    "role": "assistant",
                    "content": None,                       # 工具轮 content 是 None，这是重点
                    "tool_calls": [
                        {
                            "id": "call_abc123",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": '{"city": "北京"}',   # 注意：字符串，不是字典
                            },
                        }
                    ],
                },
            }
        ]
    }

    print("\n===== 解析出来的工具调用 =====")
    calls = parse_tool_calls(fake_resp)
    print(json.dumps(calls, ensure_ascii=False, indent=2))

    print("\n===== 本地执行结果（这一句才是模型最终能看到的）=====")
    for c in calls:
        print(run_tool(c["name"], c["args"]))

    print("\n离线部分通过 = 说明你的解析 + 执行逻辑是对的，剩下只是联网。")


def main():
    if "--call" in sys.argv:
        print("===== 提问：北京现在几点？那边天气怎么样？=====")
        answer = chat_with_tools("北京现在几点？那边天气怎么样？")
        print("\n===== 最终回答 =====")
        print(answer)
    else:
        offline_demo()


if __name__ == "__main__":
    main()
