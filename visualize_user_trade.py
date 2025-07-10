import pandas as pd
import vectorbt as vbt
import argparse

def get_user_fills(user_address, file_path):
    # 1. 读取数据
    df = pd.read_csv(file_path, parse_dates=["time"])
    df = df.sort_values("time").reset_index(drop=True)

    # 2. 过滤你参与的交易
    df_filtered = df[(df["user1"] == user_address) | (df["user2"] == user_address)].copy()
    df_filtered.set_index('time', inplace=True)

    # free df
    df = None
    return df_filtered

# 3. 判断你是买还是卖，并构建方向
def get_trade_direction(row, target_address):
    if row["user1"] == target_address and row["side"] == "Sell":
        return -1  # 卖出
    elif row["user2"] == target_address and row["side"] == "Sell":
        return 1   # 买入
    elif row["user1"] == target_address and row["side"] == "Buy":
        return -1  # 买出
    elif row["user2"] == target_address and row["side"] == "Buy":
        return 1   # 买入
    else:
        return 0   # 不相关（不应出现）

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="分析指定钱包地址的交易数据")
    parser.add_argument('--address', '-u', type=str, required=True, help='钱包地址')
    parser.add_argument('--file', '-f', type=str, required=True, help='CSV 文件路径')
    args = parser.parse_args()

    target_address = args.address
    file_path = args.file

    df_filtered = get_user_fills(target_address, file_path)

    df_filtered["direction"] = df_filtered.apply(lambda row: get_trade_direction(row, target_address), axis=1)

    # 添加 price/size 数据
    df_filtered["price"] = df_filtered["px"]
    df_filtered["size_signed"] = df_filtered["sz"] * df_filtered["direction"]

    print(df_filtered['size_signed'])

    # 4. 构建 Portfolio
    portfolio = vbt.Portfolio.from_orders(
        close=df_filtered["price"],
        size=df_filtered["size_signed"],
        price=df_filtered["price"],
        direction="both",
        init_cash=10000,
        size_type="amount",
        freq="1s",
        fees=0,
        slippage=0.001,
    )

    # 5. 打印统计信息
    print(portfolio.stats())

    # 6. 可视化
    portfolio.plot().show()
