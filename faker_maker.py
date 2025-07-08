import os
from faker_exchange import FakerExchange
from user_order_position import get_open_order_position

WHITE_LIST = ["BTC", "ETH", "SOL"]
TARGET_ADDRESS = os.environ.get("target_address")
fakerExchange = FakerExchange(symbols=WHITE_LIST, name="limit_maker_follow")

def calculate_mid_price(open_orders, position):
    """
    根据挂单信息和持仓信息计算中轨价格
    """
    # 核心参数在这里调参主要是调这里
    # position 可能是 None 空仓
    pass 
    total_price = 0
    total_quantity = 0
    for o in open_orders:
        total_price += float(o["limitPx"]) * float(o["sz"])
        total_quantity += float(o["sz"])
    total_price += float(position['position']['entryPx']) * float(position['position']['szi'])
    total_quantity += float(position['position']['szi'])

    avg_price = total_price / total_quantity
    print(f"{symbol} mid price: {avg_price:.3f}")
    


if __name__ == "__main__":
    print(f"Will follow {TARGET_ADDRESS}")
    while True:
        orders, positions = get_open_order_position(TARGET_ADDRESS, WHITE_LIST)

        # 反向计算中轨价格
        for symbol in WHITE_LIST:
            open_orders = (o for o in orders if o["coin"] == symbol)
            position = next((p for p in positions if p['position']["coin"] == symbol), None)

            avg_price = calculate_mid_price(open_orders, position)

            my_pos = fakerExchange.get_position_risk(symbol)
            # 根据avg_price 和自己的持仓更新自己的挂单
            # cancel all orders
            fakerExchange.cancel_order(symbol)

            # TODO 记录这个指标并且需要根据这个指标来挂单
