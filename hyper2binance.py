from binance import Client
import time
import os
import json
import websocket


DRY_RUN = True # 模拟交易
FACTOR  = 1  # 仓位占比
LEVERAGE = 100

symbol_mapping = {
    "BTC": "BTCUSDC",
    "ETH": "ETHUSDC",
    "SOL": "SOLUSDC"
}

if __name__ == "__main__":
    order_id_map = {}
    
    binance_client = Client(api_key=os.environ.get("BINANCE_API_KEY"), api_secret=os.environ.get("BINANCE_API_SECRET"))
    def on_message(ws, message):
        try:
            data = json.loads(message)
            
            if isinstance(data, dict) and data.get('channel') == 'orderUpdates':
                for update in data.get('data', []):
                    order = update.get('order')
                    coin = order.get('coin')
                    side = order.get('side')
                    limit_price = float(order.get('limitPx', 0))
                    size = float(order.get('sz', 0))
                    order_id = order.get('oid')

                    action = update.get('status')  # canceled open 
                    
                    if action == "open":
                        # 处理订单
                        symbol = symbol_mapping.get(coin)
                        if not symbol or size <= 0 or limit_price <= 0:
                            continue
                        
                        # 计算按比例缩小的订单数量
                        proportional_size = size * FACTOR
                        
                        # 获取市场信息以确保数量符合交易所要求
                        exchange_info = binance_client.futures_exchange_info()
                        symbol_info = next((s for s in exchange_info['symbols'] if s['symbol'] == symbol), None)
                        if not symbol_info:
                            print(f"Symbol info not found for {symbol}")
                            continue
                        
                        # 设置杠杆
                        try:
                            binance_client.futures_change_leverage(symbol=symbol, leverage=LEVERAGE)
                        except Exception as e:
                            print(f"Failed to set leverage for {symbol}: {e}")
                            continue
                        
                        # 确保数量符合交易所最小交易单位要求
                        lot_size = next((f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'), None)
                        if lot_size:
                            min_qty = float(lot_size['minQty'])
                            step_size = float(lot_size['stepSize'])
                            # 调整数量到最近的有效值
                            proportional_size = max(min_qty, proportional_size - (proportional_size % step_size))
                        
                        # 创建订单参数
                        params = {
                            "symbol": symbol,
                            "side": "SELL" if side == "A" else "BUY",
                            "type": "LIMIT",
                            "timeInForce": "GTC",  # 持续有效
                            "quantity": f"{proportional_size:.{8}f}".rstrip('0').rstrip('.') if '.' in f"{proportional_size:.{8}f}" else f"{proportional_size:.{8}f}",
                            "price": f"{limit_price:.{8}f}".rstrip('0').rstrip('.') if '.' in f"{limit_price:.{8}f}" else f"{limit_price:.{8}f}",
                            "newClientOrderId": f"HL_{order_id}"  # 使用Hyperliquid订单ID作为客户端订单ID
                        }
                        
                        # 检查订单是否已存在
                        existing_orders = binance_client.futures_get_open_orders(symbol=symbol)
                        existing_order = None
                        for eo in existing_orders:
                            if (
                                eo['side'] == params['side'] and
                                abs(float(eo['price']) - limit_price) < 1e-6 and
                                abs(float(eo['origQty']) - proportional_size) < 1e-6
                            ):
                                existing_order = eo
                                break
                        
                        if existing_order:
                            # 更新现有订单
                            print(f"Order exists: {existing_order['orderId']}, {params['side']} {params['quantity']} {symbol} @ {params['price']}")
                            # 更新订单映射
                            order_id_map[order_id] = existing_order['orderId']
                        else:
                            # 创建新订单
                            response = binance_client.create_order(**params)
                            print(f"Created new order: {response['orderId']}, {params['side']} {params['quantity']} {symbol} @ {params['price']}")
                            # 存储订单映射
                            order_id_map[order_id] = response['orderId']
                    
                    # 如果是取消订单
                    elif action == 'canceled':
                        # 检查是否存在订单映射
                        if order_id in order_id_map:
                            binance_order_id = order_id_map[order_id]
                            symbol = symbol_mapping.get(coin)
                            if not symbol:
                                continue
                            
                            try:
                                # 取消订单
                                binance_client.futures_cancel_order(
                                    symbol=symbol,
                                    orderId=binance_order_id
                                )
                                print(f"Canceled order: {binance_order_id}, {side} {size} {symbol} @ {limit_price}")
                                # 从映射中移除已取消的订单
                                del order_id_map[order_id]
                            except Exception as e:
                                print(f"Failed to cancel order {binance_order_id} for {symbol}: {e}")
                        else:
                            print(f"No corresponding order found for Hyperliquid order ID: {order_id}")
                    else:
                        print("=============================================================================")
                        print(f"Unknown status: {action}")
                        print(update)
                        print("=============================================================================")
        except Exception as e:
            print(f"Error processing message: {e}")

    def on_open(ws):
            # 订阅用户事件，替换为实际的用户地址
        target_address = os.environ.get('target_address')
        subscription_msg = {
            "method": "subscribe",
            "subscription": {
                "type": "orderUpdates",
                "user": target_address
            }
        }
        ws.send(json.dumps(subscription_msg))
        print(f"Subscribed to user events for {target_address}")
    
    websocket_url = "wss://api.hyperliquid.xyz/ws"
    ws = websocket.WebSocketApp(websocket_url, on_message=on_message, on_open=on_open)
    ws.run_forever(ping_interval=30, ping_timeout=10, reconnect=10)
