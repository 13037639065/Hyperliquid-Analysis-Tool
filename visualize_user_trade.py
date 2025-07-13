import pandas as pd
import argparse
import plotly.graph_objects as go

def get_trade_direction(row, target):
    if row["user1"] == target:
        return 1
    elif row["user2"] == target and row["side"] == "Sell":
        return -1
    return 0

# ---------- CLI ----------
parser = argparse.ArgumentParser()
parser.add_argument("-u", "--address", required=True)
parser.add_argument("-f", "--file", required=True)
args = parser.parse_args()
addr, file_path = args.address, args.file
# --------------------------

# 1) 价格曲线用全量 df_all
df_all = pd.read_csv(file_path)
df_all["time"] = pd.to_datetime(df_all["time"], format="ISO8601")
df_all.set_index("time", inplace=True)
print(f"{addr} 账户成交记录")

# 2) 只要目标地址相关行
df_target = df_all[(df_all["user1"] == addr) | (df_all["user2"] == addr)].copy()
df_target["direction"] = df_target.apply(lambda r: get_trade_direction(r, addr), axis=1)
df_target = df_target[df_target["direction"] != 0]             # 关键行

# 3) 计算 PnL

position = 0.0
avg_price = 0.0
cum_realized_pnl = 0.0

realized_pnl_list = []
unrealized_pnl_list = []
cum_pnl_list = []

for _, row in df_target.iterrows():
    px = row["px"]
    sz = row["sz"]
    dir = row["direction"]  # 1=buy, -1=sell
    if dir == -1:
        print("sdadsasddasdas")

    trade_sz = sz * dir  # 正数代表买入，负数代表卖出

    realized_pnl = 0.0

    # === 开新仓 or 加仓 ===
    if position == 0 or position * trade_sz > 0:
        # 加仓
        total_cost = abs(position) * avg_price + abs(trade_sz) * px
        position += trade_sz
        avg_price = total_cost / abs(position) if position != 0 else 0.0

    # === 减仓 or 翻转仓位 ===
    elif position * trade_sz < 0:
        if abs(trade_sz) <= abs(position):
            # 减仓
            closed_sz = abs(trade_sz)
            pnl = (px - avg_price) * closed_sz if position > 0 else (avg_price - px) * closed_sz
            realized_pnl += pnl
            position += trade_sz  # 减持
            # avg_price 保持不变
        else:
            # 反向翻仓：先平旧仓，再开新仓
            closed_sz = abs(position)
            pnl = (px - avg_price) * closed_sz if position > 0 else (avg_price - px) * closed_sz
            realized_pnl += pnl
            new_sz = trade_sz + position  # 方向翻转后新开仓大小
            avg_price = px
            position = new_sz

    cum_realized_pnl += realized_pnl

    # === 同步计算未实现盈亏 ===
    if position > 0:
        unrealized_pnl = (px - avg_price) * position
    elif position < 0:
        unrealized_pnl = (avg_price - px) * (-position)
    else:
        unrealized_pnl = 0.0

    # === 汇总 ===
    cum_pnl = cum_realized_pnl + unrealized_pnl

    # === 每一笔都存入列表 ===
    realized_pnl_list.append(cum_realized_pnl)
    unrealized_pnl_list.append(unrealized_pnl)
    cum_pnl_list.append(cum_pnl)
    # 打印信息 买入数量 均价 和 当前价格
    print(f"{row['tid']}\t{"buy" if trade_sz > 0 else "sell"}\tp={px:.2f}\ttsz={trade_sz}\tavg={avg_price:.2f}\tpnl={cum_pnl:.2f}\tupnl={unrealized_pnl:.2f}=({px} - {avg_price}) * {position}")


df_target["realized_pnl"] = realized_pnl
df_target["unrealized_pnl"] = unrealized_pnl
df_target["cum_pnl"] = df_target["realized_pnl"] + df_target["unrealized_pnl"]

# 4) 绘图
fig = go.Figure()
fig.add_trace(go.Scatter(x=df_all.index,        y=df_all["px"],        name="Price", mode="lines"))
fig.add_trace(go.Scatter(x=df_target.index,     y=df_target["cum_pnl"], name="Cumulative PnL",
                         mode="lines+markers", yaxis="y2"))
fig.update_layout(title=f"{addr[:10]}...  PnL Analysis",
                  yaxis2=dict(overlaying="y", side="right", title="Cum PnL"))
fig.show()
