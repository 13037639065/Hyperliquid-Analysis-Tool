import os
from faker_exchange import FakerExchange

WHITE_LIST = ["BTC", "ETH", "SOL"]
TARGET_ADDRESS = os.environ.get("target_address")
fakerExchange = FakerExchange(symbols=WHITE_LIST, name="limit_maker_follow")

def calculate_mid_price(open_orders, position, entryPrice, currentPrice):
    """
    根据挂单信息和持仓信息计算中轨价格
    open_orders 被监控挂单数据
    position 持仓信息
    entryPrice 进场价格
    currentPrice 当前价格
    """
    pass


if __name__ == "__main__":
    print(f"Will follow {TARGET_ADDRESS}")
    while True:

        # 反向计算中轨价格
        for symbol in WHITE_LIST:
            price = fakerExchange.get_latest_price(symbol + "USDC")
            open_orders = fakerExchange.get_position_risk(symbol + "USDC")
            # cancel all

            if open_orders != None:
                for order in open_orders:
                    order_id = order['orderId']
                    fakerExchange.cancel_order(symbol + "USDC", orderId=order_id)

         
            for i in range(3):
                lp = price * (1 + i * 0.0002)
                fakerExchange.new_order(symbol + "USDC", "SELL", "LIMIT", quantity=0.001, price=lp)

            for i in range(3):
                lp = price * (1 - i * 0.0002)
                fakerExchange.new_order(symbol + "USDC", "BUY", "LIMIT", quantity=0.001, price=lp)