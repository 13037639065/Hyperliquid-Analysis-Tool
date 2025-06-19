import websocket 
import json 
import csv 
import time 
from datetime import datetime 
import threading 
import argparse
import os

# 配置文件参数 
def parse_args():
    parser = argparse.ArgumentParser(description="Hyperliquid WebSocket Data Logger")
    parser.add_argument("--coin", type=str, default="BTC", help="Coin to subscribe to, default: BTC")
    parser.add_argument("--folder", type=str, default="./trading_data_cache/fills", help="Directory to save data, default: ./trading_data_cache/fills")
    return parser.parse_args()

ARGS = parse_args()
WEBSOCKET_URL = "wss://api.hyperliquid.xyz/ws"
RECONNECT_DELAY = 5  # 断线重连等待时间(秒)
PROGRAM_START_TIME = datetime.now().strftime("%Y_%m_%dT%H_%M_%S")
CSV_FILENAME = f"{ARGS.folder}/{PROGRAM_START_TIME}_{ARGS.coin}_trade_data.csv"

class HyperliquidWebSocket:
    def __init__(self, coin):
        self.ws = None
        self.connected = False
        self.reconnect_flag = False
        self.coin = coin
        self.DATA_DIR = "./trading_data_cache/fills"
        os.makedirs(self.DATA_DIR, exist_ok=True)
        self.CSV_FILENAME = CSV_FILENAME
        self.csv_file = open(self.CSV_FILENAME, 'a', newline='', encoding='utf-8')
        self.csv_writer = None
        self._init_csv()
        
    def _init_csv(self):
        """初始化CSV文件和写入头"""
        headers = ["coin", "px", "sz", "side", "time", "user1", "user2", "hash", "tid"]
        # 检查文件是否为空以决定是否写表头 
        self.csv_file.seek(0,  2)
        if self.csv_file.tell()  == 0:
            self.csv_writer  = csv.DictWriter(self.csv_file,  fieldnames=headers)
            self.csv_writer.writeheader() 
            self.csv_file.flush() 
        else:
            self.csv_writer  = csv.DictWriter(self.csv_file,  fieldnames=headers)
 
    def _connect(self):
        """建立WebSocket连接"""
        self.ws  = websocket.WebSocketApp(
            WEBSOCKET_URL,
            on_open=self.on_open, 
            on_message=self.on_message, 
            on_error=self.on_error, 
            on_close=self.on_close, 
        )
        self.ws.run_forever( 
            ping_interval=30,
            ping_timeout=10,
            reconnect=10  # 底层自动重连尝试 
        )
 
    def on_open(self, ws):
        """连接建立时的回调"""
        self.connected  = True 
        print(f"✅ WebSocket连接成功 @ {datetime.now().isoformat()}") 
        # 订阅所有交易数据 
        subscribe_msg = {
            "method": "subscribe",
            "subscription": {"type": "trades", "coin": self.coin}
        }
        ws.send(json.dumps(subscribe_msg)) 
        print("📡 已订阅所有交易数据")
 
    def on_message(self, ws, message):
        """处理收到的消息"""
        try:
            json_data = json.loads(message)
            print("Received data:", json_data)

            if json_data.get("channel") == "trades" and "data" in json_data:
                trades = json_data["data"]
                for trade in trades:
                    self._process_trade(trade)

        except json.JSONDecodeError as e:
            print("JSON 解析错误:", e)
        except Exception as e:
            print("消息处理错误:", e)

    def _process_trade(self, trade_data):
        """处理单个交易并保存到CSV"""
        # 提取字段（注意：users 是列表）
        coin = trade_data.get("coin", "")
        side = trade_data.get("side", "")
        px = trade_data.get("px", "0.0")
        sz = trade_data.get("sz", "0.0")
        time_ms = trade_data.get("time", 0)
        hash_value = trade_data.get("hash", "")
        tid = trade_data.get("tid", 0)
        users = trade_data.get("users", [])

        # 转换时间戳（毫秒转为 ISO 时间格式）
        timestamp = datetime.fromtimestamp(time_ms / 1000).isoformat()

        # 写入CSV行
        csv_row = {
            "coin": coin,
            "px": px,
            "sz": sz,
            "side": "Buy" if side == "B" else "Sell",
            "time": timestamp,
            "user1": users[0] if len(users) > 0 else "",
            "user2": users[1] if len(users) > 1 else "",
            "hash": hash_value,
            "tid": tid,
        }

        self.csv_writer.writerow(csv_row)
        self.csv_file.flush()
        print(f"📝 已记录交易: {coin} @ {px}")
 
    def on_error(self, ws, error):
        """错误处理"""
        print(f"❌ WebSocket错误: {error}")
        self.reconnect_flag  = True 
 
    def on_close(self, ws, close_status_code, close_msg):
        """连接关闭时的回调"""
        self.connected  = False 
        print(f"⛔ 连接关闭: Code={close_status_code}, Msg={close_msg}")
        if not self.reconnect_flag:   # 非主动关闭时触发重连 
            self.reconnect() 
 
    def reconnect(self):
        """断线重连逻辑"""
        print(f"♻️ {RECONNECT_DELAY}秒后尝试重连...")
        time.sleep(RECONNECT_DELAY) 
        self._connect()
 
    def start(self):
        """启动服务"""
        print(f"🚀 启动Hyperliquid交易记录器")
        print(f"💾 数据将保存至: {CSV_FILENAME}")
        self._connect()
 
    def graceful_shutdown(self):
        """优雅关闭"""
        self.reconnect_flag  = True 
        if self.ws: 
            self.ws.close() 
        self.csv_file.close() 
        print("🛑 服务已安全关闭")
 
# 运行主程序 
if __name__ == "__main__":
    client = HyperliquidWebSocket(coin=ARGS.coin)
    
    try:
        # 在独立线程中运行 
        thread = threading.Thread(target=client.start) 
        thread.daemon = True 
        thread.start() 
        
        # 主线程保持运行 
        while True:
            time.sleep(1) 
        
    except KeyboardInterrupt:
        print("\n🛑 接收到中断信号，关闭服务...")
        client.graceful_shutdown() 

