from binance.um_futures import UMFutures
import json

c = UMFutures()
info = c.exchange_info()
# The exchange_info() already returns a dictionary, so no need to json.loads
# obj = json.loads(info)
print(json.dumps(info, indent=4))
