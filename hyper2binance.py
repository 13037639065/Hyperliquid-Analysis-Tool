from binance import Client
from hyperliquid.info  import Info
from hyperliquid.utils  import constants
import time
import os

info = Info(constants.MAINNET_API_URL, skip_ws=True)
binance_client = Client(api_key=os.environ.get("binance_api_key"), api_secret=os.environ.get("binance_api_secret"))
target_address = os.environ.get("target_address")

DRY_RUN = True

symbol_mapping = {
    "BTC": "BTCUSDC",
    "ETH": "ETHUSDC",
    "SOL": "SOLUSDC"
}

def place_proportional_orders(open_orders):
    # 获取账户信息
    account_info = binance_client.futures_account()
    
    # 计算总资产价值（以USDT/USDC计价）
    print("Total Equity:", account_info)
    
    # 按代币分组订单
    orders_by_coin = {}
    for order in open_orders:
        coin = order['coin']
        if coin not in orders_by_coin:
            orders_by_coin[coin] = []
        orders_by_coin[coin].append(order)
    
    # 计算每个代币的总持仓量
    position_sizes = {}
    for coin, orders in orders_by_coin.items():
        total_size = sum(float(order['sz']) for order in orders)
        position_sizes[coin] = total_size
    
    # 获取当前价格
    tickers = binance_client.get_symbol_ticker()
    price_map = {ticker['symbol']: float(ticker['price']) for ticker in tickers}
    
    # 计算每个代币的总价值
    position_values = {}
    for coin, size in position_sizes.items():
        symbol = symbol_mapping.get(coin)
        if symbol in price_map:
            value = size * price_map[symbol]
            position_values[coin] = value
    
    # 计算每个代币的资金分配比例
    total_portfolio_value = sum(position_values.values())
    allocation_ratios = {coin: value/total_portfolio_value for coin, value in position_values.items()}
    
    # 获取可用余额
    available_balance = float(account_info['availableBalance'])
    
    # 为每个订单下单
    placed_orders = []
    for order in open_orders:
        coin = order['coin']
        symbol = symbol_mapping.get(coin)
        if not symbol:
            continue
        
        # 获取订单参数
        limit_price = float(order['limitPx'])
        original_size = float(order['sz'])
        
        # 计算按比例的订单大小
        portfolio_ratio = allocation_ratios[coin]
        proportional_size = (available_balance * portfolio_ratio) / limit_price
        
        # 创建订单参数
        params = {
            "symbol": symbol,
            "side": "SELL" if order['side'] == "A" else "BUY",
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": f"{proportional_size:.{8}f}".rstrip('0').rstrip('.') if '.' in f"{proportional_size:.{8}f}" else f"{proportional_size:.{8}f}",
            "price": f"{limit_price:.{8}f}".rstrip('0').rstrip('.') if '.' in f"{limit_price:.{8}f}" else f"{limit_price:.{8}f}",
        }
        
        try:
            if DRY_RUN:
                print(f"Dry run: Would place order: {params}")
            else:
                response = binance_client.create_order(**params)
                placed_orders.append({
                    "original_order": order,
                    "proportional_params": params,
                    "binance_response": response
                })
        except Exception as e:
            print(f"Failed to place order for {symbol}: {e}")
            continue
    
    return placed_orders


def main():
    poll_interval = 3
    while True:
        try:
            open_odrders = info.open_orders(target_address)
            place_proportional_orders(open_odrders)
        except Exception as e:
            print(f"获取交易记录失败: {e}")
        time.sleep(poll_interval) 

if __name__ == "__main__":
    main()