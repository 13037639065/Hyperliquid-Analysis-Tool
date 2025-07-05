from binance.um_futures import UMFutures
import os
binance_client = UMFutures(key=os.environ["binance_api_key"], secret=os.environ["binance_api_secret"])

params = {
    "symbol": "BTCUSDC",
    "side": "SELL",
    "type": "LIMIT",
    "timeInForce": "GTX",
    "quantity": 0.001,
    "price": 10000,
}

res = binance_client.new_order(**params)
print(res)