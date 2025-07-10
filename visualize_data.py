import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
fig = make_subplots(rows=1, cols=1)

# 绘制价格折线图
fig.add_trace(go.Scatter(x=df['time'], y=df['price'].astype(float), name='Price', line=dict(color='black')))

# 绘制买入订单价格与大小
fig.add_trace(go.Scatter(x=df_buy['time'], y=df_buy['buy_price'], mode='markers', name='Buy Orders', marker=dict(color='green', size=10, opacity=0.6)))

# 绘制卖出订单价格与大小
fig.add_trace(go.Scatter(x=df_sell['time'], y=df_sell['sell_price'], mode='markers', name='Sell Orders', marker=dict(color='red', size=10, opacity=0.6)))

fig.add_trace(go.Scatter(
    x=df_position['time'],
    y=df_position['position_entryPx'],
    mode='markers',
    name='Position Entry Price',
    marker=dict(
        size=df_position['position_size'].abs() * 4,  # 使用 position_size 的绝对值控制点的大小
        color=['red' if s > 0 else 'blue' for s in df_position['position_size']],  # 根据正负设置颜色        
        opacity=0.7,
        symbol='diamond',
        showscale=False  # 不显示颜色比例尺
    ),
    showlegend=False
))

# 计算 position_size 的变化用于判断买入/卖出动作
df_position = df_position.sort_values('time').reset_index(drop=True)
df_position['position_change'] = df_position['position_size'].diff()

# 在价格折线图基础上添加 position_size 变化方向标记
buy_prices = []
sell_prices = []
buy_price_times = []
sell_price_times = []
for i in range(1, len(df_position)):
    prev_size = df_position.iloc[i - 1]['position_size']
    curr_size = df_position.iloc[i]['position_size']
    time = df_position.iloc[i]['time']
    price = df['price'].loc[df['time'] == time].values[0]
    if curr_size > prev_size:
        buy_price_times.append(time)
        buy_prices.append(float(price))
    elif curr_size < prev_size:
        sell_price_times.append(time)
        sell_prices.append(float(price))
 
fig.add_trace(go.Scatter(x=buy_price_times, y=buy_prices, mode='markers', name='Buy Price', marker=dict(color="#0095f8", size=10, symbol='triangle-up')))
fig.add_trace(go.Scatter(x=sell_price_times, y=sell_prices, mode='markers', name='Sell Price', marker=dict(color="#5dff57", size=10, symbol='triangle-down'))) 

fig.update_layout(
    title='Order Book Visualization with Position Information',
    xaxis_title='Time',
    yaxis_title='Price',
    legend_title='Legend',
    template='plotly_white'
)

fig.show()
