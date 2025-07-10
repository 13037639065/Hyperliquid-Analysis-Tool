import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 读取CSV文件
df = pd.read_csv("./trading_data_cache/fills/2025_06_14T15_59_02_BTC_trade_data.csv")  # 请根据实际文件路径修改
selected_user = '0x654086857e1fad6dcf05cf6695cce51ea3984268'  # 你可以选择 'user1' 或 'user2' 作为过滤条件

# 转换时间格式
df['time'] = pd.to_datetime(df['time'], format="ISO8601")

all_orders = df[(df['user1'] == selected_user| df['user2'] == selected_user)]
buy_orders = all_orders[(all_orders["user1"] == selected_user)].copy()
sell_orders = all_orders[(all_orders["user2"] == selected_user)].copy()

# 创建上下结构的子图
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)

# 图1：买卖价格位置时间图
fig.add_trace(go.Scatter(
    x=buy_orders['time'],
    y=buy_orders['px'],
    mode='markers',
    name='Buy Orders',
    marker=dict(color='blue', size=8),
), row=1, col=1)

fig.add_trace(go.Scatter(
    x=sell_orders['time'],
    y=sell_orders['px'],
    mode='markers',
    name='Sell Orders',
    marker=dict(color='red', size=8),
), row=1, col=1)

fig.update_layout(
    title=f"Buy and Sell Orders & Cumulative Profit/Loss for {selected_user}",
    showlegend=True,
    template="plotly_dark"
)

# 盈亏计算
profit_loss_data = []
total_profit_loss = 0
for index, buy in all_orders.iterrows():
    pass
    # all_orders user1 == selected_user 是买
    # user2 == selected_user 是卖

profit_loss_df = pd.DataFrame(profit_loss_data)

# 图2：累计盈亏曲线
fig.add_trace(go.Scatter(
    x=profit_loss_df['time'],
    y=profit_loss_df['profit_loss'],
    mode='lines+markers',
    name='Cumulative Profit/Loss',
    line=dict(color='green', width=2),
), row=2, col=1)

# 更新坐标轴标签
fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
fig.update_yaxes(title_text="Cumulative Profit/Loss (USD)", row=2, col=1)
fig.update_xaxes(title_text="Time", row=2, col=1)

# 显示图表
fig.show()

# 输出总盈亏
print(f"总盈亏: {total_profit_loss:.2f} USD")