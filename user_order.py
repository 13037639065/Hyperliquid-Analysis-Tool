import websocket
import json
import csv

def on_message(ws, message):
    data = json.loads(message)
    # 将 data
    # 假设data是一个包含订单信息的字典列表，例如：
    data = [
        {
            "coin": "ETH",
            "side": "B",
            "limitPx": "2512.0",
            "sz": "6.8",
            "oid": 109565004077,
            "timestamp": 1751724620196,
            "origSz": "6.8",
            "cloid": "0x00000000000000000006392f2bb8515c",
            "status": "canceled",
            "statusTimestamp": 1751724620523
        }
    ]

    # 调用函数保存数据到CSV文件
    save_order_to_csv(data)

def on_error(ws, error):
    print("Error:", error)

def on_close(ws, close_status_code, close_msg):
    print("Connection closed")

def on_open(ws):
    # 订阅用户事件，替换为实际的用户地址
    user_address = "xxx"
    subscription_msg = {
        "method": "subscribe",
        "subscription": {
            "type": "orderUpdates",
            "user": user_address
        }
    }
    ws.send(json.dumps(subscription_msg))
    print(f"Subscribed to user events for {user_address}")

def save_order_to_csv(data, filename='order_data.csv'):
    """将订单数据保存到CSV文件中"""
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # 写入表头
        writer.writerow(data[0].keys())
        
        # 写入数据行
        for order in data:
            writer.writerow(order.values())

if __name__ == "__main__":
    websocket_url = "wss://api.hyperliquid.xyz/ws"
    
    # 创建WebSocket连接
    ws = websocket.WebSocketApp(websocket_url,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    ws.on_open = on_open
    
    # 运行WebSocket
    ws.run_forever(ping_interval=30, ping_timeout=10, reconnect=10)