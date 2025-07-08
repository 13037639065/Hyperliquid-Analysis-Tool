import argparse
from hyperliquid.info import Info
from hyperliquid.utils import constants
import csv
from datetime import datetime
import time
import os
import json
from feishu_msg import send_feishu_text

INFO = Info(constants.MAINNET_API_URL, skip_ws=True)
def get_open_order_position(address, coins):
    while True:
        try:
            orders = INFO.open_orders(address)
            state = INFO.user_state(address)
            filtered_orders = [order for order in orders if order['coin'] in coins]
            filtered_positions = [position for position in state['assetPositions'] if position['position']['coin'] in coins]
            return filtered_orders, filtered_positions
        except Exception as e:
            print(f"Error fetching orders: {e}")
            send_feishu_text("Hyperliquid 网络接口错误，请检查！", f"时间: {datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}\n" +str(e))
            time.sleep(10)

def save_to_csv(user, orders, positions, base_path="./trading_data_cache/orders"):
    if not orders:
        print("No orders found.")
        return
    
    # 创建目录（如果不存在）
    os.makedirs(base_path, exist_ok=True)
    
    # 按代币分组保存到不同文件
    from collections import defaultdict
    
    # 按时间和交易对订单进行分组
    orders_by_time_coin = defaultdict(list)
    
    for order in orders:
        coin = order['coin']
        orders_by_time_coin[coin].append(order)
    
    for coin, coin_orders in orders_by_time_coin.items():
        filename = f"{base_path}/{coin}_{user}_oop.csv"
        
        fieldnames = ['time', 'BUY', 'SELL', 'POSITION']
        
        with open(filename, mode='a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            if file.tell() == 0:
                writer.writeheader()

            # if coin_orders is None or len(coin_orders) == 0:
            if not coin_orders or len(coin_orders) == 0:
                writer.writerow({
                    'time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                    'BUY': '[]',
                    'SELL': '[]',
                    'POSITION': '[]'
                })
                continue
            
            buy_orders = []
            sell_orders = []
            position = []
            
            for order in coin_orders:
                order_data = {
                    'price': order['limitPx'],
                    'size': order['sz']
                }
                
                if order['side'] == 'A':
                    sell_orders.append(order_data)
                elif order['side'] == 'B':
                    buy_orders.append(order_data)

            for pos in positions:
                if pos['position']['coin'] == coin:
                    position.append({
                        'size': pos['position']['szi'],
                        'unrealizedPnl': pos['position']['unrealizedPnl'],
                        'entryPx': pos['position']['entryPx']
                    })
            
            # 计算买卖订单的差值 coin
            # 对买卖订单按价格排序
            buy_orders.sort(key=lambda x: x['price'])  # 买方从高到低排序
            sell_orders.sort(key=lambda x: x['price'])  # 卖方从低到高排序
            
            writer.writerow({
                'time': datetime.fromtimestamp(coin_orders[0]['timestamp'] / 1000).strftime('%Y-%m-%dT%H:%M:%S'),
                'BUY': str(json.dumps(buy_orders)),
                'SELL': str(json.dumps(sell_orders)),
                'POSITION': str(json.dumps(position))
            })
    
    print(f"{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}")

def main():
    parser = argparse.ArgumentParser(description='Fetch and save Hyperliquid open orders.')
    parser.add_argument('--user', '-u', required=True, help='User wallet address')
    parser.add_argument('--symbols', '-ss', nargs='*', default=["BTC", "ETH", "SOL"], help='Whitelisted coins (default: ["BTC", "ETH", "SOL"])')
    
    args = parser.parse_args()
    
    while True:
        orders,positions = get_open_order_position(args.user, args.symbols)
        save_to_csv(args.user, orders, positions)
        
        time.sleep(2.5)

if __name__ == "__main__":
    main()