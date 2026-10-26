# 作用：Day2 专项③ —— try/except/else/finally 结构与执行顺序
# 用法：python drill_try.py
# 坑：try 不能当光杆司令；多个 except 要从具体到宽泛；中文标点会让你 SyntaxError

print("=== 1) 执行顺序（昨晚那道半对题的答案）===")


def demo(x):
    try:
        print("  A: 进入 try")
        result = 10 / x                  # 这一行出错，后面的 B 就不执行了
        print("  B: 只在【没出错】时执行")
        return result
    except ZeroDivisionError:
        print("  C: 捕获到除零错误，程序没挂")
        return None
    finally:
        print("  D: finally 无论如何都执行")


for v in (2, 0):
    print(f"调用 demo({v}):")
    demo(v)

print("  E: 注意！except 执行完后，程序【继续往下跑】，不会退出")

print()
print("=== 2) 多个 except：从具体到宽泛，Exception 必须放最后 ===")


def safe_int(s):
    try:
        return int(s)
    except ValueError:
        print(f"  不是数字: {s!r}")
    except Exception as e:               # 兜底放最后，否则会把上面的全吃掉
        print(f"  未知错误: {type(e).__name__}: {e}")
    return -1


print("结果依次:", safe_int("123"), "|", safe_int("abc"), "|", safe_int(None))

print()
print("=== 3) else：没出错才走（可选，知道就行）===")


def parse(s):
    try:
        d = int(s)
    except ValueError:
        print("  转不了")
    else:
        print("  转换成功:", d)
    finally:
        print("  finally 收尾")


parse("42")
parse("x")

print()
print("=== 4) 调大模型 API 的标准异常模板（后天照抄，今天先认全）===")
TEMPLATE = """
try:
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()                    # 401/429/500 在这里主动炸出来
    data = r.json()
    content = safe_content(data)            # 复用昨天专项①
    if not content:
        print("模型返回为空")
    return content
except requests.Timeout:
    print("请求超时")                        # 调大模型最常见
except requests.HTTPError as e:
    print("HTTP错误:", e.response.status_code)
except Exception as e:
    print("其他错误:", e)
    return ""
"""
print(TEMPLATE)

print("=== 5) 今天必须记住的两个报错长相 ===")
print("SyntaxError: invalid character '：'  -> 你用了中文冒号")
print("IndentationError: expected an indented block  -> 缩进没写 / except 没和 try 对齐")
