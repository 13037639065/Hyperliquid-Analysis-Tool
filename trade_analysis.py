import pandas as pd
import argparse
def find_buy_sell_addresses(csv_file, buy_start_time, buy_end_time, sell_start_time, sell_end_time, min_trade_value=0.0):
    # 加载数据
    df = pd.read_csv(csv_file)

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='分析CSV文件中的交易数据。')
    parser.add_argument('--csv_file', type=str, required=True, help='CSV文件路径。')
    parser.add_argument('--buy_start_time', type=str, required=True, help='买入开始时间，格式为YYYY-MM-DDTHH:MM:SS。')
    parser.add_argument('--buy_end_time', type=str, required=True, help='买入结束时间，格式为YYYY-MM-DDTHH:MM:SS。')
    parser.add_argument('--sell_start_time', type=str, required=True, help='卖出开始时间，格式为YYYY-MM-DDTHH:MM:SS。')
    parser.add_argument('--sell_end_time', type=str, required=True, help='卖出结束时间，格式为YYYY-MM-DDTHH:MM:SS。')
    parser.add_argument('--min_trade_value', type=float, default=0.0, help='过滤掉交易价值（价格 * 数量）小于该值的订单，默认为 0，不进行过滤。')

    args = parser.parse_args()

    csv_file = args.csv_file
    buy_start_time = pd.to_datetime(args.buy_start_time)
    buy_end_time = pd.to_datetime(args.buy_end_time)
    sell_start_time = pd.to_datetime(args.sell_start_time)
    sell_end_time = pd.to_datetime(args.sell_end_time)

    result_df = find_buy_sell_addresses(csv_file, buy_start_time, buy_end_time, sell_start_time, sell_end_time)
    # result_df 按照 profit 从大到小进行排序
    result_df = result_df.sort_values(by='profit', ascending=False)

    with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', None):
        print(result_df)