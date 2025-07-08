import csv
import json 
import statistics
from collections import defaultdict
 
def analyze_order_spread(csv_file_path):
    """
    分析CSV文件中的买卖挂单价格间距 
    参数:
        csv_file_path: CSV文件路径
    返回:
        包含时间点分析结果的字典 
    """
    results = defaultdict(dict)
    
    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for idx, row in enumerate(reader):
            time = row['time']
            
            # 解析买单和卖单数据 
            try:
                buy_orders = json.loads(row['BUY'].replace("'",  '"'))
                sell_orders = json.loads(row['SELL'].replace("'",  '"'))
            except json.JSONDecodeError as e:
                print(f"第 {idx+1} 行JSON解析错误: {e}")
                continue
                
            # 提取价格并转换为浮点数 
            buy_prices = sorted([float(order['price']) for order in buy_orders], reverse=True)
            sell_prices = sorted([float(order['price']) for order in sell_orders])
            
            # 计算买单价格间距 
            buy_spreads = []
            if len(buy_prices) > 1:
                for i in range(1, len(buy_prices)):
                    spread = buy_prices[i-1] - buy_prices[i]
                    buy_spreads.append(round(spread,  2))
            
            # 计算卖单价格间距 
            sell_spreads = []
            if len(sell_prices) > 1:
                for i in range(1, len(sell_prices)):
                    spread = sell_prices[i] - sell_prices[i-1]
                    sell_spreads.append(round(spread,  2))
            
            # 计算统计信息
            analysis = {
                'buy_prices': buy_prices,
                'sell_prices': sell_prices,
                'buy_spreads': buy_spreads,
                'sell_spreads': sell_spreads,
                'buy_spread_stats': {
                    'count': len(buy_spreads),
                    'min': round(min(buy_spreads), 2) if buy_spreads else 0,
                    'max': round(max(buy_spreads), 2) if buy_spreads else 0,
                    'mean': round(statistics.mean(buy_spreads),  2) if buy_spreads else 0,
                    'median': round(statistics.median(buy_spreads),  2) if buy_spreads else 0,
                    'stdev': round(statistics.stdev(buy_spreads),  2) if len(buy_spreads) > 1 else 0
                } if buy_spreads else {},
                'sell_spread_stats': {
                    'count': len(sell_spreads),
                    'min': round(min(sell_spreads), 2) if sell_spreads else 0,
                    'max': round(max(sell_spreads), 2) if sell_spreads else 0,
                    'mean': round(statistics.mean(sell_spreads),  2) if sell_spreads else 0,
                    'median': round(statistics.median(sell_spreads),  2) if sell_spreads else 0,
                    'stdev': round(statistics.stdev(sell_spreads),  2) if len(sell_spreads) > 1 else 0 
                } if sell_spreads else {},
                'bid_ask_spread': round(sell_prices[0] - buy_prices[0], 2) if buy_prices and sell_prices else 0 
            }
            
            results[time] = analysis
    
    return dict(results)
 
def print_analysis_results(result_dict):
    """格式化打印分析结果"""
    for time, analysis in result_dict.items(): 
        print(f"\n⏰ 时间点: {time}")
        print(f"📉 买单价格 (最高到最低): {', '.join(map(str, analysis['buy_prices']))}")
        print(f"📈 卖单价格 (最低到最高): {', '.join(map(str, analysis['sell_prices']))}")
        
        if analysis['buy_spreads']:
            print(f"\n💰 买单价格间距分析:")
            print(f"  - 间距序列: {analysis['buy_spreads']}")
            stats = analysis['buy_spread_stats']
            print(f"  - 数量: {stats['count']} | 最小值: {stats['min']} | 最大值: {stats['max']}")
            print(f"  - 平均值: {stats['mean']} | 中位数: {stats['median']} | 标准差: {stats['stdev']}")
        
        if analysis['sell_spreads']:
            print(f"\n💸 卖单价格间距分析:")
            print(f"  - 间距序列: {analysis['sell_spreads']}")
            stats = analysis['sell_spread_stats']
            print(f"  - 数量: {stats['count']} | 最小值: {stats['min']} | 最大值: {stats['max']}")
            print(f"  - 平均值: {stats['mean']} | 中位数: {stats['median']} | 标准差: {stats['stdev']}")
        
        if 'bid_ask_spread' in analysis:
            print(f"\n⚖️ 买卖价差 (最佳卖价 - 最佳买价): {analysis['bid_ask_spread']}")
        
        print("-" * 70)
 
# 示例使用
if __name__ == "__main__":

    file_path = "trading_data_cache/orders/BTC_0x654086857e1fad6dcf05cf6695cce51ea3984268_orders.csv" 
    
    # 分析数据并打印结果 
    print("📊 开始分析挂单价格间距...")
    analysis_results = analyze_order_spread(file_path)
    print_analysis_results(analysis_results)
    print("✅ 分析完成！")