def get_weather(city):
	return f"{city}: 晴，26摄氏度"

def get_time():
	return "现在是上午十点"

TOOL_MAP={
	"get_weather":get_weather,
	"get_time":get_time
}

def run_tool(func_name,args):
	func = TOOL_MAP.get(func_name)
	if not func:
		return "not tool"
	return func(**args)

print(run_tool("get_weather", {"city": "北京"}))
print(run_tool("get_time", {}))
print(run_tool("get_news", {}))
