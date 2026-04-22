
import os
import sys
import hashlib
from zoneinfo import ZoneInfo
import alpaca_trade_api as tradeapi
from datetime import datetime, time, timedelta, timezone

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, f"{base_dir}")
from config.settings import Config
from servicemodels import Position, Trade, DailyPrice, db

api = tradeapi.REST(Config.ALPACA_API_KEY, Config.ALPACA_SECRET_KEY, Config.ALPACA_BASE_URL)
SYMBOLS = ["AAPL", "NVDA", "TSLA", "AMD", "MSFT", "SPY"]

#get_alpaca_prices_api("AAPL", 3, "5min", 100)
#get_alpaca_prices_api("AAPL", 20, "1Day", 30)
def get_alpaca_prices_api(symbol, days, interver, limit):
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
                "timestamp" : utc_to_est((index).strftime("%Y-%m-%d %H:%M")) 
                })             
    return result 

def write_trade_log(symbol, side, price, qty, reason):
    
    # 1️⃣ 时间
    now = datetime.now().astimezone(ZoneInfo("America/New_York"))
    date_str = now.strftime("%Y-%m-%d")

    # 2️⃣ 文件名
    filename = f"{date_str}_trading_log.txt"

    # 👉 可选：放到 logs 文件夹
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    filepath = os.path.join(log_dir, filename)

    # 3️⃣ 一行内容
    line = (
        f"{now.strftime('%Y-%m-%d %H:%M:%S')}, "
        f"{symbol}, {side}, {price}, {qty}, {reason}\n"
    )

    # 4️⃣ 追加写入
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(line)


def update_last_trade_info(symbol, sdie, price, qty):    
    
    lastTrade = Trade.query.filter_by(symbol = symbol).last()
    db.session.add(lastTrade)
    db.session.commit()
    return lastTrade


def get_top_symbols():
    assets = api.list_assets(status='active')
    symbols = [
        a.symbol for a in assets
        if a.tradable and a.exchange in ["NASDAQ", "NYSE"]
    ]

    return symbols

def get_color(symbol):
    h = int(hashlib.md5(symbol.encode()).hexdigest(), 16)
    hue = h % 360
    return f"hsl({hue}, 70%, 50%)"

SYMBOL_COLORS = {}
for symbol in SYMBOLS:
    SYMBOL_COLORS[symbol] = get_color(symbol) 

def utc_to_est(time_str):
    # 1️⃣ 解析 UTC 字符串
    dt_utc = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    dt_utc = dt_utc.replace(tzinfo=ZoneInfo("UTC"))

    # 2️⃣ 转换到纽约时区（自动 EST / EDT）
    dt_est = dt_utc.astimezone(ZoneInfo("America/New_York"))

    # 3️⃣ 输出字符串
    return dt_est.strftime("%Y-%m-%d %H:%M")


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

        bars = get_alpaca_prices_api(symbol, 3, "5min", 100)

        if len(bars) < 2:
            continue
        first = bars[0]
        last  = bars[-1]

        change = (last["price_close"] - first["price_close"]) / first["price_close"]
        volume = sum(b["volume"] for b in bars) / len(bars)
        score  = change * volume
        results.append({
            "symbol": symbol,
            "change": change,
            "volume": volume,
            "score": score
        })

        results = sorted(results, key=lambda x: x["score"], reverse=True)

    return results

from datetime import datetime, timedelta
import pytz

def get_recommended_symbols():
    # 临时：用 movers 代替
    movers = []

    for symbol in SYMBOLS:
        bars = api.get_bars(symbol, "5Min", limit=12).df
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

##################
# new models
##################
def get_current_price(symbol):
    trade = api.get_latest_trade(symbol)
    return float(trade.price)

def get_last_n_high(symbol, n=5):
    prices = get_alpaca_prices_api(symbol, 1, "5min", 30)
    #highest = max(prices, key=lambda x: x.high)
    highest = max(b["high"] for b in prices)
    return highest

def get_moving_averages(symbol, periods=[5, 20, 50]):

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

def should_buy(symbol, position):
    prices = get_alpaca_prices_api(symbol, 1, "5min", 30)
    buy_flag = False    
    """
    prices: 最近30条数据（按时间升序）
    每条: {"price_c","high","volume","timestamp"}
    """

    if len(prices) < 10:
        reason = "less prices"
        return buy_flag, reason 

    if in_cooldown(symbol):  #冷却时间（防止连续买）
        reason = f"⏳ cooldown {symbol}"        
        return buy_flag , reason

    if get_buy_count(symbol) >= MAX_ADD: #加仓控制（允许但有限制, 最多加仓2次）        
        reason = f"⛔ {symbol} max add reached"        
        return buy_flag, reason

    #account = api.get_account()
    cash = 10000 #float(account.cash)
    equity = 2000 #float(account.equity)
    current_price = get_current_price(symbol)
    if position and int(position.qty)*current_price > equity:
        return buy_flag, "over buget"

    # ===== 2️⃣ breakout =====
    #current_price = prices[-1]["price_c"]

    recent_high = max(p["high"] for p in prices[:-3])  # 不用最后3根
    breakout = current_price > recent_high

    if not breakout:
        return buy_flag, "not breakout"

    # ===== 3️⃣ 动量确认（连续上涨）=====
    momentum = (
        prices[-1]["price_close"] > prices[-2]["price_close"] >
        prices[-3]["price_close"]
    )

    if not momentum:
        return buy_flag, "not momentum"
    # ===== 4️⃣ 不追太高 =====
    recent_low = min(p["low"] for p in prices[-10:])
    pullback_ok = (current_price - recent_low) / recent_low < 0.02  # <2%

    if not pullback_ok:
        return buy_flag, "not pullback"        

    buy_flag = True
    reason = "Cooldown OK, not max add reached, not over buget, breakout OK, momentum ok, pullback ok"
    return buy_flag, reason

def should_sell(symbol, position):

    if not position or int(position.qty) == 0:
        return False, "no position"

    price = get_current_price(symbol)
    qty = int(position.qty)
    cost = float(position.cost_basis)

    pnl = (price * qty) - cost
    pct = (pnl / cost) * 100 if cost else 0

    if pct <= -2:
        return True, f"STOP LOSS {pct:.2f}%"

    if pct >= 3:
        return True, f"TAKE PROFIT {pct:.2f}%"

    # optional trailing logic
    if pct > 1 and price < max_entry_price * 0.99:
        return True, "TRAIL STOP"

    return False, f"HOLD {pct:.2f}%"


COOLDOWN_MINUTES = 15
def in_cooldown(symbol):
    buy_trades = get_recent_continuous_buys(symbol)
    if not buy_trades:
        return False
    
    latest_trade = buy_trades[0]
    delta = datetime.now(timezone.utc) - latest_trade.transaction_time
    minutes = delta.total_seconds() / 60
    return minutes < COOLDOWN_MINUTES

MAX_ADD = 2
def get_recent_continuous_buys(symbol):
    activities = get_all_activities()    
    acts = [a for a in activities if a.symbol == symbol]
    # 按时间从新到旧（假设 id 越大越新）
    acts.sort(key=lambda x: x.id, reverse=True)
    result = []
    for a in acts:
        if a.side == "buy":
            result.append(a)
        else:
            break   # ❗ 一旦遇到 sell，停止
    return result

def get_buy_count(symbol):
    activities = get_recent_continuous_buys(symbol)
    count = len(activities)
    return count

MAX_TOTAL_EXPOSURE = 10000*0.8

def get_symbol_position(symbol):
    positions = api.list_positions()
    pos = next((p for p in positions if p.symbol == symbol), None)
    return pos

def is_best_trading_time(ts):
    """
    ts: datetime (UTC or timezone-aware)
    return: True / False
    """

    ny = ts.astimezone(ZoneInfo("America/New_York"))
    t = ny.time()

    # 上午 10:00–12:00
    morning = time(10, 0) <= t <= time(12, 0)

    # 下午 13:00–15:00
    afternoon = time(13, 0) <= t <= time(15, 0)

    # 09:30–10:00 → 开盘噪音（波动大 ❌）
    # 10:00–12:00 → 趋势稳定 ✅
    # 12:00–13:00 → 午盘低量 ❌
    # 13:00–15:00 → 主趋势延续 ✅
    # 15:00–16:00 → 收盘波动 ❌（除非你做收盘策略）

    return morning or afternoon

def auto_trade():
    if is_best_trading_time(datetime.now()):
        for symbol in SYMBOLS:
            try:        
                pos = get_symbol_position(symbol) #Position.query.filter_by(symbol=symbol).first()
                # 卖出策略
                sell_flag, sell_reason = should_sell(symbol, pos)
                # 买入策略
                buy_flag, buy_reason = should_buy(symbol, pos)

                price = get_current_price(symbol)
                # ❌ 冲突处理
                if buy_flag and sell_flag:
                    print (f"Hold {symbol} at {price}, 同一根K线内冲突!")
                    continue
                if sell_flag:
                    qty = int(pos.qty)
                    side = "sell" if qty > 0 else "buy"
                    sell_qty = abs(qty) 
                    """                           
                    api.submit_order(
                        symbol=symbol,
                        qty=sell_qty,
                        side=side,
                        type="market",
                        time_in_force="day"
                    )
                    """            
                    write_trade_log(symbol, "sell", price, sell_qty, sell_reason)
                

                if buy_flag:
                    buy_qty = int(2000/price)
                    """
                    api.submit_order(
                        symbol=symbol,
                        qty= buy_qty,
                        side="buy",
                        type="market",
                        time_in_force="day"
                    )  
                    """                      
                    write_trade_log(symbol, "buy", price, buy_qty, buy_reason)        
            except Exception as e:
                print (e)                
                write_trade_log("broken", 0, 0, e)        

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

    try:
        result = api.get_bars(  # not work at NY close time
            "AAPL",
            "5min", 
            #start = start,
            #end = end,
            adjustment = 'raw',
            feed='iex'
        ).df
    except Exception as e:    
        print(e)
    return   
#alpaca_trading_api()
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
        "created_date": account.created_at.strftime("%Y-%m-%d")
    })
    return result

##################################
# Update Scan Symbols
##################################
def update_symbols_scan():    
    #from scanner import scan_market
    results = []
    bars = []
    scans = scan_market()
    for scan in scans:
        results.append({
                "symbol": scan["symbol"],
                "score": round(float(scan["score"]), 2),
                "price": round(float(scan["change"]), 2),
                "volume": round(float(scan["volume"]), 2)
            })
        bars.append({
                "x": scan["symbol"],
                "y": round(float(scan["score"]), 2),
                "color" : SYMBOL_COLORS[scan["symbol"]]
                })
        
    return results, bars

################################
#  update_symbols_positions()  #
################################
def update_symbols_positions():  # core functions
    result = []           
    bars = []
    positions = api.list_positions()
    for pos in positions:
        mv = float(pos.market_value)
        cost = float(pos.cost_basis)
        pnl = mv-cost
        pct = pnl / abs(cost) * 100 if cost else 0
        if pct <= -2:
            action = f" PNL % <= -2 SELL (STOP LOSS) "
        elif pct >= 3:
            action = f" PNL % >= 3 SELL (TAKE PROFIT) "
        else:
            action = f" PNL % (-2, 3) HOLD "        

        result.append({
                "symbol": pos.symbol,
                "qty": int(pos.qty),
                "avg_entry_price": round(float(pos.avg_entry_price), 2),
                "market_value": round(float(pos.market_value), 2),
                "cost_basis": round(float(pos.cost_basis), 2),
                "pnl": round(float(pnl), 2),
                "pct": round(float(pct), 2),
                "action": action
            })
        bars.append({
            "x": pos.symbol,
            "y" : abs(mv -cost),
            "color" : SYMBOL_COLORS[pos.symbol]
        })
    return result, bars
    

def merge_all(price_lines, trade_lines):
    result = []

    trade_map = {t["symbol"]: t["series"] for t in trade_lines}

    for p in price_lines:
        symbol = p["symbol"]
        price_series = p["series"]
        trade_series = trade_map.get(symbol, [])

        merged_series = merge_price_and_trades(price_series, trade_series)

        result.append({
            "symbol": symbol,
            "color": p["color"],
            "series": merged_series
        })

    return result

#update_symbols_daily_prices()
################################
# update_symbols_prices()  #
################################

def update_symbols_prices(daily):  # core function    
    lines = []
    grouped = {}    
    for symbol in SYMBOLS:
        if daily:
            prices = get_alpaca_prices_api(symbol, 30, "1Day", 30)      
        else:
            prices = get_alpaca_prices_api(symbol, 1, "5min", 100)   
        if not prices:
            return grouped, lines 
        grouped[symbol] = {"colors" : SYMBOL_COLORS[symbol], "items" : prices }    
        v = []
        lastPrice = 0
        priceRate = 0
        currentPrice = 0
        for price in prices:
            ts = datetime.fromisoformat(price["timestamp"])

            if daily:
                time = f"{ts.month}/{ts.day}"
            else:
                time = ts.strftime("%H:%M")
            if lastPrice==0:
                lastPrice = float(price["price_close"])
            else:
                currentPrice = float(price["price_close"])
                if lastPrice == 0:
                    priceRate = 0    
                else: 
                    priceRate = round(float(((currentPrice-lastPrice)/lastPrice)*100),2)                 
                time_price = {"x" : time, "y" : priceRate}
                v.append(time_price)

        lines.append({
            "symbol" : symbol,
            "color"  : SYMBOL_COLORS[symbol],
            "series" : v
        })
        

    #trades, trade_lines = update_symbols_trades()
    #lines_merged = merge_all(lines, trade_lines)

    return grouped, lines

def merge_price_and_trades(price_series, trade_series):
    merged = []

    # 加入 price
    for p in price_series:
        merged.append({
            "x": p["x"],
            "y": p["y"]
        })

    # 加入 trade（保持 object）
    for t in trade_series:
        merged.append({
            "x": t["x"],
            "y": t["y"]
        })

    # 🔥 关键：按时间排序
    merged.sort(key=lambda i: i["x"])

    return merged

def merge_all(price_lines, trade_lines):
    result = []

    trade_map = {t["symbol"]: t["series"] for t in trade_lines}

    for p in price_lines:
        symbol = p["symbol"]
        price_series = p["series"]
        trade_series = trade_map.get(symbol, [])

        merged_series = merge_price_and_trades(price_series, trade_series)

        result.append({
            "symbol": symbol,
            "color": p["color"],
            "series": merged_series
        })

    return result

################################
# update_symbols_trades()      #
################################

def get_all_activities():

    activities = []
    page_token = None
    # ===== 1️⃣ 拉取 Alpaca 数据 =====
    while True:  # no fee member only could get 100 data per time access
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
    return activities 

def update_symbols_trades():
    activities = get_all_activities()
    grouped = {}  # it is dict, easy go through
    lines = []
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
        lastPrice = 0
        currentPrice = 0        
        priceRate = 0
        v = [] 
        for t in trades:
            qty = int(t.qty)
            price = round(float(t.price),2)
            if t.side == "buy":
                total_qty += qty
                total_buy += qty * price
            elif t.side == "sell":
                total_qty -= qty
                total_sell += qty * price   # ✅ FIX                
            pnl = round(float(total_sell - total_buy), 2)
            time = utc_to_est((t.transaction_time).strftime("%Y-%m-%d %H:%M"))
            trade_data = {
                "symbol": symbol,
                "side": t.side,
                "price": price,
                "qty": qty,
                "total_buy": round(float(total_buy), 2),
                "total_sell": round(float(total_sell), 2),
                "total_qty": total_qty,
                "pnl": pnl,                
                "reason" : t.side,
                "id": t.id.split("::")[0],
                "transaction_time": time
            }            
            trade_datas.append(trade_data)
            
            if lastPrice==0:
                lastPrice = float(price)
            else:
                currentPrice = float(price)
                priceRate = round(float(((currentPrice-lastPrice)/lastPrice)*100),2)
                priceRate1 = (currentPrice-lastPrice)/lastPrice
                if (priceRate >= 1):
                    print(priceRate) 

            time_price = {
                "x" : time, 
                "y" : {
                    "symbol": symbol,
                    "side": t.side,
                    "price": priceRate,
                    "qty": qty,
                    "pnl": pnl,                
                    "reason" : t.side
                }}
            v.append(time_price)                     
        grouped[symbol] = {"colors" : SYMBOL_COLORS[symbol], "items" : trade_datas }
        lines.append({
            "symbol" : symbol,
            "color"  : SYMBOL_COLORS[symbol],
            "series" : v
        })
        #save_activities(grouped)
    return grouped, lines
        