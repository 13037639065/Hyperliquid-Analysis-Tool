# 使用 argparse 参数为代币和 用户地址。
# 读取交易数据，并生该用户买入卖出记录。图形化展示出来
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import os
import glob
import re
from datetime import datetime, timedelta

def find_csv_files(symbol, search_path, days):
    # 使用glob匹配所有可能符合条件的文件
    pattern = os.path.join(search_path,  f'*{symbol}_trade_data.csv') 
    files = glob.glob(pattern) 

    if not files:
        return []

    current_time = datetime.now() 
    start_time = current_time - timedelta(days=days)

    matched_files = []
    # 构建正则表达式模式：整个文件名必须符合：时间戳_代币符号_trade_data.csv 
    # 时间戳格式：2025_06_21T19_08_42
    regex_pattern = re.compile(r'^(\d{4}_\d{1,2}_\d{1,2}T\d{1,2}_\d{1,2}_\d{1,2})_'  + re.escape(symbol)  + r'_trade_data\.csv$')

    for file_path in files:
        file_name = os.path.basename(file_path) 
        match = regex_pattern.match(file_name) 
        if match:
            timestamp_str = match.group(1) 
            try:
                # 转换时间字符串为datetime对象
                file_time = datetime.strptime(timestamp_str,  '%Y_%m_%dT%H_%M_%S')
                # 检查时间是否在指定区间内
                if start_time <= file_time <= current_time:
                    matched_files.append(file_path) 
            except ValueError:
                # 如果时间格式不对，跳过
                continue

    return matched_files
def analyze_user_trades(token, path, user_address, days=7):

    relevant_files = find_csv_files(token, path, days)
   
    print(f"找到 {len(relevant_files)} 个相关的文件 \n{relevant_files}")
    # 读取CSV文件，按照 user 和时间范围过滤
    start_time  = datetime.now() - timedelta(days=days)
    dfs = []
    for file in relevant_files:
        df = pd.read_csv(file)
        # 转换时间列
        df['time'] = pd.to_datetime(df['time'], format='ISO8601')
        # 筛选在时间范围内的交易
        df = df[(df['time'] >= start_time) & ((df['user1'] == user_address) | (df['user2'] == user_address))]
        dfs.append(df)
    
  
    return dfs

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze user trading data')
    parser.add_argument('--symbal', '-s', type=str, required=True, help='Token name (e.g., UNI)')
    parser.add_argument('--user', '-u', type=str, required=True, help='User address')
    parser.add_argument('--days', '-d', type=int, default=7, help='Number of days to analyze (default: 7)')
    parser.add_argument('--csv_path', '-c', type=str, default="./trading_data_cache/fills/", help='CSV path')
    args = parser.parse_args()
    
    result_df = analyze_user_trades(args.symbal, args.csv_path, args.user, args.days)
    
    if result_df is not None:
        print(f"Latest position for user {args.user}: {result_df.iloc[-1]['cumulative_position']:.4f} {args.token}")
        print(f"Position value: ${result_df.iloc[-1]['position_value']:.2f}")
