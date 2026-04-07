
import os
import sys

from flask import app
import numpy as np


base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, f"{base_dir}")
from config.settings import Config

from servicemodels import Trade, Activities, ScanResult, Position, scan_market, DailyPrice, OneDayPrice, db

import alpaca_trade_api as tradeapi
api = tradeapi.REST(Config.ALPACA_API_KEY, Config.ALPACA_SECRET_KEY, Config.ALPACA_BASE_URL)
SYMBOLS = ["AAPL", "NVDA", "TSLA", "AMD", "MSFT", "SPY"]

from alpaca_trade_api.rest import REST
from datetime import datetime, timezone

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
        bars = api.get_bars(symbol, "5Min", limit=30).df
        #bars = get_daytrading(symbol,"2026-04-02","5min")

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

def clean_old_prices():
    today = datetime.utcnow().date()   
    OneDayPrice.query.filter(
        db.func.date(OneDayPrice.timestamp) < today
    ).delete()
    db.session.commit()

def scan_market_store():
    clock = api.get_clock()

    if not clock.is_open:
        print("Market closed, still record last data")

    new_rows = []
    clean_old_prices()   # ✅ 关键
    for symbol in SYMBOLS:
        last = OneDayPrice.query\
            .filter_by(symbol=symbol)\
            .order_by(OneDayPrice.timestamp.desc())\
            .first()

        last_ts = last.timestamp if last else None

        bars = api.get_bars(symbol, "5Min", limit=30)

        for bar in bars:
            # 假设 bar.t 是 offset-aware
            ts = bar.t  # 已经是 UTC aware

            # last_ts 从 DB 取出，需要加 tzinfo
            if last_ts:
                last_ts = last_ts.replace(tzinfo=timezone.utc)
            # ✅ 跳过旧数据
            if last_ts and ts <= last_ts:
                continue

            new_rows.append(OneDayPrice(
                symbol=symbol,
                price_open=round(float(bar.o), 2),
                price_close=round(float(bar.c), 2),
                volume=round(float(bar.v), 2),
                high=round(float(bar.h), 2),
                low=round(float(bar.l), 2),
                vw=round(float(bar.vw), 2),
                timestamp=ts
                ))

    db.session.bulk_save_objects(new_rows)
    db.session.commit()

def sync_trades_from_alpaca():
    activities = api.get_activities(activity_types="FILL")

    for a in activities:
        tradid=a.id.split("::")[0]
        exists = Activities.query.filter_by(id=tradid).first()
        if exists:
            continue
        ts = a.transaction_time
        if isinstance(ts, str):
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        else:
            dt = ts
        activities = Activities(
            id=tradid, # a.id.split("::")[0],   # 用 Alpaca ID 防重复
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
        bars = api.get_bars(symbol, "5Min", limit=12).df
        #bars = get_daytrading(symbol,"2026-04-02","5min") #api.get_bars(symbol, "5Min", limit=12).df
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
        bars = api.get_bars(symbol, "5Min", limit=12).df
        #bars = bars = get_daytrading(symbol,"2026-04-02", "5min")
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
        bars = api.get_bars(symbol, "5Min", limit=12).df
        #bars = get_daytrading(symbol,"2026-04-02", "5min")
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
        bars = api.get_bars(symbol, "5Min", limit=12).df
        #bars = get_daytrading(symbol,"2026-04-02","5min")
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
        pos = Position.query.get(symbol.symbol)
        if pos and pos.quantity > 0:
            continue

        try:
            api.submit_order(
                symbol=symbol.symbol,
                qty=1,
                side="buy",
                type="market",
                time_in_force="day"
            )

            # 写入 trades
            trade = Trade(
                symbol=symbol.symbol,
                side="BUY",
                qty=1,
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
        bars = api.get_bars(pos.symbol, "5Min", limit=1).df
        #bars = get_daytrading(pos.symbol,"2026-04-02","5min")
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




def build_daily_price(symbol, date_str):
    bars = get_daytrading(symbol, date_str, "5min")

    if len(bars) == 0:
        return None

    avg_price = bars["close"].mean()
    high = bars["high"].max()
    low = bars["low"].min()
    volume = bars["volume"].sum()

    return {
        "symbol": symbol,
        "date": bars.index[-1].date(),
        "avg_price": float(avg_price),
        "high": float(high),
        "low": float(low),
        "volume": float(volume),
    }

def update_daily_prices():
    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    for symbol in SYMBOLS:
        data = build_daily_price(symbol, today_str)

        if not data:
            continue

        existing = DailyPrice.query.filter_by(
            symbol=data["symbol"],
            date=data["date"]
        ).first()

        if existing:
            existing.avg_price = round(data["avg_price"], 2)
            existing.high = round(data["high"], 2)
            existing.low = round(data["low"], 2)
            existing.volume = round(data["volume"], 2)
        else:
            db.session.add(DailyPrice(
                symbol=data["symbol"],
                date=data["date"],
                avg_price=round(data["avg_price"], 2),
                high=round(data["high"], 2),
                low=round(data["low"], 2),
                volume=round(data["volume"], 2),
            ))

    db.session.commit()

from datetime import date
from sqlalchemy import func

def update_daily_prices():
    for symobl in SYMBOLS:
        try:
            bars = api.get_bars(symobl, "1Day", limit=30).df
            for bar in bars:
                avg_price = 0 # bar.vw
                day = "" # bar.timesample
        except Exception as e:
            print(e)
        return bars
        
        """
        daily = DailyPrice.query.filter_by(
            symbol=symobl,
            date=day
        ).first()

        if not daily:
            db.session.add(DailyPrice(
                symbol=symobl,
                avg_price=round(avg_price, 2),
                date=date
            ))

    db.session.commit()
    """

    bars = api.get_bars("AAPL", "1Day", limit=30).df

    for idx, row in bars.iterrows():
        avg_price = row["vw"]  # ✅ BEST

        daily = DailyPrice.query.filter_by(
            symbol="AAPL",
            date=idx.date()
        ).first()

        if not daily:
            db.session.add(DailyPrice(
                symbol="AAPL",
                avg_price=round(avg_price, 2),
                date=idx.date()
            ))

    db.session.commit()

#可以落地、能接你现有系统的 Top 50 自动选股方案（生产可用版）


def get_top_symbols():
    assets = api.list_assets(status='active')

    symbols = [
        a.symbol for a in assets
        if a.tradable and a.exchange in ["NASDAQ", "NYSE"]
    ]

    #return symbols[:100]   # ⚠️ 控制数量
    return symbols

def scan_top_50_symbols():
    symbols =get_top_symbols() # get_tradable_symbols()   # 你已有 or Alpaca assets
    
    scored = []

    for symbol in symbols:
        try:
            data = get_symbol_data(symbol)

            score = calculate_score(data)

            scored.append({
                "symbol": symbol,
                "score": score,
                "price": data["price"]
            })

        except Exception as e:
            continue

    # 排序
    top_50 = sorted(scored, key=lambda x: x["score"], reverse=True)[:50]

    return top_50

import requests

FINNHUB_API_KEY = "your_key"

def get_symbol_data(symbol):
    quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
    metric_url = f"https://finnhub.io/api/v1/stock/metric?symbol={symbol}&metric=all&token={FINNHUB_API_KEY}"

    q = requests.get(quote_url).json()
    m = requests.get(metric_url).json()

    return {
        "price": q.get("c", 0),
        "change": q.get("dp", 0),  # % change
        "pe": m.get("metric", {}).get("peBasicExclExtraTTM", 0),
        "growth": m.get("metric", {}).get("revenueGrowthTTM", 0),
        "rsi": m.get("metric", {}).get("rsi", 50),
        "volume": q.get("v", 0)}

def calculate_score(d):
    score = 0

    # 动量（短线）
    score += 0.3 * normalize(d["change"], -5, 5)

    # 成长性（中长线）
    score += 0.25 * normalize(d["growth"], -0.2, 0.5)

    # RSI（避免超买）
    score += 0.2 * (1 - abs(d["rsi"] - 50) / 50)

    # PE（估值）
    if d["pe"] > 0:
        score += 0.15 * normalize(1 / d["pe"], 0, 0.2)

    # 成交量（流动性）
    score += 0.1 * normalize(d["volume"], 1e5, 1e8)

    return score

def normalize(value, min_v, max_v):
    if value is None:
        return 0
    return max(0, min(1, (value - min_v) / (max_v - min_v)))

def run_trading_cycle():
    update_scan_results()     # 先选股
    sync_trades_from_alpaca()
    trade_executor()   