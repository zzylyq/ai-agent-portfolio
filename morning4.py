# ===== 第2关教学：工具分发（TOOL_MAP）=====

# 两个假工具（真工具要调 API，这里用假数据演示）
def get_weather(city):
    return f"{city}：晴，26℃"

def get_stock_price(symbol):
    return f"{symbol}：现价 18.60 元"
    
def get_time(time):
    return f"{time}：12:00"
    
def get_today_date():
    return "2026-10-25"
    
 



# 【1】工具登记表：key 是工具名（字符串），value 是函数本身（不加括号！）
TOOL_MAP = {
    "get_weather": get_weather,
    "get_stock_price": get_stock_price,
    "get_time": get_time,
    "get_today_date": get_today_date,
}

# 【2】分发函数：模型给名字+参数，代码去表里找函数并执行
def run_tool(func_name, args):
    func = TOOL_MAP.get(func_name)   # 按名字取函数对象
    if not func:                      # 查不到就兜底
        return f"没有这个工具：{func_name}"
    return func(**args)               # 双星号：把字典拆成关键字参数

# 【3】模拟模型返回的三张"单子"
print(run_tool("get_weather", {"city": "北京"}))
print(run_tool("get_stock_price", {"symbol": "600519"}))
print(run_tool("get_time", {"time": "北京"}))
print(run_tool("get_today_date", {}))       # 故意给个不存在的工具，看兜底
