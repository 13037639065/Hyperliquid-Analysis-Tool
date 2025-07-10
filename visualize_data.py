import pandas as pd
import matplotlib.pyplot as plt
import ast
import argparse
from datetime import datetime

argparser = argparse.ArgumentParser()
argparser.add_argument('--file', "-f", help='file name')
argparser.add_argument('--timedelta', "-tt", default = 60, type=int, help="时间范围，为单位是分钟")
argparser.add_argument('--time', "-t", default = datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), help='结束时间')

args = argparser.parse_args()

# 根据 args.time 和 limit 计算时间范围用于过滤数据
end_time = pd.to_datetime(args.time, format="ISO8601")
start_time = end_time - pd.Timedelta(args.timedelta, unit='m')
# 输出时间范围

print(f"时间范围：{start_time} - {end_time}")

df = pd.read_csv(args.file)

df['time'] = pd.to_datetime(df['time'], format="ISO8601")  # Convert to datetime
df = df[(df['time'] >= start_time) & (df['time'] <= end_time)]


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
plt.scatter(df_position['time'], df_position['position_entryPx'], c=df_position['position_size'], cmap='bwr', s=100, label='Position Entry Price', zorder=5,marker='s')

# 添加颜色条以表示 position_size 的大小
v_limit = max(abs(df_position['position_size'].min()), abs(df_position['position_size'].max()))
vmin = -v_limit
vmax = v_limit
sm = plt.cm.ScalarMappable(cmap='bwr', norm=plt.Normalize(vmin=vmin, vmax=vmax))
sm.set_array([])  # 只是为了让 colorbar 正常工作
plt.colorbar(sm, ax=plt.gca(), label='Position Size')

# 打印 2025-07-10T07:14:00 的 position_size
print(f"2025-07-10T07:14:00 的 position_size: {df_position.loc[df_position['time'] == '2025-07-10T07:14:00', 'position_size'].values[0]}")
# 计算 position_size 的变化用于判断买入/卖出动作
df_position = df_position.sort_values('time').reset_index(drop=True)
df_position['position_change'] = df_position['position_size'].diff()

# 在价格折线图基础上添加 position_size 变化方向标记
for i in range(1, len(df_position)):
    prev_size = df_position.iloc[i - 1]['position_size']
    curr_size = df_position.iloc[i]['position_size']
    time = df_position.iloc[i]['time']
    price = df['price'].loc[df['time'] == time].values[0]

    if curr_size > prev_size:
        # 上三角表示买入
        plt.scatter(time, float(price), marker='^', color='blue', s=100, zorder=10)
    elif curr_size < prev_size:
        # 下三角表示卖出
        plt.scatter(time, float(price), marker='v', color='orange', s=100, zorder=10)

plt.xticks(rotation=45) # 旋转x轴标签以便更好地显示时间
plt.xlabel('Time')
plt.ylabel('Price')
plt.title('Order Book Visualization with Position Information')
plt.legend()
plt.tight_layout()  # 调整布局以防止裁剪

# 显示图表
plt.show()
