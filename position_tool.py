import re
import numpy as np
import argparse
import glob

def extract_first_float(text):
    """从字符串中提取第一个浮点数"""
    pattern = r'[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?'
    match = re.search(pattern,  text)
    return float(match.group())  if match else 0
def parse_position_data(file_paths = []):
    result = {}
    for file in file_paths:
        with open(file, 'r', encoding='utf-8') as file:
            for line_number, line in enumerate(file):
                sp =line.split()
                if len(sp) < 5:
                    continue
                #sp 是地址0x123 类型
                if not sp[1].startswith('0x'):
                    continue

                addr = sp[1]
                btc = extract_first_float(sp[2])
                eth =extract_first_float(sp[3]) if sp[2] == "0.0" else extract_first_float(sp[4])
                sol = 0 if sp[-1] == '0.0' else extract_first_float(sp[-2])


                if not result.get(addr):
                    result[addr] = {
                        "BTC": [btc],
                        "ETH": [eth],
                        "SOL": [sol]
                    }
                else:
                    # append data
                    result[addr]["BTC"].append(btc)
                    result[addr]["ETH"].append(eth)
                    result[addr]["SOL"].append(sol)
            
    return result 



def calculate_max_positions(addr, sybmol, results):
    data = np.array(results[addr][sybmol])
    print(f"用户拒 {addr} {sybmol} 的历史持仓情况")
    print(f"最大持仓: {np.max(data)}")
    print(f"最小持仓: {np.min(data)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="解析并统计地址的仓位信息")
    parser.add_argument('-u', '--user', required=True, help='要查询的用户地址')

    args = parser.parse_args()
    
    # 将 ls trading_data_cache/p*.txt 列出来
    file_paths = glob.glob("trading_data_cache/p*.txt")
    position_data = parse_position_data(file_paths)
    
    max_positions = calculate_max_positions(args.user, "BTC", position_data)
    max_positions = calculate_max_positions(args.user, "ETH", position_data)
    max_positions = calculate_max_positions(args.user, "SOL", position_data)