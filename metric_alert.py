import time
import json
from datetime import datetime
from hyperliquid.info import Info
from hyperliquid.utils import constants
from feishu_msg import send_feishu_text

INFO = Info(constants.MAINNET_API_URL, skip_ws=True)

symbol = "BTC"  # 你要查询的交易对，比如 BTC、ETH
resolution = "1m"  # 分钟级别K线
time_range = 1 * 24 * 60 * 60 * 1000  # 最近7天的时间范围（毫秒）

def check_kline_data(klines):
    """
    找出最低的close价格的index
    参数:
        klines (list): 包含多个K线字典的列表，每个字典包含如 'c' (close 收盘价) 等字段
    返回:
        int: 最低收盘价的索引
    """
    min_index = -1
    min_close = float('inf')

    for i, kline in enumerate(klines):
        close_price = float(kline['c'])
        if close_price < min_close:
            min_close = close_price
            min_index = i

    return None if min_index == -1 else klines[min_index]


# 调用K线历史数据API
while True:
    try:
        date_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        now = int(time.time() * 1000)   # 当前时间戳（毫秒）
        start_time = now - time_range
        klines = INFO.candles_snapshot(symbol, resolution, start_time, now)
        result = check_kline_data(klines)

        print("============================================================================")
        print(date_time_str)
        print(result)
        print(klines[-1])
        
        if result == klines[-1]:
            send_feishu_text(f"低价提醒 {date_time_str}", json.dumps(result, indent=4))
    except Exception as e:
        print(e)
    time.sleep(60)
