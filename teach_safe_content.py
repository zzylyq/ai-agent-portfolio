# ==========================================================
# Day2 教学版：safe_content 安全取值函数（每一行都有注释）
# 用法：python teach_safe_content.py
# 学法：先整段抄一遍 → 跑通 → 再改一处 → 再改一处
# ==========================================================


# 这个函数的作用：从模型返回的数据里，安全地取出回答文字。
# 不管数据缺了哪一层，它都会返回一个字符串，绝不让程序崩溃。
def safe_content(data):
    # 第1步：去 data 里取 "choices" 这个键。
    #        取到了，就是那个列表；
    #        取不到，data.get() 会返回 None，然后 "or []" 把 None 换成空列表 []。
    #        这一步的目的：保证 choices 一定是个列表，后面才能安全地做 "判断空不空"。
    choices = data.get("choices") or []

    # 第2步：打开列看看。如果列表是空的（模型没给回答，比如被限流、拒答），
    #        就直接交回一个空字符串 ""，函数在这里提前结束。
    if not choices:
        return ""

    # 第3步：能走到这里，说明列表里至少有一个元素。
    #        choices[0] 取第一个元素（是个字典），再从里面取 "message"。
    #        取不到就用空字典 {} 代替，同样是为了不让下一步崩。
    msg = choices[0].get("message") or {}

    # 第4步：从 message 字典里取 "content"。
    #        这是唯一没有兜底也不需要兜底的一句：
    #        因为 .get("content", "") 本身就写了默认值 ""，取不到就返回空字符串。
    return msg.get("content", "")


# ==========================================================
# 下面是测试代码：故意用三种不同的坏数据喂给它，验证它不崩
# ==========================================================

# 情况1：模型正常回答（结构完整）
normal = {"choices": [{"message": {"role": "assistant", "content": "你好，我是AI助手"}}]}
print("情况1 正常返回：", repr(safe_content(normal)))

# 情况2：整个数据是空的（服务器抽风，什么都没给）
empty = {}
print("情况2 数据全空：", repr(safe_content(empty)))

# 情况3：choices 是空列表（模型拒答 / 被限流）
refused = {"choices": []}
print("情况3 模型拒答：", repr(safe_content(refused)))

# 情况4：choices 里有元素，但里面没有 message（字段缺失）
broken = {"choices": [{"finish_reason": "length"}]}
print("情况4 字段缺失：", repr(safe_content(broken)))
