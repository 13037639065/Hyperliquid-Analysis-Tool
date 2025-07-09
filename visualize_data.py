import pandas as pd
import matplotlib.pyplot as plt
import ast
import argparse
from datetime import datetime

argparser = argparse.ArgumentParser()
argparser.add_argument('--file', "-f", help='file name')
argparser.add_argument('--limit', default = 60, type=int, help="时间限制分钟")
argparser.add_argument('--time', "-t", default = datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), help='结束时间')

args = argparser.parse_args()

# 根据 args.time 和 limit 计算时间范围用于过滤数据
end_time = pd.to_datetime(args.time, format="ISO8601")
start_time = end_time - pd.Timedelta(args.limit, unit='m')
# 输出时间范围

print(f"时间范围：{start_time} - {end_time}")

df = pd.read_csv(args.file)
df['time'] = pd.to_datetime(df['time'], format="ISO8601")  # Convert to datetime

# 解析BUY, SELL, POSITION列
df['BUY'] = df['BUY'].apply(ast.literal_eval)
df['SELL'] = df['SELL'].apply(ast.literal_eval)
df['POSITION'] = df['POSITION'].apply(ast.literal_eval)

# 提取BUY订单的价格和大小信息
df_buy = pd.DataFrame([(t, item['price'], item['size']) for t, items in df[['time', 'BUY']].values for item in items if isinstance(items, list)], columns=['time', 'buy_price', 'buy_size'])

# 提取SELL订单的价格和大小信息
df_sell = pd.DataFrame([(t, item['price'], item['size']) for t, items in df[['time', 'SELL']].values for item in items if isinstance(items, list)], columns=['time', 'sell_price', 'sell_size'])

# 提取POSITION的入场价格和大小信息
df_position = pd.DataFrame([(t, item['entryPx'], item['size']) for t, items in df[['time', 'POSITION']].values for item in items if isinstance(items, list)], columns=['time', 'position_entryPx', 'position_size'])

# 转换为数值类型
df_buy[['buy_price', 'buy_size']] = df_buy[['buy_price', 'buy_size']].astype(float)
df_sell[['sell_price', 'sell_size']] = df_sell[['sell_price', 'sell_size']].astype(float)
df_position[['position_entryPx', 'position_size']] = df_position[['position_entryPx', 'position_size']].astype(float)

# 创建图表
plt.figure(figsize=(14, 7))

# 绘制价格折线图
plt.plot(df['time'], df['price'].astype(float), label='Price', color='black')

# 绘制买入订单价格与大小
plt.scatter(df_buy['time'], df_buy['buy_price'], s=df_buy['buy_size']*100, c='green', alpha=0.6, label='Buy Orders')

# 绘制卖出订单价格与大小
plt.scatter(df_sell['time'], df_sell['sell_price'], s=df_sell['sell_size']*100, c='red', alpha=0.6, label='Sell Orders')

# 绘制持仓均价折线图
plt.plot(df_position['time'], df_position['position_entryPx'], c='blue', linestyle='-', linewidth=2, label='Position Entry Price')

# 在持仓均价上标注数量信息
for _, row in df_position.iterrows():
    plt.annotate(f"{row['position_size']}", (row['time'], row['position_entryPx']), textcoords="offset points", xytext=(0,10), ha='center', fontsize=8, color='blue')

plt.xticks(rotation=45) # 旋转x轴标签以便更好地显示时间
plt.xlabel('Time')
plt.ylabel('Price')
plt.title('Order Book Visualization with Position Information')
plt.legend()
plt.tight_layout()  # 调整布局以防止裁剪

# 显示图表
plt.show()
