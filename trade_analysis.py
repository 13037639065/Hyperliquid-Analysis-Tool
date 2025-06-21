import pandas as pd
import argparse
import os
from datetime import datetime

def find_csv_files(symbol, search_path, buy_start_time, buy_end_time, sell_start_time, sell_end_time):
    """根据代币名称和时间区间查找对应的CSV文件"""
    # 获取目录下所有CSV文件
    csv_files = [f for f in os.listdir(search_path) if f.endswith('.csv') and symbol in f]
    # csv_files 按照时间排序
    csv_files.sort(key=lambda x: datetime.strptime(x[0:19], '%Y_%m_%dT%H_%M_%S'))
    
    matched_files = []
    
    # 文件名格式: 2025_06_16T02_07_56_ETH_trade_data.csv
    for file in csv_files:
        # 提取文件名中的时间信息
        file_time_str = file[0:19]  # 时间信息在文件名的前三个部分
        file_time = datetime.strptime(file_time_str, '%Y_%m_%dT%H_%M_%S')
        
        # 计算文件的结束时间（下一个文件的开始时间或当前时间）
        file_end_time = None
        if csv_files.index(file) + 1 < len(csv_files):
            next_file = csv_files[csv_files.index(file) + 1]
            next_file_time_str = next_file[0:19]
            file_end_time = datetime.strptime(next_file_time_str, '%Y_%m_%dT%H_%M_%S')
        else:
            file_end_time = datetime.now()
        buy_start = datetime.strptime(buy_start_time, '%Y-%m-%dT%H:%M:%S')
        buy_end = datetime.strptime(buy_end_time, '%Y-%m-%dT%H:%M:%S')
        sell_start = datetime.strptime(sell_start_time, '%Y-%m-%dT%H:%M:%S')
        sell_end = datetime.strptime(sell_end_time, '%Y-%m-%dT%H:%M:%S')
        if (buy_start <= file_time <= buy_end) or (sell_start <= file_time <= sell_end) or \
           (file_time <= buy_start < file_end_time) or (file_time <= sell_start < file_end_time):
            matched_files.append(os.path.join(search_path, file))
    
    return matched_files

def find_buy_sell_addresses(csv_files, buy_start_time, buy_end_time, sell_start_time, sell_end_time, min_trade_value=0.0):
    # 加载数据
    df = pd.concat([pd.read_csv(file) for file in csv_files])

    # 转换时间列
    df['time'] = pd.to_datetime(df['time'], format='ISO8601')

    # 筛选买入和卖出的交易
    buy_trades = df[(df['time'] >= buy_start_time) & (df['time'] <= buy_end_time) & (df['side'] == 'Buy')]
    sell_trades = df[(df['time'] >= sell_start_time) & (df['time'] <= sell_end_time) & (df['side'] == 'Sell')]

    # 过滤掉交易价值过小的订单
    if min_trade_value > 0:
        buy_trades = buy_trades[(buy_trades['px'].astype(float) * buy_trades['sz'].astype(float)) >= min_trade_value]
        sell_trades = sell_trades[(sell_trades['px'].astype(float) * sell_trades['sz'].astype(float)) >= min_trade_value]

    # 获取所有买入和卖出地址
    # 买入地址：在买入时间段内作为买方 (Buy交易中的user1)
    buy_addresses = set(buy_trades['user1'].unique())
    
    # 卖出地址：在卖出时间段内作为卖方 (Sell交易中的user1)
    sell_addresses = set(sell_trades['user1'].unique())

    # 找出在两个时间段内有交易的地址
    common_addresses = list(buy_addresses.intersection(sell_addresses))

    # 初始化结果列表
    results = []

    for address in common_addresses:
        # 买入信息 - 该地址作为买方 (Buy交易)
        buy_info = buy_trades[buy_trades['user1'] == address]
        buy_avg_price = (buy_info['px'].astype(float) * buy_info['sz'].astype(float)).sum() / buy_info['sz'].astype(float).sum()
        buy_quantity = buy_info['sz'].astype(float).sum()
        
        # 卖出信息 - 该地址作为卖方 (Sell交易)
        sell_info = sell_trades[sell_trades['user1'] == address]
        sell_avg_price = (sell_info['px'].astype(float) * sell_info['sz'].astype(float)).sum() / sell_info['sz'].astype(float).sum()
        sell_quantity = sell_info['sz'].astype(float).sum()
        
        # 盈亏计算
        profit = (sell_avg_price - buy_avg_price) * min(buy_quantity, sell_quantity)
        
        results.append({
            'address': address,
            'buy_avg_price': buy_avg_price,
            'sell_avg_price': sell_avg_price,
            'buy_quantity': buy_quantity,
            'sell_quantity': sell_quantity,
            'profit': profit
        })

    return pd.DataFrame(results)

def parse_args():
    parser = argparse.ArgumentParser(description='交易数据分析工具')
    
    # 原来的csv_file参数替换为以下两个参数
    parser.add_argument('--symbol', type=str, default="BTC", help='代币名称，例如BTC')
    parser.add_argument('--dir', type=str, default="./trading_data_cache/fills", help='数据文件目录')
    parser.add_argument('--buy_start_time', type=str, required=True, help='买入开始时间，格式为YYYY-MM-DDTHH:MM:SS。')
    parser.add_argument('--buy_end_time', type=str, required=True, help='买入结束时间，格式为YYYY-MM-DDTHH:MM:SS。')
    parser.add_argument('--sell_start_time', type=str, required=True, help='卖出开始时间，格式为YYYY-MM-DDTHH:MM:SS。')
    parser.add_argument('--sell_end_time', type=str, required=True, help='卖出结束时间，格式为YYYY-MM-DDTHH:MM:SS。')
    parser.add_argument('--min_trade_value', type=float, default=0.0, help='过滤掉交易价值（价格 * 数量）小于该值的订单，默认为 0，不进行过滤。')
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    # 根据代币名称和时间区间查找CSV文件
    csv_files = find_csv_files(args.symbol, args.dir, args.buy_start_time, args.buy_end_time, args.sell_start_time, args.sell_end_time)
    
    if not csv_files:
        print("没有找到符合条件的CSV文件。")
        return
    
    # 处理找到的CSV文件
    print(f'处理文件: \n{"\n".join(csv_files)}')
    result_df = find_buy_sell_addresses(csv_files, args.buy_start_time, args.buy_end_time, args.sell_start_time, args.sell_end_time, args.min_trade_value)
    # result_df 按照 profit 从大到小进行排序
    result_df = result_df.sort_values(by='profit', ascending=False)
    
    with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', None):
        print(result_df)

if __name__ == "__main__":
    main()
