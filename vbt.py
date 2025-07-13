# btc_dynamic_grid_backtest.py
"""
Back‑test Bitcoin (BTC‑USD) using a *dynamic grid* strategy.
-----------------------------------------------------------
The grid centre follows the medium‑term trend (SMA),
and grid spacing scales with a fixed percentage of price.

Requires:
  pip install yfinance vectorbt matplotlib

Run:
  python btc_dynamic_grid_backtest.py
"""

import numpy as np
import pandas as pd
import vectorbt as vbt
import matplotlib.pyplot as plt

pf = vbt.Portfolio.from_orders(
    close=[1,2,3,4,5],
    size=[0,0,0,1,0],
    size_type="amount",  # size is in BTC units
    fees=0,
    init_cash=0,
    direction="both",
    cash_sharing=True,
    freq="1min",
    call_seq="auto"  # handle long/short nets automatically
)

stats = pf.stats()
print("\n===== Performance summary =====")
print(stats.to_string())

pf.plot().show()
