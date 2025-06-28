import argparse
import time
import pandas as pd
from hyperliquid.info import Info
from hyperliquid.utils import constants
import threading
SYMBOLS = ['BTC', 'ETH', 'SOL']


def difference(last, now):
    if last is None:
        return
    
    # 从results中提取地址和对应的索引
    address_to_index = {row[0]: idx for idx, row in enumerate(last.values.tolist()) if idx > 0}
    
    # 遍历当前结果中的每一行（每个地址）
    for i, row in now.iterrows():
        if i == 0:  # 跳过标题行
            continue
        
        address = row[0]
        if address not in address_to_index:
            print(f"New address detected: {address}")
            continue
        
        # 获取上一次的索引
        last_idx = address_to_index[address]
        
        for j in range(1, len(row)):
            current_pos = now.iloc[i, j] if isinstance(now.iloc[i, j], tuple) else (0.0, 0.0)
            previous_pos = last.iloc[last_idx, j] if isinstance(last.iloc[last_idx, j], tuple) else (0.0, 0.0)
            
            current_size, current_entry, _ = current_pos
            previous_size, previous_entry, _ = previous_pos
            
            # 检测操作类型
            diff = round(abs(current_size - previous_size), 4)
            if current_size == previous_size:
                operation = ""
            elif previous_size != 0 and current_size == 0.0:
                operation = "平仓🔴"
            elif previous_size == 0.0 and current_size != 0.0:
                operation = "开仓🟢"
            elif (previous_size > 0 and current_size < 0) or (previous_size < 0 and current_size > 0):
                operation = "反手🟡"
            else:
                if abs(current_size) > abs(previous_size):
                    operation = f"⏫{diff}"
                else:
                    operation = f"⏬{diff}"

            
            now.iat[i, j] = (current_size, current_entry, operation)

def monitor_positions(symbols, addresses):
    """Monitor positions for specified token and detect changes"""

    last = None
    info = Info(constants.MAINNET_API_URL, skip_ws=True)
    while True:
        # Check for each address
        # users_positions
        users_positions = {}
        
        try:
            for address in addresses:
                # Get user's fills and positions
                positions = info.user_state(address)
                users_positions[address] = positions
        except Exception as e:
            print(f"Error: {e}")
            # 网络错误的图标
            print("network error! ⛔")
            continue
    
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
                    position_ratio = (szi, entryPx, "unknown")
                else:
                    position_ratio = (0, 0, "空仓")
                row.append(position_ratio)
            results.append(row)

        # 打印表格
        print("===============================================================================")
        date_time_str = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
        print(f"position: {date_time_str}")
        
        df_result = pd.DataFrame(results)
        difference(last, df_result)
        with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', None):
            print(df_result)

        last = df_result

        time.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='实时监控Hyperliquid用户持仓')
    parser.add_argument('--file', '-f', type=str, default='./trading_data_cache/result.txt', help='要监控的账户地址文件')
    args = parser.parse_args()
    print(f"will read file {args.file}")
    with open(args.file, 'r') as f:
        addresses = [line.strip() for line in f.readlines()]
    
    print(f"开始实时监控 {addresses} {SYMBOLS} 持仓...")
    try:
        monitor_positions(SYMBOLS, addresses)
    except KeyboardInterrupt:
        print("用户退出")
