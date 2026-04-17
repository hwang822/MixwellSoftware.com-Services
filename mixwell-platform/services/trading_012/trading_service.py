
import os
import sys

from flask import app, json, jsonify
import numpy as np


base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, f"{base_dir}")
from config.settings import Config

from servicemodels import Account, ScanResult, Position, Trade, DailyPrice, OneDayPrice, db

import alpaca_trade_api as tradeapi
api = tradeapi.REST(Config.ALPACA_API_KEY, Config.ALPACA_SECRET_KEY, Config.ALPACA_BASE_URL)
SYMBOLS = ["AAPL", "NVDA", "TSLA", "AMD", "MSFT", "SPY"]
COLORS = ["blue","orange","green","yellow","red","brown"]
from alpaca_trade_api.rest import REST
from datetime import datetime, time, timedelta, timezone

#alpaca_prices_api("AAPL", 3, "5min", 100)
#alpaca_prices_api("AAPL", 20, "1Day", 30)
def alpaca_prices_api(symbol, days, interver, limit):
    end = datetime.utcnow()
    start = end - timedelta(days=days)        

    bars = api.get_bars(
        symbol,
        interver, 
        start = start.isoformat() + "Z",
        end = end.isoformat() + "Z",
        adjustment = 'raw',
        limit = limit,
        feed='iex'
    ).df
#    bars = api.get_bars(symbol, interver, limit).df
    result = []
    if not bars.empty:
        for index, bar in bars.iterrows():
            result.append({
                "symbol" : symbol,
                "price_open" : bar.open,
                "price_close" : bar.close,
                "volume" : bar.volume,
                "high" : bar.high,
                "low" : bar.low,
                "vw" : bar.vwap,
                "timestamp" : utc_to_est((index).strftime("%Y-%m-%d %H:%M")) 
                })             
    #print(result)
    return result 

from zoneinfo import ZoneInfo  # Built-in from Python 3.9+

def utc_to_est(time_str):
    # 1️⃣ 解析 UTC 字符串
    dt_utc = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    dt_utc = dt_utc.replace(tzinfo=ZoneInfo("UTC"))

    # 2️⃣ 转换到纽约时区（自动 EST / EDT）
    dt_est = dt_utc.astimezone(ZoneInfo("America/New_York"))

    # 3️⃣ 输出字符串
    return dt_est.strftime("%Y-%m-%d %H:%M")

# Example usage

#result = alpaca_prices_api("AAPL", 30, "1Day", 30)
#print (result)
#result = alpaca_prices_api("AAPL", 3, "5min", 100)
#print (result)


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

    results = []

    for symbol in SYMBOLS:
        bars = api.get_bars(symbol, "5Min", limit=30).df
        #bars = get_daytrading(symbol,"2026-04-02","5min")
        #bars = alpaca_prices_api("AAPL", 3, "5min", 100)
        if len(bars) < 2:
            continue

        change = (bars["close"].iloc[-1] - bars["close"].iloc[0]) / bars["close"].iloc[0]
        volume = bars["volume"].mean()
        score = change * volume
        results.append({
            "symbol": symbol,
            "change": change,
            "volume": volume,
            "score": score
        })

        results = sorted(results, key=lambda x: x["score"], reverse=True)

    return results
#scan_market()
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

position = {
    "symbol": str,
    "qty": float,
    "cost": float,        # 你的 total_cost（剩余本金）
    "avg_price": float,
    "unrealized_pnl": float,
    "profit_pct": float,
    "status": str
}
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


################################
#  update_user_account()  #
################################

def update_user_account():

    result = []           
    account = api.get_account()    
    result.append({
        "account_number": account.account_number,
        "buying_power": float(account.buying_power),
        "cash": float(account.cash),
        "equity": float(account.equity),
        "position_market_value": float(account.portfolio_value),
        "long_market_value": float(account.long_market_value),
        "short_market_value": float(account.short_market_value),
        "created_at": account.created_at.strftime("%Y-%m-%d")
    })
    return result

##################################
# Update Scan Symbols
##################################
def update_symbols_scan():    
    #from scanner import scan_market
    results = []
    scans = scan_market()
    for scan in scans:
        results.append({
                "symbol": scan["symbol"],
                "score": round(float(scan["score"]), 2),
                "price": round(float(scan["change"]), 2),
                "volume": round(float(scan["volume"]), 2)
            })
    return results
        
################################
#  update_symbols_positions()  #
################################
def update_symbols_positions():  # core functions
    result = []           
    act = api.get_account()    
    cash = float(act.cash)
    equity = float(act.equity)
    positions = api.list_positions()
    for pos in positions:
        result.append({
            "cash" : cash, 
            "equity" : equity,
            "symbol": pos.symbol,
            "cost_basis": round(float(pos.cost_basis), 2),
            "market_value": round(float(pos.market_value), 2)
        })
    return result
    
################################
# update_symbols_daily_prices()#
################################

def update_symbols_daily_prices():
    grouped = {}
    #grouped = []
    for symbol in SYMBOLS:
        prices = alpaca_prices_api(symbol, 30, "1Day", 30)        
        #grouped[symbol] = {
        #    "group" : symbol,
        #    "items" : prices
        #}
        grouped[symbol] = prices
    return grouped

#update_symbols_daily_prices()
################################
# update_symbols_day_prices()  #
################################

def update_symbols_day_prices():  # core function
    
    grouped = {}
    #grouped = []
    for symbol in SYMBOLS:
        prices = alpaca_prices_api(symbol, 1, "5min", 100)        
        #grouped[symbol] = {
        #    "group" : symbol,
        #    "items" : prices
        #}
        grouped[symbol] = prices
    return grouped

################################
# update_symbols_trades()      #
################################

def update_symbols_trades():

    activities = []
    page_token = None

    # ===== 1️⃣ 拉取 Alpaca 数据 =====
    while True:
        res = api.get_activities(
            activity_types="FILL",
            page_token=page_token,
            direction="desc"
        )
        if not res:
            break

        activities.extend(res)
        page_token = res[-1].id

        if len(res) < 100:
            break

    grouped = {}  # it is dict, easy go through
    if not activities:
        return grouped

    # ===== 2️⃣ 排序（旧 → 新）=====
    activities = sorted(activities, key=lambda x: x.transaction_time)

    # ===== 3️⃣ 分组 =====
    trades_grouped = {}   # it is dict, easy to sort
    #trades_grouped = []
    for a in activities:
        trades_grouped.setdefault(a.symbol, []).append(a)

        # ===== 4️⃣ 计算每个 symbol =====    
    for symbol, trades in trades_grouped.items():
        trade_datas = []
        total_qty = 0
        total_buy = 0
        total_sell = 0
        for t in trades:
            qty = float(t.qty)
            price = float(t.price)
            if t.side == "buy":
                total_qty += qty
                total_buy += qty * price
            elif t.side == "sell":
                total_qty -= qty
                total_sell += qty * price   # ✅ FIX
            pnl = total_sell - total_buy
            trade_data = {
                "symbol": symbol,
                "side": t.side,
                "price": round(price, 2),
                "qty": qty,
                "total_buy": round(total_buy, 2),
                "total_sell": round(total_sell, 2),
                "total_qty": round(total_qty, 2),
                "pnl": round(pnl, 2),
                "id": t.id.split("::")[0],
                "transaction_time": utc_to_est((t.transaction_time).strftime("%Y-%m-%d %H:%M"))
            }
            trade_datas.append(trade_data)
        grouped[symbol] =  trade_datas
            # ===== 5️⃣ 写 DB（可选去重）=====
            #exists = Trade.query.filter_by(id=trade_data["id"]).first()
            #if not exists:
            #   db.session.add(Trade(**trade_data))
            #db.session.commit()
    return grouped            
#update_symbols_trades()

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
"""
def run_trading_cycle():
    update_symbols_scan()     # 先选股
    sync_trades_from_alpaca()
    trade_executor()   
"""

##################
# new models
##################
def get_current_price(symbol):
    trade = api.get_latest_trade(symbol)
    return float(trade.price)

def get_last_n_high(symbol, n=5):
    try:
        """
        Get the highest close price for the last n days.
        """
        rows = DailyPrice.query.filter_by(symbol=symbol) \
                                .order_by(DailyPrice.date.desc()) \
                                .limit(n).all()
        if not rows:
            return None
        return max([r.avg_price for r in rows])
    except Exception as e: 
        print(e)
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

from datetime import datetime, timedelta
last_trade_time = {}  # 存DB更好
COOLDOWN_MINUTES = 15
def in_cooldown(symbol):
    if symbol not in last_trade_time:
        return False

    return datetime.now() - last_trade_time[symbol] < timedelta(minutes=COOLDOWN_MINUTES)

MAX_ADD = 2

def get_buy_count(symbol):
    count = Trade.query.filter_by(symbol=symbol, side="BUY").count() 
    return count

def get_alpaca_user_account():
    data = api.get_account()._raw        
    return data


MAX_TOTAL_EXPOSURE = 10000*0.8
def auto_trade():
    get_alpaca_user_account()
    for symbol in SYMBOLS:

        if in_cooldown(symbol):  #冷却时间（防止连续买）
            print(f"⏳ cooldown {symbol}")
            continue

        if get_buy_count(symbol) >= MAX_ADD: #加仓控制（允许但有限制, 最多加仓2次）
            print("⛔ max add reached")
            continue

        account = api.get_account()
        cash = float(account.cash)
        equity = float(account.equity)
        if (equity - cash) / equity > MAX_TOTAL_EXPOSURE:
            print("⛔ too much exposure")
            return

        price = get_current_price(symbol)
        pos = Position.query.filter_by(symbol=symbol).first()
        qty = 10  # 固定买入数量，可改成策略
        buy_flag = False
        sell_flag = False
        # 买入策略
        if pos and pos.quantity and get_buy_count(symbol) >= 2: #防重复买入（最重要）       
            last_high = get_last_n_high(symbol, 20)
            ma = get_moving_averages(symbol, [5, 20])
            ma_short = ma[5]
            ma_long = ma[20]
            buy_flag, reason = should_buy(symbol, price, last_high, ma_short, ma_long)
        #    if buy_flag:
        #        print (f"Buy {symbol} at {price}, {reason}")
            #    buy(symbol, qty, price, reason)

        # 卖出策略
        if pos and pos.quantity > 0:
            pnl = (price - pos.avg_price) * pos.quantity
            sell_flag, reason = should_sell(symbol, price, pos.avg_price, pnl)
    #        if sell_flag:
    #            print (f"Sell {symbol} at {price}, {reason}")
                #sell(symbol, reason)


        # ❌ 冲突处理
        if buy_flag and sell_flag:
            print (f"Hold {symbol} at {price}, 同一根K线内冲突!")
        if buy_flag:
            print (f"Buy {symbol} at {price}, {reason}")

        if sell_flag:
            print (f"Sell {symbol} at {price}, {reason}")
            sell(symbol, reason)


######################

global TRADES, POSITIONS

def update_positions(prices):

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
        if activities:            
            activities = sorted(activities, key=lambda x: x.id, reverse=False)     



    grouped = {}
    
    # group trades
    for t in activities:
        grouped.setdefault(t["symbol"], []).append(t)

    new_positions = {}

    for symbol, trades in grouped.items():

        trades.sort(key=lambda x: x["time"])

        qty = 0
        cost = 0

def execute_scan(symbols, prices):
    global CASH, TRADES

    for symbol in symbols:

        if symbol in POSITIONS and POSITIONS[symbol]["qty"] > 0:
            continue  # ❗不加仓

        price = prices[symbol]

        if CASH <= 0:
            return

        invest = CASH * 0.2

        qty = invest / price

        TRADES.append({
            "symbol": symbol,
            "side": "buy",
            "qty": qty,
            "price": price,
            "time": time.time()
        })

        CASH -= invest

def run_cycle():

    symbols = SYMBOLS #scan_symbols()     # 你的选股逻辑
    prices = update_symbols_daily_prices()
    #prices = get_last_n_high(symbols)  # 或 API

#    execute_scan(symbols, prices)

    update_positions(prices)

    return POSITIONS

def alpaca_trading_api():

    ## 📚 官方文档 👉 [https://alpaca.markets/docs/](https://alpaca.markets/docs/)

    ### 1️⃣ Account（账户）
    result = api.get_account()
    print (result)
    ### 2️⃣ Orders（下单）

    #result = api.submit_order(symbol="AAPL",qty=10,side="buy", type="market",time_in_force="day")
    #print (result)

    ### 3️⃣ Positions（持仓）
    result = api.list_positions()
    print (result)

    result = api.get_position("AAPL")
    print (result)

    ### 4️⃣ Activities（你
    result = api.get_activities()
    print (result)

    ### 5️⃣ Assets（股票列表）
    #result = api.list_assets()
    #print (result)

    ### 6️⃣ Market Data（行情）
    result = api.get_latest_trade("AAPL")
    print (result)

    # get daily data
    end = datetime.utcnow()
    start = end - timedelta(days=2)        
    start = start.isoformat() + "Z",
    end = end.isoformat() + "Z",
    result = api.get_bars(
        "AAPL",
        "1Day", 
        start = start,
        end = end,
        adjustment = 'raw',
        feed='iex'
    ).df
    print (result)

    #get mins data

    est = pytz.timezone("US/Eastern")
    now = datetime.now(est)
    # 今日开盘时间
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_end = now.replace(hour=15, minute=0, second=0, microsecond=0)
    # 👉 转 UTC（Alpaca 必须）
    start = market_open.astimezone(pytz.utc)
    end = market_end.astimezone(pytz.utc)

    result = api.get_bars(
        "AAPL",
        "5min", 
        start = start,
        end = end,
        adjustment = 'raw',
        feed='iex'
    ).df
    print(result)
    return   


