from binance.um_futures import UMFutures
import os
import json
import websocket
from feishu_msg import send_feishu_text
import uuid
from hyperliquid.info  import Info
from hyperliquid.utils  import constants

DRY_RUN = False # 模拟交易
FACTOR  = 1  # 仓位占比
LEVERAGE = 20
USER_ADDRESS = os.environ.get('target_address')

INFO = Info(constants.MAINNET_API_URL, skip_ws=True)


# hyper 转 币安symbol 和一手做单大小，缩小倍数
symbol_mapping = {
    "BTC": ("BTCUSDC", 0.55, 500),
    "ETH": ("ETHUSDC", 6.8, 500),
    "SOL": ("SOLUSDC", 20, 500)
}

def hyper_log(message, level="info"):
    color_code = {
        "info": "\033[92m",   # 绿色 
        "warning": "\033[93m",# 黄色 
        "error": "\033[91m"   # 红色 
    }.get(level.lower(),  "\033[0m")  # 默认无色 
    
    reset_code = "\033[0m"
    print(f"{color_code}[{level.upper()}]  {message}{reset_code}")
    if level == "error":
        send_feishu_text(f"机器人错误报警", message)

def main():
    send_feishu_text("交易机器人", "自动交易机器人启动成功")
    order_id_map = {}
    
    binance_client = UMFutures(key=os.environ.get("binance_api_key"), secret=os.environ.get("binance_api_secret"))
    exchange_info = binance_client.exchange_info()
    def on_message(ws, message):
        try:
            data = json.loads(message)

            hyper_log(f"委托订单数量为：{len(order_id_map)}")
            
            if isinstance(data, dict) and data.get('channel') == 'orderUpdates':
                for update in data.get('data', []):
                    order = update.get('order')
                    coin = order.get('coin')
                    side = order.get('side')
                    limit_price = float(order.get('limitPx', 0))
                    size = float(order.get('sz', 0))
                    order_id = order.get('oid')

                    # open, filled, canceled, triggered, rejected, marginCanceled
                    action = update.get('status')  
                    
                    if action == "open":
                        # 处理订单
                        symbol = symbol_mapping.get(coin)[0]
                        if not symbol or size <= 0 or limit_price <= 0:
                            continue
                        
                        # 计算按比例缩小的订单数量
                        fac = symbol_mapping.get(coin)[2]
                        # proportional_size 四舍五入保留三位小数
                        proportional_size =size / fac
                        
                        # 获取市场信息以确保数量符合交易所要求
                        symbol_info = next((s for s in exchange_info['symbols'] if s['symbol'] == symbol), None)
                        if not symbol_info:
                            hyper_log(f"Symbol info not found for {symbol}", "error")
                            continue
                        
                        try:
                            binance_client.change_leverage(symbol=symbol, leverage=LEVERAGE)
                        except Exception as e:
                            hyper_log(f"Failed to set leverage for {symbol}: {e}", "error")
                            continue
                        
                        # 确保数量符合交易所最小交易单位要求
                        lot_size = next((f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'), None)
                        if lot_size:
                            min_qty = float(lot_size['minQty'])
                            step_size = float(lot_size['stepSize'])
                            # 调整数量到最近的有效值
                            proportional_size = max(min_qty, proportional_size - (proportional_size % step_size))
                        
                        # 创建订单参数
                        # 强制保留3位小数
                        proportional_size = round(proportional_size, 3)
                        params = {
                            "symbol": symbol,
                            "side": "SELL" if side == "A" else "BUY",
                            "type": "LIMIT",
                            "timeInForce": "GTX",
                            "quantity": proportional_size,
                            "price": limit_price,
                        }
                        
                        hyper_log(f"✅Created new order: {params['side']} {params['quantity']} {symbol} @ {params['price']}")

                        if not DRY_RUN:
                            try:
                                response = binance_client.new_order(**params)
                                order_id_map[order_id] = (symbol, response['orderId'])
                            except Exception as e:
                                hyper_log(f"创建失败的订单: {str(e)}")
                        else:
                            order_id_map[order_id] = (symbol, uuid.uuid1())
                    
                    # 如果是取消订单
                    elif action == 'canceled':
                        # 检查是否存在订单映射
                        if order_id in order_id_map:
                            binance_order_id = order_id_map[order_id][1]
                            symbol = symbol_mapping.get(coin)[0]
                            if not symbol:
                                continue
                            
                            try:
                                # 取消订单
                                if not DRY_RUN:
                                    binance_client.cancel_order(
                                        symbol=symbol,  
                                        orderId=binance_order_id
                                    )
                                hyper_log(f"❌Canceled order: {order_id}->{binance_order_id}, {side} {size} {symbol} @ {limit_price}")
                                del order_id_map[order_id]
                            except Exception as e:
                                hyper_log(f"❌Failed to cancel order {order_id}->{binance_order_id} for {symbol}, maybe filled: {e}", "warning")
                        else:
                            # 模拟盘或者刚启动的时候，没有订单ID
                            print(f"No corresponding order found for Hyperliquid order ID: {order_id}")
                    elif action == "filled":
                        # 检查自己的订单是否成交，如果没成交则视为没follow成功，提示错误
                        # 这里需要考虑是否市价单跟上？还是平掉已有的订单
                        binance_order_id = order_id_map[order_id][1]
                        response = binance_client.query_order(symbol = symbol_mapping.get(coin)[0], orderId=binance_order_id)
                        if str(response['status']).lower() == "filled":
                            hyper_log(f"{coin} {order_id}->{binance_order_id} follow success")
                        else:
                            # 跟单失败
                            hyper_log(f"{coin}  {order_id}->{binance_order_id} follow fail", "warning")
                    else:
                        hyper_log("未知的action: " + action)
            
            # check 是否存在未取消的订单
            if not DRY_RUN:
                open_orders = INFO.open_orders(USER_ADDRESS)
                # 将数组中 open_orders 的 oid 提取成数组
                hids = [order['oid'] for order in open_orders]

                # 遍历 order_id_map
                for hid in list(order_id_map.keys()):
                    value = order_id_map[hid]
                    if hid not in hids:
                        try:
                            binance_client.cancel_order(symbol=value[0], orderId=value[1])
                            hyper_log("取消未完成订单: " + str(order))
                            del order_id_map[hid]
                        except Exception as e:
                            print(e)
                            hyper_log("取消订单失败: " + str(e), "warning")
                        
            
            # 检查币安持仓和hyper是否差一手，如果差了则市价补齐
            hyper_positions = INFO.user_state(USER_ADDRESS)
            binance_positions = binance_client.get_position_risk()
            for coin, value in symbol_mapping.items():
                symbol = value[0]
                hyper_position = next((p for p in hyper_positions['assetPositions'] if p['position']['coin'] == coin), None)
                binance_position = next((p for p in binance_positions if p['symbol'] == symbol), None)

                hyper_sz = 0 if hyper_position is None else float( hyper_position['position']['szi'])
                binance_sz = 0 if binance_position is None else float(binance_position['positionAmt'])
                diff = hyper_sz - binance_sz * value[2]
                dir = "多" if diff > 0 else "空"
                sz = round(abs(diff) / value[2], 3)
                hyper_log(f"{coin} 持仓: ({hyper_sz} == {binance_sz * value[2]}), diff = {abs(diff)}")
                hyper_log(f"{coin} 调整：需要开-{dir} 数量{sz}")
                if abs(diff) > value[1]:
                    hyper_log(f"{coin} 调整：需要开-{dir} 数量{sz}", "warning")


                    
        except Exception as e:
            hyper_log(str(e), "error")

    def on_open(ws):
            # 订阅用户事件，替换为实际的用户地址
        target_address = USER_ADDRESS
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


if __name__ == "__main__":
    while True:
        try:
            main()
        except KeyboardInterrupt:
            hyper_log("KeyboardInterrupt will exit...", "error")
        except Exception as e:
            hyper_log(f"An error occurred, will restart bot: {e}", "error")