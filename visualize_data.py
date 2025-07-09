import pandas as pd
import matplotlib.pyplot as plt
import ast


# 
df = pd.read_csv('./trading_data_cache/oops/xxx.csv')

# 先只分析 1000条数据
df = df.head(1000)

# 解析BUY, SELL, POSITION列
df['BUY'] = df['BUY'].apply(ast.literal_eval)
df['SELL'] = df['SELL'].apply(ast.literal_eval)
df['POSITION'] = df['POSITION'].apply(ast.literal_eval)

# 展开BUY列表到单独的DataFrame行
df_buy = pd.DataFrame([(t, item['price'], item['size']) for t, items in df[['time', 'BUY']].values for item in items],
                   columns=['time', 'buy_price', 'buy_size'])

# 展开SELL列表到单独的DataFrame行
df_sell = pd.DataFrame([(t, item['price'], item['size']) for t, items in df[['time', 'SELL']].values for item in items],
                    columns=['time', 'sell_price', 'sell_size'])

# 提取POSITION信息
df_position = pd.DataFrame([(item['size'], item['unrealizedPnl'], item['entryPx']) for items in df['POSITION'] for item in items],
                        columns=['position_size', 'position_unrealizedPnl', 'position_entryPx'])

df_buy['buy_price'] = df_buy['buy_price'].astype(float)
df_buy['buy_size'] = df_buy['buy_size'].astype(float)
df_sell['sell_price'] = df_sell['sell_price'].astype(float)
df_sell['sell_size'] = df_sell['sell_size'].astype(float)
df_position['position_size'] = df_position['position_size'].astype(float)
df_position['position_unrealizedPnl'] = df_position['position_unrealizedPnl'].astype(float)
df_position['position_entryPx'] = df_position['position_entryPx'].astype(float)

# 绘图plt.figure(figsize=(14, 7))

# 买入订单价格与大小
plt.scatter(df_buy['time'], df_buy['buy_price'], s=df_buy['buy_size']*1000, alpha=0.5, c='green', label='Buy Orders')

# 卖出订单价格与大小
plt.scatter(df_sell['time'], df_sell['sell_price'], s=df_sell['sell_size']*1000, alpha=0.5, c='red', label='Sell Orders')

# 当前持仓价格
plt.axhline(y=df_position.iloc[0]['position_entryPx'], color='blue', linestyle='--', linewidth=2, label='Position Entry Price')

plt.xticks(rotation=45) # 旋转x轴标签以便更好地显示时间
plt.xlabel('Time')
plt.ylabel('Price')
plt.title('Buy/Sell Orders and Position Entry Price over Time')
plt.legend()
plt.tight_layout()  # 调整布局以防止裁剪

# 显示图表
plt.show()