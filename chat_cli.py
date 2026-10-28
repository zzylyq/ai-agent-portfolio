import os, json, requests

def stream_chat(messages):
    r = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"},
        json={"model": "deepseek-chat",
              "messages": messages,
              "stream": True},
        stream=True,
        timeout=60,
    )
    full=""
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
            full+=piece
    print()
    messages.append({"role": "assistant", "content": full})

messages=[]
q=""
while True:
    q = input("\n你：")
    if q == "exit":
        break
    messages.append({"role": "user", "content": q})
    stream_chat(messages)

