import backtrader as bt
import pandas as pd

# === 限价网格策略类 ===
class LimitGridStrategy(bt.Strategy):
    params = (
        ('grid_spacing', 0.01),   # 网格间隔（1%）
        ('grid_levels', 5),       # 每边格子数
        ('grid_size', 0.001),     # 每格下单数量
    )

    def __init__(self):
        self.base_price = None
        self.grid_orders = []

    def next(self):
        current_price = self.data.close[0]

        # 初始化时设置网格中心价
        if self.base_price is None:
            self.base_price = current_price
            self.place_grid_orders()

    def place_grid_orders(self):
        # 取消所有已有订单
        for order in self.grid_orders:
            self.cancel(order)
        self.grid_orders = []

        for i in range(-self.p.grid_levels, self.p.grid_levels + 1):
            if i == 0:
                continue  # 中心价不挂单
            price = self.base_price * (1 + i * self.p.grid_spacing)
            size = self.p.grid_size

            if i < 0:
                # 低于中心价限价买入
                order = self.buy(price=price, exectype=bt.Order.Limit, size=size)
            else:
                # 高于中心价限价卖出
                order = self.sell(price=price, exectype=bt.Order.Limit, size=size)

            self.grid_orders.append(order)

    def notify_order(self, order):
        if order.status in [order.Completed]:
            print(f"{order.executed.dt}: {'BUY' if order.isbuy() else 'SELL'} Executed at {order.executed.price}")
            # 每次成交后重设网格中心
            self.base_price = order.executed.price
            self.place_grid_orders()

# === 载入历史数据 CSV ===
def load_data():
    df = pd.read_csv('trading_data_cache/kline/BTC_1m_last30days.csv', parse_dates=[0])
    df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
    df.set_index('datetime', inplace=True)
    data = bt.feeds.PandasData(dataname=df)
    return data

# === 主函数：创建引擎，添加数据和策略 ===
def run_backtest():
    cerebro = bt.Cerebro()
    cerebro.addstrategy(LimitGridStrategy)

    data = load_data()
    cerebro.adddata(data)

    cerebro.broker.setcash(100000)   # 初始资金
    cerebro.broker.setcommission(commission=0.001)  # 手续费

    print(f"初始资金: {cerebro.broker.getvalue():.2f}")
    cerebro.run()
    print(f"最终资金: {cerebro.broker.getvalue():.2f}")

    cerebro.plot()

if __name__ == '__main__':
    run_backtest()
