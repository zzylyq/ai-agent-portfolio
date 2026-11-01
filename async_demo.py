import asyncio
import time


async def work(name, sec):
    print(f"  {name} 开始")
    await asyncio.sleep(sec)      # 模拟"等 API 返回"
    print(f"  {name} 结束")


async def serial():
    print("--- 串行：一个等完再等下一个 ---")
    t0 = time.time()
    await work("A", 2)
    await work("B", 2)
    print(f"串行总耗时：{round(time.time() - t0, 1)} 秒\n")


async def parallel():
    print("--- 并发：两个一起等 ---")
    t0 = time.time()
    await asyncio.gather(
        work("A", 2),
        work("B", 2),
    )
    print(f"并发总耗时：{round(time.time() - t0, 1)} 秒")


asyncio.run(serial())
asyncio.run(parallel())
