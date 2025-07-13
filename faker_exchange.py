import time
import asyncio
import websockets
import json
import os
import csv
import threading
import time
from datetime import datetime

class FakerExchange:
    def __init__(self, symbols=None, name="manual"):
        self.symbols = [symbol.upper() for symbol in symbols]
        self.symbols = [f"{symbol}USDC" for symbol in self.symbols]
        self.maker_fee = 0.0000  # 假设挂单手续费为0.02%
        self.taker_fee = 0.0005  # 假设吃单手续费
        self.orders = {}
        self.positions = {}
        self.balance = 0  # Initial balance
        self.pnl = 0.0
        self.unRealizedProfit = 0.0
        self.realized_profit = 0.0  # 已实现盈亏
        self.total_pnl = 0.0      # 总盈亏
        self.trade_count = 0  # 新增：订单成交次数统计，默认为0
        self.latest_prices = {symbol: None for symbol in self.symbols}
        self.oid = 10000
        self.running = True
        
        # 新增：创建 trading_data_cache 目录（如果不存在）
        self.cache_dir = "trading_data_cache/history"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 新增：初始化CSV文件
        self.csv_file_path = os.path.join(self.cache_dir, f"{datetime.now().strftime("%Y_%m_%dT%H_%M")}_{name}.csv")
        self._init_csv()
        
        # 新增：启动定时保存数据的线程
        self.save_thread = threading.Thread(target=self._save_data_periodically)
        self.save_thread.daemon = True
        self.save_thread.start()

        # 启动WebSocket连接
        self.ws_thread = threading.Thread(target=self._start_websocket)
        self.ws_thread.daemon = True
        self.ws_thread.start()
    
    def _start_websocket(self):
        """启动WebSocket连接的入口函数"""
        asyncio.run(self._connect_websocket())

    def get_latest_price(self, symbol):
        """获取最新价格"""
        return self.latest_prices.get(symbol, None)
    
    async def _connect_websocket(self):
        """建立WebSocket连接并订阅市场数据"""
        uri_template = "wss://fstream.binance.com/ws/{}@trade"
        
        # 创建所有交易对的连接
        connections = []
        for symbol in self.symbols:
            uri = uri_template.format(symbol.lower())
            try:
                ws_conn = await websockets.connect(uri)
                connections.append((symbol, ws_conn))
                print(f"Connected to {uri}")
            except Exception as e:
                print(f"Failed to connect to {uri}: {e}")
        
        if not connections:
            print("No WebSocket connections established.")
            return
        
        # 主循环监听消息
        while self.running:
            for symbol, websocket in connections:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    self._handle_websocket_message(data)
                except websockets.exceptions.ConnectionClosed:
                    print(f"Connection closed for {symbol}. Reconnecting...")
                    # 尝试重新连接
                    try:
                        new_conn = await websockets.connect(uri_template.format(symbol.lower()))
                        # 替换旧的连接
                        idx = next(i for i, (s, _) in enumerate(connections) if s == symbol)
                        connections[idx] = (symbol, new_conn)
                    except Exception as e:
                        print(f"Reconnection failed for {symbol}: {e}")
                except Exception as e:
                    print(f"Error receiving message for {symbol}: {e}")
    
    def _handle_websocket_message(self, data):
        """处理接收到的WebSocket消息"""
        if not data or "s" not in data:
            print(f"Invalid data received: {data}")
            return
        
        symbol = data["s"]
        price = float(data["p"])
        quantity = float(data["q"])
        
        # 更新最新价格
        self.latest_prices[symbol] = price
        
        # 匹配订单并更新仓位
        self._match_orders(symbol, price, quantity)
        # 更新持仓盈亏
        self._update_all_pnl()
    
    def _match_orders(self, symbol, price, quantity):
        """根据市场价格匹配订单"""
        # 使用当前市场价格尝试匹配挂单
        for order_id, order in list(self.orders.items()):
            if order["symbol"] == symbol and order["status"] == "NEW":
                if order["type"] == "LIMIT":
                    # 检查限价单是否可以成交
                    if (order["side"] == "BUY" and price < order["price"]): # 全部成交
                        order["avgPrice"] = order["price"]
                        order['status'] = "FILLED"
                        order["updateTime"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                        self._update_position(symbol, order['quantity'], price, "LIMIT")
                        self.trade_count += 1  # 订单成交，增加计数器
                        print(f"Order {order_id} partially filled. Executed: {order['executedQty']}/{order['quantity']}")
                            
                    if (order["side"] == "SELL" and price > order["price"]):
                        order["avgPrice"] = order["price"]
                        order['status'] = "FILLED"
                        order["updateTime"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                        self._update_position(symbol, -order['quantity'], price, "LIMIT")
                        self.trade_count += 1  # 订单成交，增加计数器
                        print(f"Order {order_id} partially filled. Executed: {order['executedQty']}/{order['quantity']}")
               

    def _update_all_pnl(self):
        """根据最新市场价格更新所有持仓的盈亏信息"""
        for pos_symbol in self.positions:
            current_price = self.latest_prices.get(pos_symbol)
            if current_price is not None:
                self._update_pnl(pos_symbol, current_price)
    
    def new_order(self, symbol: str, side: str, type: str, quantity: float, price: float = None, **kwargs):
        # 判断价格能否挂上limit订单
        latest_price = self.latest_prices.get(symbol)
        if latest_price is None:
            print(f"No latest price available for {symbol}. Failed to place order.")
            return False

        if type != "LIMIT": # market price
            # 更新 self.positions
            self.trade_count += 1  # 订单成交，增加计数器
            self._update_position(symbol, quantity, latest_price, "MARKET")
            return True
        else:
            # LIMIT 需要检查价格
            if quantity > 0 and price >= latest_price:
                print(f"Cannot place BUY LIMIT order for {symbol} at {price}. Latest price is {latest_price}.")
                return False
            elif quantity < 0 and price <= latest_price:
                print(f"Cannot place SELL LIMIT order for {symbol} at {price}. Latest price is {latest_price}.")
                return False

        order_id = str(self.oid)
        self.oid += 1
        timestamp = int(time.time() * 1000)
        order = {
            "symbol": symbol,
            "orderId": order_id,
            "clientOrderId": kwargs.get("newClientOrderId", order_id),
            "price": price,
            "quantity": quantity,
            "side": side,
            "type": type,
            "status": "NEW",
            "updateTime": timestamp,
            "executedQty": 0.0,
            "avgPrice": 0.0
        }
        self.orders[order_id] = order
        print("New order placed: {}".format(order))
        return True

    def get_orders(self, symbol: str = None, **kwargs):
        if symbol:
            return [order for order in self.orders.values() if order["symbol"] == symbol]
        return list(self.orders.values())

    def cancel_order(self, symbol: str, orderId: str = None, origClientOrderId: str = None, **kwargs):
        target_order_id = None
        if orderId:
            target_order_id = orderId
        elif origClientOrderId:
            for order in self.orders.values():
                if order["clientOrderId"] == origClientOrderId:
                    target_order_id = order["orderId"]
                    break

        if target_order_id and target_order_id in self.orders:
            order = self.orders[target_order_id]
            if order["status"] == "NEW":
                order["status"] = "CANCELED"
                order["updateTime"] = int(time.time() * 1000)
                print(f"Order canceled: {order}")
                return order
            else:
                print("Order {} cannot be canceled as its status is {}".format(target_order_id, order["status"]))
                return None
        else:
            print(f"Order with ID {orderId or origClientOrderId} not found.")
            return None

    def get_position_risk(self, symbol: str = None, **kwargs):
        if symbol:
            return [self.positions.get(symbol, {"symbol": symbol, "positionAmt": 0.0, "entryPrice": 0.0, "unRealizedProfit": 0.0})]
        
        all_positions = []
        for s, pos in self.positions.items():
            all_positions.append(pos)
        return all_positions

    def _update_position(self, symbol, quantity, price, type="LIMIT"):
        if symbol not in self.positions:
            self.positions[symbol] = {"symbol": symbol, "positionAmt": 0.0, "entryPrice": 0.0, "unRealizedProfit": 0.0}

        current_position = self.positions[symbol]["positionAmt"]
        current_entry_price = self.positions[symbol]["entryPrice"]

        # one way 模式
        if quantity + current_position == 0:  # close position
            new_entry_price = 0
            self.balance += price * abs(quantity)
            # 更新已实现盈亏
            self.realized_profit += (price - current_entry_price) * current_position
            
        elif current_position * quantity >= 0:  # Same direction or opening new position
            new_entry_price = (price * abs(quantity) + current_entry_price * abs(current_position)) / abs(quantity + current_position)
            self.balance -= price * abs(quantity)
        else:  # Closing or reversing position
            if abs(quantity) < abs(current_position):  # 只减持仓
                self.balance += price * abs(quantity)
                # 更新已实现盈亏
                self.realized_profit += (price - current_entry_price) * quantity
            else:  # 反手
                self.balance += price * abs(current_position)
                self.balance -= price * (abs(quantity) - abs(current_position))
                # 更新已实现盈亏
                self.realized_profit += (price - current_entry_price) * current_position
                new_entry_price = price  # Simplified: if reversing, new entry price is current price
        
        # fee计算
        fee_amount = 0
        if type != "LIMIT":  # 吃单
            fee_amount = abs(quantity) * price * self.taker_fee
            self.balance -= fee_amount
        else:  # 挂单
            fee_amount = abs(quantity) * price * self.maker_fee
            self.balance -= fee_amount

        self.positions[symbol]["positionAmt"] = current_position + quantity
        self.positions[symbol]["entryPrice"] = new_entry_price

        if self.positions[symbol]["positionAmt"] == 0:
            del self.positions[symbol]
            
        # 更新总盈亏
        self.total_pnl = self.realized_profit + self.unRealizedProfit

        print(f"Position updated for {symbol}: {self.positions[symbol]}")
        print(f"Fee deducted: {fee_amount:.6f} USDC")

    def _update_pnl(self, symbol, current_price):
        if symbol in self.positions and self.positions[symbol]["positionAmt"] != 0:
            position = self.positions[symbol]
            unrealized_pnl = (current_price - position["entryPrice"]) * position["positionAmt"]
            self.positions[symbol]["unRealizedProfit"] = unrealized_pnl
            self.unRealizedProfit = sum(pos["unRealizedProfit"] for pos in self.positions.values() if pos["positionAmt"] != 0)
            
        # 更新总盈亏
        self.total_pnl = self.realized_profit + self.unRealizedProfit

    def _init_csv(self):
        """初始化CSV文件并写入表头"""
        with open(self.csv_file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['时间', '占用资金', 'BTC持仓', 'ETH持仓', 'SOL持仓', '未实现盈亏', '已实现盈亏', '总盈亏', '收益率', '成交次数'])  # 添加'成交次数'列

    def _save_data_periodically(self):
        """每秒保存一次数据到CSV文件"""
        while self.running:
            try:
                # 获取当前时间
                current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                
                # 获取各代币持仓
                btc_position = self.positions.get("BTCUSDC", {}).get("positionAmt", 0.0)
                eth_position = self.positions.get("ETHUSDC", {}).get("positionAmt", 0.0)
                sol_position = self.positions.get("SOLUSDC", {}).get("positionAmt", 0.0)
                
                # 计算收益率
                roi = (self.total_pnl / 10000.0) * 100 if self.total_pnl != 0 else 0.0
                
                # 写入数据到CSV
                with open(self.csv_file_path, mode='a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow([
                        current_time,
                        f"{self.balance:.2f}",
                        f"{btc_position:.4f}",
                        f"{eth_position:.4f}",
                        f"{sol_position:.4f}",
                        f"{self.unRealizedProfit:.2f}",
                        f"{self.realized_profit:.2f}",
                        f"{self.total_pnl:.2f}",
                        f"{roi:.2f}%",
                        str(self.trade_count)  # 添加成交次数数据
                    ])
                
                # 每隔1秒保存一次
                time.sleep(1)
            except Exception as e:
                print(f"Error saving data to CSV: {e}")


# Placeholder for UMFutures client for reference
class UMFutures:
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret

    def new_order(self, symbol: str, side: str, type: str, quantity: float, price: float = None, **kwargs):
        # This would be the actual API call
        pass

    def get_orders(self, symbol: str = None, **kwargs):
        # This would be the actual API call
        pass

    def cancel_order(self, symbol: str, orderId: str = None, origClientOrderId: str = None, **kwargs):
        # This would be the actual API call
        pass

    def get_position_risk(self, symbol: str = None, **kwargs):
        # This would be the actual API call
        pass

