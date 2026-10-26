# 作用：可复用的 Prompt 组装器 —— 把"角色/任务/参考资料/问题"拼成标准 messages
# 用法：python prompt_builder.py          离线模式，只打印拼好的 messages（不需要密钥）
#       python prompt_builder.py --call   联网模式，真的调一次 DeepSeek
# 完成：2026-10-26（Day2）
# 踩过的坑：字典键必须加引号；外部数据一律 .get() 软取；try 必须配 except

import os
import sys
import json

API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"


# ===== 零件1（专项①）：安全取值 =====
def safe_content(resp):
    """从大模型返回的 dict 里安全取出回答文本，任何一层缺失都不崩"""
    # 取 choices，取不到就用空列表代替
    choices = resp.get("choices") or []
    # 列表是空的（模型拒答 / 被限流）
    if not choices:
        return "模型没有回答"
    # 取第一个元素里的 message，取不到就用空字典代替
    msg = choices[0].get("message") or {}
    # 取 content，取不到就给默认值
    return msg.get("content", "字段缺失")


# ===== 零件2（Prompt工程）：组装 messages =====
def build_messages(role, task, chunks, question, fmt="纯文本"):
    """把四样东西拼成标准 messages 列表，所有大模型 API 都用这个格式"""
    # system 消息 = 角色设定 + 任务要求
    system_msg = {"role": "system", "content": f"{role}\n{task}"}

    # 判断有没有参考资料，走两个分支
    if not chunks:
        # 情况A：没有参考资料，只放问题和格式要求
        user_text = f"{question}\n\n输出格式：{fmt}"
    else:
        # 情况B：有参考资料，给每段编号后用换行拼成一整块
        # enumerate 同时给出「序号 i」和「内容 c」
        refs = "\n".join([f"[{i + 1}] {c}" for i, c in enumerate(chunks)])
        user_text = f"""参考资料：
{refs}

只依据上面的参考资料回答。资料里没有的内容，就说"资料未提及"。

用户问题：{question}

输出格式：{fmt}"""

    return [system_msg, {"role": "user", "content": user_text}]


# ===== 零件3（专项③）：带完整异常处理的调用 =====
def call_llm(messages, timeout=60):
    """把 messages 发给 DeepSeek。任何失败都返回说明文字，绝不抛异常"""

    # 第1步：读密钥，读不到就提前返回
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return "错误：没读到 DEEPSEEK_API_KEY，先执行 $env:DEEPSEEK_API_KEY='sk-xxx'"

    import requests     # 放在函数里：离线模式不需要装 requests 也能跑

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": MODEL, "messages": messages, "stream": False, "temperature": 0.3}

    # 第2步：发请求，四种失败分别接住
    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
        r.raise_for_status()        # 401/429/500 在这里主动抛出
        data = r.json()
    except requests.Timeout:
        return "请求超时，检查网络后重试"
    except requests.HTTPError:
        return f"HTTP错误：{r.status_code}"
    except ValueError:
        return "JSON解析错误"
    except Exception as e:
        return f"出错了：{e}"

    # 第3步：能走到这里，说明上面没有 return，
    # 那 data 一定拿到手了，可以放心取值
    return safe_content(data)


def main():
    messages = build_messages(
        role="你是一位资深的AI应用工程师面试官",
        task="用简洁、专业、鼓励的语气回答候选人的问题",
        chunks=[
            "RAG = 检索增强生成：先检索资料再生成回答，用来降低幻觉。",
            "Function Calling = 让模型自己决定要不要调用外部函数。",
        ],
        question="零基础转行做AI应用工程师，第一步应该学什么？",
        fmt="分点说明，不超过3点",
    )

    # 离线必做：原样打印组装结果，面试官要看的就是这个结构
    print(json.dumps(messages, ensure_ascii=False, indent=2))

    if "--call" in sys.argv:
        print("\n===== 模型回答 =====")
        answer = call_llm(messages)
        print(answer or "（没拿到回答，看上面的报错）")


if __name__ == "__main__":
    main()
