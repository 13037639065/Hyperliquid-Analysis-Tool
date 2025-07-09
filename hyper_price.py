import websocket
import json
import threading
import time
from datetime import datetime

WEBSOCKET_URL = "wss://api.hyperliquid.xyz/ws"

class HyperPrice:
    """
    HyperPrice 类用于订阅特定代币的价格。
    """

    def __init__(self, coins = ["BTC", "ETH", "SOL"]):
        """
        初始化 HyperPrice 类实例。

        :param token_symbol: 代币的符号，例如 'BTC' 表示比特币。
        """
        # data cache
        self.price = {
        }
        self.ws = websocket.WebSocketApp(
            WEBSOCKET_URL,
            on_open=self.on_open, 
            on_message=self.on_message, 
            on_error=self.on_error, 
            on_close=self.on_close, 
        )

        self.subcoins = coins
        self.websockt_thread = threading.Thread(target=self.websockt_run)
        self.websockt_thread.start()


    def get_coin_price(self, coin):
        return self.price.get(coin, None)

    def stop(self):
        self.ws.keep_running = False
        self.websockt_thread.join()

    def __del__(self):
        self.stop()
    def websockt_run(self):
        self.ws.run_forever(ping_interval=10, ping_timeout=5, reconnect=3)
    
    def on_open(self, ws):
        self.connected  = True 
        print(f"✅ WebSocket连接成功 @ {datetime.now().isoformat()}") 
        for coin in self.subcoins:
            subscribe_msg = {
                "method": "subscribe",
                "subscription": {"type": "trades", "coin": coin}
            }
            ws.send(json.dumps(subscribe_msg)) 
        print("📡 已订阅所有交易数据")

    def on_message(self, ws, message):
        json_data = json.loads(message)
        if json_data.get("channel") == "trades" and "data" in json_data:
            trades = json_data["data"]
            for trade in trades:
                self.price[trade["coin"]] = trade["px"]
    def on_error(self, ws, error):
        print(f"WebSocket 错误：{error}")

    def on_close(self, ws, close_status_code, close_msg):
        print(f"WebSocket 已关闭。正在尝试重新连接...")

    def on_error(self, ws, error):
        print(f"WebSocket 错误：{error}")

    
# 示例用法
if __name__ == "__main__":
    p = HyperPrice()
    while True:
        print("==== 当前价格 ===========================")
        print(p.get_coin_price("BTC"))
        print(p.get_coin_price("ETH"))
        print(p.get_coin_price("SOL"))
        time.sleep(1)