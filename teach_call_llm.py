# ==========================================================
# Day2 教学版：带完整异常处理的 call_llm 函数
# 用法：
#   $env:DEEPSEEK_API_KEY="sk-xxx"
#   python teach_call_llm.py
# 学法：整段抄到 mycall.py 里 → 跑通 → 再改
#
# 这个函数把今天三个专项全用上了：
#   专项③ try-except  → 接住超时/HTTP错误/非JSON/未知异常
#   专项② json        → r.json() 解析返回（不用手动 loads）
#   专项① 安全取值    → choices/message/content 每层都兜底
# ==========================================================

import os
import requests


def call_llm(prompt, timeout=60):
    """
    把一句话发给 DeepSeek，拿回它的回答。
    规矩：任何失败都不许抛异常，只返回一段说明文字。
    """

    # 第1步：读密钥。读不到就提前返回，不要继续往下走。
    # 提前返回（early return）是好习惯：把不满足前提的情况拦在门口
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return "错误：没有设置 DEEPSEEK_API_KEY"

    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",      # 认证靠这一行
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }

    # 第2步：发请求。把四种可能的失败分别接住
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=timeout)
        r.raise_for_status()        # 4xx/5xx 会在这里主动抛异常
        data = r.json()             # 把返回的字符串解析成字典
    except requests.Timeout:
        # 失败了 60 秒都没回应（大模型最常见的失败）
        return "错误：请求超时，请稍后重试"
    except requests.HTTPError:
        # 401 密钥错 / 429 太频繁 / 500 服务器炸了，都会走这里
        return f"错误：HTTP {r.status_code}，服务器拒绝了请求"
    except ValueError:
        # 返回的不是合法 JSON（比如是个 HTML 错误页）
        return "错误：返回的不是合法 JSON"
    except Exception as e:
        # 兜底：任何没预料到的错误，也不能让程序崩
        return f"错误：未知异常 {e}"

    # 第3步：安全取值（和上午的 safe_content 一模一样）
    choices = data.get("choices") or []
    if not choices:
        return "模型没有返回内容"
    msg = choices[0].get("message") or {}
    return msg.get("content") or ""


if __name__ == "__main__":
    print("正在调用模型...")
    answer = call_llm("用一句话介绍你自己")
    print("回答：", answer)
