from tabulate import tabulate

# 原始数据
data = [
    {"key1": "value1", "key2": "value2", "key3": "value3"},
    {"key1": "value4", "key2": "value5", "key3": "value6"}
]

# 我们只关心'key1'和'key3'
desired_headers = ["key1", "key3"]

# 方法1：使用headers参数指定要显示的键（注意，这里我们传递的是字典列表，然后通过headers过滤）
# 注意：tabulate会自动从每个字典中提取desired_headers中存在的键对应的值，忽略其他键
table = tabulate(data, headers=desired_headers, tablefmt="grid")
print(table)

