import os
import sys

import alpaca_trade_api as tradeapi
import pandas as pd
#from config import *
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, f"{base_dir}")
from config.settings import Config

api = tradeapi.REST(Config.ALPACA_API_KEY, Config.ALPACA_SECRET_KEY, Config.ALPACA_BASE_URL)

SYMBOLS = ["AAPL", "NVDA", "TSLA", "AMD", "MSFT", "SPY"]

def scan_market():

    results = []

    for symbol in SYMBOLS:
        bars = api.get_bars(symbol, "1Min", limit=30, adjustment='raw').df

        if len(bars) < 2:
            continue

        change = (bars["close"].iloc[-1] - bars["close"].iloc[0]) / bars["close"].iloc[0]
        volume = bars["volume"].mean()

        score = change * volume

        results.append({
            "symbol": symbol,
            "score": score,
            "price": bars["close"].iloc[-1],
            "volume": volume
        })
        
    df = pd.DataFrame(results)
    df = df.sort_values("score", ascending=False)

    return df.head(3)  # 选Top 3