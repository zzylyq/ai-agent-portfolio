import asyncio
import time
import httpx

URL = "http://127.0.0.1:8000/chat"


async def one(client):
    t0 = time.time()
    r = await client.post(URL, json={"question": "今天几号"})
    cost = time.time() - t0
    return cost, r.status_code


async def bench(n):
    async with httpx.AsyncClient(timeout=120) as client:
        print(f"--- 并发 {n} 个请求 ---")
        t0 = time.time()
        results = await asyncio.gather(*[one(client) for _ in range(n)])
        total = time.time() - t0

        costs = [c for c, s in results]
        codes = set(s for c, s in results)

        print(f"全部完成总耗时：{total:.2f} 秒")
        print(f"单请求平均：{sum(costs) / len(costs):.2f} 秒")
        print(f"最慢一个：{max(costs):.2f} 秒")
        print(f"状态码：{codes}")
        print(f"如果串行执行，约需：{sum(costs):.2f} 秒")


asyncio.run(bench(5))
