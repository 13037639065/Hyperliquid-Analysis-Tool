#!/usr/bin/env python3
# coding: utf-8
"""
grid_print.py  ―― 网格挂单/持仓价格可视化
Usage:
    python grid_print.py yourfile.csv
"""

import sys, json, pandas as pd

def parse(cell: str):
    """安全解析 BUY/SELL/POSITION 的 JSON 列"""
    try:
        return json.loads(cell)
    except Exception:
        return []

label_map = {
    "BUY": "🟢",
    "SELL": "🟥",
    "ENTRY": "🟣",
    "PRICE": "🟡"
}
def colorize(num: float, cat: str) -> str:
    """把数字加上对应颜色"""
    return f"{label_map[cat]}{num}"


def process_csv(path: str):
    df = pd.read_csv(path, dtype=str)

    # 解析 JSON 列
    for col in ("BUY", "SELL", "POSITION"):
        df[col] = df[col].apply(parse)

    # 逐行处理
    for _, row in df.iterrows():
        items = []

        # 现价
        items.append(("PRICE", float(row["price"])))

        # 持仓入场价（可能有多仓）
        items += [("ENTRY", float(pos.get("entryPx", 0))) for pos in row["POSITION"]]

        # 买 / 卖 挂单
        items += [("BUY",  float(o["price"])) for o in row["BUY"]]
        items += [("SELL", float(o["price"])) for o in row["SELL"]]

        # 按价格由小到大排序
        items.sort(key=lambda x: x[1])

        print(f"{row['time']}\tsize = {row["POSITION"][0].get("size", 0)}")
        print("\t".join(colorize(p, t) for t, p in items))
        gaps = [f"{items[i+1][1] - items[i][1]:.4f}" for i in range(len(items) - 1)]
        print("\t".join(gaps))
        print("-" * 40)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python grid_print.py yourfile.csv")
        sys.exit(1)

    process_csv(sys.argv[1])
