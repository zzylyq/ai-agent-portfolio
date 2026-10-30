# mini_fastapi.py —— 用标准库复刻 FastAPI 的核心机制（约 30 行）
import sys
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

# ===== 核心就这一行：一张空字典，就是"路由表" =====
ROUTES = {}

def post(path):
    def decorator(func):
        ROUTES[("POST", path)] = func      # ← 装饰器干的事：往字典里登记一行
        return func                        # ← 原封不动把函数还回去
    return decorator


# ===== 用法和 FastAPI 一模一样 =====
@post("/chat")
def chat_api(body):
    q = body.get("question", "")
    return {"question": q, "answer": f"你问的是：{q}"}


@post("/echo")
def echo(body):
    return {"echo": body}


# ===== 下面是把路由表跑起来的"服务器" =====
class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8")
        body = json.loads(raw) if raw else {}

        func = ROUTES.get(("POST", self.path))     # ← 查表：这个方法+路径有没有函数
        if not func:
            self.send_response(404)
            self.end_headers()
            return

        result = func(body)                         # ← 查到就调用

        data = json.dumps(result, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "show":
        print("路由表里现在有什么：")
        for (method, path), func in ROUTES.items():
            print(f"  {method:6s} {path:10s} -> {func.__name__}")
        sys.exit(0)

    print("迷你服务器启动：http://127.0.0.1:8001")
    HTTPServer(("127.0.0.1", 8001), Handler).serve_forever()
