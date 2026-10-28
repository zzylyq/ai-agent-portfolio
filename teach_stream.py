# Day4 下午：流式输出（打字机效果）
# 用法：先设 key  $env:DEEPSEEK_API_KEY="sk-xxx"   然后 python teach_stream.py

import os
import json
import requests

def stream_chat(prompt):
    r = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"},
        json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,          # 【开关1】告诉模型：流式返回
        },
        stream=True,                 # 【开关2】告诉requests：别一次性读完
        timeout=60,
    )

    # 一行一行读回来
    for line in r.iter_lines():
        if not line:                 # 空行（心跳）跳过
            continue

        text = line.decode("utf-8")  # 字节 → 字符串
        if not text.startswith("data: "):
            continue                 # 不是数据行就跳过

        payload = text[6:]           # 砍掉开头 "data: " 这6个字符
        if payload == "[DONE]":      # 结束标记
            break

        data = json.loads(payload)                    # 字符串 → 字典
        delta = data["choices"][0].get("delta") or {} # 软取：本片内容
        piece = delta.get("content")
        if piece:
            print(piece, end="", flush=True)          # 不换行，立刻输出

    print()   # 最后补一个换行

stream_chat("用三句话讲讲什么是 API")
