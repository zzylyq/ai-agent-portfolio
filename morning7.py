import os, json, requests

def stream_chat(prompt):
    r = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"},
        json={"model": "deepseek-chat",
              "messages": [{"role": "user", "content": prompt}],
              "stream": True},
        stream=True,
        timeout=60,
    )
    for line in r.iter_lines():
        if not line:
            continue
        text = line.decode("utf-8")
        if not text.startswith("data: "):
            continue
        payload = text[6:]
        if payload == "[DONE]":
            break
        data = json.loads(payload)
        piece = (data["choices"][0].get("delta") or {}).get("content")
        if piece:
            print(piece, end="", flush=True)
    print()

stream_chat("用一句话介绍你自己")
