
import os
import sys

from flask import app, jsonify
import numpy as np


base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, f"{base_dir}")
from config.settings import Config

from servicemodels import Activities, ScanResult, Position, Trade, scan_market, DailyPrice, OneDayPrice, db

import alpaca_trade_api as tradeapi
api = tradeapi.REST(Config.ALPACA_API_KEY, Config.ALPACA_SECRET_KEY, Config.ALPACA_BASE_URL)
SYMBOLS = ["AAPL", "NVDA", "TSLA", "AMD", "MSFT", "SPY"]
COLORS = ["blue","orange","green","yellow","red","brown"]


from alpaca_trade_api.rest import REST
from datetime import datetime, timedelta, timezone

#get_daytrading("AAPL","2026-04-02",5)        #计算 “$/5分钟变化”
def get_daytrading(symbol, date, min):
    end = datetime.utcnow()
    start = end - timedelta(days=30)        
    bars = api.get_bars(
        symbol,
        min, 
        start = start.isoformat() + "Z",
        end = end.isoformat() + "Z",
        adjustment = 'raw',
        feed='iex'
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
    now = datetime.utcnow()
    # 今天 00:00 UTC
    today_start = datetime(now.year, now.month, now.day)
    # 删除昨天及之前的数据
    OneDayPrice.query.filter(
        OneDayPrice.timestamp < today_start
    ).delete()
    db.session.commit()    


from datetime import datetime, timedelta
import pytz

def get_today_5min(symbol):
    # 美东时间
    est = pytz.timezone("US/Eastern")

    now = datetime.now(est)

    # 今日开盘时间
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_end = now.replace(hour=15, minute=0, second=0, microsecond=0)
    # 👉 转 UTC（Alpaca 必须）
    start = market_open.astimezone(pytz.utc)
    end = market_end.astimezone(pytz.utc)

    bars = api.get_bars(
        symbol,
        "5Min",
        start=start.isoformat(),
        end=end.isoformat(),
        feed="iex"   # 🔥 免费账户必须加
    ).df

    return bars

def update_symbols_day_prices():  # core function
    try:
        clock = api.get_clock()
        if clock.is_open:
            OneDayPrice.query.delete()
            for symbol in SYMBOLS:
                bars = get_today_5min(symbol) #api.get_bars(symbol, "5Min", limit=30)
                if bars.empty:
                    continue
                for index, row in bars.iterrows():
                    db.session.add(OneDayPrice(
                        symbol=symbol,
                        price_open=round(float(row['open']), 2),
                        price_close=round(float(row['close']), 2),
                        volume=round(float(row['volume']), 2),
                        high=round(float(row['high']), 2),
                        low=round(float(row['low']), 2),
                        vw=round(float(row['vwap']), 2),
                        timestamp=index
                    ))
            db.session.commit()   # 🔥 一次提交（性能更好）
    except Exception as e:
        print(e)
    result = []

    for i, s in enumerate(SYMBOLS):
        #rows = DailyPrice.query.filter_by(symbol=s).order_by(DailyPrice.date).all()
        rows = OneDayPrice.query.filter_by(symbol=s).order_by(OneDayPrice.timestamp).all()
        dates = [r.timestamp.strftime("%H:%M") for r in rows]
        prices = [r.price_close for r in rows]

        result.append({
            "symbol": s,
            "dates": dates,
            "prices": prices,
            "color": COLORS[i]
        })

    return jsonify(result)


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
        activitie = Activities(
            id=tradid, # a.id.split("::")[0],   # 用 Alpaca ID 防重复
            symbol=a.symbol,
            side=a.side.upper(),
            qty=float(a.qty),
            price=float(a.price),
            timestamp = dt
        )
        db.session.add(activitie)

def update_symbols_trades():
    
    activities = []
    page_token = None

    while True:
        res = api.get_activities(
            activity_types="FILL",
            page_token=page_token,
            direction="desc"  # newest first
        )

        if not res:
            break

        activities.extend(res)

        # get next page token
        page_token = res[-1].id

        # stop if less than 100 (last page)
        if len(res) < 100:
            break    
    try:        
        #activities = api.get_activities(activity_types="FILL")
        if activities:
            activities = sorted(activities, key=lambda x: x.id, reverse=False)     

            Trade.query.delete()
            for a in activities:
                """                
                pnl = None                                
                if a.side == 'buy':
                    total_buy_qty = total_buy_qty + int(a.qty)
                    total_buy = total_buy + float(a.price)*int(a.qty)  
                else:
                    total_sell_qty = total_sell_qty + int(a.qty)
                    total_sell = total_sell + float(a.price)*int(a.qty)  
                if total_buy_qty == total_sell:
                    pnl = total_sell - total_buy   
                """
                tradid=a.id.split("::")[0]                
                trade = Trade(
                    id=tradid,
                    activity_type=a.activity_type,
                    cum_qty=int(a.cum_qty),                
                    leaves_qty=int(a.leaves_qty),
                    price=round(float(a.price), 2),
                    qty=int(a.qty),
                    side=a.side,
                    symbol=a.symbol,       
                    order_id = a.order_id,
                    type = a.type,
                    #pnl = pnl,          
                    transaction_time = a.transaction_time
                )
                db.session.add(trade)    
            db.session.commit()


            for symbol in SYMBOLS:
                total_buy_qty = 0
                total_sell_qty = 0
                total_buy = 0
                total_sell = 0                            
                rows = Trade.query.filter_by(symbol=symbol).order_by(Trade.id.asc()).all()
                
                for a in rows:
                    if a.side == 'buy':
                        total_buy_qty = total_buy_qty + int(a.qty)
                        total_buy = total_buy + float(a.price)*int(a.qty)  
                    else:
                        total_sell_qty = total_sell_qty + int(a.qty)
                        total_sell = total_sell + float(a.price)*int(a.qty)  
                    if total_buy_qty == total_sell_qty:
                        a.pnl = round((total_sell - total_buy),2)   
                        db.session.add(a)
            db.session.commit()

    except Exception as e:
        print(e)
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

def update_symbols_scan():
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

def update_symbols_positions():  # core functions
    try:
        positions = api.list_positions()
        if positions:
            # 🧹 清空旧表
            Position.query.delete()
            # 📝 写入新数据
            for p in positions:
                if int(p.qty) <= 0:
                    continue
                pos = Position(
                    symbol=p.symbol,
                    quantity=int(p.qty),
                    avg_price=round(float(p.avg_entry_price), 2)
                )
                db.session.add(pos)
                print(p.symbol, p.qty, p.avg_entry_price, p.unrealized_pl)        
            db.session.commit()
    except Exception as e:
        print(e)
    rows = Position.query.all()
    return [
        {
            "symbol": r.symbol,
            "qty": r.quantity,
            "price": round(r.avg_price, 2),
            "time": r.updated_at.strftime("%m/%d %H:%M") if r.updated_at else ""
        }
        for r in rows
    ]

def update_symbols_daily_prices():
    #clock = api.get_clock()
    #if clock.is_open:
    try:
        result = []    
        # ❗不要在循环里 delete
        DailyPrice.query.delete()
        for symbol in SYMBOLS:

            end = datetime.utcnow().replace(microsecond=0)
            start = end - timedelta(days=30)

            bars = api.get_bars(
                symbol,
                "1Day",
                start=start.isoformat() + "Z",
                end=end.isoformat() + "Z",
                adjustment='raw',
                feed='iex'
            ).df    

            if bars.empty:
                continue

            for index, row in bars.iterrows():

                db.session.add(DailyPrice(
                    symbol=symbol,
                    date=index.date(),
                    avg_price=round(float(row["close"]), 2)   # ✅ 修复
                ))

        db.session.commit()   # 🔥 一次提交（性能更好）
    #result = []
    except Exception as e:
        print (e)

    for i, s in enumerate(SYMBOLS):
        rows = DailyPrice.query.filter_by(symbol=s).order_by(DailyPrice.date).all()

        dates = [r.date.strftime("%Y-%m-%d") for r in rows]
        prices = [r.avg_price for r in rows]
        """
        # 🔥 获取交易记录
        trades = Activities.query.filter_by(symbol=s).all()

        trade_points = []
        for t in trades:
            t_date = t.timestamp.strftime("%Y-%m-%d")

            # 👉 找对应 index
            if t_date in dates:
                idx = dates.index(t_date)
            else:
                # 👉 fallback：找最近日期
                idx = min(range(len(dates)), key=lambda i: abs(
                    (rows[i].date - t.timestamp).total_seconds()
                ))

            trade_points.append({
                "index": idx,      # 🔥 关键：直接传 index
                "side": t.side,
                "reason": "resone", # t.reason,
                "pnl": 0 # #t.pnl
            })
        """
        result.append({
            "symbol": s,
            "dates": dates,
            "prices": prices,
            #"trades": trade_points,   # 🔥 已经对齐
            "color": COLORS[i]
        })

    return jsonify(result)



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
    update_symbols_scan()     # 先选股
    sync_trades_from_alpaca()
    trade_executor()   


##################
# new models
##################
def get_current_price(symbol):
    trade = api.get_latest_trade(symbol)
    return float(trade.price)

def get_last_n_high(symbol, n=5):
    """
    Get the highest close price for the last n days.
    """
    rows = DailyPrice.query.filter_by(symbol=symbol) \
                            .order_by(DailyPrice.date.desc()) \
                            .limit(n).all()
    if not rows:
        return None
    return max([r.avg_price for r in rows])

def get_moving_averages(symbol, periods=[5, 20, 50]):
    """
    Calculate simple moving averages for given periods.
    Returns a dict { period: avg_price }
    """
    ma = {}
    for period in periods:
        rows = DailyPrice.query.filter_by(symbol=symbol) \
                                .order_by(DailyPrice.date.desc()) \
                                .limit(period).all()
        if not rows:
            ma[period] = None
        else:
            ma[period] = sum([r.avg_price for r in rows]) / len(rows)
    return ma

def should_buy(symbol, price, last_high, ma_short, ma_long):
    # 突破策略 + 均线策略
    if price > last_high:
        return True, "Breakout above high"
    if ma_short > ma_long and price > ma_short:
        return True, "Bullish crossover"
    return False, ""

def should_sell(symbol, price, cost_price, pnl, stop_loss=-0.01, take_profit=0.02):
    # 止盈止损
    if pnl / (cost_price * Position.query.filter_by(symbol=symbol).first().quantity) <= stop_loss:
        return True, "Stop loss"
    if pnl / (cost_price * Position.query.filter_by(symbol=symbol).first().quantity) >= take_profit:
        return True, "Take profit"
    return False, ""

def buy(symbol, qty, price, reason):
    try:
        api.submit_order(
            symbol=symbol,
            qty=qty,
            side="buy",
            type="market",
            time_in_force="day"
        )


        pos = Position.query.filter_by(symbol=symbol).first()
        if pos:
            # 加仓：更新均价和数量
            total_cost = pos.avg_price * pos.quantity + price * qty
            pos.quantity += qty
            pos.avg_price = total_cost / pos.quantity
            pos.last_update = datetime.utcnow()
        else:
            pos = Position(symbol=symbol, quantity=qty, avg_price=price)
            db.session.add(pos)
        
        # 记录交易
        trade = Trade(symbol=symbol, side="BUY", qty=qty, price=price, reason=reason)
        db.session.add(trade)
        db.session.commit()
    except Exception as e:
        print(e)
def sell(symbol, reason):
    try:

        pos = Position.query.filter_by(symbol=symbol).first()
        if not pos or pos.quantity <= 0:
            return 0  # 无持仓
        qty = pos.quantity
        price = get_current_price(symbol)  # 通过 API 获取当前价格
        pnl = round((price - pos.avg_price) * qty, 2)
        
        api.submit_order(
            symbol=pos.symbol,
            qty=pos.quantity,
            side="sell",
            type="market",
            time_in_force="day"
        )


        # 更新持仓
        pos.quantity = 0
        pos.avg_price = 0
        pos.last_update = datetime.utcnow()
        
        # 记录交易
        trade = Trade(symbol=symbol, side="SELL", qty=qty, price=price, reason=reason, pnl=pnl)
        db.session.add(trade)
        db.session.commit()
    except Exception as e:
        return    
    return pnl

def auto_trade_1():
    for symbol in SYMBOLS:
        price = get_current_price(symbol)
        pos = Position.query.filter_by(symbol=symbol).first()
        # 买入策略：价格上涨突破或加仓
        if not pos or pos.quantity == 0:
            buy(symbol, 10, price, "Breakout")
        # 卖出策略：简单止盈止损
        elif pos and pos.quantity > 0:
            pnl = (price - pos.avg_price) * pos.quantity
            if pnl >= 5:
                sell(symbol, "Take Profit")
            elif pnl <= -3:
                sell(symbol, "Stop Loss")

def auto_trade():
    for symbol in SYMBOLS:
        price = get_current_price(symbol)
        pos = Position.query.filter_by(symbol=symbol).first()
        qty = 10  # 固定买入数量，可改成策略

        # 买入策略
        last_high = get_last_n_high(symbol, 20)
        ma = get_moving_averages(symbol, [5, 20])
        ma_short = ma[5]
        ma_long = ma[20]
        buy_flag, reason = should_buy(symbol, price, last_high, ma_short, ma_long)
        #if buy_flag:
        #    buy(symbol, qty, price, reason)

        # 卖出策略
        if pos and pos.quantity > 0:
            pnl = (price - pos.avg_price) * pos.quantity
            sell_flag, reason = should_sell(symbol, price, pos.avg_price, pnl)
            if sell_flag:
                sell(symbol, reason)

