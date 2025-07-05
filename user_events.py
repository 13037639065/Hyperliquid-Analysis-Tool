import websocket
import json

def on_message(ws, message):
    data = json.loads(message)
    print(json.dumps(data, indent=4))   


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