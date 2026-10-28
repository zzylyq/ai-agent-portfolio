

tools=[{
        "type":"function",
        "function":
            {
            "name":"get_weather",
            "description":"查某个城市的天气",
            "parameters":{
                "type":"object",
                "properties":{
                    "city":{"type": "string","description":"城市"}

                },
                "required":["city"]
                            }
            
            
                     }
                }
            ]

print(tools)