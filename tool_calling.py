# 作用：让模型自己决定调用本地工具的 Agent 雏形 —— 查时间 / 查天气，并流式返回最终答案
# 用法：python tool_calling.py          离线：验证 tools 结构和解析逻辑（不需要密钥）
#       python tool_calling.py --call   联网：真实两轮调用，流式打印答案
# 完成：2026-10-27（Day3）—— 手敲补完 5 个 TODO
# 踩过的坑：arguments 是 JSON 字符串；工具轮 content 是 None；流式字段叫 delta

import os
import sys
import json
import datetime

API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"


# ===== 1. 工具清单 =====
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
            # TODO 1：照着上面 get_time 的样子，给 get_weather 补 parameters
            #         要求：一个参数 city（string），并且是必填
            "description": "查询某个城市今天的天气和气温。用户问天气、下雨、穿什么时使用。",
            "parameters": {
            },
        },
    },
]


# ===== 2. 本地真函数（假数据，形式是真的）=====
def get_time(city="北京"):
    now = datetime.datetime.now()
    return f"{city} 现在是 {now:%Y-%m-%d %H:%M:%S}"


def get_weather(city="北京"):
    fake = {"北京": ("晴", 18), "上海": ("多云", 22), "深圳": ("小雨", 26)}
    desc, temp = fake.get(city, ("未知", None))
    if temp is None:
        return f"没有 {city} 的天气数据"
    return f"{city} 今天{desc}，气温 {temp}℃"


TOOL_MAP = {"get_time": get_time, "get_weather": get_weather}


# ===== 3. 执行工具 =====
def run_tool(name, args):
    # TODO 3：三步 —— ①用 TOOL_MAP.get(name) 拿到函数 ②拿不到就返回"没有这个工具"
    #         ③try 里用 **args 调用它，返回值转成 str；except Exception 里返回"工具执行失败：{e}"
    raise NotImplementedError("TODO 3：run_tool 还没写")


# ===== 4. 解析 tool_calls =====
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
        # TODO 2：这里要拿到「字典形式」的参数
        #         坑：raw 是一段 JSON 字符串，不能直接当字典用；转失败就给它空字典 {}
        args = {}
        result.append({"id": c.get("id"), "name": name, "args": args})
    return result


# ===== 5. 一次 HTTP 请求（已给你写好，不用改）=====
def call_api(messages, tools=None, stream=False, timeout=60):
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
        payload["tool_choice"] = "auto"

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


# ===== 6. 流式收字 =====
def stream_answer(resp):
    buf = []
    for line in resp.iter_lines():
        if not line:
            continue
        text = line.decode("utf-8") if isinstance(line, bytes) else line
        if not text.startswith("data: "):
            continue
        data = text[6:].strip()
        if data == "[DONE]":
            break
        try:
            chunk = json.loads(data)
        except json.JSONDecodeError:
            continue
        choices = chunk.get("choices") or []
        if not choices:
            continue
        # TODO 5：从每一块里取出新到的几个字
        #         提示：流式里字段叫 delta 不叫 message；最后一块没有 content，要能跳过
        piece = ""
        if piece:
            buf.append(piece)
            print(piece, end="", flush=True)
    print()
    return "".join(buf)


# ===== 7. 主流程 =====
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

        if not calls:
            msg = choices[0].get("message") or {}
            return msg.get("content") or ""

        # 模型要调工具：先把它的请求原样记进对话
        messages.append(choices[0].get("message") or {})

        for c in calls:
            print(f"[第{round_no}轮] 模型想调用 {c['name']}({c['args']})")
            out = run_tool(c["name"], c["args"])
            print(f"  → 本地执行：{out}")
            # TODO 4：把工具结果回填给模型。三种写法必须都对：
            #         ① role 是 "tool"  ② tool_call_id 用 c["id"] 原样带回  ③ content 放 out
            messages.append({"role": "user", "content": out})

    messages.append({"role": "user", "content": "请直接根据上面的工具结果回答我，不要再调用工具。"})
    resp, err = call_api(messages, stream=True)
    if err:
        return err
    return stream_answer(resp)


# ===== 8. 离线演示（不用密钥）=====
def offline_demo():
    print("===== 交给模型的工具清单 =====")
    print(json.dumps(TOOLS, ensure_ascii=False, indent=2))

    fake_resp = {
        "choices": [
            {
                "finish_reason": "tool_calls",
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_abc123",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": '{"city": "北京"}',
                            },
                        }
                    ],
                },
            }
        ]
    }

    try:
        print("\n===== 解析出来的工具调用 =====")
        calls = parse_tool_calls(fake_resp)
        print(json.dumps(calls, ensure_ascii=False, indent=2))
        if calls and not calls[0]["args"]:
            print("⚠️ args 是空的 —— TODO 2（json.loads）还没写对")

        print("\n===== 本地执行结果 =====")
        for c in calls:
            print(run_tool(c["name"], c["args"]))
        print("\n离线部分通过 = 解析 + 执行逻辑对了，剩下只是联网。")
    except NotImplementedError as e:
        print(f"\n⛔ 还没补完：{e}")
        print("   补完 TODO 3 再跑一次这个命令。")


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
