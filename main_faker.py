import os
import time
import threading
import json
from faker_exchange import FakerExchange
from hyer_util import hyper_file_log
from tabulate import tabulate 

# 初始化交易所实例，指定监控的交易对
# 可以传入自定义交易对列表，例如: FakerExchange(symbols=["BTCUSDT", "ETHUSDT"])
faker_exchange = FakerExchange(symbols=["BTC", "ETH", "SOL"])
def display_info():
    while True:
        # os.system("clear") # Removed clear console
        hyper_file_log("\n" + "="*50) # Add a separator
        hyper_file_log("--- 交易所控制台 ---")
        hyper_file_log(f"余额(占用资金): {faker_exchange.balance:.2f}")
        hyper_file_log(f"总盈亏(包含未实现盈亏): {faker_exchange.pnl:.2f}")
        hyper_file_log(f"成交次数: {faker_exchange.trade_count}")
        hyper_file_log("\n--- Latest Prices ---")
        if faker_exchange.latest_prices:
            for symbol, price in faker_exchange.latest_prices.items():
                if price is None:
                    hyper_file_log(f"{symbol}: No price data yet.")
                else:
                    hyper_file_log(f"{symbol}: {price:.4f}")
        else:
            hyper_file_log("No price data yet. Simulate a trade.")

        hyper_file_log("\n--- Open Orders ---")
        open_orders = [order for order in faker_exchange.get_orders() if order["status"] == "NEW"]
        headers = ['updateTime', 'orderId', "symbol", 'side', 'quantity', 'price', 'value']
        dataset = [[item["updateTime"], item['orderId'], item['symbol'], item['side'], item['quantity'], item['price'], item['quantity'] * item['price']] for item in open_orders]
        hyper_file_log(tabulate(dataset, headers=headers, tablefmt="fancy_grid"))

        hyper_file_log("\n--- Positions ---")
        positions = faker_exchange.get_position_risk()
        if positions:
            for pos in positions:
                if pos["positionAmt"] != 0:
                    hyper_file_log("{} | Amount: {:.4f} | Entry: {:.4f} | UPNL: {:.2f}".format(pos["symbol"], pos["positionAmt"], pos["entryPrice"], pos["unRealizedProfit"]))
        else:
            hyper_file_log("No open positions.")

        hyper_file_log("\n" + "="*50)
        
        time.sleep(1) # Refresh every 1 second

def input_handler():
    while True:
        try:
            command = input("> ").strip().split()
            if not command:
                continue

            action = command[0].lower()

            if action == "exit" or action == "quit":
                print("Exiting...")
                os._exit(0) # Force exit all threads
            elif (action == "cancel" or action == 'c') and len(command) == 1:
                open_orders = faker_exchange.get_orders()
                for o in open_orders:
                    faker_exchange.cancel_order(symbol=o['symbol'], orderId=order_id) # Symbol is not strictly needed for cancel by orderId in this mock
            elif (action == "cancel" or action == 'c') and len(command) == 2:
                order_id = command[1]
                faker_exchange.cancel_order(symbol="ANY", orderId=order_id) # Symbol is not strictly needed for cancel by orderId in this mock
            elif action == "free": # 市价全平仓
                positions = faker_exchange.get_position_risk()
                for pos in positions:
                    side = "SELL" if pos['positionAmt'] > 0 else "BUY"
                    faker_exchange.new_order(symbol=pos['symbol'], side=side, type="MARKET", quantity=-float(pos['positionAmt']), price=None)
            elif len(command) == 3:
                symbol = command[0].upper()
                quantity = float(command[1])
                if quantity == 0:
                    raise ValueError("Invalid quantity")

                price_str = command[2].lower()

                if price_str == "market" or price_str == "m":
                    faker_exchange.new_order(symbol=symbol, side="BUY" if quantity > 0  else "SELL", type="MARKET", quantity=quantity)
                else:
                    price = float(price_str)
                    faker_exchange.new_order(symbol=symbol, side="BUY" if quantity > 0 else "SELL", type="LIMIT", quantity=quantity, price=price)
            else:
                if action == "help" or action == "?" or action == "h":
                    print("Available commands:")
                else:
                    print("Invalid command format.")
                print("\tEnter (symbol quantity price) to place a LIMIT order (e.g., BTCUSDT 0.001 30000)")
                print("\tEnter (symbol quantity market/m) to place a MARKET order (e.g., ETHUSDT 0.01 market)")
                print("\tEnter (free) close all orders.")
                print("\tEnter (cancel/c [order_id]) to cancel an order (e.g., cancel/c 123e4567), 不写id全部取消")
                print("\tEnter \'exit\' to quit.")
        except ValueError as e:
            print(f"Invalid quantity or price. Please enter numbers. {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Start display thread
    display_thread = threading.Thread(target=display_info)
    display_thread.daemon = True
    display_thread.start()

    # Start input thread
    input_handler()
