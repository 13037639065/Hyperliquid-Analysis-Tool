import argparse
import time
import csv
import pandas as pd
from hyperliquid.info import Info
from hyperliquid.utils import constants

SYMBOLS = ['BTC', 'ETH', 'SOL']
DATA_DIR = "trading_data_cache"
# Initialize info object
info = Info(constants.MAINNET_API_URL, skip_ws=False)

def monitor_positions(symbols, addresses):
    """Monitor positions for specified token and detect changes"""
    while True:
        # Check for each address
        # users_positions
        users_positions = {}
        
        for address in addresses:
            # Get user's fills and positions
            positions = info.user_state(address)
            users_positions[address] = positions
    
        results = []
        row = []
        row.append("Address")
        row += symbols
        results.append(row)

        # 每一行对应一个地址
        for address in addresses:
            row = []
            row.append(address)
            for symbol in symbols:
                # 获取该地址的仓位信息
                positions = users_positions[address]
                # 查找当前 token 的仓位
                position_found = next((pos for pos in positions['assetPositions'] if pos['position']['coin'] == symbol), None)
                if position_found:
                    szi = float(position_found['position']['szi'])  # 假设 size 表示持仓比例
                    entryPx = float(position_found['position']['entryPx'])
                    position_ratio = (szi, entryPx)
                else:
                    position_ratio = 0.0
                row.append(position_ratio)
            results.append(row)

        # 打印表格
        print("===============================================================================")
        date_time_str = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
        print(f"position: {date_time_str}")
        with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', None):
            print(pd.DataFrame(results))

        time.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='实时监控Hyperliquid用户持仓')
    parser.add_argument('--file', '-f', type=str, default='./trading_data_cache/result.txt', help='要监控的账户地址文件')
    args = parser.parse_args()
    print(f"will read file {args.file}")
    with open(args.file, 'r') as f:
        addresses = [line.strip() for line in f.readlines()]
    
    print(f"开始实时监控 {addresses} {SYMBOLS} 持仓...")
    monitor_positions(SYMBOLS, addresses)