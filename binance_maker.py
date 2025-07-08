from binance.um_futures import UMFutures
import os
import json
import argparse

binance_client = UMFutures(key=os.environ["binance_api_key"], secret=os.environ["binance_api_secret"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='做优挂单平仓工具')
    parser.add_argument('--symbol', '-s', type=str, required=True, default="BTCUSDC", help='symbol example BTCUSDC')
  
    args = parser.parse_args()

    symbol = args.symbol
    # 查询持仓
    position = binance_client.get_position_risk()
    print(json.dumps(position, indent=4))

    # 查询持仓是否存在 symbol
    p = next((p for p in position if p['symbol'] == symbol), None)
    if not p:
        print(f"不存在{symbol}的持仓")
        exit(1)

    print(f"平仓{symbol}")
    book = binance_client.book_ticker(symbol=symbol)
    
    # 最优价
    print(json.dumps(book, indent=4))

    sz = float(p['positionAmt'])
    side = "SELL" if sz > 0 else "BUY"
    price = book['bidPrice'] if side == "BUY" else book["askPrice"]
    params = {
        "symbol": symbol,
        "side": side,
        "type": "LIMIT",
        "timeInForce": "GTX",
        "quantity": sz,
        "price": price,
    }

    print(f"params: {params}")

    res = binance_client.new_order(**params)
    print(res)