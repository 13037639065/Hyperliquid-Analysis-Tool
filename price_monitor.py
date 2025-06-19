import websocket 
import json 
import time 
import requests 
import os
import argparse

# 新增参数解析
def parse_args():
    parser = argparse.ArgumentParser(description='Price Monitor')
    parser.add_argument('--threshold', '-t', type=float, default=0.3, help='Threshold for price change (default: 0.3)')
    parser.add_argument('--symbol', "-s", type=str, default='ethusdt', help='Trading pair symbol (default: ethusdt)')
    return parser.parse_args()

last_notification_time = 0  # 新增频率限制变量
def send_feishu_text(webhook_url, title, content):
    global last_notification_time  # 引入全局时间戳
    
    # 频率限制检查（10秒冷却）
    current_time = time.time()
    if current_time - last_notification_time < 10:
        print(f"触发频率限制，跳过通知 {content}")
        return

    headers = {"Content-Type": "application/json"}
    payload = {
        "msg_type": "text",
        "content": content,
        "title": title,
    }
    response = requests.post(webhook_url,  headers=headers, data=json.dumps(payload)) 
    last_notification_time = current_time
    return response.json() 

# 全局变量 
recent_trades = []
webhook_url = os.environ.get('WEBHOOK_URL')

def on_message(ws, message):
    global recent_trades
    
    # 解析消息
    data = json.loads(message)
    current_price = float(data['p'])
    current_time = data['E'] / 1000  # 转换为秒
    
    # 添加最新交易
    recent_trades.append((current_time, current_price))
    
    # 清理超过1分钟的数据（滚动窗口）
    cutoff_time = current_time - 60
    recent_trades = [trade for trade in recent_trades if trade[0] > cutoff_time]
    
    # 当有足够数据时计算涨跌幅
    if len(recent_trades) >= 2:  # 至少需要两个数据点
        # 获取窗口内最早的价格（当前时间-60秒时的价格）
        window_start_price = recent_trades[0][1]
        
        if window_start_price:
            price_change = (current_price - window_start_price) / window_start_price * 100
            if abs(price_change) > args.threshold:
                title = ""
                datetime_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(current_time))
                dir = "▲" if price_change > 0 else "▼"
                content = f"""{args.symbol.upper()}价格1分钟涨跌幅突破 {args.threshold}%
方向：{dir}
窗口起始价: {window_start_price:.2f}
当前价格: {current_price:.2f}
涨跌幅: {price_change:.2f}%
时间: {datetime_str}"""
                send_feishu_text(webhook_url, title, content)
def on_error(ws, error): 
    print(f"Error: {error}") 

def on_close(ws, a, b): 
    print("Connection closed") 
    # 短线重连机制
    reconnect()

def on_open(ws): 
    print("Connected to Binance WebSocket") 

def reconnect():
    print("Reconnecting...")
    time.sleep(5)  # 等待5秒后重连
    ws.run_forever()

if __name__ == "__main__": 
    args = parse_args()
    symbol = args.symbol
    ws_url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}usdt@trade"
    ws = websocket.WebSocketApp(ws_url,  
                                on_open=on_open, 
                                on_message=on_message, 
                                on_error=on_error, 
                                on_close=on_close) 
    ws.run_forever(reconnect=5)