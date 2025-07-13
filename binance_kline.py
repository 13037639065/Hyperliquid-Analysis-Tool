import ccxt
import pandas as pd
from datetime import datetime, timedelta, timezone

# 1. 初始化交易所（无需 API Key 就能抓公开行情）
exchange = ccxt.binance({
    "enableRateLimit": True,       # 内置速率限制保护
})

symbol     = "BTC/USDT"            # 也可改成 BTC/BUSD、BTC/FDUSD 等
timeframe  = "1m"                  # 1‑minute kline
days_back  = 30                    # 回溯天数
limit_each = 1000                  # 每次最大返回 1000 根（Binance 限制）

# 2. 计算起始时间戳（毫秒）
utc_now = datetime.now(timezone.utc)
# 将 2025-06-21T19:08:42 转为 UTC 时间
since_dt = datetime(2025, 1, 23, 19, 8, 42)
since_ms = exchange.parse8601(since_dt.strftime("%Y-%m-%dT%H:%M:%SZ"))

all_ohlcv = []                     # 存放所有 kline
while True:
    ohlcv = exchange.fetch_ohlcv(
        symbol, timeframe=timeframe, since=since_ms, limit=limit_each
    )
    if not ohlcv:                  # 抓取完毕
        break

    all_ohlcv.extend(ohlcv)

    # 3. 设定下一轮的起点（上一次最后一根的下一分钟）
    since_ms = ohlcv[-1][0] + 60_000

    # 若少于 limit_each 说明已到最新
    if len(ohlcv) < limit_each:
        break

# 4. 转 DataFrame 并保存
cols = ["timestamp", "open", "high", "low", "close", "volume"]
df   = pd.DataFrame(all_ohlcv, columns=cols)

# 时间戳转为韩国时区（可改成你想要的）
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)\
                     .dt.tz_convert("Asia/Seoul")

# 5. 存成 CSV
csv_path = "BTC_1m_last30days.csv"
df.to_csv(csv_path, index=False, encoding="utf-8-sig")
print(f"🎉 已保存 {len(df):,} 条记录 -> {csv_path}")
