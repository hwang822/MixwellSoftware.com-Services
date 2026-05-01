
import json
import os
import sys
import hashlib
from zoneinfo import ZoneInfo
import alpaca_trade_api as tradeapi
from datetime import date, datetime, time, timedelta, timezone
import pytz

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, f"{base_dir}")
from config.settings import Config
from servicemodels import Position, Trade, DailyPrice, db

api = tradeapi.REST(Config.ALPACA_API_KEY, Config.ALPACA_SECRET_KEY, Config.ALPACA_BASE_URL)
SYMBOLS = ["AAPL", "NVDA", "TSLA", "AMD", "MSFT", "SPY"]

#get_alpaca_prices_api("AAPL", 1, "5min", 100)
#get_alpaca_prices_api("AAPL", 20, "1Day", 30)

def get_alpaca_prices_api(symbol, days, interval, limit, only_today=True):

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    bars = api.get_bars(
        symbol,
        interval,
        start=start.isoformat(),
        end=end.isoformat(),
        adjustment='raw',
        limit=limit,
        feed='iex'
    ).df

    result = []

    if not bars.empty:

        today_est = datetime.now(ZoneInfo("America/New_York")).date()

        for index, bar in bars.iterrows():

            # ✅ 先转 EST
            est = index.astimezone(ZoneInfo("America/New_York"))

            # ✅ 只取今天（可选）
            if only_today and est.date() != today_est:
                continue
            #interval_norm = interval.lower()
            # ✅ 只过滤交易时间（分钟级）
            if interval in ["1min", "5min", "15min"]:
                if not (time(9,30) <= est.time() <= time(16,0)):
                    continue

            # ✅ 时间格式
            if interval == "1Day":
                ts = est.strftime("%Y-%m-%d")
            else:
                ts = est.strftime("%Y-%m-%d %H:%M")

            result.append({
                "symbol": symbol,
                "price_close": bar.close,
                "volume" : bar.volume,
                "qty": 0,
                "mv": 0,
                "cost": 0,
                "pnl": 0,
                "pct": 0,
                "action" : "",
                "notes" : "",
                "timestamp": ts,
                "node" : None
            })

    return result

def get_top_symbols():
    assets = api.list_assets(status='active')
    symbols = [
        a.symbol for a in assets
        if a.tradable and a.exchange in ["NASDAQ", "NYSE"]
    ]

    return symbols

def get_color(symbol):
    h = int(hashlib.md5(symbol.encode()).hexdigest(), 16)
    #hue = h % 360
    index = h % 360
    hue = (index * 137.508) % 360
    return f"hsl({hue}, 70%, 50%)"

SYMBOL_COLORS = {}
for symbol in SYMBOLS:
    SYMBOL_COLORS[symbol] = get_color(symbol) 

ACTION_ICONS = {
    "buy":  "path://M512 128 L896 768 L128 768 Z",   # ▲
    "sell": "path://M128 256 L896 256 L512 896 Z",   # ▼
    "hold": "path://M512 128 A384 384 0 1 1 511 128 Z",  # ●
    "skip": "path://M128 128 H896 V896 H128 Z"       # ■
}
    
def utc_to_est(time_str):
    # 1️⃣ 解析 UTC 字符串
    dt_utc = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    #dt_utc = datetime.strptime(time_str.replace("Z", "+00:00"))
    dt_utc = dt_utc.replace(tzinfo=ZoneInfo("UTC"))

    # 2️⃣ 转换到纽约时区（自动 EST / EDT）
    dt_est = dt_utc.astimezone(ZoneInfo("America/New_York"))

    # 3️⃣ 输出字符串
    return dt_est.strftime("%Y-%m-%d %H:%M")


#计算 最近变化


def scan_market():

    results = []

    for symbol in SYMBOLS:

        bars = get_alpaca_prices_api(symbol, 1, "5min", 100, False)

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

#from datetime import datetime, timedelta
#import pytz

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
def get_latest_trade(symbol):
    trade = api.get_latest_trade(symbol)
    return trade # float(trade.price)

def get_last_n_high(symbol, n=5):
    prices = get_alpaca_prices_api(symbol, 1, "5min", 30, False)
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

COOLDOWN_MINUTES = 15
MAX_ADD = 2
MAX_TOTAL_EXPOSURE = 10000*0.8

def get_symbol_position(symbol):
    positions = api.list_positions()
    pos = next((p for p in positions if p.symbol == symbol), None)
    return pos

def is_trading_time(ts):

    """
    ts: datetime (UTC or timezone-aware)
    return: True / False
    """
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts)     

    #ny = ts.astimezone(ZoneInfo("America/New_York"))
    d = ts.date()
    #today = datetime.now().date()
    #if d != today:
    #    return False
    t = ts.time()
    # 上午 09:30–12:00
    return time(9, 30) <= t <=  time(16, 0)
    # 09:30 - 16:00 

def is_best_trading_time(ts):
    """
    ts: datetime (UTC or timezone-aware)
    return: True / False
    """

    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts)     

    t = ts.time()

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

def get_trade_color(action):
    return {
        "buy": "green",     # 买
        "sell": "red",      # 卖
        "hold": "yellow",   # 不卖
        "skip": "blue"      # 不买
    }.get(action, "gray")

def get_today_file():
    return f"{date.today()}_trading_log.jsonl"

LOG_DIR = "logs"
def save_today_log(lines):
    try:
        # 👉 确保目录存在
        os.makedirs(LOG_DIR, exist_ok=True)
        file = os.path.join(LOG_DIR, "trading_log.jsonl") #get_today_file())        
        with open(file, "w") as f:   # "w" = overwrite
            json.dump(lines, f, indent=2, default=str)
    except Exception as e:
        print (e)

def load_today_log(today=True):
    src_file = os.path.join(LOG_DIR, "trading_log.jsonl")
    dse_file = os.path.join(LOG_DIR, "lastday_traking_log.json")
    if today:
        if not os.path.exists(src_file):
            return []
        with open(src_file, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # 1️⃣ Delete old lastday file if exists
        if not os.path.exists(src_file):
            if os.path.exists(dse_file):
                with open(dse_file, "r", encoding="utf-8") as f:
                    return json.load(f)        
        else:            
            if os.path.exists(dse_file):
                os.remove(dse_file)
        # 2️⃣ Rename current → lastday
            os.rename(src_file, dse_file)
            with open(dse_file, "r", encoding="utf-8") as f:
                return json.load(f)        



    # 3️⃣ Recreate empty log for next session
    #open(src_file, "w").close()    
    """    
    file = os.path.join(LOG_DIR, "trading_log.jsonl") #get_today_file())
    if not os.path.exists(file):
        return []
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        print (e)
        return []
    """
###############################################
    """
    核心策略
    10:00–12:00 → 主交易
    13:00–15:00 → 主交易
    15:00–16:00 → 只允许卖
    16:00 → 强制清仓
    
    资金控制
    每个 symbol 固定：$2000
    不允许加仓（非常好 👍）
    
    📈 状态机（关键）

    每个 symbol 只有 2 个状态：

    0 = 无仓 → 只考虑买
    1 = 持仓 → 只考虑卖    
🟢 买入条件（推荐版）

        """

###################################
def get_volatility(prices, n=10):
    highs = [p["high"] for p in prices[-n:]]
    lows  = [p["low"]  for p in prices[-n:]]

    return (max(highs) - min(lows)) / min(lows)

def should_buy(current_price, prices):
    if len(prices) < 10:
        #print("Not enough data, skip trading")
        return False, "Not enough data, skip trading"
    else:
        # 最近 N 根（比如 10 根）
        recent = prices[-10:]

        recent_low = min(p["low"] for p in recent)
        recent_high = max(p["high"] for p in recent)

        # 1️⃣ 接近低点（核心）
        near_low = (current_price - recent_low) / recent_low < 0.003   # <0.3%
        if not near_low:
            return False, "not 接近低点（核心)"
        # 2️⃣ 不在下降趋势（防止接飞刀）
        not_falling = prices[-1]["price_close"] >= prices[-2]["price_close"]
        if not not_falling:
            return False, "在下降趋势（防止接飞刀）"

        # 3️⃣ 波动存在（避免死水）
        has_range = (recent_high - recent_low) / recent_low > 0.002
        if not not_falling:
            return False, "No 波动存在"

    return near_low and not_falling and has_range, "接近低点, 在下降趋势, 波动存在" 

def should_sell(current_time, current_price, qty, cost, prices):    
    pnl = current_price * qty - cost
    pct = pnl / cost * 100
    vol = get_volatility(prices)

    # 🎯 动态阈值
    take_profit = vol * 0.5 * 100   # 比如 0.3%~0.8%
    stop_loss   = vol * 0.4 * 100
    if current_time <= "15:50":
        return  True, f"TP clean {pct:.2f} at 15:50%" 
    elif current_time <= "15:15":
        take_profit = vol * 0.7 * 100   # 比如 0.3%~0.8%
        stop_loss   = vol * 0.8 * 100
    elif current_time <= "14:50":
        take_profit = vol * 0.5 * 100   # 比如 0.3%~0.8%
        stop_loss   = vol * 0.4 * 100
    elif current_time <= "14:50":
        return  True, f"TP clean {pct:.2f} at 09:30%" 
    if pct >= take_profit:
        return True, f"TP dynamic {pct:.2f}%"
    if pct <= -stop_loss:
        return True, f"SL dynamic {pct:.2f}%"
    return False, f"HOLD {pct:.2f}%"

def should_trade(symbol, pos, prices):
    #if len(prices)<10: 
        #print ("Not enough data for trading.")
    #    return None
    current_time = prices[-1]["timestamp"]    
    current_price = float(prices[-1]["price_close"])
    qty = 0
    cost = 0
    if pos:
        qty = int(pos.qty)
        cost = float(pos.cost_basis) 
        
    # 🟥 有仓 → 只卖
    if qty != 0:
        sell_flag, reason = should_sell(current_time, current_price, qty, cost, prices)
        sell_qty = 0
        sell_cost = 0
        if sell_flag:            
            if qty > 0:
                side = "sell"
                sell_qty = qty
            elif qty < 0:
                side = "buy"
                sell_qty = abs(qty)            
            action = "sell"
            sell_cost = round(qty*current_price)
            api.submit_order(symbol=symbol,qty=sell_qty,side=side,type="market",time_in_force="day")            
        else:
            sell_qty = qty
            action = "hold"
            sell_cost = round(qty*current_price)
        trade = {
            "icon": ACTION_ICONS[action],
            "action" : action,
            "qty": sell_qty,
            "cost" : sell_cost,
            "notes": reason
            }               
        return trade

    # 🟩 无仓 → 只买
    if is_best_trading_time(current_time):  # ⏰ 时间判断                                                                    
        if qty == 0:
            buy_flag, reason = should_buy(current_price, prices)
            buy_qty = 0
            buy_cost = 0
            if buy_flag:
                buy_qty = int(2000 / current_price)
                api.submit_order(symbol=symbol,qty= buy_qty,side="buy",type="market",time_in_force="day")  
                action = "buy"
                buy_cost = round(buy_qty*current_price,2)
            else:
                action = "skip"
            trade = {
                "icon": ACTION_ICONS[action],
                "action" : action,
                "qty": buy_qty,
                "cost" : buy_cost,
                "notes": reason
                }
            return  trade

def alpaca_trading_api():

    ## 📚 官方文档 👉 [https://alpaca.markets/docs/](https://alpaca.markets/docs/)

    ### 1️⃣ Account（账户）
    result = api.get_account()
    print (result)
    ### 2️⃣ Orders（下单）

    #result = api.submit_order(symbol="AAPL",qty=10,side="buy", type="market",time_in_force="day")
    #print (result)
    
    #判断“今天是否是交易日”
    today = date.today()
    calendar = api.get_calendar(start=today.isoformat(), end=today.isoformat())

    if len(calendar) > 0:
        print("Today is a trading day")
    else:
        print("Today is NOT a trading day (weekend/holiday)")

    clock = api.get_clock()

    if clock.is_open:
        print("Market is OPEN now")
    else:
        print("Market is CLOSED now")

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


#update_symbols_daily_prices()
################################
# update_symbols_prices()  #
###############################
def update_symbols_day_prices():  # core function        
    grouped = {}
    clock = api.get_clock()
    if clock.is_open:
        trading_log = {}
        trading_log_new = {}
        trading_log = load_today_log(True)

        for symbol in SYMBOLS:
            trading_log_new[symbol] = {}
            prices = get_alpaca_prices_api(symbol, 1, "5min", 100)
            if not prices:
                continue    
            qty = 0            
            mv = 0
            cost = 0
            pnl = 0
            pct = 0
            pos = get_symbol_position(symbol)
            if pos:
                qty = int(pos.qty)
                mv = round(float(pos.market_value), 2)
                cost = round(float(pos.cost_basis), 2)
                pnl = round(float(mv-cost), 2)
                pct = round(pnl / abs(cost) * 100 if cost else 0)
            for index, price in enumerate(prices):   # only collect prices in side tracking time.
                time = price["timestamp"]                
                if is_trading_time(time):
                    prices[index]["qty"] = qty
                    prices[index]["mv"] = mv
                    prices[index]["cost"] = cost
                    prices[index]["pnl"] = pnl
                    prices[index]["pct"] = pct          
                trading_log_new[symbol][time] = prices[index]
            current_trade = get_latest_trade(symbol)
            current_time = current_trade.t.strftime("%Y-%m-%d %H:%M")
            trade = should_trade(symbol, pos, prices)  # if trade in current price.
            print (f"{current_time} {symbol} {trade} ")
            if trade:   
                currentprice = round(float(current_trade.p), 2)                 
                prices[-1]["price_close"] = currentprice
                cost = round(float(qty*currentprice), 2)
                pnl = round(float(mv-cost), 2)
                pct = round(float(pnl / abs(cost)) * 100 if cost else 0)
                prices[-1]["qty"] = trade["qty"]                    
                prices[-1]["volume"] = trade["volume"]
                prices[-1]["mv"] = mv                 
                prices[-1]["cost"] = round(float(trade["cost"]), 2)
                prices[-1]["pnl"] = pnl
                prices[-1]["pct"] = pct
                prices[-1]["action"] = trade["action"]
                prices[-1]["notes"] = trade["notes"]
                prices[-1]["timestamp"] = current_time,
                if trade["action"] == "sell" or trade["action"] == "buy":
                    prices[-1]["node"] = trade
                trading_log_new[symbol][current_time] = prices                    

            grouped[symbol] = {
                "colors" : SYMBOL_COLORS[symbol], 
                "items" : prices }
        trading_log_ex = {}
        
        if not len(trading_log_new)==0:        
            if len(trading_log)==0:
                trading_log_ex = trading_log_new
            else:           
                for k, v in trading_log_new.items():
                    trading_log_ex[k] = v
                for k, v in trading_log.items():    
                    for vs in v:
                        trading_log_ex[k][vs] = v[vs]
                    trading_log_ex[k] = dict(sorted(trading_log_ex[k].items()))
        save_today_log(trading_log_ex)
        return update_symbols_day_prices_ui(True)
    else:
        return update_symbols_day_prices_ui(False)
def update_symbols_day_prices_ui(today=True):
    grouped_log = load_today_log(False)
    grouped_new = {}
    lines = []
    for symbol in grouped_log:
        items = grouped_log[symbol]
        v = []
        vx = []
        for item in items:
            try:
                price = items[item]
                timestamp = item.split(" ")[1]
                time_price = {
                    "x" : timestamp,
                    "y" : price["price_close"],
                    "z" : price["qty"],
                    "node" : price["node"]
                }
                v.append(time_price)
                vx.append(price)
            except Exception as e:
                print(e)
        grouped_new[symbol] = {"colors" : SYMBOL_COLORS[symbol], "items" : vx }    

        min_y = min(p["y"] for p in v)   
        for p in v:
            p["y"] = round((float(p["y"]) - float(min_y)), 2)                       
        
        lines.append({
            "symbol" : symbol,
            "color"  : SYMBOL_COLORS[symbol],
            "series" : v
        })
     
    return  grouped_new, lines

def update_symbols_daily_prices():  # core function    
    lines = []
    grouped = {}    
    for symbol in SYMBOLS:
        prices = get_alpaca_prices_api(symbol, 30, "1Day", 30, False)      
        if not prices:
            continue 
        grouped[symbol] = {"colors" : SYMBOL_COLORS[symbol], "items" : prices }    
        v = []
        lastPrice = 0
        currentPrice = 0
        lastPrice = round(float(prices[0]["price_close"]), 2)
        for price in prices:
            ts = datetime.fromisoformat(price["timestamp"]).strftime("%m-%d")
            currentPrice = round(float(price["price_close"]), 2)
            priceRate = round(float(currentPrice - lastPrice),2)
            lastPrice = currentPrice
            trade = None
            time_price = {
                "x" : ts, 
                "y" : lastPrice,
                "node" : trade
                }                     
            v.append(time_price)
        min_y = min(p["y"] for p in v)   
        for p in v:
            p["y"] = p["y"] - min_y                       

        lines.append({
            "symbol" : symbol,
            "color"  : SYMBOL_COLORS[symbol],
            "series" : v
        })
        
    return grouped, lines

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
        mv = round(float(pos.market_value), 2)
        cost = round(float(pos.cost_basis), 2)
        price = round(float(pos.current_price), 2)
        avg_price = round(float(pos.avg_entry_price), 2)
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
    grouped = {}
    lines = []

    if not activities:
        return grouped, lines

    # 1️⃣ sort by time
    activities = sorted(activities, key=lambda x: x.transaction_time)

    # 2️⃣ group by symbol
    trades_grouped = {}
    for a in activities:
        trades_grouped.setdefault(a.symbol, []).append(a)

    summary = 0

    # 3️⃣ process each symbol
    for symbol, trades in trades_grouped.items():

        trade_datas = []
        v = []

        total_qty = 0
        cost = 0.0                 # remaining position cost
        realized_pnl = 0.0         # ✅ REAL pnl only
        cost_max = 0.0

        for t in trades:
            time = utc_to_est(t.transaction_time.strftime("%Y-%m-%d %H:%M"))
            qty = int(t.qty)
            price = round(float(t.price), 2)

            # ===== BUY =====
            if t.side == "buy":
                total_qty += qty
                cost += qty * price

                cost_max = max(cost_max, cost)

            # ===== SELL =====
            elif t.side in ["sell", "sell_short"]:
                if total_qty > 0:
                    avg_cost = cost / total_qty

                    # ✅ realized pnl only
                    realized = (price - avg_cost) * qty
                    realized_pnl += realized

                    # update position
                    total_qty -= qty
                    cost -= avg_cost * qty

            # ===== Unrealized (for display only) =====
            if total_qty > 0:
                mv = total_qty * price
                unrealized_pnl = mv - cost
                pct = (unrealized_pnl / cost * 100) if cost > 0 else 0
            else:
                mv = 0
                unrealized_pnl = 0
                pct = 0
                cost = 0  # reset when flat

            total_pnl = round(realized_pnl, 2)

            # ===== trade table =====
            trade_data = {
                "symbol": symbol,
                "side": t.side,
                "price": price,
                "qty": qty,
                "total_qty": total_qty,
                "cost_base": round(cost, 2),
                "market_value": round(mv, 2),
                "pnl": round(unrealized_pnl, 2),   # display only
                "pct": round(pct, 2),
                "total_pnl": total_pnl,            # ✅ real pnl
                "reason": t.side,
                "id": t.id.split("::")[0],
                "transaction_time": time
            }

            trade_datas.append(trade_data)

            # ===== chart series =====
            if t.side == "buy":
                action = "buy"
            else:
                action = "sell" 

            time_price = {
                "x": time,
                "y": pct,   # ✅ equity curve (IMPORTANT)
                "z": 0, # total_qty,   # for your frontend logic
                "node": {                    
                    "icon": ACTION_ICONS[action],
                    "notes": action
                }
            }

            v.append(time_price)

        grouped[symbol] = {
            "colors": SYMBOL_COLORS[symbol],
            "items": trade_datas
        }

        lines.append({
            "symbol": symbol,
            "color": SYMBOL_COLORS[symbol],
            "series": v
        })

        pct_total = (realized_pnl / cost_max) if cost_max > 0 else 0

        print(
            f"{symbol} most cost: {round(cost_max, 2)}, "
            f"total pnl: {round(realized_pnl, 2)}, "
            f"pct: {round(pct_total, 2)}"
        )

        summary += realized_pnl

    print(f"Summary PnL for all: {round(summary, 2)}")

    return grouped, lines

def update_symbols_trades_1():
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
    
    summary = 0
    for symbol, trades in trades_grouped.items():
        trade_datas = []
        total_qty = 0
        total_pnl = 0
        cost = 0
        cost_max = 0
        pnl = 0
        mv = 0
        pct = 0
        qty = 0
        
        v = [] 
        for t in trades:
            time = utc_to_est((t.transaction_time).strftime("%Y-%m-%d %H:%M"))
            qty = int(t.qty)
            price = round(float(t.price),2)
            if t.side == "buy":
                total_qty += qty
                cost += qty * price
                if cost >= cost_max:
                    cost_max = cost
            elif t.side == "sell" or t.side == "sell_short":
                mv = total_qty * price
                pnl = round(float(mv - cost), 2)
                #pct = round(float(mv - cost)/cost*100, 2)
                
                total_qty -= qty                
                cost -= qty * price   # ✅ FIX
                total_pnl = round(total_pnl + pnl,)
            if (total_qty==0):
                mv = 0
                pnl = 0
                pct = 0
                cost = 0
                #total_pnl = 0
            
            trade_data = {
                "symbol": symbol,
                "side": t.side,
                "price": price,
                "qty": qty,                
                "total_qty": total_qty,
                "cost_base" : round(cost,2),
                "market_value" : round(mv,2),
                "pnl": pnl,
                "pct": pct,
                "total_pnl": total_pnl,                
                "reason" : t.side,
                "id": t.id.split("::")[0],
                "transaction_time": time
            }            
            trade_datas.append(trade_data)
            
            time_price = {
                "x" : time, 
                "y" : pnl,
                "node" : {
                    "symbol": symbol,
                    "side": t.side,
                    "price": qty,
                    "qty": qty,
                    "pnl": pnl,                
                    "reason" : t.side,
                    "color" : get_color(t.side)
                }}
            v.append(time_price)                     
        grouped[symbol] = {"colors" : SYMBOL_COLORS[symbol], "items" : trade_datas }
        lines.append({
            "symbol" : symbol,
            "color"  : SYMBOL_COLORS[symbol],
            "series" : v
        })
        
        print (f"{symbol} most cost: {round(cost_max, 2)}, total pnl: {round(total_pnl, 2)},  pct: {round(total_pnl/cost_max, 2)} ")                
        summary += total_pnl
        #save_activities(grouped)
    print (f"Summary PN for all: {summary}")
    return grouped, lines
#update_symbols_trades()        