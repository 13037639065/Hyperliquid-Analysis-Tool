from binance.um_futures import UMFutures
import json
import os

c = UMFutures(key=os.environ["binance_api_key"], secret=os.environ["binance_api_secret"])
info = c.exchange_info()
ticker = c.book_ticker("BTCUSDC")
print(json.dumps(ticker, indent=4))