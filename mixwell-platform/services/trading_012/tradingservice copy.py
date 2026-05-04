
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
                "timestamp": ts,
                "price_close": bar.close,
                "qty": 0,
                "mv": 0,
                "cost": 0,
                #"mv_chagne($)": 0,
                "mv": 0,                
                "pnl": 0,
                "pct": 0,
                "total_pnl": 0,
                "action" : "",
                "notes" : "",
                "price_low": bar.low,
                "price_high": bar.high,
                "volume" : bar.volume,
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
    return f"{date.today()}_trading_log.json"

LOG_DIR = "logs"
def save_today_log(lines):
    try:
        # 👉 确保目录存在
        os.makedirs(LOG_DIR, exist_ok=True)
        file = os.path.join(LOG_DIR, "trading_log.json") #get_today_file())        
        with open(file, "w") as f:   # "w" = overwrite
            json.dump(lines, f, indent=2, default=str)
    except Exception as e:
        print (e)

def load_today_log(today=True):
    src_file = os.path.join(LOG_DIR, "trading_log.json")
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
    file = os.path.join(LOG_DIR, "trading_log.json") #get_today_file())
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
    highs = [p["price_high"] for p in prices[-n:]]
    lows  = [p["price_low"]  for p in prices[-n:]]

    return (max(highs) - min(lows)) / min(lows)

def should_buy(prices):
    if len(prices) < 5:
        #print("Not enough data, skip trading")
        return False, "Not enough data, skip trading"
    else:
        current_price = prices[-1]["price_close"]
        # 最近 N 根（比如 10 根）
        recent = prices[-5:]

        recent_low = min(p["price_low"] for p in recent)
        recent_high = max(p["price_high"] for p in recent)

        # 3️⃣ 波动存在（避免死水）
        has_range = abs(recent_high - recent_low) / recent_low < 0.002
        if has_range:
            return False, f"up-down not out of range {recent_high} - {recent_low}"

        # 1️⃣ 接近低点（核心）
        near_low = (current_price - recent_low) / recent_low < 0.003   # <0.3%
        if near_low:
            return False, f"near lowest point {recent_low}"
        
    return not near_low and not has_range, f"not near lowest point {recent_low}, up-down out of rang {recent_high} - {recent_low}" 

def should_sell(prices):    
    current_price = prices[-1]
    recent = prices[-10:]

    recent_low = min(p["price_low"] for p in recent)
    recent_high = max(p["price_high"] for p in recent)

    # 3️⃣ 波动存在（避免死水）
    has_range = abs(recent_high - recent_low) / recent_low < 0.002
    if has_range:
        return False, f"up-down in the range {recent_high} - {recent_low}"

    # 1️⃣ 接近High点（核心）
    near_high = (recent_high - current_price) / recent_low < 0.003   # <0.3%
    if near_high:
        return False, f"near Highest point {recent_high}"

    return True, f"Sell: lower than Highest {recent_high} and outut of range {recent_high} - {recent_low}%"

def should_trade(symbol, prices):
    #if len(prices)<10: 
        #print ("Not enough data for trading.")
    #    return None
    current_time = prices[-1]["timestamp"]    
    current_price = float(prices[-1]["price_close"])
    qty = prices[-1]["qty"]
    cost = prices[-1]["cost"]
    #if pos:
    #    qty = int(pos.qty)
    #    cost = float(pos.cost_basis) 
        
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
            #sell_cost = round(qty*current_price)
            #api.submit_order(symbol=symbol,qty=sell_qty,side=side,type="market",time_in_force="day")            
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
    #if is_best_trading_time(current_time):  # ⏰ 时间判断                                                                    
    if qty == 0:
        buy_flag, reason = should_buy(current_price, prices)
        buy_qty = 0
        buy_cost = 0
        if buy_flag:
            buy_qty = int(2000 / current_price)
            #api.submit_order(symbol=symbol,qty= buy_qty,side="buy",type="market",time_in_force="day")  
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
def should_buy_test(prices):
    return False

def should_sell_test(prices):
    return False

def save_test_log(lines):
    try:
        # 👉 确保目录存在
        os.makedirs(LOG_DIR, exist_ok=True)
        file = os.path.join(LOG_DIR, "trading_test.json")         
        with open(file, "w") as f:   # "w" = overwrite
            json.dump(lines, f, indent=2, default=str)
    except Exception as e:
        print (e)


def load_test_log():
    src_file = os.path.join(LOG_DIR, "trading_test.json")
    if not os.path.exists(src_file):
        return []
    with open(src_file, "r", encoding="utf-8") as f:
        return json.load(f)

def get_alpaca_prices_test(symbol):
    src_file = os.path.join(LOG_DIR, "trading_test_data.json")
    if not os.path.exists(src_file):
        return []
    with open(src_file, "r", encoding="utf-8") as f:
        data = json.load(f)        
        result = data[symbol]["items"]
        """        
        new_items = []
        for price in result:
            print (price)
            new_items.append({
                "symbol": symbol,
                "timestamp": price["timestamp"],
                "price_close":price["price_close"],
                "qty": 0,
                "mv": 0,
                "cost": 0,
                "mv_chagne($)": 0,
                "mv_ref": 0,                
                "pnl": 0,
                "pct": 0,
                "total_pnl": 0,
                "action" : None,
                "notes" : None,
                "price_low": price["price_low"],
                "price_high": price["price_high"],
                "volume" : price["volume"],
                "node" : None
            })
        data[symbol]["items"].append(new_items)
        save_test_log(data)    
        """
    return result


def exitTrade(side, qty):
    return

def update_symbols_day_prices():  # core function        
    grouped = {}
    grouped_log = {}
    
    clock = api.get_clock()    
    if clock.is_open:
        grouped = load_today_log(True)
        for symbol in SYMBOLS:            
            if not symbol == "TSLA":
                continue 
            trading_log = []
            start = 0
            lastTrade = None
            last_qty = 0
            last_cost = 0
            last_price = 0
            if len(grouped) >0:
                trading_log = grouped[symbol]["items"]            
                start = len(trading_log)                        
                lastTrade = trading_log[-1]             
                last_qty = int(lastTrade["qty"])
                last_cost = round(float(lastTrade["cost"]), 2)
                last_price = round(float(lastTrade["price_close"]), 2)
            prices = get_alpaca_prices_api(symbol, 1, "5min", 100)
            if not prices:
                continue 
            
            recent_prices = prices[:(start+1)]
            recent_price = recent_prices[-1]            
            current_price = float(recent_price["price_close"])            
            current_change = 0
            current_qty = last_qty
            current_mv = round(current_qty*current_price, 2)
            recent_price["mv"] = round(current_mv, 2)                                 
            #current_ref = last_cost
            
            if start > 0:
                current_change = round(((current_price-last_price)/last_price)*100, 2)
            else:
                current_change = 0            
                last_price = current_price
            if start <= 5:
                current_ref = current_price
            else:
                if current_qty == 0:
                    recent = recent_prices[-5:]
                    current_ref = min(p["price_low"] for p in recent)                                            
            
            recent_price["mv"] = current_mv
            recent_price["mv_chagne($)"] = current_change
            recent_price["mv_ref"] = current_ref                        
            if current_qty == 0:  # buy only
                if (current_mv - current_ref) > 2: # start up from lower
                    acction = "buy"
                    current_qty = round(2000/current_price)            
                    exitTrade(acction, current_qty)
                    recent_price["action"] = acction
                    recent_price["notes"] = f"{acction}: mv={current_mv} > ref={current_ref} in range 2$ "                        
                    recent_price["cost"] = current_mv
                    recent_price["qty"] = current_qty
                    recent_price["mv"] = current_mv    

                else:
                    if abs(current_ref-current_mv) < -2:
                        current_ref = current_mv  # move up current_ref
                        recent_price["mv"] = current_ref
                    recent_price["action"] = None
                    recent_price["notes"] = f"Skip: mv={current_mv} with ref={current_ref} in range 2$ "                    
            else: # sell only
                if (current_mv > current_ref) <-2 :
                    acction = "sell"
                    current_pnl = current_mv - last_cost
                    recent_price["pnl"] = current_pnl
                    total_pnl += current_pnl                    
                    exitTrade(acction, current_qty)
                    recent_price["action"] = acction
                    recent_price["notes"] = f"{acction}: mv={current_mv} < ref={current_ref}  take win {current_mv-current_ref} $ "                       
                    recent_price["pnl"] = 0
                    recent_price["cost"] = 0
                    recent_price["qty"] = 0
                    recent_price["mv"] = current_mv    
                elif abs(current_ref-current_mv) >2:
                    current_ref = current_mv   # move up current_ref
                    recent_price["mv"] = current_ref
                else:
                    recent_price["action"] = None
                    recent_price["notes"] = f"Hold: mv={current_mv} - ref={current_ref} in range 2$"                    

            trading_log.append(recent_price)
            grouped_log[symbol] = {
                "colors" : SYMBOL_COLORS[symbol], 
                "items" : trading_log }            
        save_today_log(grouped_log)
        return update_symbols_day_prices_ui(True)
    else:
        return update_symbols_day_prices_ui(False)

def update_symbols_day_prices_ui(today=True):
    grouped_log = load_today_log(today)
    lines = []
    for symbol in grouped_log:
        items = grouped_log[symbol]["items"]
        v = []
        for item in items:
            timestamp = item["timestamp"]
            timestamp = timestamp.split(" ")[1]
            time_price = {
                "x" : timestamp,
                "y" : item["mv"],
                "z" : item["qty"],
                "node" : item["node"]
            }
            v.append(time_price)            
        min_y = min(p["y"] for p in v)   
        for p in v:
            p["y"] = round((float(p["y"]) - float(min_y)), 2)                       
        
        lines.append({
            "symbol" : symbol,
            "color"  : SYMBOL_COLORS[symbol],
            "series" : v
        })
     
    return  grouped_log, lines

TRADING_INDEX = 0

def update_symbols_day_prices_test_ui():  # core function        
    log_data = load_test_log()    
    new_log_data = {}
    lines = []        
    #for symbol in log_data:
    symbol = "AAPL"    
    # for html data
    trading_log = []
    # for line chart data
    v = []        

    items = log_data[symbol]["items"]
    new_items = []
    for item in items:
        timestamp = item["timestamp"]        
        timestamp = timestamp.split(" ")[1]
        action = item["action"]
        notes =  item["notes"]
        node = item["node"]
        mv_change = round(float(item["price_change($)"]), 2)
        mv = round(float(item["mv"]), 2)
        qty = int(item["qty"])
        new_item = {
            "time" : timestamp,
            "symbol" : item["symbol"], 
            "price" : round(float(item["price_close"]), 2), 
            "qty" : qty,
            "mv" : mv,
            "mv_ref" : round(float(item["price_ref"]), 2),
            "mv_change($)" : mv_change,
            "cost" : round(float(item["cost"]), 2),
            "pnl" : round(float(item["pnl"]), 2),
            "pct" : round(float(item["pct"]), 2),
            "total_pnl" : round(float(item["total_pnl"]), 2),
            "action" : action,
            "notes" : notes,
            "trade" : node
        }                        
        new_items.append(new_item)
        if action == "sell" or action == "buy":
            node = {
                "icon": ACTION_ICONS[action],
                "notes" : notes 
            }    
        time_price = {
            "x" : timestamp,
            "y" : mv,
            "z" : qty,
            "node" : node
        }

        v.append(time_price)            
        print (f"v: {v}")

    #if len(v) == 1:
    #    min_y = 0
    #else:
    min_y = min(p["y"] for p in v)   
    for p in v:
        p["y"] = (p["y"] - min_y)             
    #print (f"min y: {min_y}")
        

    new_log_data[symbol] = {
        "symbol" : symbol,
        "colors" : SYMBOL_COLORS[symbol],
        "items" : new_items
    }
    #print (f"series:,  {v}")
    lines.append({
        "symbol" : symbol,
        "color"  : SYMBOL_COLORS[symbol],
        "series" : v
    })

    return  new_log_data, lines    #save_today_log(grouped_log)

def update_symbols_day_prices_test():  # core function        

    grouped = {}
    grouped_log = {}
    
    grouped = load_test_log()
    symbol = "AAPL"
    trading_log = []
    start = 0
    lastTrade = None
    last_ref = 0
    last_cost = 0
    last_mv = 0
    if len(grouped) >0:
        trading_log = grouped[symbol]["items"]            
        start = len(trading_log)                        
        lastTrade = trading_log[-1]             
        last_ref = lastTrade["price_ref"]
        last_cost = lastTrade["cost"]  # same as postion.qty
        last_mv = lastTrade["mv"]

    prices = get_alpaca_prices_test(symbol)        
    test_price = prices[0]["price_close"]
    test_qty = round(2000/test_price)    
    recent_prices = prices[:(start+1)]
    recent_price = recent_prices[-1]            
    current_price = float(recent_price["price_close"])            
    current_qty = test_qty
    #current_qty = 2000/current_price    
    current_mv = current_qty*current_price
    recent_price["mv"] = current_mv         
    recent_price["price_ref"] = current_mv
    if last_mv==0:
        recent_price["price_change($)"] = 0
    else:
        recent_price["price_change($)"] = current_mv - last_mv
             
    if start < 5:
        recent = recent_prices[-5:]
        current_ref = min(p["price_close"] for p in recent) * current_qty                                                           
        recent_price["price_ref"] = current_ref
    if start>=5:  # start check if trade        
        if last_cost == 0:  # buy only
            current_ref = last_ref
            current_qty = round(2000/current_price)
            if (current_mv - current_ref) > 3: # start up from lower
                acction = "buy"
                current_mv = current_price * current_qty
                exitTrade(acction, current_mv)
                recent_price["action"] = acction
                recent_price["notes"] = f"{acction}: mv:{round(current_mv, 2)} - ref:{round(current_ref, 2)} = {round((current_mv-current_ref),2)}  > 3$ "                        
                recent_price["pnl"] = 0  #buy now, no pnl                
                recent_price["cost"] = current_mv
                recent_price["mv"] = current_mv
                recent_price["qty"] = current_qty                
                recent_price["price_ref"] = current_mv
            else:
                action = "skip"
                recent_price["cost"] = last_cost
                recent_price["action"] = action
                recent_price["notes"] = f"Skip: mv={round(current_mv, 2)} with ref={round(current_ref, 2)} in range 3$ "                    
                if (current_mv < current_ref) <3:
                    current_ref = current_mv  # move down current_ref
                    recent_price["price_ref"] = current_ref

        else: # sell only
            #current_qty = round(2000/current_price)
            current_ref = last_ref
            #recent_price["price_ref"] = current_ref
            if (current_mv - current_ref) < -3:
                acction = "sell"                    
                exitTrade(acction, current_qty)
                current_mv = current_qty*current_price
                current_ref = current_mv
                recent_price["action"] = acction
                recent_price["notes"] = f"{acction}: mv:{round(current_mv,2)} < ref:{round(current_ref,2)} = {round(current_mv-current_ref,2)} to take win {round(last_cost, 2)}$ "                       
                pnl = current_mv - last_cost
                recent_price["pnl"] = pnl
                recent_price["cost"] = 0
                recent_price["qty"] = current_qty
                recent_price["mv"] = current_mv
                recent_price["price_ref"] = current_ref                         
            else:
                acction = "hold"
                recent_price["action"] = acction
                recent_price["notes"] = f"Hold: mv:{round(current_mv,2)} - ref:{round(current_ref,2)} = {round((current_mv-current_ref), 2)} in range 3$"                    
                recent_price["cost"] = last_cost
                recent_price["mv"] = current_mv                    
                recent_price["qty"] = current_qty 
                if (current_mv > current_ref): # move up current_ref
                    current_ref = current_mv            
                    recent_price["price_re"] = current_ref

    trading_log.append(recent_price)
    grouped_log[symbol] = {
        "colors" : SYMBOL_COLORS[symbol], 
        "items" : trading_log }

    save_test_log(grouped_log)            

    return update_symbols_day_prices_test_ui()
    """
    trading_log.append(recent_price)
    grouped_log[symbol] = {
        "colors" : SYMBOL_COLORS[symbol], 
        "items" : trading_log }

    save_test_log(grouped_log)            
    lines = []
    items = grouped_log[symbol]["items"]
    v = []
    for item in items:        
        timestamp = item["timestamp"]        
        timestamp = timestamp.split(" ")[1]
        action = item["action"]
        notes =  item["notes"]
        node = None
        if action == "sell" or action == "buy":
            node = {
                "icon": ACTION_ICONS[action],
                "notes" : notes 
            }
        time_price = {
            "x" : timestamp,
            "y" : item["mv"],
            "z" : item["cost"],
            "node" : node
        }
        v.append(time_price)            
    min_y = min(p["y"] for p in v)   
    for p in v:
        p["y"] = round((float(p["y"]) - float(min_y)), 2)                       
    
    lines.append({
        "symbol" : symbol,
        "color"  : SYMBOL_COLORS[symbol],
        "series" : v
    })
     
    return  grouped_log, lines    #save_today_log(grouped_log)
    """

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