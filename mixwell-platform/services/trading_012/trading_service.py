import os
import sys

from flask import app
import numpy as np


base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, f"{base_dir}")
from config.settings import Config

from servicemodels import Trade, Activities, ScanResult, Position, scan_market, db

import alpaca_trade_api as tradeapi
api = tradeapi.REST(Config.ALPACA_API_KEY, Config.ALPACA_SECRET_KEY, Config.ALPACA_BASE_URL)
SYMBOLS = ["AAPL", "NVDA", "TSLA", "AMD", "MSFT", "SPY"]

from alpaca_trade_api.rest import REST
from datetime import datetime

#get_daytrading("AAPL","2026-04-02",5)        #计算 “$/5分钟变化”
def get_daytrading(symbol, date, min):
    bars = api.get_bars(
        symbol,
        min, 
        start= date,
        end=date,
        adjustment='raw'
    ).df
    print(bars.head())
    return bars    

#计算 最近变化
def scan_market():
    clock = api.get_clock()

    if not clock.is_open:
        print("Market closed, skip scanning")
#        return []

    results = []

    for symbol in SYMBOLS:
#        bars = api.get_bars(symbol, "1Min", limit=30).df
        bars = get_daytrading(symbol,"2026-04-02","5min")

        if len(bars) < 2:
            continue

        change = (bars["close"].iloc[-1] - bars["close"].iloc[0]) / bars["close"].iloc[0]
        volume = bars["volume"].mean()

        results.append({
            "symbol": symbol,
            "change": change,
            "volume": volume
        })

    return results

def sync_trades_from_alpaca():
    activities = api.get_activities(activity_types="FILL")

    for a in activities:
        exists = Activities.query.filter_by(id=a.id).first()
        if exists:
            continue
        ts = a.transaction_time
        if isinstance(ts, str):
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        else:
            dt = ts
        activities = Activities(
            id=a.id.split("::")[0],   # 用 Alpaca ID 防重复
            symbol=a.symbol,
            side=a.side.upper(),
            qty=float(a.qty),
            price=float(a.price),
            timestamp = dt
        )
        db.session.add(activities)

    db.session.commit()

def get_recommended_symbols():
    # 临时：用 movers 代替
    movers = []

    for symbol in SYMBOLS:
        bars = get_daytrading(symbol,"2026-04-02","5min") #api.get_bars(symbol, "5Min", limit=12).df
        if len(bars) < 2:
            continue

        change = (bars["close"].iloc[-1] - bars["close"].iloc[0]) / bars["close"].iloc[0]
        movers.append((symbol, change))

    movers.sort(key=lambda x: x[1], reverse=True)

    return [m[0] for m in movers[:5]]

def build_scan_results():
    scan = scan_market()
    scan_symbols = [x["symbol"] for x in scan[:5]]

    recommended = get_recommended_symbols()

    combined = list(dict.fromkeys(scan_symbols + recommended))

    final = []

    for symbol in combined:
        bars = get_daytrading(symbol, "2026-04-02", "5min")

        if len(bars) < 2:
            continue

        change = (bars["close"].iloc[-1] - bars["close"].iloc[0]) / bars["close"].iloc[0]
        volume = bars["volume"].mean()
        volatility = bars["close"].pct_change().std()

        # 防止 volatility 为 0 或 NaN
        if volatility is None or volatility == 0 or np.isnan(volatility):
            volatility = 1e-6

        score = change * volume / volatility

        # 价格和时间
        price = float(bars["close"].iloc[-1])
        timestamp = bars.index[-1]

        # ✅ 保留 2 位小数
        final.append({
            "symbol": symbol,
            "score": round(score, 2),
            "price": round(price, 2),
            "volume": round(float(volume), 2),
            "timestamp": timestamp,
        })

    # 按 score 排序
    final.sort(key=lambda x: x["score"], reverse=True)

    return final

def build_scan_results1():
    scan = scan_market()
    scan_symbols = [x["symbol"] for x in scan[:5]]

    recommended = get_recommended_symbols()

    combined = list(dict.fromkeys(scan_symbols + recommended))

    final = []

    for symbol in combined:
        #bars = api.get_bars(symbol, "5Min", limit=12).df
        bars = bars = get_daytrading(symbol,"2026-04-02", "5min")
        if len(bars) < 2:
            continue

        change = (bars["close"].iloc[-1] - bars["close"].iloc[0]) / bars["close"].iloc[0]
        volume = bars["volume"].mean()
        volatility = bars["close"].pct_change().std()
        price = float(bars["close"].iloc[-1])
        timestamp = bars.index[-1]
        score = change * volume / (volatility + 1e-6)

        final.append({
            "symbol": symbol,
            "score": score,
            "price": price,
            "volume": volume,
            "timestamp": timestamp,
        })

    final.sort(key=lambda x: x["score"], reverse=True)

    return final

def update_scan_results():
    results = build_scan_results()
    ScanResult.query.delete()
    for r in results:
        db.session.add(ScanResult(
            symbol=r["symbol"],
            score=float(r["score"]),   # ✅ 修复这里
            price=float(r["price"]) if r.get("price") else None,
            volume=float(r["volume"]) if r.get("volume") else None,
            timestamp=r.get("timestamp")
        ))

    db.session.commit()

def get_top_movers():
    movers = []

    for symbol in SYMBOLS:   # 或扩展成 S&P500
        #bars = api.get_bars(symbol, "5Min", limit=12).df
        bars = get_daytrading(symbol,"2026-04-02", "5min")
        if len(bars) < 2:
            continue

        change = (bars["close"].iloc[-1] - bars["close"].iloc[0]) / bars["close"].iloc[0]

        movers.append((symbol, change))

    movers.sort(key=lambda x: x[1], reverse=True)

    return [m[0] for m in movers[:5]]

def get_final_symbols():
    # 1️⃣ 你自己的扫描
    scan_results = scan_market()
    scan_symbols = [x["symbol"] for x in scan_results[:5]]

    # 2️⃣ “推荐”股票（模拟或 movers）
    recommended = get_top_movers()

    # 3️⃣ 合并 + 去重
    combined = list(dict.fromkeys(scan_symbols + recommended))

    # 4️⃣ 再排序（再打一层分）
    scored = []

    for symbol in combined:
        #bars = api.get_bars(symbol, "5Min", limit=12).df
        bars = get_daytrading(symbol,"2026-04-02","5min")
        if len(bars) < 2:
            continue

        change = (bars["close"].iloc[-1] - bars["close"].iloc[0]) / bars["close"].iloc[0]
        volume = bars["volume"].mean()

        score = change * volume

        scored.append((symbol, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    # 5️⃣ 只选3个
    final_symbols = [s[0] for s in scored[:3]]

    return final_symbols

def trade_executor(symbols):
    for symbol in symbols:

        # 已持仓跳过
        pos = Position.query.get(symbol)
        if pos and pos.quantity > 0:
            continue

        try:
            api.submit_order(
                symbol=symbol,
                qty=1,
                side="buy",
                type="market",
                time_in_force="day"
            )

            # 写入 trades
            trade = Trade(
                symbol=symbol,
                side="BUY",
                quantity=1,
                price=0   # 可后面补真实成交价
            )
            db.session.add(trade)

        except Exception as e:
            print("Trade error:", e)

    db.session.commit()    

def execute_sell(pos, price, reason):
    try:
        api.submit_order(
            symbol=pos.symbol,
            qty=pos.quantity,
            side="sell",
            type="market",
            time_in_force="day"
        )

        # 记录 trade
        db.session.add(Trade(
            symbol=pos.symbol,
            side="SELL",
            quantity=pos.quantity,
            price=price
        ))

        # 清仓
        pos.quantity = 0
        pos.avg_price = 0

        print(f"SELL {pos.symbol} due to {reason}")

        db.session.commit()

    except Exception as e:
        print("Sell error:", e)

def check_sell_signals():
    positions = Position.query.all()

    for pos in positions:
#        bars = api.get_bars(pos.symbol, "5Min", limit=1).df
        bars = get_daytrading(pos.symbol,"2026-04-02","5min")
        if bars.empty:
            continue

        current_price = bars["close"].iloc[-1]
        change = (current_price - pos.avg_price) / pos.avg_price

        # ✅ 止盈
        if change >= 0.03:
            execute_sell(pos, current_price, "take_profit")

        # ✅ 止损
        elif change <= -0.02:
            execute_sell(pos, current_price, "stop_loss")

def get_activities():
    trades = Activities.query.order_by(Activities.timestamp.desc()).all()
    return trades 

def get_final_symbols():    
    symbos = ScanResult.query.order_by(ScanResult.score.desc()).limit(3).all()
    return symbos

def get_positions():    
    positions = Position.query.all()
    return positions


def run_bot():
    sync_trades_from_alpaca()

    update_scan_results()

    symbols = get_final_symbols()

    trade_executor(symbols)

    check_sell_signals()

