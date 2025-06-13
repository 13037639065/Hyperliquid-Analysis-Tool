# Hyperliquid分析工具

该工具主要利用hyperliquid python sdk这个lib来进行数据分析。寻找链上内幕哥

## 主要功能

### 地址分析

python工具1：用户地址分析

功能如下：
1. 输入地址和代币信息。展示该地址在代币K线下的买入卖出信息。以K线图展示。总结他的收益和ROI信息

## 安装

``` bash
conda create -n trade python=3.12.9
conda activate trade
pip3 install hyperliquid-python-sdk python-binance matplotlib mplfinance numpy
```