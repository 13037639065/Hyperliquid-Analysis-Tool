import pandas as pd

df = pd.read_csv("./trading_data_cache/user_fills/a3984268_2025_07_13T15_05_12.csv")

# 检查时间 time 是否从小到大
if df['time'].is_monotonic_increasing:  # 检查时间列是否递增
    print("时间列递增")  # 如果是递增的，则输出 "时间列递增"
else:
    print("时间列非递增")  # 如果不是递增的，则输出 "时间列非递增"