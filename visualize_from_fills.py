import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="Visualize fills from Hyperliquid")
    parser.add_argument('--coin', '-c', type=str, default='BTC', help='Coin to filter (default: BTC)')
    parser.add_argument('--file', '-f', required=True, type=str, help='Path to CSV file')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    # 读取 CSV 文件
    df = pd.read_csv(args.file)

    # 过滤 coin
    df = df[df['coin'] == args.coin]

    # 把时间戳列（毫秒）转成可读时间
    df['datetime'] = pd.to_datetime(df['time'], unit='ms', utc=True).dt.tz_convert('Asia/Shanghai')


    # 把数值字符串转 float
    num_cols = ['px', 'sz', 'closedPnl', 'fee', 'startPosition']
    df[num_cols] = df[num_cols].astype(float)

    # df['position']  = float(df['startPosition']) + float(df['sz']) * (1 if df['side'] == 'B' else -1)
    df['position'] = df['startPosition'] + df['sz'] * np.where(df['side'] == 'B', 1, -1)
    df['realized']  = df['closedPnl'].cumsum()              # 已实现盈亏曲线

    # —— 逐行跟踪平均持仓成本，并算未实现盈亏 ——
    pos = avg_entry = 0.0
    unrealized = []
    # 假设 df 包含 ['px', 'sz', 'side', 'dir', 'closedPnl']
    pos = 0
    avg_entry = 0.0
    unrealized = []
    realized_pnl = 0.0
    import numpy as np

    pos = 0.0
    avg_entry = 0.0
    unrealized = []
    realized_pnl = 0.0

    df['total_pnl'] = df['closedPnl'].cumsum()
    # ------------- 3. 画图 ---------------------------
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        row_heights=[0.4, 0.25, 0.35], vertical_spacing=0.02,
        subplot_titles=('Price', 'Position', 'Total PnL')
    )

    # 价格线
    fig.add_trace(go.Scatter(
        x=df['datetime'], y=df['px'],
        mode='lines+markers', name='Price'
    ), row=1, col=1)

    # 持仓柱
    fig.add_trace(go.Scatter(
        x=df['datetime'], y=df['position'],
        name='Position'
    ), row=2, col=1)

    # 总盈亏线
    fig.add_trace(go.Scatter(
        # y=unrealized
        x=df['datetime'], y=df['total_pnl'],
        mode='lines+markers', name='Total PnL'
    ), row=3, col=1)

    fig.add_trace(go.Scatter(
        # y=unrealized
        x=df['datetime'], y=df['closedPnl'],
        mode='lines+markers', name='closedPnl'
    ), row=3, col=1)

    fig.update_layout(
        height=850,
        title_text='Order/Position/PnL Dashboard',
        xaxis3_title='Datetime'
    )
    fig.show()
