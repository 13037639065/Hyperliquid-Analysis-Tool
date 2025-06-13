"""
Hyperliquid交易分析工具 v1.0
功能：获取用户交易记录、币安K线数据，绘制交易点位并计算盈亏 
依赖库：hyperliquid, binance, mplfinance, pandas 
"""
 
from hyperliquid.info  import Info
from hyperliquid.utils  import constants 
import json
import pandas as pd 
from binance.client  import Client
import mplfinance as mpf
import datetime 
import os
import argparse 
import time 
import matplotlib.pyplot  as plt 
import matplotlib.dates  as mdates 
import numpy as np
from dateutil.relativedelta  import relativedelta
 
# 缓存目录配置 
CACHE_DIR = "trading_data_cache"
os.makedirs(CACHE_DIR,  exist_ok=True)

def get_hyperliquid_trades(address, symbol):
    """获取并缓存Hyperliquid交易记录"""
    cache_file = os.path.join(CACHE_DIR,  f"{address}_{symbol.upper()}_trades.json") 
    
    # 检查缓存 
    if os.path.exists(cache_file): 
        print(f"从缓存加载交易数据: {cache_file}")
        with open(cache_file, 'r') as f:
            return json.load(f) 
    
    print(f"从Hyperliquid API获取数据: {address} - {symbol}")
    info = Info(constants.MAINNET_API_URL, skip_ws=True)
    all_trades = info.user_fills(address)
    
    # 过滤指定代币
    trades = [trade for trade in all_trades if trade['coin'].upper() == symbol.upper()] 
    
    # 缓存数据 
    with open(cache_file, 'w') as f:
        json.dump(trades,  f, indent=2)
    
    return trades
 
def get_binance_klines(symbol, interval, time_range):
    """获取并缓存币安K线数据"""
    cache_file = os.path.join(CACHE_DIR,  f"{symbol.upper()}_{interval}_{time_range}_klines.csv") 
    
    # 检查缓存 
    if os.path.exists(cache_file): 
        print(f"从缓存加载K线数据: {cache_file}")
        return pd.read_csv(cache_file,  index_col=0, parse_dates=True)
    
    print(f"从币安API获取数据: {symbol} {interval} {time_range}")
    client = Client()
    
    # 解析时间范围 
    now = datetime.datetime.now() 
    if time_range.endswith('d'): 
        days = int(time_range[:-1])
        start_date = now - datetime.timedelta(days=days) 
    elif time_range.endswith('w'): 
        weeks = int(time_range[:-1])
        start_date = now - datetime.timedelta(weeks=weeks) 
    elif time_range.endswith('m'): 
        months = int(time_range[:-1])
        start_date = now - relativedelta(months=months)
    else:
        raise ValueError("时间范围格式错误 (示例: 30d, 3m, 1y)")
    
    # 获取K线数据 
    klines = client.get_historical_klines( 
        symbol=symbol + "USDT",
        interval=interval,
        start_str=start_date.strftime("%d  %b, %Y"),
        end_str=now.strftime("%d  %b, %Y")
    )
    
    # 转换为DataFrame 
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'trades',
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])
    
    # 数据处理 
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')  # 保留 datetime 类型
    df.set_index('timestamp', inplace=True)
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, axis=1)
    df = df[['open', 'high', 'low', 'close', 'volume']]
    
    # 缓存数据 
    df.to_csv(cache_file) 
    
    return df
 
def process_trades(trades, symbol):
    """处理交易数据并计算盈亏"""
    open_long_events = []
    close_short_events = []
    close_long_events = []
    open_short_events = []
    positions = []
    realized_pnl = 0
    total_buy_qty = 0 
    total_sell_qty = 0 

    for trade in trades:
        if trade['coin'].upper() != symbol.upper(): 
            continue 
            
        timestamp = datetime.datetime.fromtimestamp(int(trade['time']) / 1000.)
        price = float(trade['px'])
        qty = float(trade['sz'])

        # Open Long
        if trade['dir'] == 'Open Long':
            open_long_events.append((timestamp, price, qty))
            positions.append({'timestamp': timestamp, 'price': price, 'qty': qty})
            total_buy_qty += qty

        # Close Short
        elif trade['dir'] == 'Close Short':
            close_short_events.append((timestamp, price, qty))
            total_buy_qty += qty
            
            remaining_qty = qty
            while remaining_qty > 0 and positions:
                position = positions[0]
                if position['qty'] > remaining_qty:
                    realized_pnl += remaining_qty * (position['price'] - price)
                    position['qty'] -= remaining_qty
                    remaining_qty = 0
                else:
                    realized_pnl += position['qty'] * (position['price'] - price)
                    remaining_qty -= position['qty']
                    positions.pop(0)

        # Close Long
        elif trade['dir'] == 'Close Long':
            close_long_events.append((timestamp, price, qty))
            total_sell_qty += qty
            
            remaining_qty = qty
            while remaining_qty > 0 and positions:
                position = positions[0]
                if position['qty'] > remaining_qty:
                    realized_pnl += remaining_qty * (price - position['price'])
                    position['qty'] -= remaining_qty
                    remaining_qty = 0
                else:
                    realized_pnl += position['qty'] * (price - position['price'])
                    remaining_qty -= position['qty']
                    positions.pop(0)

        # Open Short
        elif trade['dir'] == 'Open Short':
            open_short_events.append((timestamp, price, qty))
            total_sell_qty += qty
            positions.append({
                'timestamp': timestamp,
                'price': price,
                'qty': qty,
                'position_type': 'short'
            })

    # 计算未实现盈亏
    unrealized_pnl = 0 
    for position in positions:
        if position.get('position_type') == 'short':
            unrealized_pnl += position['qty'] * (position['price'] - df['close'].iloc[-1])
        else:
            unrealized_pnl += position['qty'] * (df['close'].iloc[-1] - position['price'])

    total_pnl = realized_pnl + unrealized_pnl

    # 构建交易标记 DataFrame
    open_long_df = pd.DataFrame(open_long_events, columns=['timestamp', 'price', 'qty']).set_index('timestamp')
    close_short_df = pd.DataFrame(close_short_events, columns=['timestamp', 'price', 'qty']).set_index('timestamp')
    close_long_df = pd.DataFrame(close_long_events, columns=['timestamp', 'price', 'qty']).set_index('timestamp')
    open_short_df = pd.DataFrame(open_short_events, columns=['timestamp', 'price', 'qty']).set_index('timestamp')

    return {
        'open_long_events': open_long_df,
        'close_short_events': close_short_df,
        'close_long_events': close_long_df,
        'open_short_events': open_short_df,
        'realized_pnl': realized_pnl,
        'unrealized_pnl': unrealized_pnl,
        'total_pnl': total_pnl,
        'positions': positions,
        'total_buy_qty': total_buy_qty,
        'total_sell_qty': total_sell_qty 
    }
 
def plot_trading_data(df, trade_data, args):
    """绘制K线图并标记交易点位"""
    plt.style.use('dark_background') 
    
    # Ensure both dataframes have the same timezone
    df = df.copy()
    
    # Make sure all timestamps are in UTC and properly localized
    df.index = pd.to_datetime(df.index)
    print(df.index)
    
    fig, axes = mpf.plot( 
        df,
        type='candle',
        volume=True,
        title=f"\n{args.symbol} analysis | time range: {args.time_range}  | interval: {args.interval}", 
        style='charles',
        ylabel='price (USDT)',
        figratio=(14, 7),
        figscale=1.2,
        returnfig=True,
        xrotation=0  # Keep default rotation to preserve date formatting
    )
    
    ax1 = axes[0]
    
    # 标记 Open Long（绿色三角）
    # if not trade_data['open_long_events'].empty:
    #     trade_data['open_long_events'].index = pd.to_datetime(trade_data['open_long_events'].index)
    #     ax1.scatter(
    #         trade_data['open_long_events'].index,
    #         trade_data['open_long_events']['price'],
    #         marker='^',
    #         color='#00FF7F',  # 绿色
    #         s=120,
    #         edgecolors='white',
    #         zorder=10,
    #         label='Buy (Open Long)'
    #     )

    # 标记 Close Short（橙色三角）
    # if not trade_data['close_short_events'].empty:
    #     print(trade_data['close_short_events'].index[0])
    #     ax1.scatter(
    #         trade_data['close_short_events'].index,
    #         trade_data['close_short_events']['price'],
    #         marker='^',
    #         color='#FFA500',  # 橙色
    #         s=120,
    #         edgecolors='white',
    #         zorder=10,
    #         label='Buy to Close Short'
    #     )
    test_time = pd.to_datetime('2023-05-05 09:00:00')
    ax1.axvline(test_time, color='red', linestyle='--', linewidth=1, zorder=20)

    # # 标记 Close Long（红色倒三角）
    if not trade_data['close_long_events'].empty:
        trade_data['close_long_events'].index = pd.to_datetime(trade_data['close_long_events'].index, format='%Y-%m-%d %H:%M:%S')
        print("xxxxxxxxxx")
        print(trade_data['close_long_events'].index)
        ax1.scatter(
            trade_data['close_long_events'].index,
            trade_data['close_long_events']['price'],
            marker='v',
            color='#FF6347',  # 红色
            s=120,
            edgecolors='white',
            zorder=10,
            label='Sell to Close Long'
        )

    # # 标记 Open Short（蓝色倒三角）
    # if not trade_data['open_short_events'].empty:
    #     ax1.scatter(
    #         trade_data['open_short_events'].index,
    #         trade_data['open_short_events']['price'],
    #         marker='v',
    #         color='#1E90FF',  # 蓝色
    #         s=120,
    #         edgecolors='white',
    #         zorder=10,
    #         label='Sell (Open Short)'
    #     )
    
    # 添加图例
    ax1.legend(loc='best') 
    
    # 添加盈亏信息
    pnl_text = (
        f"Trade Statistics:\n"
        f"Open Long Count: {len(trade_data['open_long_events'])}\n"
        f"Close Short Count: {len(trade_data['close_short_events'])}\n"
        f"Close Long Count: {len(trade_data['close_long_events'])}\n"
        f"Open Short Count: {len(trade_data['open_short_events'])}\n"
        f"Total Buy Quantity: {trade_data['total_buy_qty']:.4f} {args.symbol}\n"
        f"Total Sell Quantity: {trade_data['total_sell_qty']:.4f} {args.symbol}\n"
        f"Realized P&L: ${trade_data['realized_pnl']:.2f}\n"
        f"Unrealized P&L: ${trade_data['unrealized_pnl']:.2f}\n"
        f"Total P&L: ${trade_data['total_pnl']:.2f}"
    )
    
    ax1.text( 
        0.02, 0.98, pnl_text,
        transform=ax1.transAxes, 
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='#1f1f1f', alpha=0.9, edgecolor='#444')
    )
    
    # 格式化日期
    fig.autofmt_xdate() 
    
    # 添加网格
    ax1.grid(True,  linestyle='--', alpha=0.3)
    
    # 保存图表 
    output_file = f"./{CACHE_DIR}/{args.address[:6]}_{args.symbol}_{args.interval}_{args.time_range}_analysis.png" 
    plt.savefig(output_file,  dpi=150, bbox_inches='tight')
    print(f"\n图表已保存至: {output_file}")
    
    plt.show()
 
if __name__ == "__main__":
    # 解析命令行参数 
    parser = argparse.ArgumentParser(description='Hyperliquid交易分析工具')
    parser.add_argument('address',  type=str, help='Hyperliquid用户地址')
    parser.add_argument('symbol',  type=str, help='代币符号 (如BTC)')
    parser.add_argument('interval',  type=str, help='K线时间间隔 (如1h, 4h, 1d)')
    parser.add_argument('time_range',  type=str, help='时间范围 (如7d, 30d, 3m)')
    
    args = parser.parse_args() 
    
    # 记录执行时间
    start_time = time.time() 
    
    print("\n" + "="*60)
    print(f"Hyperliquid 交易分析工具启动")
    print(f"时间: {datetime.datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}")
    print("="*60)
    print(f"地址: {args.address}") 
    print(f"代币: {args.symbol}") 
    print(f"K线间隔: {args.interval}") 
    print(f"时间范围: {args.time_range}") 
    print("="*60 + "\n")
    
    # 获取数据
    trades = get_hyperliquid_trades(args.address,  args.symbol) 
    df = get_binance_klines(args.symbol,  args.interval,  args.time_range) 
    
    if not trades:
        print(f"\n⚠️ 警告: 未找到 {args.symbol}  的交易记录")
        exit()
    
    # 处理交易数据 
    trade_data = process_trades(trades, args.symbol) 
    
    # 打印摘要 
    print("\n交易摘要:")
    print(f"• 找到 {len(trades)} 条交易记录")
    print(f"• 开多仓 (Open Long) 次数: {len(trade_data['open_long_events'])}")
    print(f"• 平空仓 (Close Short) 次数: {len(trade_data['close_short_events'])}")
    print(f"• 平多仓 (Close Long) 次数: {len(trade_data['close_long_events'])}")
    print(f"• 开空仓 (Open Short) 次数: {len(trade_data['open_short_events'])}")
    print(f"• 总买入量: {trade_data['total_buy_qty']:.6f} {args.symbol}") 
    print(f"• 总卖出量: {trade_data['total_sell_qty']:.6f} {args.symbol}") 
    print(f"• 当前持仓: {len(trade_data['positions'])} 个仓位")
    print(f"• 已实现盈亏: ${trade_data['realized_pnl']:.2f}")
    print(f"• 未实现盈亏: ${trade_data['unrealized_pnl']:.2f}")
    print(f"• 总计盈亏: ${trade_data['total_pnl']:.2f}")
    
    # 绘制图表 
    print("\n生成交易分析图表...")
    plot_trading_data(df, trade_data, args)
    
    # 性能统计 
    elapsed = time.time()  - start_time 
    print(f"\n✅ 分析完成! 耗时: {elapsed:.2f}秒")
    print("="*60)